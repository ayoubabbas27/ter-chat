import json

try:
    from .chat import generate_gorgias_chat
    from .progress import format_chat_progress_line
    from .utils import display_code
except ImportError:
    from chat import generate_gorgias_chat
    from progress import format_chat_progress_line
    from utils import display_code


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
                line = format_chat_progress_line(stage, payload)
                if line:
                    print(f"[log] {line}")

            result = generate_gorgias_chat(messages, progress_callback=on_progress)
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
