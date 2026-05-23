/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0d1110",
        graphite: "#161a18",
        moss: "#22C55E",
        signal: "#80d4ff",
        brass: "#f5b84b"
      },
      boxShadow: {
        glow: "0 0 80px rgba(34,197,94,0.18)"
      }
    }
  },
  plugins: []
};

