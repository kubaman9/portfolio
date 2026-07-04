import { useState } from 'react';
import './App.css';
import "./index.css";
import { LoadingScreen } from './components/LoadingScreen';
import { Navbar } from './components/Navbar';
import { MobileMenu } from './components/MobileMenu';
import { Home } from './components/sections/Home';
import { About } from './components/sections/About';
import { Projects } from './components/sections/Projects';
import { Contact } from './components/sections/Contact';
import { Footer } from './components/Footer';
import ChatBot from './components/sections/ChatBot';

function App() {

    const [isLoaded, setLoaded] = useState(false);
    const [menuLoaded, setMenuLoaded] = useState(false);

    return (
        <>
            {!isLoaded && <LoadingScreen onComplete={() => setLoaded(true)} />}

            <div className={`min-h-screen w-full transition-opacity duration-700 ${isLoaded ? "opacity-100" : "opacity-0"} bg-black text-gray-100`}>

                <Navbar menuLoaded={menuLoaded} setMenuLoaded={setMenuLoaded}/>
                <MobileMenu menuLoaded={menuLoaded} setMenuLoaded={setMenuLoaded}/>
                <Home />
                <About />
                <Projects />
                <Contact/>
                <Footer />
                <ChatBot/>
            </div>
        </>
    );
}

export default App;
