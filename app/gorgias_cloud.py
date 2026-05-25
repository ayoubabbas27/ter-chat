import json
import os
import re
import tempfile
import uuid
from typing import Any

import requests
import urllib3

from env import load_project_env

load_project_env()
urllib3.disable_warnings()

DEFAULT_BASE = "http://aiasvm1.amcl.tuc.gr:8085"

RULE_PATTERN = re.compile(
    r"rule\s*\(\s*(r\w+)\s*,\s*([a-z_][a-zA-Z0-9_]*)\s*,[^)]*\)\s*:-\s*([^.]+)\.",
    re.MULTILINE,
)


def _cloud_base_url() -> str:
    return (
        os.getenv("GORGIAS_CLOUD_BASE")
        or os.getenv("BASE")
        or DEFAULT_BASE
    ).strip().rstrip("/")


def _cloud_configured() -> bool:
    return bool(os.getenv("GORGIAS_USER") and os.getenv("GORGIAS_PASSWORD"))


def _request(method: str, path: str, **kwargs):
    kwargs.setdefault("timeout", 20)
    kwargs.setdefault("verify", False)
    url = f"{_cloud_base_url()}{path}"
    auth = (os.getenv("GORGIAS_USER", ""), os.getenv("GORGIAS_PASSWORD", ""))
    return getattr(requests, method)(url, auth=auth, **kwargs)


def _response_body(response: requests.Response, max_len: int = 8000) -> Any:
    try:
        return response.json()
    except ValueError:
        text = response.text
        return text[:max_len] + ("..." if len(text) > max_len else "")


def _extract_dynamic_facts(code: str) -> list[str]:
    match = re.search(r":-dynamic\s+([^\.]+)\.", code, re.DOTALL)
    if not match:
        return []
    facts = []
    for part in match.group(1).split(","):
        part = part.strip()
        functor_match = re.match(r"([a-z_][a-zA-Z0-9_]*)/\d+", part)
        if functor_match:
            facts.append(functor_match.group(1))
    return facts


def _body_dynamic_facts(body: str, dynamic_facts: set[str]) -> list[str]:
    found = []
    for atom in re.findall(r"\b([a-z_][a-zA-Z0-9_]*)\b", body):
        if atom in dynamic_facts and atom not in found:
            found.append(atom)
    return found


def _build_smoke_attempts(code: str) -> list[dict[str, Any]]:
    """
    Build (query, facts) pairs to try on Gorgias Cloud.
    Prefer each r-rule's conclusion with the facts from its body, then broader sets.
    """
    dynamic_facts = _extract_dynamic_facts(code)
    dynamic_set = set(dynamic_facts)
    attempts: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()

    def add_attempt(label: str, query: str, facts: list[str]) -> None:
        key = (query, tuple(facts))
        if key in seen:
            return
        seen.add(key)
        attempts.append({"label": label, "query": query, "facts": facts})

    for match in RULE_PATTERN.finditer(code):
        rule_id, conclusion, body = match.group(1), match.group(2), match.group(3)
        body_facts = _body_dynamic_facts(body, dynamic_set)
        add_attempt(f"{rule_id} ({conclusion}) with body facts", conclusion, body_facts)

    for match in RULE_PATTERN.finditer(code):
        conclusion = match.group(2)
        add_attempt(f"{conclusion} with all dynamic facts", conclusion, dynamic_facts)

    if dynamic_facts:
        for match in RULE_PATTERN.finditer(code):
            conclusion = match.group(2)
            add_attempt(f"{conclusion} with [{dynamic_facts[0]}]", conclusion, [dynamic_facts[0]])

    return attempts


def _run_gorgias_query(
    project: str,
    filename: str,
    query: str,
    facts: list[str],
) -> tuple[int, dict[str, Any]]:
    query_request = {
        "facts": facts,
        "gorgiasFiles": [f"{project}/{filename}"],
        "query": query,
        "resultSize": 10,
    }
    response = _request("post", "/GorgiasQuery", json=query_request)
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_text": response.text[:2000]}
    return response.status_code, {"request": query_request, "response": payload}


def validate_on_cloud(
    code: str,
    facts: list[str] | None = None,
    query: str | None = None,
) -> tuple[bool, list[dict], str, dict[str, Any]]:
    """
    Upload code to Gorgias Cloud and run smoke queries until one succeeds.
    Returns (valid, issues_for_llm, status_message, details_for_logging).
    """
    details: dict[str, Any] = {"base_url": _cloud_base_url(), "steps": {}, "attempts": []}

    if not _cloud_configured():
        return False, [{
            "check": "cloud",
            "rule": "-",
            "message": (
                "Gorgias Cloud credentials missing. Set GORGIAS_USER and GORGIAS_PASSWORD in .env."
            ),
        }], "Cloud credentials missing", details

    if query and facts is not None:
        smoke_attempts = [{"label": "caller-provided", "query": query, "facts": facts}]
    elif query:
        smoke_attempts = [{"label": "caller query", "query": query, "facts": _extract_dynamic_facts(code)}]
    else:
        smoke_attempts = _build_smoke_attempts(code)

    if not smoke_attempts:
        return False, [{
            "check": "cloud",
            "rule": "-",
            "message": "Could not build smoke queries (no r-rules found).",
        }], "No smoke queries available", details

    uid = uuid.uuid4().hex[:8]
    project = f"ter_{uid}"
    filename = f"policy_{uid}.pl"
    details["project"] = project
    details["filename"] = filename
    details["all_dynamic_facts"] = _extract_dynamic_facts(code)

    try:
        create = _request("post", f"/createProject?project_name={project}")
        details["steps"]["createProject"] = {
            "status_code": create.status_code,
            "body": _response_body(create),
        }
        if create.status_code != 200:
            return False, [{
                "check": "cloud",
                "rule": "-",
                "message": f"createProject failed: {create.text[:200]}",
            }], "Cloud project creation failed", details

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pl", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp.flush()
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as file_handle:
                upload = _request(
                    "post",
                    f"/addFile?project={project}&type=gorgias",
                    files={"file": (filename, file_handle, "text/plain")},
                )
        finally:
            os.unlink(tmp_path)

        details["steps"]["addFile"] = {
            "status_code": upload.status_code,
            "body": _response_body(upload),
        }
        if upload.status_code != 200:
            return False, [{
                "check": "cloud",
                "rule": "-",
                "message": f"addFile rejected the program: {upload.text[:300]}",
            }], "Cloud rejected the uploaded program", details

        for attempt in smoke_attempts:
            status_code, result = _run_gorgias_query(
                project,
                filename,
                attempt["query"],
                attempt["facts"],
            )
            payload = result["response"]
            record = {
                "label": attempt["label"],
                "query": attempt["query"],
                "facts": attempt["facts"],
                "http_status": status_code,
                "hasResult": payload.get("hasResult") if isinstance(payload, dict) else None,
                "hasError": payload.get("hasError") if isinstance(payload, dict) else None,
                "errorMsg": payload.get("errorMsg") if isinstance(payload, dict) else None,
                "result_count": len(payload.get("result", [])) if isinstance(payload, dict) else 0,
                "request": result["request"],
                "response": payload,
            }
            details["attempts"].append(record)

            if status_code != 200:
                continue
            if isinstance(payload, dict) and payload.get("hasError"):
                continue
            if isinstance(payload, dict) and payload.get("hasResult"):
                details["winning_attempt"] = record
                return True, [], (
                    f"Cloud OK — query '{attempt['query']}' with facts {attempt['facts']} "
                    f"({attempt['label']})."
                ), details

        summary_lines = [
            f"  - {a['label']}: query={a['query']}, facts={a['facts']}, "
            f"hasResult={a['hasResult']}, hasError={a['hasError']}"
            + (f", errorMsg={a['errorMsg']}" if a.get("errorMsg") else "")
            for a in details["attempts"]
        ]
        return False, [{
            "check": "cloud",
            "rule": "-",
            "message": (
                "Gorgias Cloud accepted the file but no smoke query returned a result. "
                "This often means the query goal is not derivable under the facts tried "
                "(e.g. querying stay_home when go_out is preferred with only day_off).\n"
                "Attempts:\n" + "\n".join(summary_lines)
            ),
        }], "Cloud smoke test: no query returned a result", details

    except requests.ConnectionError:
        return False, [{
            "check": "cloud",
            "rule": "-",
            "message": "Gorgias Cloud server unreachable (network/VPN required).",
        }], "Cloud server unreachable", details
    except Exception as exc:
        return False, [{
            "check": "cloud",
            "rule": "-",
            "message": str(exc),
        }], f"Cloud error: {exc}", details
    finally:
        for path in (
            f"/deleteFile?filename={filename}&project={project}",
            f"/deleteProject?project={project}",
        ):
            try:
                _request("post", path)
            except Exception:
                pass
