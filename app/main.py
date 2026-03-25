from chat import generate_system_prompt, nl_to_gorgias_with_history
import json
from utils import display_code

def main():
    print("====== Gorgias Chatbot Started ======")
    print("Type 'quit' or 'exit' to stop\n")

    system_prompt = generate_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

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
            result = nl_to_gorgias_with_history(messages)
            print(f"\n==> Assistant: {result.message}\n")
            display_code(result.code_lines)
            print("\n"+"-" * 60)
            assistant_content = json.dumps({"message": result.message, "code": "\n".join(result.code_lines)})
            messages.append({"role": "assistant", "content": assistant_content})
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Try rephrasing your request.\n")

if __name__ == "__main__":
    main()
