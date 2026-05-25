import re

from lark import Token as LarkToken
from lark import Tree

from gorgias_syntax import check_syntax


def _term_repr(node) -> str:
    if isinstance(node, LarkToken):
        return str(node)
    if node.data in ("atom", "variable", "number", "wildcard"):
        return str(node.children[0]) if node.children else "_"
    if node.data == "compound":
        return f"{node.children[0]}({', '.join(_term_repr(c) for c in node.children[1:])})"
    return repr(node)


def _extract_complements(tree: Tree) -> list[tuple[str, str]]:
    pairs = []
    for clause in tree.children:
        inner = clause.children[0]
        if inner.data != "complement_decl":
            continue
        terms = [c for c in inner.children if isinstance(c, Tree)]
        if len(terms) >= 2:
            pairs.append((_term_repr(terms[0]), _term_repr(terms[1])))
    return pairs


def _extract_rule_ids(tree: Tree) -> set[str]:
    ids: set[str] = set()
    for clause in tree.children:
        inner = clause.children[0]
        if inner.data == "rule_decl":
            ids.add(str(inner.children[0]))
    return ids


def _extract_prefer_refs(tree: Tree) -> list[tuple[str, str, str]]:
    result = []
    for clause in tree.children:
        inner = clause.children[0]
        if inner.data != "rule_decl":
            continue
        rule_id = str(inner.children[0])
        conclusion = inner.children[1]
        if (
            isinstance(conclusion, Tree)
            and conclusion.data == "compound"
            and str(conclusion.children[0]) == "prefer"
            and len(conclusion.children) == 3
        ):
            result.append((
                rule_id,
                _term_repr(conclusion.children[1]),
                _term_repr(conclusion.children[2]),
            ))
    return result


def _rule_level(rule_id: str) -> str:
    match = re.match(r"^([rpc])", rule_id)
    return match.group(1) if match else "?"


def check_gorgias_requirement(tree: Tree) -> list[dict]:
    """Return semantic issues (empty list = valid). Checks S1–S4."""
    issues: list[dict] = []
    rule_ids = _extract_rule_ids(tree)
    prefer_refs = _extract_prefer_refs(tree)
    prefer_map = {rule_id: (a, b) for rule_id, a, b in prefer_refs}

    comp_pairs = _extract_complements(tree)
    declared = set(comp_pairs)
    for a, b in comp_pairs:
        if (b, a) not in declared:
            issues.append({
                "check": "S1",
                "rule": "complement",
                "message": (
                    f"complement({a},{b}) is declared but complement({b},{a}) is missing. "
                    "Complements must always be declared in both directions."
                ),
            })

    for rule_id, a, b in prefer_refs:
        for ref in (a, b):
            if ref not in rule_ids:
                issues.append({
                    "check": "S2",
                    "rule": rule_id,
                    "message": f"prefer({a},{b}): '{ref}' is not a declared rule id.",
                })

    for rule_id, a, b in prefer_refs:
        level = _rule_level(rule_id)
        a_level = _rule_level(a) if a in rule_ids else "?"
        b_level = _rule_level(b) if b in rule_ids else "?"
        if level == "p":
            for ref, ref_level in ((a, a_level), (b, b_level)):
                if ref_level not in ("r", "?"):
                    issues.append({
                        "check": "S3",
                        "rule": rule_id,
                        "message": (
                            f"prefer({a},{b}): '{ref}' is level '{ref_level}'. "
                            "p-rules must only prefer r-rules."
                        ),
                    })
        elif level == "c":
            for ref, ref_level in ((a, a_level), (b, b_level)):
                if ref_level == "r":
                    issues.append({
                        "check": "S3",
                        "rule": rule_id,
                        "message": (
                            f"prefer({a},{b}): '{ref}' is an r-rule. "
                            "c-rules must only prefer p-rules or c-rules."
                        ),
                    })
            if (a_level == "p" and b_level == "c") or (a_level == "c" and b_level == "p"):
                issues.append({
                    "check": "S3",
                    "rule": rule_id,
                    "message": f"prefer({a},{b}): cannot mix p and c levels ('{a}'={a_level}, '{b}'={b_level}).",
                })

    for rule_id, a, b in prefer_refs:
        if _rule_level(rule_id) != "c":
            continue
        if a not in prefer_map or b not in prefer_map:
            continue
        a_pair, b_pair = prefer_map[a], prefer_map[b]
        if set(a_pair) != set(b_pair):
            issues.append({
                "check": "S4",
                "rule": rule_id,
                "message": (
                    f"prefer({a},{b}): different pairs — {a}=prefer{a_pair} vs {b}=prefer{b_pair}."
                ),
            })
        elif a_pair == b_pair:
            issues.append({
                "check": "S4",
                "rule": rule_id,
                "message": f"prefer({a},{b}): same direction — not a genuine conflict.",
            })

    return issues


def check_semantic(code: str) -> tuple[bool, list[dict], Tree | None]:
    """Parse and run S1–S4 semantic checks. Returns (valid, issues, tree)."""
    syntax_ok, syntax_errors, tree = check_syntax(code)
    if not syntax_ok:
        return False, [{"check": "syntax", "rule": "-", "message": e["message"]} for e in syntax_errors], None
    issues = check_gorgias_requirement(tree)
    return len(issues) == 0, issues, tree
