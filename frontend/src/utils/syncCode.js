/** Keep the latest assistant message's embedded code in sync with the editor. */
export function syncCodeInMessages(messages, newCode) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i].role !== "assistant") continue;
    try {
      const parsed = JSON.parse(messages[i].content);
      if (!parsed || typeof parsed !== "object") break;
      return messages.map((msg, index) =>
        index === i
          ? { ...msg, content: JSON.stringify({ ...parsed, code: newCode }) }
          : msg,
      );
    } catch {
      break;
    }
  }
  return messages;
}
