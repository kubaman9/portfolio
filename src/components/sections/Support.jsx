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

  const base = "rounded-2xl px-3 py-2 text-sm transition-all duration-300 ease-out " + anim;

  const original =
    role === "user"
      ? "ml-auto max-w-fit text-right bg-blue-500/20 text-blue-100"
      : "mr-auto max-w-fit text-left bg-white/10 text-gray-100";

  return (
    <div className={`${base} ${original}`} tabIndex={0}>
      {children}
    </div>
  );
}

export const Support = ({ compact = false }) => {
  const [messages, setMessages] = useState([
    // You can keep a greeting in UI, but we’ll drop leading model lines from the request.
    { id: 1, role: "model", text: "Hi! How can I get you to hire Jakub?" },
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
            "x-goog-api-key": "AIzaSyCNPoajD0LtZ4XwRjaEXgihbX6lnZ7MS_o",
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
      id="about"
      className={
        compact
          ? "h-full flex flex-col border-none" // fill modal panel
          : "min-h-screen flex items-center justify-center py-20"
      }
    >
      <div className="relative w-full max-w-2xl mx-auto px-4 glass rounded-xl border border-white/10">
        {/* Header
        <div className="absolute top-4 left-4 px-4 text-3xl font-bold bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent">
          Chatbot
        </div>  
        <div className="absolute top-4 left-36 px-0 text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-400">
          .AI
        </div>
        <button
          type="button"
          aria-label="Toggle chatbot"
          className="absolute top-4 right-4 bg-blue-500 text-white py-2 px-4 rounded font-medium hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          ▼
        </button> */}

        {/* Content */}
        <div className="pt-16 flex flex-col gap-4 ">
          {/* Messages area */}
          <div className="h-96 overflow-y-auto rounded-lg border border-blue-500/30 p-4 space-y-3 bg-black/20">
            {messages.map((m) => (
              <MessageBubble key={m.id} role={m.role === "user" ? "user" : "model"}>
                {m.text}
              </MessageBubble>
            ))}
            <div ref={endRef} />
          </div>

          {/* Input row */}
          <form onSubmit={handleSend} className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 bg-neutral-900/70 text-gray-100 placeholder-gray-400 rounded-lg px-3 py-2 border border-white/10 focus:outline-none focus:ring-2 focus:ring-blue-400"
              aria-label="Message input"
              autoComplete="off"
            />
            <button
              type="submit"
              disabled={!input.trim()}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </section>
  );
};
