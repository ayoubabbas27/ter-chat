/** Clean Gorgias Cloud humanExplanation strings for display. */
export function cleanHumanExplanation(raw) {
  if (raw == null) return "";
  let text = String(raw).trim();

  if (
    (text.startsWith("'") && text.endsWith("'")) ||
    (text.startsWith('"') && text.endsWith('"'))
  ) {
    text = text.slice(1, -1);
  }

  text = text.replace(/\t/g, "  ");
  text = text
    .split("\n")
    .map((line) => line.replace(/ +/g, " ").trim())
    .join("\n");
  text = text.replace(/\n{3,}/g, "\n\n");

  return text.trim();
}

export function formatExplanations(results) {
  if (!Array.isArray(results) || results.length === 0) return "";

  return results
    .map((item, index) => {
      const body = cleanHumanExplanation(
        item.humanExplanation ?? item.explanationStr ?? "",
      );
      return body ? `--- Result ${index + 1} ---\n${body}` : `--- Result ${index + 1} ---\n(no explanation text)`;
    })
    .join("\n\n");
}

export function formatRawResponse(data) {
  const payload = data.response ?? data.details ?? data;
  return JSON.stringify(payload, null, 2);
}
