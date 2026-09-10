import { useEffect, useRef, useState } from "react";
import { RevealOnScroll } from "../RevealOnScroll";
import { Prompt } from "../Prompt";
import { HeroTerminal } from "../HeroTerminal";

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
  "ex-intern @ Trim-Tex",
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
      <span className="term-glow" style={{ color: "var(--term-accent)" }}>{text}</span>
      <span className="cursor-block ml-1" />
    </span>
  );
};

export const Home = () => {
  const bannerRef = useRef(null);

  // Subtle parallax: banner drifts up slower than the page and fades as you scroll away
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let raf = 0;
    const onScroll = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const el = bannerRef.current;
        if (!el) return;
        const y = window.scrollY;
        el.style.transform = `translateY(${y * 0.18}px)`;
        el.style.opacity = `${Math.max(0, 1 - y / 600)}`;
      });
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section id="home" className="min-h-screen flex items-center justify-center py-24">
      <RevealOnScroll>
        <div className="max-w-3xl mx-auto px-4 w-full">
          <Prompt path="~" command="whoami" className="mb-6" />

          <pre ref={bannerRef} className="ascii-banner mb-2 term-flicker" aria-hidden="true">{banner}</pre>
          <p className="sr-only">Jakub Kielczewski</p>

          <p className="text-base sm:text-lg mb-6 mt-4">
            <span className="term-comment"># </span>
            <TypeWriter />
          </p>

          <RevealOnScroll variant="stagger" className="text-sm sm:text-base space-y-1 mb-10 term-output">
            <p>
              <span className="term-comment">&gt; </span>
              I'm <span style={{ color: "var(--term-accent)" }}>Jakub (Kuba) Kielczewski</span> — a Computer
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
          </RevealOnScroll>

          <RevealOnScroll variant="stagger" className="flex flex-wrap gap-4">
            <a href="#projects" className="term-btn term-btn-solid">
              ./view_projects.sh
            </a>
            <a href="#contact" className="term-btn">
              ./contact_me.sh
            </a>
          </RevealOnScroll>

          <HeroTerminal />
        </div>
      </RevealOnScroll>
    </section>
  );
};
