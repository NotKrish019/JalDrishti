import React from 'react';

export interface EmptyStateProps {
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  /** Optional illustration or icon rendered above the title. */
  visual?: React.ReactNode;
  className?: string;
}

/** An open composition — no box — marked by the stepped terrace rule used across the workspace. */
export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, actions, visual, className = '' }) => (
  <div className={`max-w-2xl py-6 sm:py-10 ${className}`}>
    <div className="ws-terrace mb-8 w-40 text-ws-moss-deep" aria-hidden="true">
      <span />
    </div>
    {visual}
    <h2 className="font-display text-[clamp(1.85rem,3vw,2.5rem)] font-medium leading-tight">{title}</h2>
    {description && <div className="mt-4 max-w-xl text-[0.9375rem] leading-relaxed opacity-80">{description}</div>}
    {actions && <div className="mt-8 flex flex-wrap items-center gap-3">{actions}</div>}
  </div>
);

export default EmptyState;
