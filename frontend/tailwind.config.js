/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E8E9F0',
          100: '#D1D3E1',
          200: '#A3A7C3',
          300: '#757BA5',
          400: '#474F87',
          500: '#1A1F3B', // Deep Space Blue
          600: '#15192F',
          700: '#101323',
          800: '#0B0D17',
          900: '#06070B',
        },
        secondary: {
          50: '#EDEBF9',
          100: '#DBD7F3',
          200: '#B7AFE7',
          300: '#9387DB',
          400: '#6F5FCF',
          500: '#6C5DD3', // Neural Violet
          600: '#564AA9',
          700: '#40387F',
          800: '#2B2555',
          900: '#15132A',
        },
        success: {
          50: '#E0F7F4',
          100: '#C1EFE9',
          200: '#83DFD3',
          300: '#45CFBD',
          400: '#07BFA7',
          500: '#00C6A7', // Teal AI
          600: '#009E86',
          700: '#007764',
          800: '#004F43',
          900: '#002722',
        },
        warning: {
          50: '#FDF6E8',
          100: '#FBEDD1',
          200: '#F7DBA3',
          300: '#F3C975',
          400: '#EFB747',
          500: '#F5A524', // Amber
          600: '#C4841D',
          700: '#936316',
          800: '#62420E',
          900: '#312107',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        brand: {
          deepBlue: '#1A1F3B',
          neuralViolet: '#6C5DD3',
          tealAI: '#00C6A7',
          amber: '#F5A524',
          whiteSmoke: '#F9FAFB',
          darkSlate: '#212121',
          textDark: '#212121',
          textLight: '#FFFFFF',
          borderGray: '#E0E0E0',
          placeholderGray: '#999999'
        }
      },
      fontFamily: {
        sans: ['Inter', 'Nunito Sans', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'Inter', 'Nunito Sans', 'system-ui', 'sans-serif']
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
