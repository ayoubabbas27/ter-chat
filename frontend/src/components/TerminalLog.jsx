import { useEffect, useRef } from "react";
import "./TerminalLog.css";

export default function TerminalLog({ lines, active }) {
  const endRef = useRef(null);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (active && endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [lines, active]);

  return (
    <div className="terminal">
      <div className="terminal-header">
        <span className="terminal-title">Logs</span>
        <span className="terminal-status">{active ? "● live" : "○ idle"}</span>
      </div>
      <div className="terminal-body" ref={bodyRef}>
        {lines.length === 0 ? (
          <div className="terminal-line terminal-muted">
            <span className="terminal-prompt">$</span> Waiting for activity…
          </div>
        ) : (
          lines.map((line, index) => (
            <div key={index} className="terminal-line">
              {line === "" ? (
                <br />
              ) : (
                <>
                  <span className="terminal-prompt">$</span>
                  <span className="terminal-text">{line}</span>
                </>
              )}
            </div>
          ))
        )}
        <span ref={endRef} />
      </div>
    </div>
  );
}
