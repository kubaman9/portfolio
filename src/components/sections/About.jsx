import { RevealOnScroll } from "../RevealOnScroll";
import { SectionPrompt, Prompt } from "../Prompt";

const languages = ["Java", "Python", "C#", "C++", "C", "JavaScript", "TypeScript", "PHP", "Swift", "Kotlin", "SQL", "HTML", "CSS"];
const toolsAndFrameworks = [
    "React", ".NET / ASP.NET Core", "GraphQL", "REST APIs", "MySQL", "Scikit-learn", "NumPy", "n8n",
    "Node.js", "Vite", "TailwindCSS", "Android", "MongoDB", "Firebase", "Git",
];

export const About = () => {
    return (
        <section id="about" className="min-h-screen flex items-center justify-center py-24">
            <RevealOnScroll>
                <div className="max-w-3xl mx-auto px-4 w-full">
                    <SectionPrompt path="~/about" command="cat about.txt" />

                    <div className="term-window transition-all hover:-translate-y-1">
                        <div className="term-titlebar">
                            <span className="term-dot" style={{ background: "#f87171" }} />
                            <span className="term-dot" style={{ background: "#fbbf24" }} />
                            <span className="term-dot" style={{ background: "#4ade80" }} />
                            <span className="ml-2">about.txt — less</span>
                        </div>

                        <div className="p-6 sm:p-8 text-sm sm:text-base">
                            <p className="term-output mb-8 leading-relaxed">
                                <span className="term-comment"># whoami, in more than one line</span>
                                <br />
                                I enjoy tackling challenges across the whole stack — from Android apps in Kotlin
                                to full-stack web apps with custom APIs to AI-powered tools. As a Software Development
                                Intern at Trim-Tex, I built and shipped four internal tools now used across the business
                                every day, from ERP-integrated dashboards to a UPS API integration. Beyond coding, I bring
                                strengths in leadership, problem-solving, and building bridges between business and
                                technology: whether it's debugging complex code or organizing guest lectures with
                                industry leaders, I combine technical know-how with communication and collaboration.
                            </p>

                            <div className="mb-8">
                                <Prompt path="~/about" command="ls skills/languages/" className="mb-3" />
                                <div className="flex flex-wrap gap-2">
                                    {languages.map((tech) => (
                                        <span key={tech} className="term-tag">{tech}</span>
                                    ))}
                                </div>
                            </div>

                            <div className="mb-8">
                                <Prompt path="~/about" command="ls skills/tools/" className="mb-3" />
                                <div className="flex flex-wrap gap-2">
                                    {toolsAndFrameworks.map((tech) => (
                                        <span key={tech} className="term-tag">{tech}</span>
                                    ))}
                                </div>
                            </div>

                            <div className="mb-8">
                                <Prompt path="~/about" command="cat education.log" className="mb-3" />
                                <div className="term-output space-y-2 pl-4" style={{ borderLeft: "2px solid var(--term-border)" }}>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[2023–2027]</span>{" "}
                                        <strong>B.S. Computer Science (AI Specialization), Minor in Business</strong> —
                                        Indiana University, Bloomington (Luddy School of Informatics, Direct Admit).
                                        Expected May 2027. Merit scholarship.
                                    </p>
                                    <p className="term-comment">
                                        coursework: data-structures discrete-structures systems-programming-c-unix
                                        software-systems mobile-app-development php-web-development intro-to-programming
                                    </p>
                                </div>
                            </div>

                            <div className="mb-8">
                                <Prompt path="~/about" command="cat experience.log" className="mb-3" />
                                <div className="term-output space-y-3 pl-4" style={{ borderLeft: "2px solid var(--term-border)" }}>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[May 2026 – Aug 2026]</span>{" "}
                                        <strong>Software Development Intern, IT/IS — Trim-Tex Inc.</strong> (Lincolnwood, IL).
                                        Built and shipped four internal tools now used across the business every day:
                                        rebuilt the plant maintenance system (asset and work-order tracking with automated
                                        Teams alerts) to replace a legacy app, moved production scheduling off a physical
                                        whiteboard onto a live drag-and-drop dashboard tied directly to the ERP, developed a
                                        UPS rate-quoting tool on the UPS API plus a tool that automatically organizes customer
                                        files, and connected the ERP to surrounding systems while delivering the company's
                                        first digital form.
                                    </p>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[Dec 2019 – now]</span>{" "}
                                        <strong>Martial Arts Instructor — DK Fitness Arts</strong> (Arlington Heights, IL).
                                        Instructing children ages 3–14 in discipline, focus and fitness, and keeping parents
                                        informed on their progress.
                                    </p>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[Jun 2023 – Aug 2023]</span>{" "}
                                        <strong>Lifeguard — Mount Prospect Park District.</strong> Certified emergency
                                        responder (CPR and lifesaving); enforced health and safety regulations.
                                    </p>
                                </div>
                            </div>

                            <div>
                                <Prompt path="~/about" command="cat leadership.log" className="mb-3" />
                                <div className="term-output space-y-2 pl-4" style={{ borderLeft: "2px solid var(--term-border)" }}>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[Aug 2024 – now]</span>{" "}
                                        <strong>President — AI in Business Club, IU.</strong> Leading the club's strategy,
                                        events and member programming, including Welcome Week recruiting and a semester
                                        Callout Night. Designed and built the club website in React and JavaScript with an
                                        AI chatbot on the Gemini API, and coordinate guest lectures with industry leaders
                                        from companies like Gillson Capital, Accenture and Blockboard on practical AI in
                                        business.
                                    </p>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[Jan 2024 – now]</span>{" "}
                                        <strong>Alpha Sigma Phi.</strong> Raised $5,000 in three weeks through creative
                                        fundraising and hosted a social event for RAINN; ongoing campus philanthropy.
                                    </p>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[Feb 2020 – now]</span>{" "}
                                        <strong>Masters Club — 3rd Dan Black Belt.</strong> Mentoring peers for competitions;
                                        completed leadership and instructional development seminars.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </RevealOnScroll>
        </section>
    );
};
