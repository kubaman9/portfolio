import { useEffect, useRef, useState } from "react";

const CHARS = "アイウエオカキクケコサシスセソ0123456789ABCDEF<>/{}[]$#*+=";
const RUN_MS = 9000;

/**
 * Light-blue Matrix rain easter egg.
 * Trigger anywhere with: window.dispatchEvent(new CustomEvent("jakub:matrix"))
 * Stops on its own after ~9s, or on Escape.
 */
export const MatrixRain = () => {
  const canvasRef = useRef(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const start = () => setActive(true);
    window.addEventListener("jakub:matrix", start);
    return () => window.removeEventListener("jakub:matrix", start);
  }, []);

  useEffect(() => {
    if (!active) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const fontSize = 16;
    const columns = Math.ceil(canvas.width / fontSize);
    const drops = Array.from({ length: columns }, () => Math.floor(Math.random() * -40));

    let raf = 0;
    const draw = () => {
      // fading trail
      ctx.fillStyle = "rgba(9, 14, 20, 0.12)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = `${fontSize}px monospace`;

      for (let i = 0; i < drops.length; i++) {
        const char = CHARS[Math.floor(Math.random() * CHARS.length)];
        const x = i * fontSize;
        const y = drops[i] * fontSize;

        // leading char brighter
        ctx.fillStyle = Math.random() > 0.92 ? "#e0f2fe" : "#7dd3fc";
        ctx.fillText(char, x, y);

        if (y > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }

      raf = requestAnimationFrame(draw);
    };
    draw();

    const stopTimer = setTimeout(() => setActive(false), RUN_MS);
    const onKey = (e) => e.key === "Escape" && setActive(false);
    window.addEventListener("keydown", onKey);

    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(stopTimer);
      window.removeEventListener("keydown", onKey);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [active]);

  return <canvas ref={canvasRef} className={`matrix-canvas ${active ? "on" : ""}`} aria-hidden="true" />;
};
