export function createTestEntry(kind, data, meta = {}) {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    kind,
    at: new Date().toISOString(),
    ...meta,
    ...data,
  };
}

export function emptySessionState() {
  return {
    messages: [],
    code: "",
    input_draft: "",
    test_facts: [],
    test_query: "",
    test_history: [],
    active_tab: "code",
  };
}
