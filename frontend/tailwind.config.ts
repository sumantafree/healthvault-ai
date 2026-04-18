import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue:   "#3B82F6",
          indigo: "#6366F1",
          green:  "#22C55E",
          yellow: "#F59E0B",
          red:    "#EF4444",
          purple: "#8B5CF6",
          teal:   "#14B8A6",
        },
        risk: {
          low:      "#22C55E",
          moderate: "#F59E0B",
          high:     "#EF4444",
          critical: "#991B1B",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          subtle:  "#F8FAFC",
          muted:   "#F1F5F9",
          border:  "#E2E8F0",
          "border-strong": "#CBD5E1",
        },
        text: {
          primary:   "#0F172A",
          secondary: "#64748B",
          muted:     "#94A3B8",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "14px",
        xl:   "16px",
        "2xl":"20px",
        "3xl":"24px",
      },
      boxShadow: {
        xs:           "0 1px 2px rgba(0,0,0,0.05)",
        card:         "0 1px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "card-hover": "0 8px 30px rgba(0,0,0,0.09), 0 4px 10px rgba(0,0,0,0.05)",
        modal:        "0 24px 64px rgba(0,0,0,0.18), 0 8px 24px rgba(0,0,0,0.08)",
        glow:         "0 0 0 3px rgba(59,130,246,0.15)",
        "glow-green": "0 0 0 3px rgba(34,197,94,0.15)",
        "inner-sm":   "inset 0 1px 3px rgba(0,0,0,0.06)",
      },
      backgroundImage: {
        "gradient-brand":   "linear-gradient(135deg, #3B82F6 0%, #6366F1 100%)",
        "gradient-health":  "linear-gradient(135deg, #22C55E 0%, #14B8A6 100%)",
        "gradient-warning": "linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)",
        "gradient-subtle":  "linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%)",
        "gradient-card":    "linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)",
        "grid-pattern":     "radial-gradient(circle, #e2e8f0 1px, transparent 1px)",
      },
      animation: {
        "fade-in":      "fadeIn 0.2s ease-out",
        "fade-in-up":   "fadeInUp 0.3s ease-out",
        "slide-in":     "slideIn 0.25s ease-out",
        "slide-up":     "slideUp 0.3s ease-out",
        "scale-in":     "scaleIn 0.2s ease-out",
        "pulse-slow":   "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "shimmer":      "shimmer 1.5s infinite",
        "bounce-sm":    "bounceSm 0.6s ease-in-out",
        "spin-slow":    "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn:    { from: { opacity: "0" },                                 to: { opacity: "1" } },
        fadeInUp:  { from: { opacity: "0", transform: "translateY(12px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        slideIn:   { from: { opacity: "0", transform: "translateX(-8px)" },  to: { opacity: "1", transform: "translateX(0)" } },
        slideUp:   { from: { opacity: "0", transform: "translateY(8px)" },   to: { opacity: "1", transform: "translateY(0)" } },
        scaleIn:   { from: { opacity: "0", transform: "scale(0.95)" },       to: { opacity: "1", transform: "scale(1)" } },
        shimmer:   { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        bounceSm:  { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-4px)" } },
      },
      spacing: {
        sidebar: "260px",
      },
    },
  },
  plugins: [],
};

export default config;
