import React from 'react';

export interface SectionIndexProps {
  /** Omitted for framing sections that sit outside the numbered method. */
  number?: string;
  label: string;
  tone?: 'light' | 'dark';
  className?: string;
}

/** Numbered section marker shared by every landing section: "03 ── The challenge". */
export const SectionIndex: React.FC<SectionIndexProps> = ({ number, label, tone = 'dark', className = '' }) => (
  <p
    data-reveal
    className={`eyebrow flex items-center gap-4 ${tone === 'dark' ? 'text-ink-700' : 'text-stone-300'} ${className}`}
  >
    {number && <span>{number}</span>}
    <span aria-hidden="true" className={`h-px w-10 ${tone === 'dark' ? 'bg-ink-900/30' : 'bg-stone-50/30'}`} />
    <span>{label}</span>
  </p>
);

export default SectionIndex;
