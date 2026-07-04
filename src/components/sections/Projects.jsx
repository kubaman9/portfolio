import { RevealOnScroll } from "../RevealOnScroll";

const projects = [
    {
        title: "Jakub.AI Portfolio (This Site)",
        description:
            "This portfolio itself — a React + Vite single-page app styled with TailwindCSS, " +
            "featuring scroll-reveal animations, an EmailJS-powered contact form, and a built-in " +
            "AI chatbot that answers recruiter questions about me in real time.",
        tech: ["React", "Vite", "TailwindCSS", "Gemini API"],
        link: "https://github.com/kubaman9/portfolio",
    },
    {
        title: "ListApp (Android)",
        description:
            "An Android list manager that persists data locally, supports token-based list flows, and " +
            "remembers the last selected list for a faster “open-to-task” experience. Includes user " +
            "authentication and a clean Kotlin/Gradle setup.",
        tech: ["Kotlin", "Android", "Gradle"],
        link: "https://github.com/kubaman9/ListApp",
    },
    {
        title: "Project9Jakub (Cloud To-Do)",
        description:
            "A Kotlin Android to-do app that authenticates users by email and syncs lists to a cloud " +
            "datastore — designed to keep tasks consistent across sessions and devices with a " +
            "straightforward, mobile-first UX.",
        tech: ["Kotlin", "Android", "Cloud Database", "Auth"],
        link: "https://github.com/kubaman9/Project9Jakub",
    },
    {
        title: "PyTest Projects (GUI Utilities)",
        description:
            "A collection of small Python GUI tools — including a web scraper, calculator, graph " +
            "visualizer, and image modifier — organized for quick experimentation and learning across " +
            "multiple desktop-app patterns.",
        tech: ["Python", "GUI"],
        link: "https://github.com/kubaman9/PyTestProjects",
    },
    {
        title: "InfaNote",
        description:
            "A lightweight, single-page notes canvas built with semantic HTML and custom CSS. Focuses " +
            "on an “infinite” writing surface with simple text editing and personalization, ideal for " +
            "quick capture and distraction-free drafting.",
        tech: ["HTML", "CSS"],
        link: "https://github.com/kubaman9/InfaNote",
    },
];

export const Projects = () => {
    return (
        <section id="projects" className="min-h-screen flex items-center justify-center py-20">
            <RevealOnScroll>
                <div className="max-w-5xl mx-auto px-4">
                    <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent text-center">
                        Featured Projects
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {projects.map((project) => (
                            <div
                                key={project.title}
                                className="p-6 rounded-xl border border-white/10 hover:-translate-y-1 hover:border-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition text-left flex flex-col"
                            >
                                <h3 className="text-xl font-bold mb-2">{project.title}</h3>
                                <p className="text-gray-400 mb-4 flex-1">{project.description}</p>
                                <div className="flex flex-wrap gap-2 mb-2">
                                    {project.tech.map((tech, key) => (
                                        <span
                                            key={key}
                                            className="bg-blue-500/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition"
                                        >
                                            {tech}
                                        </span>
                                    ))}
                                </div>
                                <div className="flex justify-between items-center">
                                    <a
                                        href={project.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-500 hover:text-blue-300 transition-colors my-4"
                                    >
                                        View Project →
                                    </a>
                                </div>
                            </div>
                        ))}
                    </div>

                    <p className="text-center text-gray-400 mt-8">
                        More on my{" "}
                        <a
                            href="https://github.com/kubaman9"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:text-blue-300 transition-colors"
                        >
                            GitHub profile →
                        </a>
                    </p>
                </div>
            </RevealOnScroll>
        </section>
    );
};
