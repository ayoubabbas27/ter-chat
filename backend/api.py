import asyncio
import json
from queue import Empty, Queue
from threading import Thread
from typing import Any

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .chat import generate_gorgias_chat, get_anthropic_model, validate_user_code_syntax
from .db import create_session, delete_session, get_session, init_db, list_sessions, update_session
from .gorgias_cloud import run_query_on_cloud
from .progress import format_chat_progress_line, format_user_syntax_progress_line


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Gorgias Chatbot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str
    test_context: list[dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    code: str = ""


class CodeOnlyRequest(BaseModel):
    code: str


class RunRequest(BaseModel):
    code: str
    query: str
    facts: list[str] = Field(default_factory=list)


class SessionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=56)


class SessionUpdateRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    code: str = ""
    input_draft: str = ""
    test_facts: list[str] = Field(default_factory=list)
    test_query: str = ""
    test_history: list[dict[str, Any]] = Field(default_factory=list)
    active_tab: str = "code"


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_chat(messages: list[dict], queue: Queue, current_code: str = "") -> None:
    def on_progress(stage: str, payload: dict[str, Any]) -> None:
        line = format_chat_progress_line(stage, payload)
        queue.put({
            "type": "progress",
            "stage": stage,
            "message": line,
            "payload": payload,
        })

    try:
        result = generate_gorgias_chat(
            messages,
            progress_callback=on_progress,
            current_code=current_code,
        )
        code = "\n".join(result.code_lines)
        assistant_content = json.dumps({"message": result.message, "code": code})
        queue.put({
            "type": "done",
            "message": result.message,
            "code": code,
            "assistant_content": assistant_content,
        })
    except Exception as exc:
        queue.put({"type": "error", "message": str(exc)})
    finally:
        queue.put(None)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "anthropic_model": get_anthropic_model()}


@app.get("/api/sessions")
def sessions_list() -> dict[str, Any]:
    return {"sessions": list_sessions()}


@app.post("/api/sessions")
def sessions_create(request: SessionCreateRequest) -> dict[str, Any]:
    try:
        return create_session(request.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sessions/{session_id}")
def sessions_get(session_id: str) -> dict[str, Any]:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.put("/api/sessions/{session_id}")
def sessions_update(session_id: str, request: SessionUpdateRequest) -> dict[str, Any]:
    session = update_session(session_id, request.model_dump())
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/sessions/{session_id}")
def sessions_delete(session_id: str) -> dict[str, str]:
    if not delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "id": session_id}


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    messages = [m.model_dump() for m in request.messages]
    current_code = request.code.strip()

    async def event_stream():
        queue: Queue = Queue()
        thread = Thread(target=_run_chat, args=(messages, queue, current_code), daemon=True)
        thread.start()

        while True:
            try:
                item = await asyncio.to_thread(queue.get, timeout=0.25)
            except Empty:
                yield _sse("ping", {})
                continue

            if item is None:
                yield _sse("end", {})
                break

            event_type = item.pop("type", "progress")
            if event_type == "progress" and not item.get("message"):
                continue
            yield _sse(event_type, item)

        thread.join(timeout=1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _run_user_syntax_validation(code: str, queue: Queue) -> None:
    def on_progress(stage: str, payload: dict[str, Any]) -> None:
        line = format_user_syntax_progress_line(stage, payload)
        if line:
            queue.put({
                "type": "progress",
                "stage": stage,
                "message": line,
                "payload": payload,
            })

    try:
        ok, errors = validate_user_code_syntax(code, progress_callback=on_progress)
        if ok:
            queue.put({
                "type": "done",
                "ok": True,
                "message": "Syntax valid. Code saved.",
            })
        else:
            summary = "\n".join(e.get("message", str(e)) for e in errors)
            queue.put({
                "type": "done",
                "ok": False,
                "message": "Syntax invalid. Fix the errors in the logs and try Save again.",
                "errors": errors,
                "summary": summary,
            })
    except Exception as exc:
        queue.put({"type": "error", "message": str(exc)})
    finally:
        queue.put(None)


@app.post("/api/code/validate-syntax/stream")
async def validate_syntax_stream(request: CodeOnlyRequest) -> StreamingResponse:
    code = request.code.strip()

    async def event_stream():
        queue: Queue = Queue()
        thread = Thread(target=_run_user_syntax_validation, args=(code, queue), daemon=True)
        thread.start()

        while True:
            try:
                item = await asyncio.to_thread(queue.get, timeout=0.25)
            except Empty:
                yield _sse("ping", {})
                continue

            if item is None:
                yield _sse("end", {})
                break

            event_type = item.pop("type", "progress")
            if event_type == "progress" and not item.get("message"):
                continue
            yield _sse(event_type, item)

        thread.join(timeout=1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/run")
def run_query(request: RunRequest) -> dict[str, Any]:
    """Run a user-provided query + facts on Gorgias Cloud."""
    return run_query_on_cloud(
        request.code.strip(),
        request.query.strip(),
        [f.strip() for f in request.facts if f.strip()],
    )
