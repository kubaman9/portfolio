import { useState } from "react";
import { RevealOnScroll } from "../RevealOnScroll";
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
    <section id="contact" className="min-h-screen flex items-center justify-center py-20">
      <RevealOnScroll>
        <div className="px-4 w-full max-w-xl">
          <h2 className="text-3xl font-bold mb-4 bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent text-center">
            Get In Touch
          </h2>

          <p className="text-gray-400 text-center mb-8">
            Interested in working together, or just want to say hi? Drop me a message below,
            or reach me directly at{" "}
            <a href="mailto:jkielcz@iu.edu" className="text-blue-500 hover:text-blue-300 transition-colors">
              jkielcz@iu.edu
            </a>.
          </p>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="relative">
              <input
                value={formData.name}
                type="text"
                id="name"
                name="name"
                required
                className="w-full bg-white/5 border border-white/10 rounded px-4 py-3 text-white transition focus:outline-none focus:border-blue-500 focus:bg-blue-500/5"
                placeholder="Name..."
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="relative">
              <input
                value={formData.email}
                type="email"
                id="email"
                name="email"
                required
                className="w-full bg-white/5 border border-white/10 rounded px-4 py-3 text-white transition focus:outline-none focus:border-blue-500 focus:bg-blue-500/5"
                placeholder="you@example.com"
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>

            <div>
              <textarea
                value={formData.message}
                name="message"
                id="message"
                required
                rows={5}
                className="w-full bg-white/5 border border-white/10 rounded px-4 py-3 text-white transition focus:outline-none focus:border-blue-500"
                placeholder="Message..."
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
              ></textarea>
            </div>

            <button
              type="submit"
              disabled={status === "sending"}
              className="w-full bg-blue-500 text-white py-3 px-6 rounded font-medium transition relative overflow-hidden hover:-translate-y-0.5 hover:shadow-[0_2px_8px_rgba(59,130,246,0.2)] disabled:opacity-60 disabled:hover:translate-y-0"
            >
              {status === "sending" ? "Sending…" : "Send Message"}
            </button>

            {status === "sent" && (
              <p className="text-center text-green-400" role="status">
                Message sent — thanks! I'll get back to you soon.
              </p>
            )}
            {status === "error" && (
              <p className="text-center text-red-400" role="alert">
                Oops, something went wrong. Please try again or email me directly.
              </p>
            )}
          </form>
        </div>
      </RevealOnScroll>
    </section>
  );
};
