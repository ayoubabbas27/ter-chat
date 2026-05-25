from lark import Lark, Tree, UnexpectedCharacters, UnexpectedToken
from lark import Token as LarkToken

GRAMMAR = (
    "start: clause*\n"
    "clause: dynamic_decl | rule_decl | complement_decl | abducible_decl\n"
    "dynamic_decl: \":-\" \"dynamic\" functor_spec (\",\" functor_spec)* \".\"\n"
    "functor_spec: LNAME \"/\" UINT\n"
    "rule_decl: \"rule\" \"(\" LNAME \",\" term \",\" belief_list \")\" rule_body \".\"\n"
    "belief_list: \"[\" (term (\",\" term)*)? \"]\"\n"
    "rule_body: (\":-\" body_lit (\",\" body_lit)*)?\n"
    "body_lit: expr COMP_OP expr -> cmp_lit | expr -> plain_lit\n"
    "expr: term ARITH_OP term -> arith_expr | term\n"
    "complement_decl: \"complement\" \"(\" term \",\" term \")\" \".\"\n"
    "abducible_decl: \"abducible\" \"(\" term \",\" belief_list \")\" \".\"\n"
    "term: LNAME \"(\" term (\",\" term)* \")\" -> compound\n"
    "    | LNAME -> atom | UNAME -> variable | \"_\" -> wildcard | NUMBER -> number\n"
    "COMP_OP.5: \">=\" | \"=<\" | \">\" | \"<\" | \"=:=\" | \"=\\=\" | \"\\=\" | \"is\"\n"
    "ARITH_OP.5: \"+\" | \"-\" | \"*\" | \"/\"\n"
    "LNAME: /[a-z_][a-zA-Z0-9_]*/\n"
    "UNAME: /[A-Z][a-zA-Z0-9_]*/\n"
    "NUMBER: /[0-9]+(\\.[0-9]+)?/\n"
    "UINT: /[0-9]+/\n"
    "%ignore /\\s+/\n"
    "%ignore /%[^\\n]*/\n"
)

_parser = Lark(GRAMMAR, parser="earley", ambiguity="resolve", propagate_positions=True)


def check_syntax(code: str) -> tuple[bool, list[dict], Tree | None]:
    """Validate Gorgias syntax. Returns (valid, errors, parse_tree)."""
    try:
        tree = _parser.parse(code)
        return True, [], tree
    except UnexpectedCharacters as e:
        lines = code.split("\n")
        ctx = lines[e.line - 1] if 0 < e.line <= len(lines) else ""
        char = ctx[e.column - 1] if ctx and 0 < e.column <= len(ctx) else "?"
        exp = ", ".join(list(e.allowed)[:4]) if e.allowed else "?"
        arrow = " " * (e.column - 1) + "^"
        return False, [{
            "type": "syntax",
            "message": (
                f"Line {e.line}, col {e.column}: unexpected '{char}' — expected: {exp}\n"
                f"  {ctx}\n  {arrow}"
            ),
            "line": e.line,
            "col": e.column,
        }], None
    except UnexpectedToken as e:
        lines = code.split("\n")
        ctx = lines[e.line - 1] if 0 < e.line <= len(lines) else ""
        exp = ", ".join(list(e.expected)[:4]) if e.expected else "?"
        arrow = " " * (e.column - 1) + "^"
        return False, [{
            "type": "syntax",
            "message": (
                f"Line {e.line}, col {e.column}: unexpected token '{e.token}' — expected: {exp}\n"
                f"  {ctx}\n  {arrow}"
            ),
            "line": e.line,
            "col": e.column,
        }], None
    except Exception as e:
        return False, [{"type": "syntax", "message": str(e), "line": 0, "col": 0}], None
