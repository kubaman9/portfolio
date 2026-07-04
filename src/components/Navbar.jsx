import { useEffect } from "react"

const navLinks = [
    { href: "#home", label: "Home" },
    { href: "#about", label: "About" },
    { href: "#projects", label: "Projects" },
    { href: "#contact", label: "Contact" },
];

export const Navbar = ({ menuLoaded, setMenuLoaded }) => {

    useEffect(() => {
        document.body.style.overflow = menuLoaded ? "hidden" : "";
    }, [menuLoaded]);

    return (
        <nav className="fixed top-0 w-full z-10 bg-[rgba(10,10,10,0.8)] backdrop-blur-lg border-b border-white/5">
            <div className="max-w-5xl mx-auto px-4">
                <div className="flex justify-between items-center h-16">
                    <a href="#home" className="font-mono text-xl font-bold text-white">
                        Jakub<span className="text-blue-500">.AI</span>
                    </a>

                    <button
                        type="button"
                        aria-label="Open menu"
                        className="text-2xl relative cursor-pointer z-40 md:hidden"
                        onClick={() => setMenuLoaded((prev) => !prev)}
                    >
                        &#9776;
                    </button>

                    <div className="hidden md:flex items-center space-x-6 z-50">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className="text-gray-300 hover:text-white transition-colors"
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
