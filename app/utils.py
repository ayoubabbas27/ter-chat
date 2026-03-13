import json
import re

def _load_json_content(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))

def display_code(code_lines: list[str]) -> None:
    print("# Code:")
    for line in code_lines:
        print(line)