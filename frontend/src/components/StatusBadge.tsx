import React from 'react';

export type BadgeVariant = 'neutral' | 'jade' | 'ochre' | 'danger' | 'laterite' | 'ink';

export interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
  /** Show a small leading dot. */
  dot?: boolean;
  className?: string;
}

const STYLES: Record<BadgeVariant, string> = {
  neutral: 'border-ink-900/15 bg-stone-100 text-ink-700',
  jade: 'border-jade-500/30 bg-jade-50 text-jade-700',
  ochre: 'border-ochre-500/40 bg-ochre-100 text-ochre-700',
  danger: 'border-danger-500/30 bg-danger-100 text-danger-700',
  laterite: 'border-laterite-500/30 bg-laterite-300/20 text-laterite-600',
  ink: 'border-ink-900 bg-ink-900 text-stone-50',
};

const DOTS: Record<BadgeVariant, string> = {
  neutral: 'bg-ink-500',
  jade: 'bg-jade-500',
  ochre: 'bg-ochre-500',
  danger: 'bg-danger-500',
  laterite: 'bg-laterite-500',
  ink: 'bg-stone-50',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ label, variant = 'neutral', dot = false, className = '' }) => (
  <span
    className={`inline-flex max-w-full items-center gap-1.5 rounded-md border px-2 py-[3px] leading-tight font-mono text-[0.6875rem] uppercase tracking-[0.08em] ${STYLES[variant]} ${className}`}
  >
    {dot && <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${DOTS[variant]}`} aria-hidden="true" />}
    {label}
  </span>
);

/**
 * Declares where a block of information came from, so model output, rule-based
 * engine output and items needing expert confirmation are never conflated.
 */
export type OriginKind = 'model' | 'unverified' | 'rules' | 'knowledge' | 'expert' | 'user' | 'fixture';

const ORIGIN: Record<OriginKind, { label: string; variant: BadgeVariant }> = {
  model: { label: 'Model output', variant: 'laterite' },
  unverified: { label: 'Not from a trained model', variant: 'ochre' },
  rules: { label: 'Rule-based engine', variant: 'jade' },
  knowledge: { label: 'Knowledge base', variant: 'neutral' },
  expert: { label: 'Requires expert verification', variant: 'ochre' },
  user: { label: 'Your input', variant: 'neutral' },
  fixture: { label: 'Development sample', variant: 'ochre' },
};

export const OriginTag: React.FC<{ kind: OriginKind; className?: string }> = ({ kind, className }) => (
  <StatusBadge label={ORIGIN[kind].label} variant={ORIGIN[kind].variant} dot className={className} />
);

export default StatusBadge;
