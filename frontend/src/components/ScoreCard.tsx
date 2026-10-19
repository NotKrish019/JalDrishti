import React from 'react';
import { MetricScore } from '../types';
import { humanize } from '../utils/analysis';

export interface ScoreCardProps {
  label: string;
  metric: MetricScore;
  /** Reading guide shown beneath the scale. */
  direction?: 'higher_better' | 'higher_worse';
  className?: string;
}

/**
 * One engineering metric exactly as returned: value on its declared scale,
 * the rule that produced it, the engine's own confidence and its limitations.
 */
export const ScoreCard: React.FC<ScoreCardProps> = ({ label, metric, direction = 'higher_better', className = '' }) => {
  const span = metric.scale_max - metric.scale_min || 1;
  const fraction = Math.min(1, Math.max(0, (metric.value - metric.scale_min) / span));
  const digits = span <= 1 ? 2 : 1;

  return (
    <article className={`flex flex-col border-t border-ink-900/15 pt-4 ${className}`}>
      <div className="flex items-baseline justify-between gap-3">
        <h4 className="text-sm font-medium text-ink-900">{label}</h4>
        <p className="font-mono text-xs text-ink-500 tabular-nums">
          scale {metric.scale_min}–{metric.scale_max}
        </p>
      </div>

      <p className="mt-2 font-display text-[2.75rem] font-medium leading-none text-ink-900 tabular-nums">
        {metric.value.toFixed(digits)}
      </p>

      <div className="relative mt-3 h-[3px] bg-ink-900/10" aria-hidden="true">
        <div className="absolute inset-y-0 left-0 bg-ink-900" style={{ width: `${fraction * 100}%` }} />
      </div>
      <p className="mt-1.5 text-[0.6875rem] text-ink-500">
        {direction === 'higher_better' ? 'Higher indicates better observed condition' : 'Higher indicates greater burden or urgency'}
      </p>

      <dl className="mt-4 grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-xs">
        <dt className="text-ink-500">Method</dt>
        <dd className="break-words font-mono text-ink-700">{metric.method}</dd>
        <dt className="text-ink-500">Engine confidence</dt>
        <dd className="font-mono text-ink-700 tabular-nums">{(metric.confidence * 100).toFixed(0)}%</dd>
      </dl>

      {metric.limitations.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-ink-500">Limitations</p>
          <ul className="mt-1 space-y-1 text-xs leading-relaxed text-ink-700">
            {metric.limitations.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-[7px] h-px w-2 shrink-0 bg-ink-500" aria-hidden="true" />
                <span>{humanize(item)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
};

export default ScoreCard;
