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
  as?: 'section' | 'div' | 'article' | 'aside';
  /** Heading level for the title; use 2 when the card is a top-level region under the page h1. */
  headingLevel?: 2 | 3;
}

const TONES = {
  white: 'rounded-lg border border-ink-900/10 bg-ws-paper text-ink-900',
  stone: 'rounded-lg border border-ink-900/10 bg-ws-mist text-ink-900',
  ink: 'rounded-lg border border-ws-stone bg-ws-stone text-ws-text',
};

const PADDING = { none: '', sm: 'p-4', md: 'p-5 sm:p-6' };

/** A quiet bordered panel, for content that genuinely needs its own surface. Prefer open layouts. */
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
  headingLevel = 3,
}) => {
  const Heading = headingLevel === 2 ? 'h2' : 'h3';
  const hasHeader = eyebrow || title || subtitle || aside;
  const muted = tone === 'ink' ? 'text-stone-300' : 'text-ink-600';

  return (
    <Tag className={`${TONES[tone]} ${PADDING[padding]} ${className}`}>
      {hasHeader && (
        <header className="mb-4 flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
          <div className="min-w-0">
            {eyebrow && <div className={`eyebrow mb-2 ${muted}`}>{eyebrow}</div>}
            {title && <Heading className="text-base font-semibold leading-snug">{title}</Heading>}
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
