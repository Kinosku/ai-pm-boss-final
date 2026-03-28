/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#00ffb4",
        background: "#06090f",
        "surface-container": "rgba(255,255,255,0.04)",
        "surface-container-high": "rgba(255,255,255,0.07)",
        "surface-container-highest": "rgba(255,255,255,0.10)",
        "surface-container-lowest": "rgba(255,255,255,0.02)",
        "on-surface": "#e8eaed",
        "on-surface-variant": "rgba(255,255,255,0.5)",
      },
      fontFamily: {
        headline: ["'DM Sans'", "sans-serif"],
        mono: ["'Space Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
