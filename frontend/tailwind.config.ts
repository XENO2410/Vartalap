import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        axis: {
          DEFAULT: '#97144D',      // deep maroon (Axis pink/burgundy)
          dark: '#6D0F3A',
          bright: '#E5006C',
          soft: '#FFF0F5',
          softer: '#FBE4EC',
          ink: '#2B0A1A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        deva: ['"Noto Sans Devanagari"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 4px 20px rgba(151, 20, 77, 0.08)',
      },
      animation: {
        pulseDot: 'pulseDot 1.2s infinite ease-in-out both',
      },
      keyframes: {
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
