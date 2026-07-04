import { useRef, useState, useEffect } from "react";
import jakubInfo from "../JakubInfo"

/** Small bubble component that fades in + moves up on mount */
function MessageBubble({ role, children }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const anim = mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2";

  const base = "rounded px-3 py-2 text-sm transition-all duration-300 ease-out border " + anim;

  const original =
    role === "user"
      ? "ml-auto max-w-fit text-right"
      : "mr-auto max-w-fit text-left";

  const style =
    role === "user"
      ? { background: "rgba(251, 191, 36, 0.08)", borderColor: "rgba(251, 191, 36, 0.3)", color: "#fde68a" }
      : { background: "rgba(74, 222, 128, 0.07)", borderColor: "rgba(74, 222, 128, 0.25)", color: "var(--term-text)" };

  const prefix = role === "user" ? "$ " : "> ";

  return (
    <div className={`${base} ${original}`} style={style} tabIndex={0}>
      <span className="term-comment">{prefix}</span>
      {children}
    </div>
  );
}

export const Support = ({ compact = false }) => {
  const [messages, setMessages] = useState([
    // You can keep a greeting in UI, but we’ll drop leading model lines from the request.
    { id: 1, role: "model", text: "Hi! I'm Jakub's AI assistant — ask me anything about his skills, projects, or experience." },
  ]);
  const [input, setInput] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "auto" });
  }, [messages.length]);

  // Append a pending "Thinking..." model message
  const appendThinking = () => {
    const thinking = {
      id: `pending-${Date.now()}`,
      role: "model",
      text: "Thinking…",
      pending: true,
    };
    setMessages((m) => [...m, thinking]);
    return thinking.id;
  };

  // Replace the latest pending model message with real content
  const replacePendingBot = (text) => {
    setMessages((m) => {
      const idx = [...m].map((x) => x.pending).lastIndexOf(true);
      if (idx === -1) return m;
      const copy = [...m];
      copy[idx] = { ...copy[idx], text, pending: false };
      return copy;
    });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const userText = input.trim();
    if (!userText) return;

    // Build next transcript locally (avoid stale state)
    const userMsg = { id: Date.now(), role: "user", text: userText };
    const nextMessages = [...messages, userMsg];

    // Update UI
    setMessages(nextMessages);
    setInput("");
    appendThinking();

    let mapped = nextMessages.map(({ role, text }) => ({
      role: role === "model" ? "model" : "user",
      parts: [{ text }],
    }));

    // Insert your recruiting info as a user turn **right before the latest question**
    const infoTurn = { role: "user", parts: [{ text: jakubInfo }] };
    if (mapped.length === 0) {
      mapped = [infoTurn];
    } else {
      mapped = [...mapped.slice(0, -1), infoTurn, mapped[mapped.length - 1]];
    }

    // Ensure the first item sent is from 'user' (Gemini requirement)
    while (mapped.length && mapped[0].role !== "user") {
      mapped.shift();
    }

    // Drop empty parts to avoid 400s
    mapped = mapped.filter((c) => c?.parts?.[0]?.text?.trim());

    try {
      const resp = await fetch(
        "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // Prefer env var; if you were hardcoding before, you can keep that instead.
            "x-goog-api-key":
              import.meta.env.VITE_GEMINI_API_KEY ||
              "AIzaSyCNPoajD0LtZ4XwRjaEXgihbX6lnZ7MS_o",
          },
          body: JSON.stringify({ contents: mapped }),
        }
      );

      const raw = await resp.text();
      let data;
      try {
        data = JSON.parse(raw);
      } catch {
        data = null;
      }

      if (!resp.ok) {
        const msg = data?.error?.message || raw || "Bad Request";
        replacePendingBot(`Error: ${msg}`);
        return;
      }

      const modelText =
        data?.candidates?.[0]?.content?.parts?.map((p) => p.text).join("") ||
        "(no reply)";
      replacePendingBot(modelText);
    } catch (err) {
      replacePendingBot("Network error: " + String(err));
    }
  };

  return (
    <section
      id="chat"
      className={
        compact
          ? "h-full flex flex-col border-none" // fill modal panel
          : "min-h-screen flex items-center justify-center py-20"
      }
    >
      <div className={`relative w-full max-w-2xl mx-auto px-4 ${compact ? "h-full py-4" : ""}`}>
        <div className={`flex flex-col gap-3 ${compact ? "h-full" : ""}`}>
          {/* Messages area */}
          <div
            className={`${compact ? "flex-1 min-h-0" : "h-96"} overflow-y-auto rounded p-4 space-y-3`}
            style={{ border: "1px solid var(--term-border)", background: "rgba(0, 0, 0, 0.35)" }}
          >
            {messages.map((m) => (
              <MessageBubble key={m.id} role={m.role === "user" ? "user" : "model"}>
                {m.text}
              </MessageBubble>
            ))}
            <div ref={endRef} />
          </div>

          {/* Input row */}
          <form onSubmit={handleSend} className="flex items-center gap-2 pb-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="ask about jakub..."
              className="term-input flex-1"
              aria-label="Message input"
              autoComplete="off"
            />
            <button
              type="submit"
              disabled={!input.trim()}
              className="term-btn term-btn-solid disabled:opacity-50 !py-2.5"
            >
              ↵
            </button>
          </form>
        </div>
      </div>
    </section>
  );
};
