import { useEffect } from "react";

const links = [
  { href: "#home", label: "cd ~/home" },
  { href: "#about", label: "cd ~/about" },
  { href: "#projects", label: "cd ~/projects" },
  { href: "#contact", label: "cd ~/contact" },
];

export const MobileMenu = ({ menuLoaded, setMenuLoaded }) => {
  useEffect(() => {
    document.body.style.overflow = menuLoaded ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuLoaded]);

  return (
    <div
      className={`fixed top-0 left-0 w-full z-[60] flex flex-col items-center justify-center transition-all duration-300 ease-in-out
        ${menuLoaded ? "h-screen opacity-100 pointer-events-auto" : "h-0 opacity-0 pointer-events-none"}`}
      style={{ background: "rgba(9, 14, 20, 0.96)" }}
    >
      <button
        onClick={() => setMenuLoaded(false)}
        className="absolute top-5 right-5 text-2xl focus:outline-none cursor-pointer"
        style={{ color: "var(--term-accent)" }}
        aria-label="Close Menu"
      >
        [x]
      </button>

      {links.map((link) => (
        <a
          key={link.href}
          href={link.href}
          onClick={() => setMenuLoaded(false)}
          className={`text-xl font-semibold my-4 transform transition-transform duration-300
            ${menuLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-5"}`}
        >
          <span className="prompt-symbol">$ </span>
          <span style={{ color: "var(--term-accent)" }}>{link.label}</span>
        </a>
      ))}
    </div>
  );
};
