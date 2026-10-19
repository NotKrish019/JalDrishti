import React from 'react';

export interface LoadingStateProps {
  label: string;
  /** 0–1 when real progress is known; omit for an indeterminate indicator. */
  progress?: number;
  className?: string;
}

/**
 * Progress line. Shows a percentage only when the caller has a real
 * measurement; otherwise an indeterminate sweep — never a simulated count.
 */
export const LoadingState: React.FC<LoadingStateProps> = ({ label, progress, className = '' }) => {
  const known = typeof progress === 'number';
  const pct = known ? Math.round(Math.min(1, Math.max(0, progress)) * 100) : undefined;

  return (
    <div className={className} role="status" aria-live="polite">
      <div className="mb-2 flex items-baseline justify-between gap-3 text-xs text-ink-600">
        <span>{label}</span>
        {known && <span className="font-mono tabular-nums text-ink-900">{pct}%</span>}
      </div>
      <div
        className="relative h-[3px] w-full overflow-hidden bg-ink-900/10"
        role="progressbar"
        aria-label={label}
        aria-valuemin={known ? 0 : undefined}
        aria-valuemax={known ? 100 : undefined}
        aria-valuenow={pct}
      >
        {known ? (
          <div className="h-full bg-jade-500 transition-[width] duration-base ease-out" style={{ width: `${pct}%` }} />
        ) : (
          <div className="animate-indeterminate absolute inset-y-0 left-0 w-2/5 bg-jade-500" />
        )}
      </div>
    </div>
  );
};

export default LoadingState;
