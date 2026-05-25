from typing import Any

# Stages emitted during chat (syntax only) — used to filter logs in the UI
CHAT_PROGRESS_STAGES = frozenset({
    "generating",
    "generated",
    "syntax_check",
    "syntax_failed",
    "syntax_ok",
    "correcting_syntax",
    "complete",
})


def format_progress_line(stage: str, payload: dict[str, Any]) -> str | None:
    if stage == "generating":
        return "Generating Gorgias response..."
    if stage == "generated":
        return "Response received from model."
    if stage == "syntax_check":
        return f"Checking syntax (attempt {payload.get('attempt', 1)})..."
    if stage == "syntax_failed":
        n = len(payload.get("errors", []))
        return f"Syntax errors found ({n}). Asking model to fix..."
    if stage == "syntax_ok":
        return "Syntax valid."
    if stage == "correcting_syntax":
        return f"Correcting syntax (attempt {payload.get('attempt', 1)})..."
    if stage == "complete":
        return "Done."
    return None


def format_chat_progress_line(stage: str, payload: dict[str, Any]) -> str | None:
    """Chat-only logs (no cloud / semantic stages)."""
    if stage not in CHAT_PROGRESS_STAGES:
        return None
    return format_progress_line(stage, payload)


USER_SYNTAX_STAGES = frozenset({
    "syntax_check",
    "syntax_failed",
    "syntax_ok",
    "syntax_error_detail",
    "complete",
})


def format_user_syntax_progress_line(stage: str, payload: dict[str, Any]) -> str | None:
    """Single-pass syntax check when the user saves manual edits."""
    if stage == "syntax_check":
        return "Checking syntax..."
    if stage == "syntax_failed":
        n = len(payload.get("errors", []))
        return f"Syntax errors found ({n})."
    if stage == "syntax_error_detail":
        return f"  - {payload.get('message', payload)}"
    if stage == "syntax_ok":
        return "Syntax valid."
    if stage == "complete":
        return "Done."
    return None
