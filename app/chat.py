import os
from typing import Any, Callable
from dotenv import load_dotenv
from huggingface_hub import InferenceClient, ChatCompletionOutput
import models
from utils import _load_json_content
from prompts import GORGIAS_CORRECTION_TEMPLATE, GORGIAS_SPEC_2, build_code_correction_prompt, build_intent_extraction_prompt

load_dotenv()
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))
DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct:cheapest" # "Qwen/Qwen3-4B-Instruct-2507:cheapest"
INTENT_CONFIDENCE_THRESHOLD = 0.70
ProgressCallback = Callable[[str, dict[str, Any]], None]


def _emit_progress(progress_callback: ProgressCallback | None, stage: str, payload: dict[str, Any] | None = None) -> None:
    if not progress_callback:
        return

    progress_callback(stage, payload or {})

def generate_system_prompt():
    return (
        "You are an expert in the Gorgias argumentation framework. Your task is to update a syntactically correct but semantically generic baseline Gorgias program so it satisfies extracted user intents using ONLY this spec:\n"
        f"{GORGIAS_SPEC_2}\n"
        "IMPORTANT MINIMALITY RULE: The final code must satisfy ONLY the extracted user intents. Remove any unrelated or leftover baseline/template rules, facts, complements, and abducibles that are not required by the current intents.\n"
        "Do not preserve prior scenario logic unless it is directly required by the current intents.\n"
        "Response MUST ONLY be valid JSON. No explanations outside JSON:\n"
        '- "message": Brief technical summary of the FINAL GENERATED CODE ONLY (1 sentence). Describe the visible rule structure in the final code and why it captures the intent. Do NOT mention removed/old/template code or revision history.\n'
        '- "code": Complete, Syntaxically and Semantically correct Gorgias Prolog code.'
    )


def generate_intent_extractor_system_prompt():
    return build_intent_extraction_prompt()

def _extract_completion_text(completion: ChatCompletionOutput) -> models.GorgiasUserOutput:

    message = completion.choices[0].message
    content = getattr(message, "content", None)

    if not content:
        raise ValueError("No content in model response")
    
    parsed = _load_json_content(content)

    if "message" not in parsed or "code" not in parsed:
        raise ValueError("Response missing required keys: 'message' or 'code'")
    
    response_message = str(parsed["message"]).strip()
    response_code_lines = str(parsed["code"]).strip().splitlines()
    
    return models.GorgiasUserOutput(message=response_message, code_lines=response_code_lines)


def _extract_intent_result(completion: ChatCompletionOutput) -> models.GorgiasIntentExtractionOutput:
    message = completion.choices[0].message
    content = getattr(message, "content", None)

    if not content:
        raise ValueError("No content in intent extraction response")

    parsed = _load_json_content(content)

    if "confidence" not in parsed or "intents" not in parsed:
        raise ValueError("Response missing required keys: 'confidence' or 'intents'")

    confidence = float(parsed["confidence"])
    intents = [str(intent).strip() for intent in parsed["intents"] if str(intent).strip()]

    return models.GorgiasIntentExtractionOutput(confidence=confidence, intents=intents)


def _extract_latest_baseline_code(messages) -> str:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue

        content = message.get("content", "")
        parsed = None
        try:
            parsed = _load_json_content(content)
        except Exception:
            continue

        code = parsed.get("code") if isinstance(parsed, dict) else None
        if isinstance(code, str) and code.strip():
            return code.strip()

    return GORGIAS_CORRECTION_TEMPLATE.strip()


def syntax_check(code_lines: list[str]) -> bool:
    return True


def extract_user_intents_with_history(
    messages,
    progress_callback: ProgressCallback | None = None,
) -> models.GorgiasIntentExtractionOutput:
    _emit_progress(progress_callback, "intent_extraction_started")
    conversation: list[dict[str, str]] = [message for message in messages if message.get("role") != "system"]

    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": generate_intent_extractor_system_prompt()},
            *conversation,
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "GorgiasIntentExtractionOutput",
                "schema": models.GorgiasIntentExtractionOutput.model_json_schema(),
                "strict": True,
            },
        },
    )

    intent_result = _extract_intent_result(completion)
    _emit_progress(
        progress_callback,
        "intent_extraction_completed",
        {"confidence": intent_result.confidence, "intents": intent_result.intents},
    )

    return intent_result


def correct_gorgias_from_intents(
    messages,
    intent_result: models.GorgiasIntentExtractionOutput,
    progress_callback: ProgressCallback | None = None,
) -> models.GorgiasUserOutput:
    _emit_progress(progress_callback, "code_generation_started")
    baseline_code = _extract_latest_baseline_code(messages)

    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": generate_system_prompt()},
            {"role": "user", "content": build_code_correction_prompt(intent_result.intents, intent_result.confidence, baseline_code)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "GorgiasOutput",
                "schema": models.GorgiasChatOutput.model_json_schema(),
                "strict": True,
            },
        },
    )

    result = _extract_completion_text(completion)

    if syntax_check(result.code_lines):
        _emit_progress(progress_callback, "code_generation_completed", {"retry": False})
        return result

    correction_prompt = "The previous Gorgias code had syntax errors. Correct the code and return only valid JSON as before."
    retry_completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": generate_system_prompt()},
            {"role": "user", "content": build_code_correction_prompt(intent_result.intents, intent_result.confidence, baseline_code)},
            {"role": "user", "content": correction_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "GorgiasOutput",
                "schema": models.GorgiasChatOutput.model_json_schema(),
                "strict": True,
            },
        },
    )

    retry_result = _extract_completion_text(retry_completion)
    _emit_progress(progress_callback, "code_generation_completed", {"retry": True})
    return retry_result

def nl_to_gorgias_with_history(
    messages,
    progress_callback: ProgressCallback | None = None,
) -> models.GorgiasUserOutput:
    intent_result = extract_user_intents_with_history(messages, progress_callback=progress_callback)

    if intent_result.confidence < INTENT_CONFIDENCE_THRESHOLD:
        return models.GorgiasUserOutput(
            message=(
                "I need a bit more detail before I can update the Gorgias code. "
                "Please clarify the scenario, candidate actions, and the exact preference/exception conditions "
                f"(intent confidence {intent_result.confidence:.2f} < {INTENT_CONFIDENCE_THRESHOLD:.2f})."
            ),
            code_lines=[],
        )

    return correct_gorgias_from_intents(messages, intent_result, progress_callback=progress_callback)
