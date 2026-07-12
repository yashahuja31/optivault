import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B1220",
        panel: "#131D30",
        "panel-hover": "#1A2740",
        border: "#263352",
        text: "#E8ECF4",
        muted: "#7E8CAD",
        savings: "#2FD9A8",
        waste: "#F0A63A",
        danger: "#F2685C",
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
    },
  },
  plugins: [],
};

export default config;
