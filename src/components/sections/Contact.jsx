import { useState } from "react";
import { RevealOnScroll } from "../RevealOnScroll";
import { SectionPrompt } from "../Prompt";
import emailjs from "@emailjs/browser";

export const Contact = () => {
  const [formData, setFormData] = useState({ name: "", email: "", message: "" });
  const [status, setStatus] = useState("idle"); // idle | sending | sent | error

  const handleSubmit = (e) => {
    e.preventDefault();
    setStatus("sending");

    emailjs
      .sendForm("service_fersdcf", 'template_uz4tgdj', e.target, 'EiJleWTavSt29u8Do')
      .then(() => {
        setStatus("sent");
        setFormData({ name: "", email: "", message: "" });
      })
      .catch(() => setStatus("error"));
  };

  return (
    <section id="contact" className="min-h-screen flex items-center justify-center py-24">
      <RevealOnScroll>
        <div className="px-4 w-full max-w-xl mx-auto">
          <SectionPrompt path="~/contact" command="./send_message.sh" />

          <div className="term-window">
            <div className="term-titlebar">
              <span className="term-dot" style={{ background: "#f87171" }} />
              <span className="term-dot" style={{ background: "#fbbf24" }} />
              <span className="term-dot" style={{ background: "#4ade80" }} />
              <span className="ml-2">send_message.sh — interactive</span>
            </div>

            <div className="p-6 sm:p-8">
              <p className="term-output text-sm mb-6">
                <span className="term-comment"># </span>
                Interested in working together, or just want to say hi? Fill in the fields below,
                or reach me directly at{" "}
                <a href="mailto:jkielcz@iu.edu" className="term-link">jkielcz@iu.edu</a>.
              </p>

              <form onSubmit={handleSubmit}>
              <RevealOnScroll variant="stagger" className="space-y-5">
                <div>
                  <label htmlFor="name" className="block text-sm mb-1">
                    <span className="prompt-symbol">$ </span>
                    <span className="prompt-user">enter_name:</span>
                  </label>
                  <input
                    value={formData.name}
                    type="text"
                    id="name"
                    name="name"
                    required
                    className="term-input"
                    placeholder="Jane Recruiter"
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm mb-1">
                    <span className="prompt-symbol">$ </span>
                    <span className="prompt-user">enter_email:</span>
                  </label>
                  <input
                    value={formData.email}
                    type="email"
                    id="email"
                    name="email"
                    required
                    className="term-input"
                    placeholder="you@example.com"
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm mb-1">
                    <span className="prompt-symbol">$ </span>
                    <span className="prompt-user">enter_message:</span>
                  </label>
                  <textarea
                    value={formData.message}
                    name="message"
                    id="message"
                    required
                    rows={5}
                    className="term-input"
                    placeholder="We'd love to interview you..."
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  ></textarea>
                </div>

                <button
                  type="submit"
                  disabled={status === "sending"}
                  className="term-btn term-btn-solid w-full disabled:opacity-60"
                >
                  {status === "sending" ? "sending ▓▓▓░░░ ..." : "./send_message.sh --execute"}
                </button>

                {status === "sent" && (
                  <p className="text-sm" role="status" style={{ color: "var(--term-green)" }}>
                    [ OK ] Message sent — exit code 0. I'll get back to you soon!
                  </p>
                )}
                {status === "error" && (
                  <p className="text-sm" role="alert" style={{ color: "#f87171" }}>
                    [FAIL] Something went wrong — try again or email me directly.
                  </p>
                )}
              </RevealOnScroll>
              </form>
            </div>
          </div>
        </div>
      </RevealOnScroll>
    </section>
  );
};
