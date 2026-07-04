import { useEffect, useRef } from "react";

const variantClass = {
  fade: "reveal",
  stagger: "reveal-stagger",
  scan: "reveal-scan",
};

/**
 * Scroll-triggered reveal.
 * variant="fade"    fade + slide up (default)
 * variant="stagger" cascades direct children in one by one, like terminal output printing
 * variant="scan"    text wipes in left-to-right, like a line being typed
 */
export const RevealOnScroll = ({
  children,
  variant = "fade",
  delay = 0,
  className = "",
  style,
  as,
}) => {
  const Tag = as || "div";
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("visible");
          observer.unobserve(el);
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -50px 0px" }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      className={`${variantClass[variant] || "reveal"} ${className}`}
      style={delay ? { ...style, transitionDelay: `${delay}ms` } : style}
    >
      {children}
    </Tag>
  );
};
