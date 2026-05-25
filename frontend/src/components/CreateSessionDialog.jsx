import { useEffect, useState } from "react";
import "./CreateSessionDialog.css";

export default function CreateSessionDialog({ open, onClose, onCreate, creating = false }) {
  const [name, setName] = useState("");

  useEffect(() => {
    if (open) {
      setName("");
    }
  }, [open]);

  if (!open) return null;

  const handleSubmit = (event) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || creating) return;
    onCreate(trimmed);
  };

  return (
    <div className="create-session-overlay" onClick={onClose}>
      <div
        className="create-session-dialog"
        role="dialog"
        aria-labelledby="create-session-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="create-session-title">New session</h2>
        <p className="create-session-hint">Choose a name for this session.</p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Session name"
            maxLength={56}
            disabled={creating}
            autoFocus
          />
          <div className="create-session-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={creating}>
              Cancel
            </button>
            <button type="submit" disabled={creating || !name.trim()}>
              {creating ? "Creating…" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
