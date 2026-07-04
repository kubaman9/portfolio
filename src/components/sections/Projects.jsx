import { RevealOnScroll } from "../RevealOnScroll";
import { SectionPrompt, Prompt } from "../Prompt";

const featured = [
    {
        name: "ironlog",
        title: "IronLog + IronLogAPI",
        year: "2026",
        description:
            "Full-stack lift-tracking web app: a TypeScript frontend for logging workouts and " +
            "tracking progress, backed by a custom REST API I built from scratch (IronLogAPI).",
        tech: ["TypeScript", "JavaScript", "Node.js", "REST API"],
        link: "https://github.com/kubaman9/IronLog",
    },
    {
        name: "watchnext",
        title: "WatchNext",
        year: "2026",
        description:
            "A JavaScript web app for tracking movies and shows and deciding what to watch next — " +
            "my latest build, actively in development.",
        tech: ["JavaScript", "Web"],
        link: "https://github.com/kubaman9/WatchNext",
    },
    {
        name: "mma-predictor",
        title: "MMA Predictor",
        year: "2026",
        description:
            "A Python project that predicts MMA fight outcomes — combining my black-belt-level " +
            "obsession with martial arts and my interest in data-driven prediction.",
        tech: ["Python", "Data"],
        link: "https://github.com/kubaman9/MMA-predictor",
    },
    {
        name: "aib-website",
        title: "AI in Business Club Website",
        year: "2025",
        description:
            "The official website I built and maintain for the AI in Business Club at Indiana " +
            "University, where I serve as Vice President.",
        tech: ["JavaScript", "Web"],
        link: "https://github.com/kubaman9/AIBWebsite",
    },
    {
        name: "portfolio",
        title: "Jakub.AI Portfolio (this site)",
        year: "2025–2026",
        description:
            "You're looking at it: a React + Vite terminal-themed portfolio with a Gemini-powered " +
            "AI chatbot that answers recruiter questions about me, plus an EmailJS contact form.",
        tech: ["React", "Vite", "TailwindCSS", "Gemini API"],
        link: "https://github.com/kubaman9/portfolio",
    },
    {
        name: "listapp",
        title: "ListApp (Android)",
        year: "2024",
        description:
            "An Android list manager with local persistence, user authentication, token-based " +
            "list flows, and a clean Kotlin/Gradle setup.",
        tech: ["Kotlin", "Android", "Gradle"],
        link: "https://github.com/kubaman9/ListApp",
    },
];

const allRepos = [
    { name: "WatchNext",     lang: "JavaScript", year: "2026", link: "https://github.com/kubaman9/WatchNext" },
    { name: "IronLogAPI",    lang: "JavaScript", year: "2026", link: "https://github.com/kubaman9/IronLogAPI" },
    { name: "IronLog",       lang: "TypeScript", year: "2026", link: "https://github.com/kubaman9/IronLog" },
    { name: "FolderParser",  lang: "Utility",    year: "2026", link: "https://github.com/kubaman9/FolderParser" },
    { name: "MMA-predictor", lang: "Python",     year: "2026", link: "https://github.com/kubaman9/MMA-predictor" },
    { name: "AIBWebsite",    lang: "JavaScript", year: "2025", link: "https://github.com/kubaman9/AIBWebsite" },
    { name: "portfolio",     lang: "JavaScript", year: "2025", link: "https://github.com/kubaman9/portfolio" },
    { name: "InfaNote",      lang: "HTML/CSS",   year: "2025", link: "https://github.com/kubaman9/InfaNote" },
    { name: "PyTestProjects",lang: "Python",     year: "2025", link: "https://github.com/kubaman9/PyTestProjects" },
    { name: "ListApp",       lang: "Kotlin",     year: "2024", link: "https://github.com/kubaman9/ListApp" },
    { name: "Project9Jakub", lang: "Kotlin",     year: "2024", link: "https://github.com/kubaman9/Project9Jakub" },
    { name: "MobileDev",     lang: "Mobile",     year: "2024", link: "https://github.com/kubaman9/MobileDev" },
    { name: "Chillis",       lang: "Swift",      year: "2019", link: "https://github.com/kubaman9/Chillis" },
];

export const Projects = () => {
    return (
        <section id="projects" className="min-h-screen flex items-center justify-center py-24">
            <RevealOnScroll>
                <div className="max-w-5xl mx-auto px-4 w-full">
                    <SectionPrompt path="~/projects" command="ls --featured" />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
                        {featured.map((project) => (
                            <div
                                key={project.name}
                                className="term-window transition-all hover:-translate-y-1 flex flex-col"
                            >
                                <div className="term-titlebar">
                                    <span className="term-dot" style={{ background: "#f87171" }} />
                                    <span className="term-dot" style={{ background: "#fbbf24" }} />
                                    <span className="term-dot" style={{ background: "#4ade80" }} />
                                    <span className="ml-2">{project.name}.sh — {project.year}</span>
                                </div>

                                <div className="p-5 sm:p-6 flex flex-col flex-1 text-sm sm:text-base">
                                    <h3 className="font-bold mb-2 term-glow" style={{ color: "var(--term-green)" }}>
                                        {project.title}
                                    </h3>
                                    <p className="term-output mb-4 flex-1 leading-relaxed">
                                        <span className="term-comment">&gt; </span>
                                        {project.description}
                                    </p>
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {project.tech.map((tech) => (
                                            <span key={tech} className="term-tag">{tech}</span>
                                        ))}
                                    </div>
                                    <a
                                        href={project.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="term-link text-sm"
                                    >
                                        $ git clone {project.link.replace("https://", "")}.git
                                    </a>
                                </div>
                            </div>
                        ))}
                    </div>

                    <SectionPrompt path="~/projects" command="ls -la ~/github --sort=year" />

                    <div className="term-window">
                        <div className="term-titlebar">
                            <span className="term-dot" style={{ background: "#f87171" }} />
                            <span className="term-dot" style={{ background: "#fbbf24" }} />
                            <span className="term-dot" style={{ background: "#4ade80" }} />
                            <span className="ml-2">github.com/kubaman9 — {allRepos.length} public repos</span>
                        </div>

                        <div className="p-5 sm:p-6 overflow-x-auto">
                            <table className="w-full text-xs sm:text-sm whitespace-nowrap">
                                <tbody>
                                    {allRepos.map((repo) => (
                                        <tr key={repo.name} className="group">
                                            <td className="term-comment pr-4 py-1.5">drwxr-xr-x</td>
                                            <td className="pr-4 py-1.5" style={{ color: "var(--term-amber)" }}>{repo.year}</td>
                                            <td className="pr-4 py-1.5">
                                                <a
                                                    href={repo.link}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="term-link font-bold"
                                                >
                                                    {repo.name}/
                                                </a>
                                            </td>
                                            <td className="term-comment py-1.5">{repo.lang}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--term-border)" }}>
                                <Prompt
                                    path="~/projects"
                                    command={
                                        <a
                                            href="https://github.com/kubaman9"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="term-link"
                                        >
                                            open github.com/kubaman9 →
                                        </a>
                                    }
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </RevealOnScroll>
        </section>
    );
};
