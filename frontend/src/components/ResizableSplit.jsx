import { useCallback, useEffect, useRef, useState } from "react";
import "./ResizableSplit.css";

const MIN_TOP = 80;
const MIN_BOTTOM = 72;
const DEFAULT_BOTTOM = 160;

export default function ResizableSplit({ main, bottom, storageKey }) {
  const containerRef = useRef(null);
  const [bottomHeight, setBottomHeight] = useState(() => {
    const saved = storageKey && localStorage.getItem(storageKey);
    return saved ? Number(saved) : DEFAULT_BOTTOM;
  });
  const dragging = useRef(false);

  const onMouseMove = useCallback((event) => {
    if (!dragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const fromBottom = rect.bottom - event.clientY;
    const maxBottom = rect.height - MIN_TOP;
    const next = Math.min(Math.max(fromBottom, MIN_BOTTOM), maxBottom);
    setBottomHeight(next);
  }, []);

  const onMouseUp = useCallback(() => {
    dragging.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [onMouseMove, onMouseUp]);

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(storageKey, String(bottomHeight));
    }
  }, [bottomHeight, storageKey]);

  const startDrag = () => {
    dragging.current = true;
    document.body.style.cursor = "ns-resize";
    document.body.style.userSelect = "none";
  };

  return (
    <div className="resizable-split" ref={containerRef}>
      <div className="resizable-split-main" style={{ minHeight: MIN_TOP }}>
        {main}
      </div>
      <div
        className="resizable-split-handle"
        role="separator"
        aria-orientation="horizontal"
        aria-label="Resize terminal"
        onMouseDown={startDrag}
      />
      <div className="resizable-split-bottom" style={{ height: bottomHeight }}>
        {bottom}
      </div>
    </div>
  );
}
