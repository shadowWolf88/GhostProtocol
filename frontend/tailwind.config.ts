import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#0a0a0a',
          surface: '#111111',
          border: '#1a1a1a',
          green: '#00ff41',
          'green-dim': '#00aa2a',
          'green-bright': '#39ff14',
          amber: '#ffb000',
          red: '#ff2020',
          blue: '#0088ff',
          purple: '#9933ff',
          cyan: '#00ffff',
          white: '#e0e0e0',
          muted: '#666666',
        },
      },
      fontFamily: {
        mono: ['"Fira Code"', '"JetBrains Mono"', '"Cascadia Code"', 'Consolas', 'monospace'],
      },
      animation: {
        blink: 'blink 1s step-end infinite',
        'fade-in': 'fadeIn 0.3s ease-in',
        'slide-up': 'slideUp 0.3s ease-out',
        scanline: 'scanline 8s linear infinite',
        glow: 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        glow: {
          '0%': { textShadow: '0 0 5px #00ff41' },
          '100%': { textShadow: '0 0 20px #00ff41, 0 0 40px #00ff41' },
        },
      },
      boxShadow: {
        'terminal-green': '0 0 10px rgba(0, 255, 65, 0.3)',
        'terminal-red': '0 0 10px rgba(255, 32, 32, 0.3)',
        'terminal-amber': '0 0 10px rgba(255, 176, 0, 0.3)',
      },
    },
  },
  plugins: [],
} satisfies Config
