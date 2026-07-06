import { useRef, useState } from "react";

const MAX_TILT = 5; // degrees

/** Wraps a card in a subtle 3D tilt-toward-cursor effect with a moving glare highlight. */
export const TiltCard = ({ children, className = "" }) => {
  const ref = useRef(null);
  const [tilting, setTilting] = useState(false);

  const onMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;

    const rotY = (px - 0.5) * 2 * MAX_TILT;
    const rotX = (0.5 - py) * 2 * MAX_TILT;

    el.style.transform = `rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-4px)`;
    el.style.setProperty("--glare-x", `${(px * 100).toFixed(1)}%`);
    el.style.setProperty("--glare-y", `${(py * 100).toFixed(1)}%`);
  };

  const onLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = "";
    setTilting(false);
  };

  return (
    <div className="tilt-wrap h-full">
      <div
        ref={ref}
        className={`tilt-card ${tilting ? "tilting" : ""} ${className}`}
        onMouseMove={onMove}
        onMouseEnter={() => setTilting(true)}
        onMouseLeave={onLeave}
      >
        {children}
        <span className="tilt-glare" aria-hidden="true" />
      </div>
    </div>
  );
};
