import { RevealOnScroll } from "../RevealOnScroll";
import { SectionPrompt, Prompt } from "../Prompt";

const languages = ["Java", "Python", "JavaScript", "TypeScript", "Kotlin", "Swift", "C", "C++", "C#", "PHP"];
const toolsAndFrameworks = ["React", "Vite", "TailwindCSS", "Node.js", "Android", "Gradle", "MySQL", "Firebase", "MongoDB", "Git"];

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
                                to full-stack web apps with custom APIs to AI-powered tools. Beyond coding, I bring
                                strengths in leadership, problem-solving, and building bridges between business and
                                technology: whether it's debugging complex code or organizing guest lectures with
                                industry leaders, I combine technical know-how with communication and collaboration.
                            </p>

                            <div className="mb-8">
                                <Prompt path="~/about" command="ls skills/languages/" className="mb-3" />
                                <RevealOnScroll variant="stagger" className="flex flex-wrap gap-2">
                                    {languages.map((tech) => (
                                        <span key={tech} className="term-tag">{tech}</span>
                                    ))}
                                </RevealOnScroll>
                            </div>

                            <div className="mb-8">
                                <Prompt path="~/about" command="ls skills/tools/" className="mb-3" />
                                <RevealOnScroll variant="stagger" className="flex flex-wrap gap-2">
                                    {toolsAndFrameworks.map((tech) => (
                                        <span key={tech} className="term-tag">{tech}</span>
                                    ))}
                                </RevealOnScroll>
                            </div>

                            <div className="mb-8">
                                <Prompt path="~/about" command="cat education.log" className="mb-3" />
                                <RevealOnScroll
                                    variant="stagger"
                                    className="term-output space-y-2 pl-4"
                                    style={{ borderLeft: "2px solid var(--term-border)" }}
                                >
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[2023–2027]</span>{" "}
                                        <strong>B.S. Computer Science, Minor in Business</strong> — Indiana University,
                                        Bloomington (Luddy School, Direct Admit). Expected May 2027. Merit scholarship.
                                    </p>
                                    <p className="term-comment">
                                        coursework: discrete-structures software-systems mobile-app-development
                                    </p>
                                </RevealOnScroll>
                            </div>

                            <div>
                                <Prompt path="~/about" command="cat leadership.log" className="mb-3" />
                                <RevealOnScroll
                                    variant="stagger"
                                    className="term-output space-y-2 pl-4"
                                    style={{ borderLeft: "2px solid var(--term-border)" }}
                                >
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[2024–now]</span>{" "}
                                        <strong>Vice President — AI in Business Club, IU.</strong> Organizing guest
                                        lectures and connecting students with industry AI experts. Built the club's
                                        website.
                                    </p>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[2019–now]</span>{" "}
                                        <strong>Martial Arts Instructor — DK Fitness Arts.</strong> 2nd Dan black belt.
                                        Leading classes (ages 3–14) and mentoring students.
                                    </p>
                                    <p>
                                        <span style={{ color: "var(--term-green)" }}>[ongoing]</span>{" "}
                                        <strong>Alpha Sigma Phi.</strong> Helped raise $5,000 in three weeks for RAINN.
                                    </p>
                                </RevealOnScroll>
                            </div>
                        </div>
                    </div>
                </div>
            </RevealOnScroll>
        </section>
    );
};
