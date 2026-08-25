import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Snow / frost palette. Class names kept as `axis-*` so components
        // don't need to change — only the rendered colors do.
        axis: {
          DEFAULT: '#2563EB',      // frost — sky-blue-600
          dark: '#1E3A8A',         // deep winter navy
          bright: '#60A5FA',       // ice-bright highlight
          soft: '#EFF6FF',         // fresh snow tint
          softer: '#DBEAFE',       // light ice
          ink: '#0F172A',          // midnight — text
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        deva: ['"Noto Sans Devanagari"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 4px 20px rgba(37, 99, 235, 0.10)',
        frost: '0 8px 32px rgba(96, 165, 250, 0.18)',
      },
      backgroundImage: {
        'snow-sky': 'radial-gradient(ellipse at top, #EFF6FF 0%, #DBEAFE 55%, #BFDBFE 100%)',
      },
      animation: {
        pulseDot: 'pulseDot 1.2s infinite ease-in-out both',
        snowfall: 'snowfall 12s linear infinite',
        drift: 'drift 8s ease-in-out infinite',
      },
      keyframes: {
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
        snowfall: {
          '0%': { transform: 'translateY(-10%)', opacity: '0' },
          '10%': { opacity: '0.85' },
          '90%': { opacity: '0.85' },
          '100%': { transform: 'translateY(110vh)', opacity: '0' },
        },
        drift: {
          '0%, 100%': { transform: 'translateX(0) rotate(0deg)' },
          '50%': { transform: 'translateX(12px) rotate(6deg)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
