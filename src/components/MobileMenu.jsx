import { useEffect } from "react"

export const MobileMenu = ( {menuLoaded, setMenuLoaded} ) => {


    return (
       <div className={`fixed top-0 left-0 w-full bg-[rgba(10,10,10,0.8)] flex flex-col items-center justify-center transition-all duration-300 ease-in-out 
    ${menuLoaded ? "h-screen opacity-100 pointer-events-auto" : "h-0 opacity-0 pointer-events-none"}`}>

    <button
        onClick={() => setMenuLoaded(false)}
        className="absolute top-6 right-5 text-white text-3xl focus:outline-none cursor-pointer"
        aria-label="Close Menu"
    >
        &times;
    </button>

    <a href="#home" onClick={() => setMenuLoaded(false)}  className={'text-2xl font-semibold text-white my-4 transform transition-trasnform durration-300 ${ menuLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-5"}'} >
        {" "}
        Home{" "}
    </a>
    <a href="#about" className={'text-2xl font-semibold text-white my-4 transform transition-trasnform durration-300 ${ menuLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-5"}'} onClick={() => setMenuLoaded(false)}>
        {" "}
        About{" "}
    </a>
    <a href="#projects" className={'text-2xl font-semibold text-white my-4 transform transition-trasnform durration-300 ${ menuLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-5"}'} onClick={() => setMenuLoaded(false)}>
        {" "}
        Projects{" "}
    </a>
    <a href="#contact" className={'text-2xl font-semibold text-white my-4 transform transition-trasnform durration-300 ${ menuLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-5"}'} onClick={() => setMenuLoaded(false)}>
        {" "}
        Contact{" "}
    </a>

</div>
    );

}  