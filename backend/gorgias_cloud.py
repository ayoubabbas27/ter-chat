import json
import os
import tempfile
import uuid
from typing import Any

import requests
import urllib3

from .env import load_project_env

load_project_env()
urllib3.disable_warnings()

DEFAULT_BASE = "http://aiasvm1.amcl.tuc.gr:8085"


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


def run_query_on_cloud(code: str, query: str, facts: list[str]) -> dict[str, Any]:
    """
    Upload program and run a single Gorgias query with user-provided facts.
    Returns a JSON-serializable result for the API/UI.
    """
    details: dict[str, Any] = {"base_url": _cloud_base_url(), "steps": {}, "query": query, "facts": facts}

    if not _cloud_configured():
        return {
            "ok": False,
            "message": "Gorgias Cloud credentials missing in backend/.env",
            "details": details,
        }

    uid = uuid.uuid4().hex[:8]
    project = f"ter_{uid}"
    filename = f"policy_{uid}.pl"
    details["project"] = project
    details["filename"] = filename

    try:
        create = _request("post", f"/createProject?project_name={project}")
        details["steps"]["createProject"] = {
            "status_code": create.status_code,
            "body": _response_body(create),
        }
        if create.status_code != 200:
            return {"ok": False, "message": "Cloud project creation failed", "details": details}

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
            return {"ok": False, "message": "Cloud rejected the uploaded program", "details": details}

        status_code, result = _run_gorgias_query(project, filename, query, facts)
        payload = result["response"]
        details["steps"]["GorgiasQuery"] = {
            "status_code": status_code,
            "request": result["request"],
            "body": payload,
        }

        if status_code != 200:
            return {"ok": False, "message": f"GorgiasQuery HTTP {status_code}", "details": details, "response": payload}

        if isinstance(payload, dict) and payload.get("hasError"):
            return {
                "ok": False,
                "message": payload.get("errorMsg") or "Gorgias execution error",
                "details": details,
                "response": payload,
            }

        if isinstance(payload, dict) and payload.get("hasResult"):
            return {
                "ok": True,
                "message": f"Query '{query}' succeeded with facts {facts}",
                "details": details,
                "response": payload,
            }

        return {
            "ok": False,
            "message": f"Query '{query}' with facts {facts} produced no result",
            "details": details,
            "response": payload,
        }

    except requests.ConnectionError:
        return {"ok": False, "message": "Gorgias Cloud server unreachable", "details": details}
    except Exception as exc:
        return {"ok": False, "message": str(exc), "details": details}
    finally:
        for path in (
            f"/deleteFile?filename={filename}&project={project}",
            f"/deleteProject?project={project}",
        ):
            try:
                _request("post", path)
            except Exception:
                pass
