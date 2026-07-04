import { useEffect, useState } from "react";
import { RevealOnScroll } from "../RevealOnScroll";
import { Prompt } from "../Prompt";

const banner = `     ██╗ █████╗ ██╗  ██╗██╗   ██╗██████╗
     ██║██╔══██╗██║ ██╔╝██║   ██║██╔══██╗
     ██║███████║█████╔╝ ██║   ██║██████╔╝
██   ██║██╔══██║██╔═██╗ ██║   ██║██╔══██╗
╚█████╔╝██║  ██║██║  ██╗╚██████╔╝██████╔╝
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝`;

const roles = [
  "software engineer",
  "full-stack developer",
  "AI builder",
  "CS senior @ Indiana University",
  "2nd dan black belt",
];

/** Cycling typewriter effect */
const TypeWriter = () => {
  const [roleIndex, setRoleIndex] = useState(0);
  const [text, setText] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const current = roles[roleIndex];
    const timeout = setTimeout(() => {
      if (!deleting) {
        const next = current.substring(0, text.length + 1);
        setText(next);
        if (next === current) setTimeout(() => setDeleting(true), 1600);
      } else {
        const next = current.substring(0, text.length - 1);
        setText(next);
        if (next === "") {
          setDeleting(false);
          setRoleIndex((i) => (i + 1) % roles.length);
        }
      }
    }, deleting ? 35 : 70);

    return () => clearTimeout(timeout);
  }, [text, deleting, roleIndex]);

  return (
    <span>
      <span className="term-glow" style={{ color: "var(--term-green)" }}>{text}</span>
      <span className="cursor-block ml-1" />
    </span>
  );
};

export const Home = () => {
  return (
    <section id="home" className="min-h-screen flex items-center justify-center py-24">
      <RevealOnScroll>
        <div className="max-w-3xl mx-auto px-4 w-full">
          <Prompt path="~" command="whoami" className="mb-6" />

          <pre className="ascii-banner mb-2 term-flicker" aria-hidden="true">{banner}</pre>
          <p className="sr-only">Jakub Kielczewski</p>

          <p className="text-base sm:text-lg mb-6 mt-4">
            <span className="term-comment"># </span>
            <TypeWriter />
          </p>

          <div className="text-sm sm:text-base space-y-1 mb-10 term-output">
            <p>
              <span className="term-comment">&gt; </span>
              I'm <span style={{ color: "var(--term-green)" }}>Jakub (Kuba) Kielczewski</span> — a Computer
              Science senior at Indiana University, graduating May 2027.
            </p>
            <p>
              <span className="term-comment">&gt; </span>
              I build full-stack apps, AI-powered tools, and Android software — and as VP of the
              AI in Business Club, I connect engineers with the people who need them.
            </p>
            <p>
              <span className="term-comment">&gt; </span>
              Off the keyboard: teaching martial arts, exploring outdoors, mentoring.
            </p>
          </div>

          <div className="flex flex-wrap gap-4">
            <a href="#projects" className="term-btn term-btn-solid">
              ./view_projects.sh
            </a>
            <a href="#contact" className="term-btn">
              ./contact_me.sh
            </a>
          </div>
        </div>
      </RevealOnScroll>
    </section>
  );
};
