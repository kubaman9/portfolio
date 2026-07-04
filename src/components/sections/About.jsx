import { RevealOnScroll } from "../RevealOnScroll";

export const About = () => {

    const frontendSkills = ["React", "TailwindCSS", "JavaScript", "HTML", "CSS", "Kotlin", "Swift"];
    const backendSkills = ["Java", "Python", "C", "C++", "C#", "PHP", "MySQL", "Firebase", "MongoDB"];

    return (
        <section id="about" className="min-h-screen flex items-center justify-center py-20">
            <RevealOnScroll>
                <div className="max-w-3xl mx-auto px-4">
                    <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent text-center">
                        About Me
                    </h2>

                    <div className="glass rounded-xl p-8 border-white/10 border hover:-translate-y-1 transition-all">
                        <p className="text-gray-300 mb-6">
                            I enjoy tackling challenges across multiple programming environments. My toolkit
                            includes Java, Python, JavaScript, HTML, CSS, Kotlin, Swift, C++, and C#. Beyond
                            coding, I bring strengths in leadership, problem-solving, and building bridges
                            between business and technology. Whether it's debugging complex code or organizing
                            guest lectures with industry leaders, I combine technical know-how with
                            communication and collaboration.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="rounded-xl p-6 hover:-translate-y-1 transition-all">
                                <h3 className="text-xl font-bold mb-4">
                                    Frontend &amp; Mobile
                                </h3>

                                <div className="flex flex-wrap gap-2">
                                    {frontendSkills.map((tech, key) => (
                                        <span key={key} className="bg-blue-500/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition">
                                            {tech}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div className="rounded-xl p-6 hover:-translate-y-1 transition-all">
                                <h3 className="text-xl font-bold mb-4">
                                    Backend &amp; Data
                                </h3>

                                <div className="flex flex-wrap gap-2">
                                    {backendSkills.map((tech, key) => (
                                        <span key={key} className="bg-blue-500/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition">
                                            {tech}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                            <div className="p-6 rounded-xl border-white/20 border hover:-translate-y-1 transition-all">
                                <h3 className="text-xl font-bold mb-4">
                                    Education
                                </h3>
                                <ul className="list-disc list-inside space-y-3 text-gray-300">
                                    <li>
                                        <strong>B.S. in Computer Science, Minor in Business</strong> — Indiana
                                        University, Bloomington (Luddy School, Direct Admit). Expected May 2027.
                                    </li>
                                    <li>
                                        Relevant coursework: Discrete Structures, Software Systems, Mobile App
                                        Development.
                                    </li>
                                </ul>
                            </div>

                            <div className="p-6 rounded-xl border-white/20 border hover:-translate-y-1 transition-all">
                                <h3 className="text-xl font-bold mb-4">
                                    Leadership
                                </h3>
                                <ul className="list-disc list-inside space-y-3 text-gray-300">
                                    <li>
                                        <strong>Vice President</strong> — AI in Business Club, Indiana University
                                        (2024–present). Organizing guest lectures and connecting students with
                                        industry AI experts.
                                    </li>
                                    <li>
                                        <strong>Martial Arts Instructor</strong> — DK Fitness Arts (2019–present).
                                        2nd Dan black belt, leading classes and mentoring students.
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </RevealOnScroll>
        </section>
    );
};
