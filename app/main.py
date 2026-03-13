from chat import nl_to_gorgias
import os
from utils import display_code

def main():
    print("====== Gorgias Prolog Chatbot Started ======")
    print("Type 'quit' or 'exit' to stop\n")
    
    while True:
        # Get user input
        user_input = input("==> You: ").strip()
        
        # Exit conditions
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("====== Gorgias Prolog Chatbot Closed ======")
            break
        
        if not user_input:
            print("Please enter a natural language description.\n")
            continue
        
        try:
            # Generate Gorgias code
            result = nl_to_gorgias(user_input)
            print(f"\n==> Assistant: {result.message}\n")
            display_code(result.code_lines)
            print("\n"+"-" * 60)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Try rephrasing your request.\n")

if __name__ == "__main__":
    main()
