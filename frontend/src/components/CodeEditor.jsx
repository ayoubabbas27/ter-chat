import { useEffect, useState } from "react";
import "./CodeEditor.css";

function PenIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 20h9M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z"
      />
    </svg>
  );
}

export default function CodeEditor({
  code,
  onSave,
  onEditStart,
  disabled = false,
  saving = false,
  saveError = null,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(code);
  const [snapshot, setSnapshot] = useState(code);

  useEffect(() => {
    if (!isEditing) {
      setDraft(code);
      setSnapshot(code);
    }
  }, [code, isEditing]);

  useEffect(() => {
    if (disabled && isEditing && !saving) {
      setIsEditing(false);
      setDraft(code);
    }
  }, [disabled, isEditing, code, saving]);

  const startEditing = () => {
    onEditStart?.();
    setSnapshot(code);
    setDraft(code);
    setIsEditing(true);
  };

  const handleUndo = () => {
    setDraft(snapshot);
    setIsEditing(false);
  };

  const handleSave = async () => {
    const ok = await onSave(draft);
    if (ok) {
      setIsEditing(false);
    }
  };

  const lines = (isEditing ? draft : code).split("\n");
  const isEmpty = !(isEditing ? draft : code);
  const busy = disabled || saving;

  return (
    <div className="code-editor-panel">
      <div className="code-editor-bar">
        <span className={`code-editor-mode ${isEditing ? "is-editing" : ""}`}>
          {saving
            ? "Checking syntax…"
            : isEditing
              ? "Editing — Save runs a syntax check"
              : "View only"}
        </span>
        <div className="code-editor-actions">
          {isEditing ? (
            <>
              <button
                type="button"
                className="code-editor-btn"
                onClick={handleUndo}
                disabled={busy}
              >
                Undo
              </button>
              <button
                type="button"
                className="code-editor-btn code-editor-btn-primary"
                onClick={handleSave}
                disabled={busy}
              >
                {saving ? "Saving…" : "Save"}
              </button>
            </>
          ) : (
            <button
              type="button"
              className="code-editor-btn code-editor-btn-icon"
              onClick={startEditing}
              disabled={busy}
              aria-label="Edit code"
              title="Edit code"
            >
              <PenIcon />
            </button>
          )}
        </div>
      </div>

      {saveError && isEditing && (
        <p className="code-editor-save-error" role="alert">
          {saveError}
        </p>
      )}

      <div className="code-editor" aria-label="Gorgias code">
        {isEmpty && !isEditing ? (
          <div className="code-editor-empty">
            <p>No code yet. You can write a program here, run tests, then chat about it.</p>
            <button
              type="button"
              className="code-editor-empty-btn"
              onClick={startEditing}
              disabled={busy}
            >
              Write code
            </button>
          </div>
        ) : isEditing ? (
          <>
            <div className="code-editor-gutter" aria-hidden="true">
              {lines.map((_, index) => (
                <span key={index} className="code-editor-ln">
                  {index + 1}
                </span>
              ))}
            </div>
            <textarea
              className="code-editor-textarea"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              spellCheck={false}
              disabled={saving}
              aria-label="Edit Gorgias code"
            />
          </>
        ) : (
          <>
            <div className="code-editor-gutter" aria-hidden="true">
              {lines.map((_, index) => (
                <span key={index} className="code-editor-ln">
                  {index + 1}
                </span>
              ))}
            </div>
            <pre className="code-editor-content">
              <code>{code}</code>
            </pre>
          </>
        )}
      </div>
    </div>
  );
}
