import React from 'react';

export interface SectionProps {
  id?: string;
  /** Index shown in mono, e.g. "A" or "03". */
  index?: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  aside?: React.ReactNode;
  className?: string;
  /** Hairline rule above the section; off for the first section on a surface. */
  rule?: boolean;
  children: React.ReactNode;
}

/** A titled region within a page, separated by a hairline rule. */
export const Section: React.FC<SectionProps> = ({ id, index, title, description, aside, className = '', rule = true, children }) => {
  const headingId = id ? `${id}-title` : undefined;
  return (
    <section id={id} aria-labelledby={headingId} className={`${rule ? 'border-t border-ink-900/[0.12] pt-7' : ''} ${className}`}>
      <header className="mb-5 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
        <div className="flex gap-4">
          {index && <span className="eyebrow pt-1.5 text-ink-500 tabular-nums">{index}</span>}
          <div>
            <h2 id={headingId} className="font-display text-[1.65rem] font-medium leading-tight text-ink-900">
              {title}
            </h2>
            {description && <p className="mt-1 max-w-prose text-sm leading-relaxed text-ink-600">{description}</p>}
          </div>
        </div>
        {aside && <div className="flex flex-wrap items-center gap-2">{aside}</div>}
      </header>
      {children}
    </section>
  );
};

export default Section;
