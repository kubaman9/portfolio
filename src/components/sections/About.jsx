import { RevealOnScroll } from "../RevealOnScroll";

export const About = () => {

    const frontendSkills = ["React", "Kotlin", "Swift", "TailwindCSS", "HTML", "JavaScript"];
    const backendSkills = ["PHP", "Python", "C", "Java", "MySql", "Firebase", "MongoDB"];

    return <section id="about" className="min-h-screen flex items-center justify-center py-20">
        <RevealOnScroll>

        <div className="max-w-3xl mx-auto px-4">
            <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent text-center">
                About Me
            </h2>

            <div className="glass rounded-xl p-8 border-white/10 border hover:-translate-y-1 transition-all">
                <p className="text-gray-300 mb-6">
                    I enjoy tackling challenges across multiple programming environments. My toolkit includes Java, Python, JavaScript, HTML, CSS, Kotlin, Swift, C++, and C#. Beyond coding, I bring strengths in leadership, problem-solving, and building bridges between business and technology. Whether it’s debugging complex code or organizing guest lectures with industry leaders, I combine technical know-how with communication and collaboration.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="rounded-xl p-6 hover:-translate-y-1 transition-all">
                        <h3 className="text-xl font-blod mb-4">
                            Frontend
                        </h3>

                        <div className="flex flex-wrap gap-2">
                            {frontendSkills.map((tech, key) => (
                                <span key={key} className="bg-blue/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,2246,0.2)] transition">
                                        {tech}
                                </span>
                            ))}
                        </div>
                    </div>
                     <div className="rounded-xl p-6 hover:-translate-y-1 transition-all">
                        <h3 className="text-xl font-blod mb-4">
                            Backend
                        </h3>

                        <div className="flex flex-wrap gap-2">
                            {backendSkills.map((tech, key) => (
                                <span key={key} className="bg-blue/10 text-blue-500 py-1 px-2 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,2246,0.2)] transition">
                                        {tech}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="grid grid-clos-1 md:grid-cols-1 gap-6 mt-8">
                    <div className="p-6 rounded-xl border-white/20 border hover-translate-y-1 transition-all">
                            <h3 className="text-xl font-bold mb-4">
                                Education 
                            </h3>
                            <ul className="list-disc p-6 rounded-xl">
                                <li className="py-3 hover:-translate-y-1 transition all">
                                    <strong>Studying For a B.S. in Computer Science and a Minor in Business</strong> - Indiana University, Bloomington
                                </li>
                                <li className="py-3 hover:-translate-y-1 transition all">
                                    <strong>Vice President</strong> - AI in Business Club, Indiana University
                                </li>

                            </ul>
                    </div>
                </div>
            </div>
        </div>
    </RevealOnScroll>
    </section>
}