// ChatBot.jsx
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Support } from "./Support"; // adjust path if needed

/** Floating Action Button */
function ChatFab({ open, onToggle }) {
    if (open) return null; // hide while chat is open
    return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      aria-label={open ? "Close chat" : "Open chat"}
      className="fixed bottom-6 right-6 z-40
                 inline-flex items-center gap-2
                 rounded px-4 py-3 font-bold text-sm
                 active:scale-95 transition-all
                 focus:outline-none focus:ring-2 focus:ring-offset-2"
      style={{
        background: "var(--term-accent)",
        color: "#051019",
        boxShadow: "0 0 20px rgba(125, 211, 252, 0.45)",
      }}
    >
      <span aria-hidden="true">&gt;_</span>
      <span className="hidden sm:inline">ask_ai.sh</span>
    </button>
  );
}

/** Modal rendered in a portal */
function ChatPortal({ open, onClose, title = "Chatbot", children }) {
  const [mounted, setMounted] = useState(false);

  // ESC to close
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // Mount animation trigger
  useEffect(() => {
    let id;
    if (open) id = requestAnimationFrame(() => setMounted(true));
    else setMounted(false);
    return () => cancelAnimationFrame(id);
  }, [open]);

  if (!open && !mounted) return null;

  return createPortal(
    <div className={`fixed inset-0 z-[1000] ${open ? "" : "pointer-events-none"}`}>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={`absolute inset-0 bg-black/50 transition-opacity duration-300 ${
          open ? "opacity-100" : "opacity-0"
        }`}
      />
      {/* Panel */}
      <section
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`absolute right-4 bottom-4 sm:right-6 sm:bottom-6
          w-[min(92vw,28rem)] h-[min(80vh,36rem)]
          term-window
          transform transition-all duration-300 ease-out
          ${open ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}
        `}
      >
        {children}
      </section>
    </div>,
    document.body
  );
}

export default function ChatBot({ title = "Chatbot", initialOpen = false }) {
  const [open, setOpen] = useState(initialOpen);

  // Let the hero terminal's `chat` command open this panel
  useEffect(() => {
    const openChat = () => setOpen(true);
    window.addEventListener("jakub:openchat", openChat);
    return () => window.removeEventListener("jakub:openchat", openChat);
  }, []);

  return (
    <>
      <ChatFab open={open} onToggle={() => setOpen((o) => !o)} />

      <ChatPortal open={open} onClose={() => setOpen(false)} title={title}>
  {/* fixed the small typos: use w-full px-4 */}
  <div className="w-full h-full flex flex-col">
    {/* Terminal title bar */}
    <div className="term-titlebar justify-between">
      <div className="flex items-center gap-2">
        <span className="term-dot" style={{ background: "#f87171" }} />
        <span className="term-dot" style={{ background: "#fbbf24" }} />
        <span className="term-dot" style={{ background: "#4ade80" }} />
        <span className="ml-2 font-bold" style={{ color: "var(--term-accent)" }}>ask_ai.sh — gemini</span>
      </div>
      <button
        onClick={() => setOpen(false)}
        className="focus:outline-none px-2"
        style={{ color: "var(--term-muted)" }}
        aria-label="Close chat"
      >
        [x]
      </button>
    </div>

    {/* Body: make interior scrollable */}
    <div className="flex-1 min-h-0">
      <Support compact />
    </div>
  </div>
</ChatPortal>
    </>
  );
}
