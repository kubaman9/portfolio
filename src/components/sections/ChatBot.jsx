// ChatBot.jsx
import { useEffect, useRef, useState } from "react";
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
                 rounded-full px-4 py-3
                 bg-gradient-to-r from-blue-500 to-cyan-400
                 text-white font-semibold shadow-lg
                 hover:shadow-xl active:scale-95
                 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-400 focus:ring-offset-neutral-900"
    >
      {/* Chat bubble icon */}
      <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" aria-hidden="true">
        <path
          d="M7 17l-3 3v-4A7 7 0 017 5h10a7 7 0 017 7v0a7 7 0 01-7 7H9"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="hidden sm:inline">{open ? "Close" : "Chat"}</span>
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
          bg-neutral-900 rounded-2xl shadow-2xl border border-white/10 overflow-hidden
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

  return (
    <>
      <ChatFab open={open} onToggle={() => setOpen((o) => !o)} />

      <ChatPortal open={open} onClose={() => setOpen(false)} title={title}>
  {/* fixed the small typos: use w-full px-4 */}
  <div className="w-full px-4">
    {/* Header area (absolute elements live here) */}
    <div className="relative pt-2">
      {/* Title (same styling, same positions) */}
      <div className="absolute top-4 left-4 px-4 text-3xl font-bold bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent">
        Chatbot
      </div>
      <div className="absolute top-4 left-36 px-0 text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-400">
        .AI
      </div>

      {/* Close button (same styling/position) */}
      <button
        onClick={() => setOpen(false)}
        className="absolute right-4 top-4 z-100 text-white/70 hover:text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 rounded-md px-2 py-1"
        aria-label="Close chat"
      >
        ✕
      </button>
    </div>

    {/* Body: make interior scrollable */}
    <div className="flex-1 min-h-0 border-none">
      <Support compact />
    </div>
  </div>
</ChatPortal>
    </>
  );
}
