import { useCallback, useEffect, useRef, useState } from "react";
import AssistantMarkdown from "./AssistantMarkdown.jsx";
import { getTestBadgeLabel } from "../utils/testChatContext.js";
import "./ChatPanel.css";

const SCROLL_THRESHOLD = 64;

export default function ChatPanel({
  messages,
  input,
  onInputChange,
  onSubmit,
  loading,
  error,
  anthropicModel = "",
  chatTestIds = [],
  testHistory = [],
  onRemoveChatTest,
}) {
  const scrollRef = useRef(null);
  const bottomRef = useRef(null);
  const [showScrollDown, setShowScrollDown] = useState(false);

  const canSend = Boolean(input.trim() || chatTestIds.length);

  const chatTestBadges = chatTestIds
    .map((id) => testHistory.find((e) => e.id === id))
    .filter(Boolean)
    .map((entry) => ({
      id: entry.id,
      label: getTestBadgeLabel(entry),
      ok: Boolean(entry.ok),
    }));

  const isNearBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < SCROLL_THRESHOLD;
  }, []);

  const scrollToBottom = useCallback((behavior = "smooth") => {
    bottomRef.current?.scrollIntoView({ behavior });
  }, []);

  const updateScrollButton = useCallback(() => {
    setShowScrollDown(!isNearBottom());
  }, [isNearBottom]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", updateScrollButton, { passive: true });
    return () => el.removeEventListener("scroll", updateScrollButton);
  }, [updateScrollButton]);

  useEffect(() => {
    updateScrollButton();
  }, [messages, loading, updateScrollButton]);

  useEffect(() => {
    const last = messages[messages.length - 1];
    const userJustSent = last?.role === "user";
    if (userJustSent || isNearBottom()) {
      scrollToBottom(userJustSent ? "smooth" : "smooth");
    }
  }, [messages, loading, isNearBottom, scrollToBottom]);

  const handleKeyDown = (event) => {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    if (loading || !canSend) return;
    event.currentTarget.form?.requestSubmit();
  };

  return (
    <section className="chat-panel">
      <div className="chat-messages-wrap">
        <div className="chat-messages" ref={scrollRef}>
          {messages.map((msg, index) =>
            msg.role === "user" ? (
              <UserMessage key={index} message={msg} />
            ) : (
              <AssistantMarkdown key={index} content={msg.content} />
            ),
          )}
          {loading && <p className="chat-assistant-loading">Working…</p>}
          <span ref={bottomRef} />
        </div>

        {showScrollDown && (
          <button
            type="button"
            className="chat-scroll-down"
            aria-label="Scroll to latest messages"
            onClick={() => scrollToBottom("smooth")}
          >
            <svg
              className="chat-scroll-down-icon"
              viewBox="0 0 24 24"
              width="18"
              height="18"
              aria-hidden="true"
            >
              <path
                fill="none"
                stroke="currentColor"
                strokeWidth="2.25"
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 9l6 6 6-6"
              />
            </svg>
          </button>
        )}
      </div>

      <form className="chat-form" onSubmit={onSubmit}>
        {chatTestBadges.length > 0 && (
          <div className="chat-test-badges" role="list" aria-label="Tests attached to next message">
            {chatTestBadges.map((badge) => (
              <span
                key={badge.id}
                className={`chat-test-badge ${badge.ok ? "chat-test-badge-ok" : "chat-test-badge-fail"}`}
                role="listitem"
              >
                {badge.label}
                <button
                  type="button"
                  className="chat-test-badge-remove"
                  aria-label={`Remove ${badge.label}`}
                  onClick={() => onRemoveChatTest(badge.id)}
                  disabled={loading}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about Gorgias or describe changes to your program…"
          rows={3}
          disabled={loading}
        />
        <div className="chat-form-actions">
          <span className="chat-model-label" title="Anthropic model used for chat">
            Model : <span className="chat-model-name">{anthropicModel || "—"}</span>
          </span>
          <button type="submit" className="chat-form-submit" disabled={loading || !canSend}>
            Send
          </button>
        </div>
      </form>

      {error && <p className="chat-error">{error}</p>}
    </section>
  );
}

function UserMessage({ message }) {
  const tests = Array.isArray(message.test_context) ? message.test_context : [];
  const hasText =
    message.content?.trim() &&
    message.content.trim() !== "Please use the attached test result(s).";

  return (
    <div className="chat-bubble chat-bubble-user">
      {tests.length > 0 && (
        <div className="chat-bubble-tests" aria-label="Attached tests">
          {tests.map((test) => (
            <span
              key={test.id}
              className={`chat-bubble-test-chip ${test.ok ? "chat-bubble-test-chip-ok" : "chat-bubble-test-chip-fail"}`}
            >
              {getTestBadgeLabel(test)}
            </span>
          ))}
        </div>
      )}
      {hasText && <div className="chat-bubble-text">{message.content}</div>}
    </div>
  );
}
