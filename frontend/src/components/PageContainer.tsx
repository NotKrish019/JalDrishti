import React from 'react';

export interface PageContainerProps {
  /** e.g. "02 — Findings" */
  eyebrow?: string;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  /** Full-width notice rendered under the header (provenance, warnings). */
  banner?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

/** Page frame for application routes: editorial title block, then content. */
export const PageContainer: React.FC<PageContainerProps> = ({
  eyebrow,
  title,
  subtitle,
  actions,
  banner,
  children,
  className = '',
}) => (
  <div className={`gutter mx-auto w-full max-w-content pb-24 ${className}`}>
    <header className="flex flex-col gap-6 pb-8 pt-10 sm:pt-14 lg:flex-row lg:items-end lg:justify-between">
      <div className="max-w-3xl">
        {eyebrow && <p className="eyebrow mb-4 text-laterite-500">{eyebrow}</p>}
        <h1 className="font-display text-display-md font-medium text-ink-900">{title}</h1>
        {subtitle && <p className="mt-4 max-w-prose text-base leading-relaxed text-ink-600">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-3 print:hidden">{actions}</div>}
    </header>
    {banner && <div className="mb-8">{banner}</div>}
    {children}
  </div>
);

export default PageContainer;
