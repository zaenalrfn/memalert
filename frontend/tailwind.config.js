/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#fcd535",
        "primary-active": "#f0b90b",
        "primary-disabled": "#3a3a1f",
        ink: "#181a20",
        body: "#eaecef",
        muted: "#707a8a",
        "muted-strong": "#929aa5",
        "hairline-dark": "#2b3139",
        "canvas-dark": "#0b0e11",
        "surface-card": "#1e2329",
        "surface-elevated": "#2b3139",
        "surface-soft-light": "#fafafa",
        "trading-up": "#0ecb81",
        "trading-down": "#f6465d",
      },
      fontFamily: {
        sans: ['BinanceNova', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['BinancePlex', 'JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'xs': '2px',
        'sm': '4px',
        'md': '6px',
        'lg': '8px',
        'xl': '12px',
      }
    },
  },
  plugins: [],
}
