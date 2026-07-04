import { useEffect } from "react"

const navLinks = [
    { href: "#home", label: "~/home" },
    { href: "#about", label: "~/about" },
    { href: "#projects", label: "~/projects" },
    { href: "#contact", label: "~/contact" },
];

export const Navbar = ({ menuLoaded, setMenuLoaded }) => {

    useEffect(() => {
        document.body.style.overflow = menuLoaded ? "hidden" : "";
    }, [menuLoaded]);

    return (
        <nav
            className="fixed top-0 w-full z-10 backdrop-blur-lg"
            style={{ background: "rgba(10, 15, 11, 0.85)", borderBottom: "1px solid var(--term-border)" }}
        >
            <div className="max-w-5xl mx-auto px-4">
                <div className="flex justify-between items-center h-14">
                    <a href="#home" className="text-base font-bold">
                        <span className="prompt-user">jakub@iu</span>
                        <span className="term-comment">:</span>
                        <span className="prompt-path">~</span>
                        <span className="prompt-symbol">$</span>
                        <span className="cursor-block ml-2 align-middle" style={{ height: "0.9em" }} />
                    </a>

                    <button
                        type="button"
                        aria-label="Open menu"
                        className="text-xl relative cursor-pointer z-40 md:hidden"
                        style={{ color: "var(--term-green)" }}
                        onClick={() => setMenuLoaded((prev) => !prev)}
                    >
                        [≡]
                    </button>

                    <div className="hidden md:flex items-center space-x-6 z-50 text-sm">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className="term-link"
                                style={{ color: "var(--term-muted)" }}
                                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--term-green)")}
                                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--term-muted)")}
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
