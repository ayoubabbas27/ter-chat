import json
import os
from typing import Any, Callable

import anthropic

import models
from env import load_project_env
from gorgias_cloud import validate_on_cloud
from gorgias_semantic import check_semantic
from gorgias_syntax import check_syntax
from prompts import (
    GORGIAS_CORRECTION_TEMPLATE,
    build_conversation_context,
    build_semantic_correction_prompt,
    build_syntax_correction_prompt,
    generate_system_prompt,
)
from utils import _load_json_content

load_project_env()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
MAX_CONTEXT_MESSAGES = 12
MAX_SYNTAX_RETRIES = 5
MAX_SEMANTIC_RETRIES = 3

ProgressCallback = Callable[[str, dict[str, Any]], None]


def _emit_progress(
    progress_callback: ProgressCallback | None,
    stage: str,
    payload: dict[str, Any] | None = None,
) -> None:
    if progress_callback:
        progress_callback(stage, payload or {})


def _extract_latest_code(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        content = message.get("content", "")
        try:
            parsed = _load_json_content(content)
        except Exception:
            continue
        code = parsed.get("code") if isinstance(parsed, dict) else None
        if isinstance(code, str) and code.strip():
            return code.strip()
    return GORGIAS_CORRECTION_TEMPLATE.strip()


def _conversation_window(messages: list[dict]) -> list[dict]:
    conversation = [m for m in messages if m.get("role") in ("user", "assistant")]
    return conversation[-MAX_CONTEXT_MESSAGES:]


def _parse_llm_response(response: anthropic.types.Message) -> models.GorgiasUserOutput:
    text = "".join(block.text for block in response.content if block.type == "text")
    if not text.strip():
        raise ValueError("No text in model response")
    parsed = _load_json_content(text)
    if "message" not in parsed or "code" not in parsed:
        raise ValueError("Response missing required keys: 'message' or 'code'")
    return models.GorgiasUserOutput(
        message=str(parsed["message"]).strip(),
        code_lines=str(parsed["code"]).strip().splitlines(),
    )


def _call_llm(user_content: str, extra_messages: list[dict] | None = None) -> models.GorgiasUserOutput:
    api_messages: list[dict] = list(extra_messages or [])
    api_messages.append({"role": "user", "content": user_content})
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=8192,
        system=generate_system_prompt(),
        messages=api_messages,
    )
    return _parse_llm_response(response)


def _code_to_str(result: models.GorgiasUserOutput) -> str:
    return "\n".join(result.code_lines)


def _assistant_json(result: models.GorgiasUserOutput) -> str:
    return json.dumps({"message": result.message, "code": _code_to_str(result)})


def _generate_initial(
    messages: list[dict],
    current_code: str,
    progress_callback: ProgressCallback | None,
) -> models.GorgiasUserOutput:
    window = _conversation_window(messages)
    user_content = build_conversation_context(window, current_code)
    _emit_progress(progress_callback, "generating")
    result = _call_llm(user_content)
    _emit_progress(progress_callback, "generated")
    return result


def _last_user_turn(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content", "")).strip()
    return ""


def _fix_syntax(
    result: models.GorgiasUserOutput,
    errors: list[dict],
    messages: list[dict],
    progress_callback: ProgressCallback | None,
    attempt: int,
) -> models.GorgiasUserOutput:
    code = _code_to_str(result)
    _emit_progress(
        progress_callback,
        "correcting_syntax",
        {"attempt": attempt, "max_attempts": MAX_SYNTAX_RETRIES},
    )
    prompt = build_syntax_correction_prompt(code, errors)
    user_turn = _last_user_turn(messages)
    if user_turn:
        prompt += f"\n\nOriginal user request to preserve:\n{user_turn}"
    return _call_llm(
        prompt,
        extra_messages=[{"role": "assistant", "content": _assistant_json(result)}],
    )


def _fix_semantic(
    result: models.GorgiasUserOutput,
    issues: list[dict],
    messages: list[dict],
    progress_callback: ProgressCallback | None,
    attempt: int,
) -> models.GorgiasUserOutput:
    code = _code_to_str(result)
    _emit_progress(
        progress_callback,
        "correcting_semantic",
        {"attempt": attempt, "max_attempts": MAX_SEMANTIC_RETRIES},
    )
    prompt = build_semantic_correction_prompt(code, issues)
    user_turn = _last_user_turn(messages)
    if user_turn:
        prompt += f"\n\nOriginal user request to preserve:\n{user_turn}"
    return _call_llm(
        prompt,
        extra_messages=[{"role": "assistant", "content": _assistant_json(result)}],
    )


def _run_syntax_loop(
    result: models.GorgiasUserOutput,
    messages: list[dict],
    progress_callback: ProgressCallback | None,
) -> models.GorgiasUserOutput:
    for attempt in range(1, MAX_SYNTAX_RETRIES + 1):
        code = _code_to_str(result)
        _emit_progress(progress_callback, "syntax_check", {"attempt": attempt})
        syntax_ok, errors, _ = check_syntax(code)
        if syntax_ok:
            _emit_progress(progress_callback, "syntax_ok")
            return result
        _emit_progress(progress_callback, "syntax_failed", {"errors": errors, "attempt": attempt})
        if attempt >= MAX_SYNTAX_RETRIES:
            raise RuntimeError(
                f"Syntax validation failed after {MAX_SYNTAX_RETRIES} attempts.\n"
                + "\n".join(e["message"] for e in errors)
            )
        result = _fix_syntax(result, errors, messages, progress_callback, attempt)
    return result


def _run_semantic_loop(
    result: models.GorgiasUserOutput,
    messages: list[dict],
    progress_callback: ProgressCallback | None,
) -> models.GorgiasUserOutput:
    for attempt in range(1, MAX_SEMANTIC_RETRIES + 1):
        result = _run_syntax_loop(result, messages, progress_callback)

        code = _code_to_str(result)
        _emit_progress(progress_callback, "semantic_check", {"attempt": attempt})

        local_ok, local_issues, _ = check_semantic(code)
        if not local_ok:
            _emit_progress(
                progress_callback,
                "semantic_failed",
                {"issues": local_issues, "source": "local", "attempt": attempt},
            )
            if attempt >= MAX_SEMANTIC_RETRIES:
                raise RuntimeError(
                    f"Semantic validation failed after {MAX_SEMANTIC_RETRIES} attempts.\n"
                    + "\n".join(i["message"] for i in local_issues)
                )
            result = _fix_semantic(result, local_issues, messages, progress_callback, attempt)
            continue

        _emit_progress(progress_callback, "semantic_local_ok")

        _emit_progress(progress_callback, "cloud_check", {"attempt": attempt})
        cloud_ok, cloud_issues, cloud_message, cloud_details = validate_on_cloud(code)
        if cloud_ok:
            _emit_progress(
                progress_callback,
                "cloud_ok",
                {"message": cloud_message, "details": cloud_details},
            )
            _emit_progress(progress_callback, "semantic_ok")
            return result

        _emit_progress(
            progress_callback,
            "cloud_failed",
            {
                "issues": cloud_issues,
                "message": cloud_message,
                "details": cloud_details,
                "attempt": attempt,
            },
        )
        if attempt >= MAX_SEMANTIC_RETRIES:
            raise RuntimeError(
                f"Cloud semantic validation failed after {MAX_SEMANTIC_RETRIES} attempts.\n"
                + (cloud_message or "")
                + "\n"
                + "\n".join(i["message"] for i in cloud_issues)
            )
        result = _fix_semantic(result, cloud_issues, messages, progress_callback, attempt)

    return result


def nl_to_gorgias_with_history(
    messages: list[dict],
    progress_callback: ProgressCallback | None = None,
) -> models.GorgiasUserOutput:
    current_code = _extract_latest_code(messages)
    result = _generate_initial(messages, current_code, progress_callback)
    result = _run_semantic_loop(result, messages, progress_callback)
    _emit_progress(progress_callback, "complete")
    return result
