/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        indigo: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        beige: {
          50: '#fafaf8',
          100: '#f5f5f3',
          200: '#f0f0ee',
          300: '#e8e8e6',
          400: '#d4d4d1',
          500: '#a8a8a5',
          600: '#8b8b88',
        },
      },
      backgroundColor: {
        light: '#f0f0ee',
        'light-secondary': '#fafaf8',
        dark: '#0f172a',
        'dark-secondary': '#1e293b',
      },
      textColor: {
        light: '#1f2937',
        'light-secondary': '#6b7280',
        dark: '#f3f4f6',
        'dark-secondary': '#d1d5db',
      },
    },
  },
  darkMode: 'class',
  plugins: [require('@tailwindcss/typography')],
}
