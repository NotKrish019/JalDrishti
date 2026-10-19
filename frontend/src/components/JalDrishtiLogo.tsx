import React from 'react';

export interface JalDrishtiLogoProps {
  className?: string;
  /** 'light' renders for dark backgrounds, 'dark' for parchment backgrounds. */
  tone?: 'light' | 'dark';
  showText?: boolean;
  /** Show the Devanagari name beneath the wordmark. */
  showDevanagari?: boolean;
}

/**
 * Mark: a stepwell in plan — three descending rings, the entry stair, and the water.
 */
export const JalDrishtiLogo: React.FC<JalDrishtiLogoProps> = ({
  className = '',
  tone = 'dark',
  showText = true,
  showDevanagari = false,
}) => {
  const stroke = tone === 'light' ? '#E2D3BA' : '#17140F';
  const text = tone === 'light' ? 'text-stone-50' : 'text-ink-900';
  const sub = tone === 'light' ? 'text-stone-300' : 'text-ink-600';

  return (
    <span className={`inline-flex items-center gap-3 select-none ${className}`}>
      <svg viewBox="0 0 32 32" className="h-7 w-7 shrink-0" aria-hidden="true">
        <g fill="none" stroke={stroke} strokeWidth="1.4">
          <circle cx="16" cy="16" r="14" />
          <circle cx="16" cy="16" r="10" strokeOpacity="0.75" />
          <circle cx="16" cy="16" r="6.5" strokeOpacity="0.55" />
          <path d="M16 2v7.5" />
        </g>
        <circle cx="16" cy="16" r="3.6" fill="#2F6152" />
      </svg>
      {showText && (
        <span className="flex flex-col leading-none">
          <span className={`font-sans text-[0.8125rem] font-semibold uppercase tracking-[0.22em] ${text}`}>
            JalDrishti
          </span>
          {showDevanagari && (
            <span className={`mt-1 font-deva text-[0.8125rem] ${sub}`} lang="hi">
              जलदृष्टि
            </span>
          )}
        </span>
      )}
    </span>
  );
};

export default JalDrishtiLogo;
