import { useEffect } from "react"

export const Navbar = ( {menuLoaded, setMenuLoaded} ) => {

    useEffect(()=> {
        document.body.style.overflow = menuLoaded ? "hidden" : "";
    }, [menuLoaded]);

    return (
        <nav className="fixed top-0 w-full z-10 bg-[rgba(10,10,10,0.8)] backdrop-blur-lg">
            <div className="max-w-10xl mx-full px-4">
                <div className="flex justify-between items-center h-16">
                    <a href="#home" className="font-mono text-xl font-bold text-white">
                        {""}
                        Jakub<span className="text-blue-500">.AI</span>
                    </a>

                    <div className="w-7 h-5 relative cursor-pointer z-40 md:hidden" onClick={() => setMenuLoaded((prev) => !prev)}>
                        &#9776;
                    </div>

                    <div className="hidden md:flex items-center space-x-4">
                        <a href="#home" className='text-gray-300 hover:text-white transition-colors ${ menuOpen ? "opacity-100 translate-y-0" : "opacity-0 tanslate-y-5"}'>
                            Home
                        </a>
                        <a href="#about" className='text-gray-300 hover:text-white transition-colors ${ menuOpen ? "opacity-100 translate-y-0" : "opacity-0 tanslate-y-5"}'>
                            About
                        </a>
                        <a href="#projects" className='text-gray-300 hover:text-white transition-colors ${ menuOpen ? "opacity-100 translate-y-0" : "opacity-0 tanslate-y-5"}'>
                            Projects
                        </a>
                        <a href="#contact" className='text-gray-300 hover:text-white transition-colors ${ menuOpen ? "opacity-100 translate-y-0" : "opacity-0 tanslate-y-5"}'>
                            Contact
                        </a>
                    </div>
                </div>
            </div>
        </nav>
    )

}