export const Footer = () => {
  return (
    <footer className="border-t border-white/10 py-8">
      <div className="max-w-5xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-gray-400 text-sm">
          © {new Date().getFullYear()} Jakub Kielczewski. Built with React, Vite &amp; Tailwind.
        </p>
        <div className="flex items-center gap-6 text-sm">
          <a
            href="https://github.com/kubaman9"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-white transition-colors"
          >
            GitHub
          </a>
          <a
            href="mailto:jkielcz@iu.edu"
            className="text-gray-400 hover:text-white transition-colors"
          >
            jkielcz@iu.edu
          </a>
          <a href="#home" className="text-gray-400 hover:text-white transition-colors">
            Back to top ↑
          </a>
        </div>
      </div>
    </footer>
  );
};
