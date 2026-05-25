import json

from chat import nl_to_gorgias_with_history
from utils import display_code


def _print_cloud_details(details: dict) -> None:
    print("[log] --- Gorgias Cloud response ---")
    if details.get("all_dynamic_facts"):
        print(f"[log]   all :-dynamic facts: {details['all_dynamic_facts']}")
    if win := details.get("winning_attempt"):
        print(f"[log]   passed: {win.get('label')} → query={win.get('query')}, facts={win.get('facts')}")
    for step_name, step in details.get("steps", {}).items():
        print(f"[log]   [{step_name}] HTTP {step.get('status_code', '?')}")
        body = step.get("body")
        if body is not None:
            formatted = json.dumps(body, indent=2, ensure_ascii=False)
            for line in formatted.splitlines():
                print(f"[log]     {line}")
    for attempt in details.get("attempts", []):
        print(
            f"[log]   try: {attempt.get('label')} | query={attempt.get('query')} "
            f"| facts={attempt.get('facts')} | hasResult={attempt.get('hasResult')} "
            f"| hasError={attempt.get('hasError')}"
        )
        if attempt.get("errorMsg"):
            print(f"[log]        errorMsg: {attempt['errorMsg']}")
    print("[log] --- end cloud response ---")


def _format_log(stage: str, payload: dict) -> str | None:
    if stage == "generating":
        return "Generating Gorgias code..."
    if stage == "generated":
        return "Initial code received from model."
    if stage == "syntax_check":
        return f"Checking syntax (attempt {payload.get('attempt', 1)})..."
    if stage == "syntax_failed":
        n = len(payload.get("errors", []))
        return f"Syntax errors found ({n}). Asking model to fix..."
    if stage == "syntax_ok":
        return "Syntax valid."
    if stage == "correcting_syntax":
        return f"Correcting syntax (attempt {payload.get('attempt', 1)})..."
    if stage == "semantic_check":
        return f"Checking semantics (attempt {payload.get('attempt', 1)})..."
    if stage == "semantic_local_ok":
        return "Local semantic rules OK (S1–S4)."
    if stage == "semantic_failed":
        source = payload.get("source", "local")
        return f"Semantic check failed ({source}). Asking model to fix..."
    if stage == "cloud_check":
        return "Validating on Gorgias Cloud..."
    if stage == "cloud_failed":
        return f"Cloud validation failed: {payload.get('message', '')}"
    if stage == "cloud_ok":
        return payload.get("message", "Cloud validation passed.")
    if stage == "semantic_ok":
        return "All semantic checks passed."
    if stage == "correcting_semantic":
        n = payload.get("attempt", 1)
        max_n = payload.get("max_attempts", "?")
        return f"Asking model to fix code (semantic retry {n}/{max_n})..."
    if stage == "complete":
        return "Done."
    return None


def main():
    print("====== Gorgias Chatbot Started ======")
    print("Type 'quit' or 'exit' to stop\n")

    messages: list[dict] = []

    while True:
        user_input = input("==> You: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            print("====== Gorgias Chatbot Closed ======")
            break

        if not user_input:
            print("Please enter a natural language description.\n")
            continue

        messages.append({"role": "user", "content": user_input})

        try:

            def on_progress(stage: str, payload: dict) -> None:
                line = _format_log(stage, payload)
                if line:
                    print(f"[log] {line}")
                if stage in ("cloud_failed", "cloud_ok") and payload.get("details"):
                    _print_cloud_details(payload["details"])

            result = nl_to_gorgias_with_history(messages, progress_callback=on_progress)
            print(f"\n==> Assistant: {result.message}\n")
            if result.code_lines:
                display_code(result.code_lines)
            print("\n" + "-" * 60)
            assistant_content = json.dumps({
                "message": result.message,
                "code": "\n".join(result.code_lines),
            })
            messages.append({"role": "assistant", "content": assistant_content})
        except Exception as e:
            print(f"Error: {e}")
            print("Try rephrasing your request.\n")


if __name__ == "__main__":
    main()
