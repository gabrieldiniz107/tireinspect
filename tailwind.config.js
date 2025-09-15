/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./core/templates/**/*.html",
    "./**/templates/**/*.html",
    "./**/*.py",
    "./**/site-packages/crispy_tailwind/**/*.html",
    "./venv/**/site-packages/crispy_tailwind/**/*.html",
    "./env/**/site-packages/crispy_tailwind/**/*.html",
    "./.venv/**/site-packages/crispy_tailwind/**/*.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#FFD100",
        secondary: "#111111",
      },
    },
  },
  plugins: [],
};

