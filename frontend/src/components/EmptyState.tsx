import React from 'react';

export interface EmptyStateProps {
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  /** Optional illustration or icon rendered above the title. */
  visual?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, actions, visual, className = '' }) => (
  <div
    className={`flex flex-col items-start gap-5 rounded-sm border border-dashed border-ink-900/20 bg-stone-100/60 px-6 py-12 sm:px-10 sm:py-16 ${className}`}
  >
    {visual}
    <div className="max-w-xl">
      <h2 className="font-display text-display-sm font-medium text-ink-900">{title}</h2>
      {description && <div className="mt-3 text-sm leading-relaxed text-ink-600">{description}</div>}
    </div>
    {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
  </div>
);

export default EmptyState;
