/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Telegram theme (compatibility)
        tg: {
          bg: 'var(--tg-theme-bg-color)',
          text: 'var(--tg-theme-text-color)',
          hint: 'var(--tg-theme-hint-color)',
          link: 'var(--tg-theme-link-color)',
          button: 'var(--tg-theme-button-color)',
          'button-text': 'var(--tg-theme-button-text-color)',
          secondary: 'var(--tg-theme-secondary-bg-color)',
        },
        // Lecto 2.0 Premium (Redesigned)
        lecto: {
          bg: {
            primary: '#FFFFFF',   // White
            secondary: '#F8F9FA', // Light Gray
            tertiary: '#F3F4F6',
          },
          text: {
            primary: '#152886',   // Dark Blue
            secondary: '#6E7681', // Gray
            muted: '#9CA3AF',
          },
          accent: {
            primary: '#9452ea',   // Purple
            secondary: '#152886', // Dark Blue
            gold: '#9452ea',      // Legacy support (now purple)
          },
          border: '#E1E4E8',
        }
      },
      backgroundImage: {
        'lecto-gradient-purple': 'linear-gradient(135deg, #9452ea 0%, #152886 100%)',
        'lecto-gradient-gold': 'linear-gradient(135deg, #9452ea 0%, #152886 100%)', // Legacy support
      },
      borderRadius: {
        'lecto-card': '16px',
        'lecto-btn': '12px',
      },
      fontFamily: {
        sans: ['Outfit', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      fontSize: {
        'body-regular': ['15px', { lineHeight: '1.4' }],
      },
      letterSpacing: {
        'tight-header': '-0.5px',
      },
      boxShadow: {
        'lecto-card': '0 4px 24px rgba(21, 40, 134, 0.1)',
        'lecto-glow-purple': '0 0 20px rgba(148, 82, 234, 0.3)',
        'lecto-glow-gold': '0 0 20px rgba(148, 82, 234, 0.3)', // Legacy support
      },
    },
  },
  plugins: [],
}