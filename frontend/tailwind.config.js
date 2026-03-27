/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary:          "#00ffb4",
        secondary:        "#00c8ff",
        tertiary:         "#a78bfa",
        background:       "#10131a",
        surface:          "#10131a",
        "surface-dim":    "#10131a",
        "surface-container-lowest": "#0b0e14",
        "surface-container-low":    "#181c22",
        "surface-container":        "#1c2026",
        "surface-container-high":   "#272a31",
        "surface-container-highest":"#31353c",
        "on-surface":     "#e0e2eb",
        "on-surface-variant": "#b9cbbf",
        "outline":        "#83958a",
        "outline-variant":"#3a4a41",
        "primary-container": "#00ffb4",
        "on-primary":     "#003825",
        error:            "#ffb4ab",
        "error-container":"#93000a",
      },
      fontFamily: {
        headline: ["Space Grotesk", "sans-serif"],
        body:     ["DM Sans", "sans-serif"],
        mono:     ["Space Mono", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg:  "0.5rem",
        xl:  "12px",
        "2xl": "18px",
        full: "9999px",
      },
      backgroundImage: {
        "velocity-gradient": "linear-gradient(90deg, #00ffb4 0%, #00c8ff 100%)",
      },
    },
  },
  plugins: [],
};
