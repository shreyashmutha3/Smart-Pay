/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        fintech: {
          navy: '#0b1329',
          card: '#111c38',
          border: '#1e293b',
          muted: '#64748b',
          accent: '#2563eb',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#ef4444',
          sky: '#0284c7'
        }
      }
    },
  },
  plugins: [],
}
