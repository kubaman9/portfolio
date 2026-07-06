import { useEffect, useState } from "react"

const navLinks = [
    { href: "#home", label: "~/home" },
    { href: "#about", label: "~/about" },
    { href: "#projects", label: "~/projects" },
    { href: "#contact", label: "~/contact" },
];

export const Navbar = ({ menuLoaded, setMenuLoaded }) => {
    const [activeSection, setActiveSection] = useState("home");

    useEffect(() => {
        document.body.style.overflow = menuLoaded ? "hidden" : "";
    }, [menuLoaded]);

    // Track which section fills the viewport and light up its nav link
    useEffect(() => {
        const sections = ["home", "about", "projects", "contact"]
            .map((id) => document.getElementById(id))
            .filter(Boolean);

        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) setActiveSection(entry.target.id);
                }
            },
            { rootMargin: "-40% 0px -55% 0px" }
        );

        sections.forEach((s) => observer.observe(s));
        return () => observer.disconnect();
    }, []);

    return (
        <nav
            className="fixed top-0 w-full z-10 backdrop-blur-lg"
            style={{ background: "rgba(9, 14, 20, 0.85)", borderBottom: "1px solid var(--term-border)" }}
        >
            <div className="max-w-5xl mx-auto px-4">
                <div className="flex justify-between items-center h-14">
                    <a href="#home" className="text-base font-bold">
                        <span className="prompt-user">jakub@iu</span>
                        <span className="term-comment">:</span>
                        <span className="prompt-path">{activeSection === "home" ? "~" : `~/${activeSection}`}</span>
                        <span className="prompt-symbol">$</span>
                        <span className="cursor-block ml-2 align-middle" style={{ height: "0.9em" }} />
                    </a>

                    <button
                        type="button"
                        aria-label="Open menu"
                        className="text-xl relative cursor-pointer z-40 md:hidden"
                        style={{ color: "var(--term-accent)" }}
                        onClick={() => setMenuLoaded((prev) => !prev)}
                    >
                        [≡]
                    </button>

                    <div className="hidden md:flex items-center space-x-6 z-50 text-sm">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className={`nav-link ${activeSection === link.href.slice(1) ? "active" : ""}`}
                            >
                                {link.label}
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        </nav>
    );
};
