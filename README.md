# Jakub.AI — Personal Portfolio

Personal portfolio site for **Jakub (Kuba) Kielczewski** — Computer Science senior at
Indiana University (Luddy School), graduating May 2027.

**Live site:** https://kubaman9.github.io/portfolio

## Features

- Single-page React app with scroll-reveal animations
- About, Projects, and Contact sections
- Contact form powered by EmailJS
- Built-in AI chatbot (Google Gemini) that answers recruiter questions about me

## Tech Stack

- [React 19](https://react.dev) + [Vite](https://vite.dev)
- [TailwindCSS 4](https://tailwindcss.com)
- [EmailJS](https://www.emailjs.com/) for the contact form
- Google Gemini API for the chatbot

## Development

```bash
npm install
npm run dev      # local dev server
npm run build    # production build
npm run lint     # eslint
npm run deploy   # publish to GitHub Pages
```

To use your own Gemini API key for the chatbot, set `VITE_GEMINI_API_KEY` in a `.env`
file at the project root.
