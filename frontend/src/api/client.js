async function consumeSseStream(response, handlers) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.split("\n");
      let event = "message";
      let dataLine = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) event = line.slice(7).trim();
        if (line.startsWith("data: ")) dataLine = line.slice(6);
      }

      if (!dataLine || event === "ping") continue;

      const data = JSON.parse(dataLine);

      if (event === "progress" && data.message) {
        handlers.onLog?.(data.message);
      } else if (event === "done") {
        handlers.onDone?.(data);
        return data;
      } else if (event === "error") {
        handlers.onError?.(data.message);
        throw new Error(data.message || "Request failed");
      }
    }
  }

  return null;
}

export async function checkHealth() {
  const response = await fetch("/api/health");
  if (!response.ok) throw new Error("API unreachable");
  return response.json();
}

export async function listSessions() {
  const response = await fetch("/api/sessions");
  if (!response.ok) throw new Error("Failed to load sessions");
  const data = await response.json();
  return data.sessions ?? [];
}

export async function createSession(name) {
  const response = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: name.trim() }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to create session");
  }
  return response.json();
}

export async function getSession(sessionId) {
  const response = await fetch(`/api/sessions/${sessionId}`);
  if (!response.ok) throw new Error("Failed to load session");
  return response.json();
}

export async function updateSession(sessionId, state) {
  const response = await fetch(`/api/sessions/${sessionId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  if (!response.ok) throw new Error("Failed to save session");
  return response.json();
}

export async function deleteSession(sessionId) {
  const response = await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
  if (response.status === 404) throw new Error("Session not found");
  if (!response.ok) throw new Error("Failed to delete session");
  return response.json();
}

/**
 * Chat: LLM + syntax validation only (SSE).
 */
export async function streamChat(messages, code = "", handlers = {}) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, code }),
  });
  return consumeSseStream(response, handlers);
}

/**
 * User manual save: single syntax check (SSE).
 */
export async function validateSyntaxStream(code, handlers = {}) {
  const response = await fetch("/api/code/validate-syntax/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  return consumeSseStream(response, handlers);
}

export async function runGorgiasQuery(code, query, facts) {
  const response = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, query, facts }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Run failed (${response.status})`);
  }
  return response.json();
}
