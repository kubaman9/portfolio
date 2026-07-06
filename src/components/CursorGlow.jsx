import { useEffect, useRef } from "react";

/** Soft light-blue spotlight that follows the mouse, like a phosphor glow under the cursor. */
export const CursorGlow = () => {
  const ref = useRef(null);

  useEffect(() => {
    // Skip entirely on touch-only devices
    if (window.matchMedia("(pointer: coarse)").matches) return;

    let raf = 0;
    const onMove = (e) => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        if (ref.current) {
          ref.current.style.background = `radial-gradient(560px circle at ${e.clientX}px ${e.clientY}px, rgba(125, 211, 252, 0.07), transparent 65%)`;
        }
      });
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    return () => {
      window.removeEventListener("mousemove", onMove);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return <div ref={ref} className="cursor-glow" aria-hidden="true" />;
};
