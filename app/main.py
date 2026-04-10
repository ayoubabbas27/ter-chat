from chat import nl_to_gorgias_with_history
import json
from utils import display_code

def main():
    print("====== Gorgias Chatbot Started ======")
    print("Type 'quit' or 'exit' to stop\n")

    messages = []

    while True:
        user_input = input("==> You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("====== Gorgias Chatbot Closed ======")
            break

        if not user_input:
            print("Please enter a natural language description.\n")
            continue

        messages.append({"role": "user", "content": f"Convert to Gorgias Prolog: {user_input}"})

        try:
            def on_progress(stage: str, payload: dict) -> None:
                if stage == "intent_extraction_started":
                    print("\n[status] Extracting intents...")
                elif stage == "intent_extraction_completed":
                    confidence = payload.get("confidence")
                    intents = payload.get("intents")
                    if isinstance(confidence, (int, float)):
                        print(f"[status] Intents extracted (confidence: {confidence:.2f})")
                    else:
                        print("[status] Intents extracted")
                    if isinstance(intents, list) and intents:
                        print("[status] Extracted intents:")
                        for index, intent in enumerate(intents, start=1):
                            print(f"  {index}. {intent}")
                elif stage == "code_generation_started":
                    print("[status] Generating Gorgias code...")

            result = nl_to_gorgias_with_history(messages, progress_callback=on_progress)
            print(f"\n==> Assistant: {result.message}\n")
            if result.code_lines:
                display_code(result.code_lines)
            print("\n"+"-" * 60)
            assistant_content = json.dumps({"message": result.message, "code": "\n".join(result.code_lines)})
            messages.append({"role": "assistant", "content": assistant_content})
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Try rephrasing your request.\n")

if __name__ == "__main__":
    main()
