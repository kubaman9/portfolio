import { RevealOnScroll } from "../RevealOnScroll";

export const Home = () => {
  return (
    <section id="home" className="min-h-screen flex items-center justify-center py-20">
      <RevealOnScroll>
        <div className="text-center z-10 px-4">
          <p className="text-blue-400 font-mono text-sm mb-4 tracking-widest uppercase">
            Software Engineer · AI Enthusiast · Leader
          </p>

          <h1 className="text-5xl md:text-7xl font-bold md:mt-2 mb-6 leading-tight bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent">
            Hi, I'm Jakub
          </h1>

          <p className="text-gray-400 text-md mb-8 max-w-lg mx-auto">
            I'm Jakub (Kuba) Kielczewski — a Computer Science senior at Indiana University
            graduating in May 2027, passionate about blending technology, business, and
            creativity. From building apps and AI-powered tools to serving as Vice President
            of the AI in Business Club, I thrive on turning ideas into real-world impact.
            Outside of code, you'll find me teaching martial arts as a 2nd Dan black belt,
            exploring the outdoors, or mentoring others through leadership roles.
          </p>

          <div className="flex justify-center space-x-4">
            <a
              href="#projects"
              className="bg-blue-500 text-white py-3 px-6 rounded font-medium transition relative overflow-hidden hover:-translate-y-0.5 hover:shadow-[0_0_15px_rgba(59,130,246,0.4)]"
            >
              View Projects
            </a>
            <a
              href="#contact"
              className="border border-blue-500/50 text-blue-500 py-3 px-6 rounded font-medium transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_0_15px_rgba(59,130,246,0.4)] hover:bg-blue-500 hover:text-black"
            >
              Contact Me
            </a>
          </div>
        </div>
      </RevealOnScroll>
    </section>
  );
};
