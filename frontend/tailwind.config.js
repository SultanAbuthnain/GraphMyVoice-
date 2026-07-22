/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0F1116", // page background
          900: "#171A22", // panel background
          800: "#232733", // raised surface / borders
          600: "#4A5065", // muted text
        },
        paper: "#EDEEF2", // primary text on dark
        signal: {
          teal: "#4FD1C5",  // primary accent — the "waveform" color
          amber: "#F2B84B", // task / attention accent
          coral: "#F2665A", // error / failed state
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      keyframes: {
        wave: {
          "0%, 100%": { transform: "scaleY(0.3)" },
          "50%": { transform: "scaleY(1)" },
        },
      },
      animation: {
        wave: "wave 1s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
