import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'quiet' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: React.ReactNode;
}

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-ink-900 text-stone-50 hover:bg-jade-600',
  secondary: 'border border-ink-900/25 text-ink-900 hover:border-ink-900 hover:bg-ink-900/[0.04]',
  quiet: 'text-ink-700 hover:text-ink-900 hover:bg-ink-900/[0.05]',
  danger: 'border border-danger-500/40 text-danger-700 hover:border-danger-500 hover:bg-danger-100/60',
};

const SIZES: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-sm',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', isLoading = false, icon, className = '', children, disabled, type = 'button', ...rest },
  ref,
) {
  return (
  <button
    ref={ref}
    type={type}
    disabled={disabled || isLoading}
    aria-busy={isLoading || undefined}
    className={`inline-flex items-center justify-center gap-2 rounded-sm font-medium tracking-wide transition-colors duration-fast ease-out disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
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
