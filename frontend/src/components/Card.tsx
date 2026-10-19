import React from 'react';

export interface CardProps {
  /** Small mono label above the title. */
  eyebrow?: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  /** Right-aligned header content: origin tags, actions. */
  aside?: React.ReactNode;
  tone?: 'white' | 'stone' | 'ink';
  padding?: 'none' | 'sm' | 'md';
  className?: string;
  children?: React.ReactNode;
  as?: 'section' | 'div' | 'article';
}

const TONES = {
  white: 'bg-white border-ink-900/10 text-ink-900',
  stone: 'bg-stone-100 border-ink-900/10 text-ink-900',
  ink: 'bg-ink-900 border-ink-900 text-stone-50',
};

const PADDING = { none: '', sm: 'p-4', md: 'p-5 sm:p-6' };

/** A bordered panel. Flat, hairline-bordered, tight radius — a sheet in a dossier, not a floating card. */
export const Card: React.FC<CardProps> = ({
  eyebrow,
  title,
  subtitle,
  aside,
  tone = 'white',
  padding = 'md',
  className = '',
  children,
  as: Tag = 'section',
}) => {
  const hasHeader = eyebrow || title || subtitle || aside;
  const muted = tone === 'ink' ? 'text-stone-300' : 'text-ink-600';

  return (
    <Tag className={`rounded-sm border ${TONES[tone]} ${PADDING[padding]} ${className}`}>
      {hasHeader && (
        <header className="mb-4 flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
          <div className="min-w-0">
            {eyebrow && <div className={`eyebrow mb-2 ${muted}`}>{eyebrow}</div>}
            {title && <h3 className="text-base font-semibold leading-snug">{title}</h3>}
            {subtitle && <p className={`mt-1 text-sm leading-relaxed ${muted}`}>{subtitle}</p>}
          </div>
          {aside && <div className="flex shrink-0 flex-wrap items-center gap-2">{aside}</div>}
        </header>
      )}
      {children}
    </Tag>
  );
};

export default Card;
