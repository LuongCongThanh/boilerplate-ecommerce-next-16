import type { Config } from "tailwindcss";
import tailwindcssAnimate from "tailwindcss-animate";

const config: Config = {
  darkMode: ["class", "dark"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@shadcn/ui/dist/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@shadcn/ui/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // Core Colors
        primary: {
          20: '#f5fbff',
          50: '#e6eef6',
          100: '#b0cbe3',
          200: '#8ab1d6',
          300: '#558ec3',
          400: '#3478b8',
          500: '#0156a6', // Main (500)
          600: '#014e97',
          700: '#013d76',
          800: '#012f5b',
          900: '#002446',
          950: '#f5fbff',
        },
        'primary-light': {
          50: '#e6f5fb',
          100: '#b0def3',
          200: '#8acfed',
          300: '#54b9e4',
          400: '#33abdf',
          500: '#0096d7', // Main (500)
          600: '#0089c4',
          700: '#006b99',
          800: '#005376',
          900: '#003f5a',
        },
        secondary: {
          50: '#eeeeee',
          100: '#cacbcb',
          200: '#b0b2b2',
          300: '#8c8e8e',
          400: '#767979',
          500: '#545757', // Main (500)
          600: '#4c4f4f',
          700: '#3c3e3e',
          800: '#2e3030',
          900: '#232525',
        },
        'secondary-light': {
          50: '#fdfdfd',
          100: '#fdfdfd',
          200: '#f4f4f4',
          300: '#eeeff0',
          400: '#ebeced',
          500: '#e6e7e8', // Main (500)
          600: '#d1d2d3',
          700: '#a3a4a5',
          800: '#7f7f80',
          900: '#616161',
        },
        darkRed: {
          100: '#FEECEC',
          200: '#FDCACA',
          300: '#FB9A9A',
          400: '#F86A6A',
          500: '#F43C3C',// Main (500)
          600: '#D83232',
          700: '#B22929',
          800: '#8C2020',
          900: '#661717',
        },
        volcano: {
          100: '#FFF2E8',
          200: '#FFD8BF',
          300: '#FFA940',
          400: '#FA8C16',
          500: '#D46B08',// Main (500)
          600: '#AD4E00',
          700: '#873800',
          800: '#612500',
          900: '#3D1800',
        },
        sunsetOrange: {
          100: '#FFF1F0',
          200: '#FFCCC7',
          300: '#FFA39E',
          400: '#FF7875',
          500: '#F5222D',// Main (500)
          600: '#CF1322',
          700: '#A8071A',
          800: '#820014',
          900: '#5C0011',
        },
        cyan: {
          100: '#E6FFFB',
          200: '#B5F5EC',
          300: '#87E8DE',
          400: '#5CDBD3',
          500: '#36CFC9',// Main (500)
          600: '#13A8A8',
          700: '#08979C',
          800: '#006D75',
          900: '#00474F',
        },
        lime: {
          100: '#FCFFE6',
          200: '#F4FFB8',
          300: '#EAFF8F',
          400: '#D3F261',
          500: '#BAE637',// Main (500)
          600: '#A0D911',
          700: '#7CB305',
          800: '#5B8C00',
          900: '#3F6600',
        },
        goldenPurple: {
          100: '#F9F0FF',
          200: '#EFDBFF',
          300: '#D3ADF7',
          400: '#B37FEB',
          500: '#9254DE',// Main (500)
          600: '#722ED1',
          700: '#531DAB',
          800: '#391085',
          900: '#22075E',
        },
        white: {
          50: '#ffffff',
          100: '#ffffff',
          200: '#ffffff',
          300: '#ffffff',
          400: '#ffffff',
          500: '#ffffff', // Main (500)
          600: '#ffffff',
          700: '#ffffff',
          800: '#ffffff',
          900: '#ffffff',
        },
        black: {
          50: '#000000',
          100: '#000000',
          200: '#000000',
          300: '#000000',
          400: '#000000',
          500: '#000000', // Main (500)
          600: '#000000',
          700: '#000000',
          800: '#000000',
          900: '#000000',
        },
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "#FFFFFF",
          foreground: "#000000",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        chart: {
          "1": "hsl(var(--chart-1))",
          "2": "hsl(var(--chart-2))",
          "3": "hsl(var(--chart-3))",
          "4": "hsl(var(--chart-4))",
          "5": "hsl(var(--chart-5))",
        },
      },
      fontFamily: {
        sans: ["Arial", "sans-serif"],
        serif: ["Georgia", "serif"],
        mono: ["Menlo", "monospace"],
      },
      fontSize: {
        xs: "0.75rem",// 12px
        sm: "0.875rem",// 14px
        base: "1rem",// 16px
        lg: "1.125rem", // 18px
        xl: "1.25rem",// 20px
        "2xl": "1.5rem",// 24px
        "3xl": "1.875rem",// 30px
        "4xl": "2.25rem",// 36px
        "5xl": "3rem",// 48px
        "6xl": "3.75rem",// 60px
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [tailwindcssAnimate],
};

export default config;
