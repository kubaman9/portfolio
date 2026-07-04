export const Footer = () => {
  return (
    <footer className="py-10" style={{ borderTop: "1px solid var(--term-border)" }}>
      <div className="max-w-5xl mx-auto px-4 text-sm space-y-2">
        <p>
          <span className="prompt-user">jakub@iu</span>
          <span className="term-comment">:</span>
          <span className="prompt-path">~</span>
          <span className="prompt-symbol">$ </span>
          <span className="term-output">exit</span>
        </p>
        <p className="term-comment">
          Connection to jakub.ai closed. © {new Date().getFullYear()} Jakub Kielczewski —
          built with React, Vite &amp; Tailwind.
        </p>
        <p className="flex flex-wrap gap-x-6 gap-y-1">
          <a href="https://github.com/kubaman9" target="_blank" rel="noopener noreferrer" className="term-link">
            github/kubaman9
          </a>
          <a href="mailto:jkielcz@iu.edu" className="term-link">
            jkielcz@iu.edu
          </a>
          <a href="#home" className="term-link">
            cd ~/ ↑
          </a>
        </p>
      </div>
    </footer>
  );
};
