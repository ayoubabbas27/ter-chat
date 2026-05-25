from typing import Any


def format_test_context_block(tests: list[dict[str, Any]]) -> str:
    if not tests:
        return ""
    lines = ["## Test results attached to this message"]
    for index, test in enumerate(tests, start=1):
        status = "succeeded" if test.get("ok") else "failed"
        lines.append(f"\n### Attached test {index} ({status})")
        if test.get("at"):
            lines.append(f"- When: {test['at']}")
        lines.append(f"- Query: {test.get('query') or '(none)'}")
        facts = test.get("facts") or []
        lines.append(f"- Facts: {', '.join(facts) if facts else '(none)'}")
        if test.get("message"):
            lines.append(f"- Outcome: {test['message']}")
        code = (test.get("code") or "").strip()
        if code:
            lines.append("- Program used in that test:")
            lines.append(f"```prolog\n{code}\n```")
        explanations = (test.get("explanations") or "").strip()
        if explanations:
            lines.append("- Gorgias explanations:")
            lines.append(explanations)
    lines.append(
        "\nThe user may ask you to explain this test, compare it to the current editor program, "
        "or reason about differences. The current editor program is listed separately below."
    )
    return "\n".join(lines)
