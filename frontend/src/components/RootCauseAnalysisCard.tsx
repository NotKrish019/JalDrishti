import React from 'react';
import { RootCauseItem } from '../types';
import { StatusBadge, BadgeVariant } from './StatusBadge';
import { humanize } from '../utils/analysis';

const URGENCY: Record<string, BadgeVariant> = {
  critical: 'danger',
  high: 'danger',
  medium: 'ochre',
  low: 'neutral',
};

export interface RootCauseAnalysisCardProps {
  causes: RootCauseItem[];
  className?: string;
}

/** Probable causes inferred by the rule engine, each with the evidence rules that fired. */
export const RootCauseAnalysisCard: React.FC<RootCauseAnalysisCardProps> = ({ causes, className = '' }) => {
  if (causes.length === 0) {
    return <p className={`text-sm text-ink-600 ${className}`}>The rule engine did not infer any probable causes from these findings.</p>;
  }

  return (
    <ol className={`divide-y divide-ink-900/10 border-y border-ink-900/10 ${className}`}>
      {causes.map((cause, i) => (
        <li key={`${cause.finding}-${i}`} className="grid gap-3 py-5 md:grid-cols-[2.5rem_minmax(0,1fr)_auto] break-inside-avoid">
          <span className="font-mono text-xs text-ink-500 tabular-nums">{String(i + 1).padStart(2, '0')}</span>
          <div>
            <p className="text-sm font-medium text-ink-900">{cause.finding}</p>
            <p className="mt-1.5 text-sm leading-relaxed text-ink-700">
              <span className="text-ink-500">Probable cause — </span>
              {cause.probable_cause}
            </p>
            {cause.evidence_rules.length > 0 && (
              <ul className="mt-3 space-y-1 text-xs text-ink-600">
                {cause.evidence_rules.map((rule) => (
                  <li key={rule} className="flex gap-2">
                    <span className="font-mono text-ink-500">rule</span>
                    <span>{rule}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {cause.urgency && (
            <div>
              <StatusBadge label={`${humanize(cause.urgency)} urgency`} variant={URGENCY[cause.urgency] ?? 'neutral'} />
            </div>
          )}
        </li>
      ))}
    </ol>
  );
};

export default RootCauseAnalysisCard;
