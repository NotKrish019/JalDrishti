import React, { createContext, useContext } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'quiet' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';
/** The ground the button sits on: light mist (default) or dark stone. */
export type ButtonSurface = 'light' | 'dark';

/** Set by PageContainer (and any dark region) so buttons pick legible colours for their ground. */
export const ButtonSurfaceContext = createContext<ButtonSurface>('light');

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: React.ReactNode;
}

const VARIANTS: Record<ButtonSurface, Record<ButtonVariant, string>> = {
  light: {
    primary: 'bg-ws-stone text-ws-text hover:bg-ws-jade',
    secondary: 'border border-ink-900/25 text-ink-900 hover:border-ink-900/60 hover:bg-ink-900/[0.04]',
    quiet: 'text-ink-700 hover:text-ink-900 hover:bg-ink-900/[0.05]',
    danger: 'border border-danger-500/40 text-danger-700 hover:border-danger-500 hover:bg-danger-100/60',
  },
  dark: {
    primary: 'bg-ws-text text-ws-stone hover:bg-white',
    secondary: 'border border-ws-text/30 text-ws-text hover:border-ws-text/60 hover:bg-ws-text/[0.06]',
    quiet: 'text-ws-muted hover:text-ws-text hover:bg-ws-text/[0.07]',
    danger: 'border border-laterite-300/50 text-laterite-300 hover:border-laterite-300 hover:bg-laterite-300/10',
  },
};

const SIZES: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-[0.8125rem]',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-[0.9375rem]',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', isLoading = false, icon, className = '', children, disabled, type = 'button', ...rest },
  ref,
) {
  const surface = useContext(ButtonSurfaceContext);
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-fast ease-out disabled:cursor-not-allowed disabled:opacity-45 ${VARIANTS[surface][variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {isLoading ? (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-[1.5px] border-current border-r-transparent" aria-hidden="true" />
      ) : (
        icon
      )}
      {children}
    </button>
  );
});

export default Button;
