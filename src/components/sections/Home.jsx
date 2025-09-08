import { RevealOnScroll } from "../RevealOnScroll";
export const Home = () => {
  return (
    <section id="home" className="min-h-screen flex items-center justify-center py-20">
      <RevealOnScroll>
      <div className="text-center z-10 px-4">
        <h1 className="text-5xl md:text-7xl font-bold md:mt-6 gradient-text leading-tight bg-gradient-to-r from-blue-900 to-blue-300 bg-clip-text text-transparent">
          Hi, I'm Jakub
        </h1>

        <p className="text-gray-400 text-md mb-8 max-w-lg mx-auto">
          Hi, I’m Jakub Kielczewski — a Computer Science major at Indiana University passionate about blending technology, business, and creativity. From building apps and AI solutions to leading student organizations, I thrive on turning ideas into real-world impact. Outside of the classroom, you’ll find me training in martial arts, exploring the outdoors, or mentoring others through leadership roles.
        </p>
        
        <div className="flex justify-center space-x-4 ">
          <a href="#projects" className="bg-blue-500 text-white py-3 px-6 rounded font-medium transition relative overflow-hidden hover:-traslate-y-0.5 hover:shadow-[0_0_15px_rgba(59, 130,246,0.4)]">Projects</a>
          <a href="#contacts" className="border border-blue-500/50 text-blue-500 py-3 px-6 rounded font-medium transition-all duration-200 hover:-traslate-y-0.5 hover:shadow-[0_0_15px_rgba(59, 130,246,0.4)] hover:bg-blue-500 hover:text-black">Contact Me</a>
        </div>

      </div>
      </RevealOnScroll>
    </section>
  );
};
