import { RevealOnScroll } from "../RevealOnScroll";

export const Projects = () => {

    return (
        <section id="projects" className="min-h-screen flex items-center justify-center py-20">
            <RevealOnScroll>
            <div className="max-w-5xl mx-auto px-4">
                <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent text-center">
                    Featured Projects
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="p-6 rounded-xl border border-white/10 hover:-translate-y-1 hover:border-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,2246,0.2)] transition text-left">
                        <h2 className="text-xl font-bold mb-2">ListApp (Android)</h2>
                        <p className="text-gray-400 mb-4">
                        An Android list manager that persists data locally, supports token-based list flows, and
                        remembers the last selected list for a faster “open-to-task” experience. Includes user
                        authentication and a clean Kotlin/Gradle setup.
                        </p>
                        <div className="flex flex-wrap gap-2 mb-2">
                        {["Kotlin", "Android", "Gradle"].map((tech, key) => (
                            <span
                            key={key}
                            className="bg-blue/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition"
                            >
                            {tech}
                            </span>
                        ))}
                        </div>
                        <div className="flex justify-between items-center">
                        <a href="https://github.com/kubaman9/ListApp" className="text-blue-500 hover:text-blue-300 transition-colors my-4">
                            View Project
                        </a>
                        </div>

                    </div>
                    <div className="p-6 rounded-xl border border-white/10 hover:-translate-y-1 hover:border-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,2246,0.2)] transition text-left">
                        <h2 className="text-xl font-bold mb-2">InfaNote</h2>
                            <p className="text-gray-400 mb-4">
                            A lightweight, single-page notes canvas built with semantic HTML and custom CSS. Focuses on an
                            “infinite” writing surface with simple text editing and personalization, ideal for quick capture
                            and distraction-free drafting.
                            </p>
                            <div className="flex flex-wrap gap-2 mb-2">
                            {["HTML", "CSS"].map((tech, key) => (
                                <span
                                key={key}
                                className="bg-blue/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition"
                                >
                                {tech}
                                </span>
                            ))}
                            </div>
                            <div className="flex justify-between items-center">
                            <a href="https://github.com/kubaman9/InfaNote" className="text-blue-500 hover:text-blue-300 transition-colors my-4">
                                View Project
                            </a>
                            </div>
                    </div>

                    <div className="p-6 rounded-xl border border-white/10 hover:-translate-y-1 hover:border-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,2246,0.2)] transition text-left">
                        <h2 className="text-xl font-bold mb-2">PyTest Projects (GUI Utilities)</h2>
                        <p className="text-gray-400 mb-4">
                        A collection of small Python GUI tools—including a web scraper, calculator, graph visualizer,
                        and image modifier—organized for quick experimentation and learning across multiple
                        desktop-app patterns.
                        </p>
                        <div className="flex flex-wrap gap-2 mb-2">
                        {["Python", "GUI"].map((tech, key) => (
                            <span
                            key={key}
                            className="bg-blue/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition"
                            >
                            {tech}
                            </span>
                        ))}
                        </div>
                        <div className="flex justify-between items-center">
                        <a href="https://github.com/kubaman9/PyTestProjects" className="text-blue-500 hover:text-blue-300 transition-colors my-4">
                            View Project
                        </a>
                        </div>

                    </div>

                    <div className="p-6 rounded-xl border border-white/10 hover:-translate-y-1 hover:border-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,2246,0.2)] transition text-left">
                        <h2 className="text-xl font-bold mb-2">Project9Jakub (Cloud To-Do)</h2>
                            <p className="text-gray-400 mb-4">
                            A Kotlin Android to-do app that authenticates users by email and syncs lists to a cloud
                            datastore—designed to keep tasks consistent across sessions and devices with a straightforward,
                            mobile-first UX.
                            </p>
                            <div className="flex flex-wrap gap-2 mb-2">
                            {["Kotlin", "Android", "Cloud Database", "Auth"].map((tech, key) => (
                                <span
                                key={key}
                                className="bg-blue/10 text-blue-500 py-1 px-3 rounded-full text-sm hover:bg-blue-500/30 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] transition"
                                >
                                {tech}
                                </span>
                            ))}
                            </div>
                            <div className="flex justify-between items-center">
                            <a href="https://github.com/kubaman9/Project9Jakub" className="text-blue-500 hover:text-blue-300 transition-colors my-4">
                                View Project
                            </a>
                            </div>


                    </div>
                </div>
            </div>
            </RevealOnScroll>
        </section>
    );

};