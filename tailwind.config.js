/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./views/**/*.{html,tpl}"],
  theme: {
    extend: {
      colors: {
        'slate-gray': '#E1E2E2',
        'off-white': '#F7F7F6',
        'accent-orange': '#FF8800',
        'light-orange': '#F5B000',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'display': ['Outfit', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },
      boxShadow: {
        'soft': '0 2px 15px rgb(0 0 0 / 0.08)',
        'strong': '0 4px 25px rgb(0 0 0 / 0.15)',
      },
    },
  },
  plugins: [],
}

