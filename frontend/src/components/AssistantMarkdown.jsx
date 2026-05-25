import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function parseAssistantMessage(content) {
  try {
    const parsed = JSON.parse(content);
    const text = String(parsed.message ?? "").trim();
    return text || "_No answer text returned._";
  } catch {
    return content;
  }
}

export default function AssistantMarkdown({ content }) {
  const markdown = parseAssistantMessage(content);

  return (
    <div className="chat-assistant-markdown">
      <Markdown remarkPlugins={[remarkGfm]}>{markdown}</Markdown>
    </div>
  );
}
