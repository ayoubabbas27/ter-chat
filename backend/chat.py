import json
import os
from typing import Any, Callable

import anthropic

from . import models
from .env import load_project_env
from .gorgias_syntax import check_syntax
from .prompts import build_conversation_context, generate_system_prompt
from .utils import _load_json_content

load_project_env()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


def get_anthropic_model() -> str:
    """Model id used for Anthropic API calls (from ANTHROPIC_MODEL env)."""
    return DEFAULT_MODEL


MAX_CONTEXT_MESSAGES = 12
MAX_SYNTAX_RETRIES = 5

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
    return ""


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


def _generate_response(
    messages: list[dict],
    program_code: str,
    progress_callback: ProgressCallback | None,
    *,
    syntax_errors: list[dict] | None = None,
    prior_result: models.GorgiasUserOutput | None = None,
) -> models.GorgiasUserOutput:
    """Single LLM turn: conversation + current program (+ optional syntax errors)."""
    window = _conversation_window(messages)
    user_content = build_conversation_context(window, program_code, syntax_errors)
    extra = (
        [{"role": "assistant", "content": _assistant_json(prior_result)}]
        if prior_result
        else None
    )
    _emit_progress(progress_callback, "generating")
    result = _call_llm(user_content, extra_messages=extra)
    _emit_progress(progress_callback, "generated")
    return result


def _run_syntax_loop(
    result: models.GorgiasUserOutput,
    messages: list[dict],
    progress_callback: ProgressCallback | None,
) -> models.GorgiasUserOutput:
    for attempt in range(1, MAX_SYNTAX_RETRIES + 1):
        code = _code_to_str(result)
        if not code.strip():
            _emit_progress(progress_callback, "syntax_ok")
            return result
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
        _emit_progress(
            progress_callback,
            "correcting_syntax",
            {"attempt": attempt, "max_attempts": MAX_SYNTAX_RETRIES},
        )
        result = _generate_response(
            messages,
            code,
            progress_callback,
            syntax_errors=errors,
            prior_result=result,
        )
    return result


def validate_user_code_syntax(
    code: str,
    progress_callback: ProgressCallback | None = None,
) -> tuple[bool, list[dict]]:
    """One syntax check for manually edited code (no LLM correction loop)."""
    _emit_progress(progress_callback, "syntax_check", {"attempt": 1})
    syntax_ok, errors, _ = check_syntax(code)
    if syntax_ok:
        _emit_progress(progress_callback, "syntax_ok")
        _emit_progress(progress_callback, "complete")
        return True, []

    _emit_progress(progress_callback, "syntax_failed", {"errors": errors, "attempt": 1})
    for err in errors:
        _emit_progress(progress_callback, "syntax_error_detail", err)
    return False, errors


def generate_gorgias_chat(
    messages: list[dict],
    progress_callback: ProgressCallback | None = None,
    current_code: str | None = None,
) -> models.GorgiasUserOutput:
    """LLM generation + syntax validation only. No cloud or semantic loops."""
    if current_code is None:
        current_code = _extract_latest_code(messages)
    result = _generate_response(messages, current_code, progress_callback)
    result = _run_syntax_loop(result, messages, progress_callback)
    _emit_progress(progress_callback, "complete")
    return result


# Backwards compatibility for CLI
def nl_to_gorgias_with_history(
    messages: list[dict],
    progress_callback: ProgressCallback | None = None,
) -> models.GorgiasUserOutput:
    return generate_gorgias_chat(messages, progress_callback=progress_callback)
