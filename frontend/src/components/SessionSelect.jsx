import { useEffect, useRef, useState } from "react";
import "./SessionSelect.css";

export default function SessionSelect({
  sessions,
  currentSessionId,
  currentSessionName,
  onSelect,
  onCreate,
  disabled = false,
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (id) => {
    setOpen(false);
    if (id !== currentSessionId) {
      onSelect(id);
    }
  };

  const handleCreate = () => {
    setOpen(false);
    onCreate();
  };

  return (
    <div className="session-select" ref={rootRef}>
      <button
        type="button"
        className="session-select-trigger"
        onClick={() => setOpen((value) => !value)}
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className="session-select-label">
          {currentSessionName || "Select a session"}
        </span>
        <span className="session-select-chevron" aria-hidden="true">
          ▾
        </span>
      </button>

      {open && (
        <div className="session-select-menu" role="listbox">
          <button type="button" className="session-select-new" onClick={handleCreate}>
            + New session
          </button>
          <div className="session-select-list">
            {sessions.length === 0 ? (
              <p className="session-select-empty">No sessions yet</p>
            ) : (
              sessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  role="option"
                  aria-selected={session.id === currentSessionId}
                  className={
                    session.id === currentSessionId
                      ? "session-select-item active"
                      : "session-select-item"
                  }
                  onClick={() => handleSelect(session.id)}
                >
                  {session.name}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
