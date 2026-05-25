import CodeEditor from "./CodeEditor.jsx";
import ResizableSplit from "./ResizableSplit.jsx";
import TagInput from "./TagInput.jsx";
import TerminalLog from "./TerminalLog.jsx";
import { formatExplanations, formatRawResponse } from "../utils/formatGorgias.js";
import "./RightPanel.css";

const TABS = [
  { id: "code", label: "Code" },
  { id: "test", label: "Test" },
];

export default function RightPanel({
  code,
  onCodeSave,
  onCodeEditStart,
  codeEditorDisabled,
  codeSaveError,
  savingCode,
  logs,
  logActive,
  activeTab,
  onTabChange,
  onRun,
  running,
  testHistory,
  testFacts,
  onTestFactsChange,
  testQueryTags,
  onTestQueryChange,
  chatTestIds = [],
  onAddTestToChat,
}) {
  return (
    <section className="right-panel">
      <div className="right-panel-toolbar">
        <div className="right-panel-tabs" role="tablist">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              className={activeTab === tab.id ? "active" : ""}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="right-panel-body">
        {activeTab === "code" && (
          <ResizableSplit
            storageKey="ter-chatbot-terminal-height-code"
            main={
              <CodeEditor
                code={code}
                onSave={onCodeSave}
                onEditStart={onCodeEditStart}
                disabled={codeEditorDisabled}
                saving={savingCode}
                saveError={codeSaveError}
              />
            }
            bottom={<TerminalLog lines={logs} active={logActive} />}
          />
        )}

        {activeTab === "test" && (
          <div className="test-view">
            <p className="test-hint">
              Add facts and a query (Enter), then run your scenario on Gorgias Cloud.
            </p>

            <TagInput
              label="Facts"
              variant="facts"
              tags={testFacts}
              onAdd={(value) => onTestFactsChange([...testFacts, value])}
              onRemove={(index) => onTestFactsChange(testFacts.filter((_, i) => i !== index))}
              placeholder="e.g. day_off"
            />
            <TagInput
              label="Query"
              variant="query"
              tags={testQueryTags}
              single
              onAdd={(value) => onTestQueryChange([value])}
              onRemove={() => onTestQueryChange([])}
              placeholder="e.g. go_out"
            />
            <div className="test-run">
              <button
                type="button"
                className="btn-run"
                onClick={onRun}
                disabled={!code.trim() || testQueryTags.length === 0 || running}
              >
                {running ? "Running…" : "Run test"}
              </button>
              {!code.trim() && (
                <span className="test-run-hint">Add or save code in the Code tab before running a test.</span>
              )}
              {code.trim() && testQueryTags.length === 0 && !running && (
                <span className="test-run-hint">Add facts and a query before running a test.</span>
              )}
            </div>

            {testHistory.length > 0 && (
              <div className="test-history">
                <TestHistoryHeader entries={testHistory} />
                {[...testHistory].reverse().map((entry) => (
                  <ResultBlock
                    key={entry.id}
                    entry={entry}
                    inChat={chatTestIds.includes(entry.id)}
                    onAddToChat={
                      entry.kind === "run" && entry.query ? () => onAddTestToChat?.(entry.id) : null
                    }
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

function TestHistoryHeader({ entries }) {
  const passed = entries.filter((e) => e.ok).length;
  const failed = entries.length - passed;

  return (
    <div className="test-history-header">
      <h3 className="test-history-title">Test history</h3>
      <div className="test-history-stats">
        <span className="test-stat test-stat-ok">{passed} succeeded</span>
        <span className="test-stat test-stat-fail">{failed} failed</span>
      </div>
    </div>
  );
}

function ResultBlock({ entry, inChat = false, onAddToChat = null }) {
  const ok = Boolean(entry.ok);
  const results = entry.response?.result;
  const hasExplanations = Array.isArray(results) && results.length > 0;
  const status = formatEntryStatus(entry, ok);
  const time = formatEntryTime(entry);

  return (
    <div className={`result-block ${ok ? "result-ok" : "result-fail"}`}>
      <div className="result-header">
        <span className="result-status">{status}</span>
        {time && <span className="result-time">{time}</span>}
        {onAddToChat && (
          <button
            type="button"
            className={`result-add-chat ${inChat ? "is-added" : ""}`}
            onClick={onAddToChat}
            disabled={inChat}
            title={inChat ? "Already attached to your next message" : "Attach to next chat message"}
          >
            {inChat ? "In chat" : "Add to chat"}
          </button>
        )}
      </div>
      <div className="result-message">{entry.message}</div>
      {hasExplanations && (
        <details className="result-details">
          <summary>Gorgias explanations</summary>
          <pre className="result-pre result-pre-text">{formatExplanations(results)}</pre>
        </details>
      )}
      {entry.code?.trim() && (
        <details className="result-details">
          <summary>Code used</summary>
          <pre className="result-pre result-pre-code">{entry.code}</pre>
        </details>
      )}
      <details className="result-details">
        <summary>Raw response</summary>
        <pre className="result-pre result-pre-json">{formatRawResponse(entry)}</pre>
      </details>
    </div>
  );
}

function formatEntryStatus(entry, ok) {
  const label = entry.kind === "validate" ? "Validation" : "Run";
  return ok ? `${label} succeeded` : `${label} failed`;
}

function formatEntryTime(entry) {
  if (!entry.at) return "";
  return new Date(entry.at).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
