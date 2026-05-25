import { formatExplanations } from "./formatGorgias.js";

/** Short label for a test badge in the chat composer. */
export function getTestBadgeLabel(entry) {
  const query = entry.query?.trim() || "no query";
  const status = entry.ok ? "passed" : "failed";
  const time = entry.at
    ? new Date(entry.at).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";
  return time ? `Test · ${query} · ${status} · ${time}` : `Test · ${query} · ${status}`;
}

/** Snapshot sent to the API and stored on the user message. */
export function snapshotTestForChat(entry) {
  const results = entry.response?.result;
  return {
    id: entry.id,
    at: entry.at ?? "",
    ok: Boolean(entry.ok),
    query: entry.query ?? "",
    facts: Array.isArray(entry.facts) ? [...entry.facts] : [],
    message: entry.message ?? "",
    code: entry.code ?? "",
    explanations: Array.isArray(results) ? formatExplanations(results) : "",
  };
}

export function resolveTestSnapshots(testHistory, testIds) {
  const byId = new Map(testHistory.map((e) => [e.id, e]));
  return testIds
    .map((id) => byId.get(id))
    .filter(Boolean)
    .map(snapshotTestForChat);
}
