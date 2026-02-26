import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#e71837",
          dark: "#b80e29",
        },
        santander: {
          red: "#e71837",
          dark: "#192734",
        },
      },
      fontFamily: {
        sans: ["SantanderTextW05-Regular", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
