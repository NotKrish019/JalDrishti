/** @type {import('tailwindcss').Config} */
// JalDrishti design tokens.
// Palette is derived from the four stepwell references (jal1–jal4):
//   ink      – the shadowed stone of deep shafts
//   stone    – sun-lit sandstone, from parchment highlights to weathered ochre
//   jade     – the green of standing stepwell water (not cyan)
//   laterite – carved red-brown friezes; used sparingly as the single accent
//   ochre    – caution states
//   mist     – the warm haze above the opening
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    screens: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
    extend: {
      colors: {
        // ink, the three lightest stones, white and the status tints/texts resolve through CSS variables
        // (index.css :root, same values as before) so the internal workspace's dark
        // ground can invert them locally. Everywhere else they are unchanged.
        white: 'rgb(var(--c-white) / <alpha-value>)',
        ink: {
          950: 'rgb(var(--c-ink-950) / <alpha-value>)',
          900: 'rgb(var(--c-ink-900) / <alpha-value>)',
          800: 'rgb(var(--c-ink-800) / <alpha-value>)',
          700: 'rgb(var(--c-ink-700) / <alpha-value>)',
          600: 'rgb(var(--c-ink-600) / <alpha-value>)',
          500: 'rgb(var(--c-ink-500) / <alpha-value>)',
        },
        stone: {
          50: 'rgb(var(--c-stone-50) / <alpha-value>)',
          100: 'rgb(var(--c-stone-100) / <alpha-value>)',
          200: 'rgb(var(--c-stone-200) / <alpha-value>)',
          300: '#CDB38F',
          400: '#B8956A',
          500: '#9C7A52',
          600: '#7C5F40',
          700: '#5E4732',
        },
        jade: {
          50: 'rgb(var(--c-jade-50) / <alpha-value>)',
          100: '#CADBD2',
          200: '#A6C2B4',
          300: '#7FA393',
          400: '#4F8070',
          500: '#2F6152',
          600: '#214A3F',
          700: 'rgb(var(--c-jade-700) / <alpha-value>)',
          800: '#0F2622',
          900: '#0A1A17',
        },
        laterite: {
          300: '#D9997C',
          400: '#C0714F',
          500: '#A4553A',
          600: 'rgb(var(--c-laterite-600) / <alpha-value>)',
        },
        ochre: {
          100: 'rgb(var(--c-ochre-100) / <alpha-value>)',
          500: '#B8863B',
          700: 'rgb(var(--c-ochre-700) / <alpha-value>)',
        },
        danger: {
          100: 'rgb(var(--c-danger-100) / <alpha-value>)',
          500: '#A33A2E',
          700: 'rgb(var(--c-danger-700) / <alpha-value>)',
        },
        mist: '#D9D3C7',
        // Internal workspace (AppShell pages). Mirrors the --ws-* variables in index.css;
        // drawn from sample1–3: well-interior stone, lichen moss, tank water.
        ws: {
          night: '#121512',
          stone: '#181C18',
          raised: '#1F2420',
          field: '#232923',
          text: '#EEF0EA',
          muted: '#B3BBAE',
          faint: '#868F82',
          mist: '#EFE9DE',
          paper: '#FBF8F2',
          moss: '#8FA25F',
          'moss-deep': '#56653A',
          jade: '#2F6A5C',
          'jade-light': '#8CC1AC',
          sandstone: '#CDB38F',
        },
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans: ['"Instrument Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
        deva: ['"Tiro Devanagari Hindi"', 'serif'],
      },
      fontSize: {
        // Editorial scale: display sizes are fluid; UI sizes are fixed.
        'display-xl': ['clamp(3.5rem, 9vw, 9rem)', { lineHeight: '0.9', letterSpacing: '-0.02em' }],
        'display-lg': ['clamp(2.5rem, 5.5vw, 5.25rem)', { lineHeight: '0.98', letterSpacing: '-0.015em' }],
        'display-md': ['clamp(2rem, 3.6vw, 3.25rem)', { lineHeight: '1.04', letterSpacing: '-0.01em' }],
        'display-sm': ['clamp(1.5rem, 2.4vw, 2.125rem)', { lineHeight: '1.12' }],
        eyebrow: ['0.6875rem', { lineHeight: '1', letterSpacing: '0.18em' }],
      },
      maxWidth: {
        prose: '62ch',
        content: '76rem',
        wide: '90rem',
      },
      borderRadius: {
        none: '0',
        xs: '1px',
        sm: '2px',
        DEFAULT: '3px',
        md: '4px',
        lg: '6px',
        full: '9999px',
      },
      boxShadow: {
        hairline: '0 0 0 1px rgb(23 20 15 / 0.08)',
        raised: '0 1px 0 rgb(23 20 15 / 0.04), 0 8px 24px -12px rgb(23 20 15 / 0.18)',
        overlay: '0 24px 64px -24px rgb(14 12 10 / 0.45)',
      },
      transitionTimingFunction: {
        out: 'cubic-bezier(0.22, 1, 0.36, 1)',
        inout: 'cubic-bezier(0.65, 0, 0.35, 1)',
      },
      transitionDuration: {
        fast: '160ms',
        base: '320ms',
        slow: '700ms',
      },
      zIndex: {
        scene: '0',
        content: '10',
        nav: '40',
        overlay: '50',
        toast: '60',
      },
    },
  },
  plugins: [],
};
