import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Inter", "Segoe UI", "Roboto"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        border: "var(--border)",
        "border-strong": "var(--border-strong)",
        text: "var(--text)",
        "text-dim": "var(--text-dim)",
        "text-mute": "var(--text-mute)",
        accent: "var(--accent)",
        "accent-strong": "var(--accent-strong)",
        success: "var(--success)",
        danger: "var(--danger)",
        warn: "var(--warn)",
      },
      boxShadow: {
        soft: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px -10px rgba(0,0,0,0.6)",
      },
    },
  },
  plugins: [],
};

export default config;
