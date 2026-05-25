import { useState } from "react";
import "./TagInput.css";

/**
 * @param {string[]} tags
 * @param {(value: string) => void} onAdd
 * @param {(index: number) => void} onRemove
 * @param {boolean} [single] - at most one tag; adding replaces
 */
export default function TagInput({
  label,
  tags,
  onAdd,
  onRemove,
  placeholder,
  single = false,
  variant = "default",
}) {
  const [draft, setDraft] = useState("");

  const commit = () => {
    const value = draft.trim();
    if (!value) return;
    if (single) {
      onAdd(value);
    } else if (!tags.includes(value)) {
      onAdd(value);
    }
    setDraft("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      commit();
    } else if (event.key === "Backspace" && !draft && tags.length > 0) {
      onRemove(tags.length - 1);
    }
  };

  return (
    <div className="tag-input">
      <label className="tag-input-label" htmlFor={`tag-input-${label}`}>
        {label}
      </label>
      <input
        id={`tag-input-${label}`}
        type="text"
        className="tag-input-field"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
      />
      <span className="tag-input-hint">Press Enter to add</span>
      {tags.length > 0 && (
        <div className="tag-badges" role="list">
          {tags.map((tag, index) => (
            <span
              key={`${tag}-${index}`}
              className={`tag-badge tag-badge-${variant}`}
              role="listitem"
            >
              {tag}
              <button
                type="button"
                className="tag-badge-remove"
                aria-label={`Remove ${tag}`}
                onClick={() => onRemove(index)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
