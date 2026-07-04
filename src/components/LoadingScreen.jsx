import { useEffect, useState } from "react";

const bootLines = [
  "[ OK ] Mounting /dev/jakub ...",
  "[ OK ] Loading skills: java python js kotlin swift c++ ...",
  "[ OK ] Starting ai-in-business.service ...",
  "[ OK ] Compiling portfolio v3.0 ...",
  "[ OK ] Establishing connection ...",
];

export const LoadingScreen = ({ onComplete }) => {
  const [lines, setLines] = useState([]);
  const [text, setText] = useState("");
  const fullText = "ssh recruiter@jakub.ai";

  // Type the ssh command first, then print boot lines
  useEffect(() => {
    let index = 0;
    const typing = setInterval(() => {
      setText(fullText.substring(0, index));
      index++;

      if (index > fullText.length) {
        clearInterval(typing);

        let line = 0;
        const printer = setInterval(() => {
          line++;
          setLines(bootLines.slice(0, line));
          if (line >= bootLines.length) {
            clearInterval(printer);
            setTimeout(() => onComplete(), 700);
          }
        }, 220);
      }
    }, 55);

    return () => clearInterval(typing);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-50 crt flex flex-col items-center justify-center px-4" style={{ background: "var(--term-bg)" }}>
      <div className="w-full max-w-xl text-left">
        <p className="text-lg sm:text-2xl font-bold mb-4">
          <span className="prompt-user">guest@web</span>
          <span className="term-comment">:</span>
          <span className="prompt-path">~</span>
          <span className="prompt-symbol">$ </span>
          <span className="term-output">{text}</span>
          <span className="cursor-block ml-1" />
        </p>

        <div className="text-xs sm:text-sm space-y-1 min-h-[7rem]">
          {lines.map((line, i) => (
            <p key={i}>
              <span className="prompt-user">{line.slice(0, 6)}</span>
              <span className="term-comment">{line.slice(6)}</span>
            </p>
          ))}
        </div>

        <div className="mt-6 w-full h-[4px] rounded relative overflow-hidden" style={{ background: "rgba(74,222,128,0.12)" }}>
          <div className="w-[20%] h-full animate-loading-bar" style={{ background: "var(--term-green)", boxShadow: "0 0 15px rgba(74,222,128,0.8)" }} />
        </div>
      </div>
    </div>
  );
};
