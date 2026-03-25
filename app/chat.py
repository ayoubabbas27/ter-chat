import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient, ChatCompletionOutput
import models
from utils import _load_json_content
from prompts import GORGIAS_SPEC
import copy

load_dotenv()
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))
DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct:cheapest" # "Qwen/Qwen3-4B-Instruct-2507:cheapest"

def generate_system_prompt():
    return (
        "You are an expert in the Gorgias argumentation framework. Your task is to translate a natural language decision scenario into valid Gorgias code using ONLY this spec:\n"
        f"{GORGIAS_SPEC}\n"
        "Response MUST ONLY be valid JSON. No explanations outside JSON:\n"
        '- "message": Brief technical summary of rules created. List rule types and key structure (1 sentence). Examples: "Default fly rule r1(X) defeated by penguin conflict c1(X)." or "Preference pr1(X) between r_low(X) and r_high(X) over cash condition."\n'
        '- "code": Complete and Syntaxically correct Gorgias Prolog code.'
    )

def _extract_completion_text(completion: ChatCompletionOutput) -> models.GorgiasUserOutput:

    message = completion.choices[0].message
    content = getattr(message, "content", None)

    if not content:
        raise ValueError("No content in model response")
    
    parsed = _load_json_content(content)

    if "message" not in parsed or "code" not in parsed:
        raise ValueError("Response missing required keys: 'message' or 'code'")
    
    response_message = str(parsed["message"]).strip()
    response_code_lines = str(parsed["code"]).strip().split("\\n")
    
    return models.GorgiasUserOutput(message=response_message, code_lines=response_code_lines)


def syntax_check(code_lines: list[str]) -> bool:
    return True

def nl_to_gorgias_with_history(messages) -> models.GorgiasUserOutput:    
    conversation: list[dict[str, str]] = copy.deepcopy(messages)
    
    while True:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=conversation,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "GorgiasOutput",
                    "schema": models.GorgiasChatOutput.model_json_schema(),
                    "strict": True,
                },
            }
        )
        result = _extract_completion_text(completion)

        if syntax_check(result.code_lines):
            return result

        correction_prompt = "The previous Gorgias code had syntax errors. Correct the code and return only valid JSON as before."
        conversation.append({"role": "user", "content": correction_prompt})
