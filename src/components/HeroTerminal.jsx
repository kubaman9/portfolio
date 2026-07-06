import { useRef, useState } from "react";

const scrollTo = (id) => {
  document.querySelector(id)?.scrollIntoView({ behavior: "smooth" });
};

const HELP_TEXT = [
  "available commands:",
  "  help              show this list",
  "  whoami            about jakub",
  "  ls projects       list featured projects",
  "  cd projects       jump to the projects section",
  "  cd about          jump to the about section",
  "  contact           jump to the contact form",
  "  chat              open the AI assistant",
  "  github            open my GitHub profile",
  "  clear             clear this terminal",
  "  ...and maybe an easter egg or two 👀",
];

const PROJECT_LIST = [
  "ironlog/        full-stack lift tracker (TS + custom API)",
  "watchnext/      what-to-watch-next web app",
  "mma-predictor/  python fight outcome predictor",
  "aib-website/    AI in Business Club site (I'm the VP)",
  "portfolio/      this very site",
  "listapp/        kotlin android list manager",
];

/** Runs a command, returns output lines. May trigger side effects (scrolling, events). */
const runCommand = (raw) => {
  const cmd = raw.trim().toLowerCase().replace(/\s+/g, " ");

  switch (cmd) {
    case "help":
    case "?":
      return HELP_TEXT;
    case "whoami":
      return [
        "jakub (kuba) kielczewski — CS senior @ Indiana University, grad may 2027.",
        "builds full-stack apps, AI tools & android software. VP of AI in Business Club.",
      ];
    case "ls":
    case "ls projects":
    case "ls ~/projects":
      return PROJECT_LIST;
    case "cd projects":
    case "open projects":
      scrollTo("#projects");
      return ["→ jumping to ~/projects ..."];
    case "cd about":
    case "open about":
      scrollTo("#about");
      return ["→ jumping to ~/about ..."];
    case "cd contact":
    case "contact":
    case "open contact":
      scrollTo("#contact");
      return ["→ jumping to ~/contact ..."];
    case "cd ~":
    case "cd":
    case "cd home":
      scrollTo("#home");
      return ["→ already home :)"];
    case "chat":
    case "ask":
    case "ai":
      window.dispatchEvent(new CustomEvent("jakub:openchat"));
      return ["→ launching ask_ai.sh ..."];
    case "github":
    case "gh":
      window.open("https://github.com/kubaman9", "_blank", "noopener");
      return ["→ opening github.com/kubaman9 ..."];
    case "email":
      window.location.href = "mailto:jkielcz@iu.edu";
      return ["→ opening mail client (jkielcz@iu.edu) ..."];
    case "sudo hire jakub":
    case "hire jakub":
    case "hire":
      scrollTo("#contact");
      return [
        "[sudo] password for recruiter: ********",
        "access granted. excellent decision — routing you to the contact form ...",
      ];
    case "matrix":
    case "neo":
      window.dispatchEvent(new CustomEvent("jakub:matrix"));
      return ["wake up, neo... (press ESC to exit)"];
    case "coffee":
      return ["☕ brewing... done. productivity +200%"];
    case "vim":
      return ["error: you will never exit. request denied for your own safety."];
    case "rm -rf /":
    case "rm -rf":
      return ["nice try. this portfolio is read-only ;)"];
    case "clear":
    case "cls":
      return null; // special-cased: clears history
    case "":
      return [];
    default:
      return [`command not found: ${raw.trim()} — try 'help'`];
  }
};

/** An actually-typeable terminal prompt for the hero section. */
export const HeroTerminal = () => {
  const [history, setHistory] = useState([
    { type: "out", text: "tip: this prompt is real — type 'help' and hit enter." },
  ]);
  const [input, setInput] = useState("");
  const inputRef = useRef(null);
  const outputRef = useRef(null);

  const submit = (e) => {
    e.preventDefault();
    const result = runCommand(input);

    if (result === null) {
      setHistory([]);
    } else {
      setHistory((h) => [
        ...h.slice(-30),
        { type: "cmd", text: input },
        ...result.map((text) => ({ type: "out", text })),
      ]);
    }
    setInput("");

    // keep newest output in view
    requestAnimationFrame(() => {
      if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
    });
  };

  return (
    <div
      className="mt-10 text-sm sm:text-base cursor-text"
      onClick={() => inputRef.current?.focus()}
    >
      <div ref={outputRef} className="hero-terminal-output space-y-0.5 mb-1">
        {history.map((line, i) =>
          line.type === "cmd" ? (
            <p key={i} className="hero-terminal-line">
              <span className="prompt-user">jakub@iu</span>
              <span className="term-comment">:</span>
              <span className="prompt-path">~</span>
              <span className="prompt-symbol">$ </span>
              <span className="term-output">{line.text}</span>
            </p>
          ) : (
            <p key={i} className="hero-terminal-line term-comment whitespace-pre-wrap">
              {line.text}
            </p>
          )
        )}
      </div>

      <form onSubmit={submit} className="flex items-center">
        <span className="prompt-user">jakub@iu</span>
        <span className="term-comment">:</span>
        <span className="prompt-path">~</span>
        <span className="prompt-symbol">$&nbsp;</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="hero-terminal-input"
          aria-label="Terminal command input — type help for a list of commands"
          autoComplete="off"
          autoCapitalize="off"
          spellCheck="false"
          placeholder="type a command..."
        />
      </form>
    </div>
  );
};
