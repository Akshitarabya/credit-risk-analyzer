import type { Config } from "tailwindcss";

/**
 * Design tokens for "Ledgerline" — the product's visual identity.
 *
 * Palette rationale: a cool ink-navy + paper canvas instead of the generic
 * warm-cream/terracotta or near-black/acid-green combos, because this is a
 * bank-facing tool — it should read as precise and calm, not trendy.
 * The three semantic risk colors (teal / amber / brick) double as the
 * approved / review / rejected states throughout the product.
 */
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0B1526",
          light: "#101E36",
        },
        navy: {
          DEFAULT: "#10213D",
          light: "#1C2E52",
          dark: "#08111F",
        },
        canvas: "#F4F6FA",
        surface: "#FFFFFF",
        line: "#DFE4ED",
        muted: "#62697A",
        teal: {
          DEFAULT: "#0E8F7E",
          soft: "#E4F5F1",
        },
        amber: {
          DEFAULT: "#C97F1E",
          soft: "#FBF0DF",
        },
        coral: {
          DEFAULT: "#C1473F",
          soft: "#FBEAE8",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 33, 61, 0.04), 0 8px 24px -12px rgba(16, 33, 61, 0.12)",
        "card-hover": "0 4px 8px rgba(16, 33, 61, 0.06), 0 16px 32px -16px rgba(16, 33, 61, 0.18)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
};

export default config;
