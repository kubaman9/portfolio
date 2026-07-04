import { RevealOnScroll } from "./RevealOnScroll";

/** A shell prompt line: jakub@iu:~$ <command> */
export const Prompt = ({ path = "~", command, className = "" }) => (
  <p className={`text-sm sm:text-base ${className}`}>
    <span className="prompt-user">jakub@iu</span>
    <span className="term-comment">:</span>
    <span className="prompt-path">{path}</span>
    <span className="prompt-symbol">$ </span>
    <span className="term-output">{command}</span>
  </p>
);

/** Section heading rendered as a typed command that wipes in on scroll */
export const SectionPrompt = ({ path = "~", command }) => (
  <div className="mb-8">
    <RevealOnScroll variant="scan">
      <Prompt path={path} command={command} className="text-lg sm:text-xl font-bold term-glow" />
    </RevealOnScroll>
  </div>
);
