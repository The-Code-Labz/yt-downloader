/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Netflix/Jellyfin-inspired dark palette
        background: "hsl(220 14% 6%)",
        surface: "hsl(220 14% 9%)",
        surface2: "hsl(220 14% 12%)",
        border: "hsl(220 14% 18%)",
        muted: "hsl(220 8% 55%)",
        foreground: "hsl(210 20% 96%)",
        accent: {
          DEFAULT: "hsl(2 84% 55%)",     // crimson
          hover: "hsl(2 84% 60%)",
          ring: "hsl(2 84% 55% / 0.45)",
        },
        success: "hsl(142 71% 45%)",
        warn: "hsl(38 92% 55%)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      borderRadius: { lg: "0.75rem", xl: "1rem", "2xl": "1.25rem" },
      boxShadow: {
        glass: "0 1px 0 0 hsl(0 0% 100% / 0.04) inset, 0 30px 60px -20px hsl(0 0% 0% / 0.6)",
      },
      backgroundImage: {
        "noise":
          "radial-gradient(circle at 20% 0%, hsl(2 84% 55% / 0.10), transparent 40%), radial-gradient(circle at 80% 0%, hsl(220 100% 60% / 0.06), transparent 40%)",
      },
      keyframes: {
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: { shimmer: "shimmer 1.6s infinite" },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
