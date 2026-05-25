import "./CreateSessionDialog.css";

export default function DeleteSessionDialog({
  open,
  sessionName,
  onClose,
  onConfirm,
  deleting = false,
}) {
  if (!open) return null;

  const label = sessionName?.trim() || "this session";

  return (
    <div className="create-session-overlay" onClick={onClose}>
      <div
        className="create-session-dialog"
        role="dialog"
        aria-labelledby="delete-session-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="delete-session-title">Delete session</h2>
        <p className="create-session-hint">
          Delete &ldquo;{label}&rdquo;? This cannot be undone.
        </p>
        <div className="create-session-actions">
          <button type="button" className="btn-secondary" onClick={onClose} disabled={deleting}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={onConfirm}
            disabled={deleting}
          >
            {deleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}
