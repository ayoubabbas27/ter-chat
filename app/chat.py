import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient, ChatCompletionOutput
import models
from utils import _load_json_content

load_dotenv()
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))
DEFAULT_MODEL = "Qwen/Qwen3-4B-Instruct-2507:cheapest"

GORGIAS_SPEC = """
Gorgias Syntax Spec (Prolog-based Argumentation Framework)

CORE: rule/3 defines all defeasible knowledge.
- rule(Label, Head, Body).
  - Label: unique compound term (e.g., r1(X), pr1(X,Y))
  - Head: literal (p(X) or neg(p(X)))
  - Body: [lit1, lit2], cond1, cond2
    Conditions: Prolog arithmetic (=, \\=, >=, =<, >, <, =:=, \\==)

TYPES:
- Facts: rule(f1, p(a), []).
- Rules: rule(r1(X), p(X), [q(X)]).
- Conflicts: rule(c1(X), neg(p(X)), [r(X)]).
- Preferences: rule(pr1(X), prefer(r2(X), r1(X)), [context(X)]).

ABDUCIBLES: abducible(Lit, Preconditions).
QUERIES: decide(Lit). explain(Lit, Args).
HIERARCHY: Level N+1 preferences resolve conflicts from Level N.
BACKGROUND: Standard Prolog facts/rules (strict).
"""

def generate_system_prompt():
    return (
        f"You are a Gorgias Prolog expert. Convert natural language to valid Gorgias Prolog code using ONLY this spec:\n"
        f"{GORGIAS_SPEC}\n"
        "Response MUST ONLY be valid JSON. No explanations outside JSON:\n"
        # '- "message": Short, conversational response. Confirm successful conversion or explain any assumptions made.'
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

def nl_to_gorgias(nl_input: str) -> models.GorgiasUserOutput:
    system_prompt = generate_system_prompt()
    user_prompt = f"Convert to Gorgias Prolog: {nl_input}"
    
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "GorgiasOutput",
                "schema": models.GorgiasChatOutput.model_json_schema(),
                "strict": True,
            },
        }
    )

    return _extract_completion_text(completion)
