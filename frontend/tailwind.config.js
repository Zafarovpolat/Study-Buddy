/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Telegram theme (сохраняем для совместимости)
        tg: {
          bg: 'var(--tg-theme-bg-color)',
          text: 'var(--tg-theme-text-color)',
          hint: 'var(--tg-theme-hint-color)',
          link: 'var(--tg-theme-link-color)',
          button: 'var(--tg-theme-button-color)',
          'button-text': 'var(--tg-theme-button-text-color)',
          secondary: 'var(--tg-theme-secondary-bg-color)',
        },
        // Lecto 2.0 Premium
        lecto: {
          bg: {
            primary: 'var(--lecto-bg-primary)',
            secondary: 'var(--lecto-bg-secondary)',
            tertiary: 'var(--lecto-bg-tertiary)',
          },
          text: {
            primary: 'var(--lecto-text-primary)',
            secondary: 'var(--lecto-text-secondary)',
            muted: 'var(--lecto-text-muted)',
          },
          accent: {
            blue: 'var(--lecto-blue)',
            green: 'var(--lecto-green)',
            red: 'var(--lecto-red)',
            purple: 'var(--lecto-purple)',
          },
          border: 'var(--lecto-border)',
        }
      },
      borderRadius: {
        'lecto-sm': 'var(--lecto-radius-sm)',
        'lecto-md': 'var(--lecto-radius-md)',
        'lecto-lg': 'var(--lecto-radius-lg)',
        'lecto-xl': 'var(--lecto-radius-xl)',
      },
      boxShadow: {
        'lecto-card': 'var(--lecto-shadow-card)',
        'lecto-glow-gold': 'var(--lecto-shadow-glow-gold)',
        'lecto-glow-blue': 'var(--lecto-shadow-glow-blue)',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      letterSpacing: {
        'tight': '-0.5px',
      },
      lineHeight: {
        'relaxed': '1.4',
      },
    },
  },
  plugins: [],
}