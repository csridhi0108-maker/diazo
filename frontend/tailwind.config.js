/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Calming health-app palette, per the "clean, visually
        // pleasant health app" requirement — soft blues/greens
        // rather than clinical white/red.
        primary: {
          50: '#f0f9f6',
          100: '#dbf0e8',
          400: '#4fb894',
          500: '#2e9d78',
          600: '#227d5f',
        },
        accent: {
          400: '#6b9fd8',
          500: '#4a84c4',
        },
      },
    },
  },
  plugins: [],
}