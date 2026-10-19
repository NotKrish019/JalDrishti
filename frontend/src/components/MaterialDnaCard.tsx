import React from 'react';
import { CandidateIntervention, CompatibilityDimensions, RecommendationLevel } from '../types';
import { StatusBadge, BadgeVariant } from './StatusBadge';
import { humanize } from '../utils/analysis';

const DIMENSIONS: { key: keyof CompatibilityDimensions; label: string; meaning: string }[] = [
  { key: 'mechanical', label: 'Mechanical', meaning: 'Strength and stiffness relative to the original' },
  { key: 'moisture', label: 'Moisture', meaning: 'Vapour permeability and water behaviour' },
  { key: 'thermal', label: 'Thermal', meaning: 'Expansion under heating and cooling' },
  { key: 'chemical', label: 'Chemical', meaning: 'Salt and binder compatibility' },
  { key: 'reversibility', label: 'Reversibility', meaning: 'Can be removed without harming the original' },
  { key: 'heritage', label: 'Heritage', meaning: 'Consistency with traditional practice' },
  { key: 'visual', label: 'Visual', meaning: 'Colour and texture match' },
];

const RECOMMENDATION: Record<RecommendationLevel, { label: string; variant: BadgeVariant }> = {
  strongly_recommended: { label: 'Strongly recommended', variant: 'jade' },
  recommended: { label: 'Recommended', variant: 'jade' },
  acceptable_conditional: { label: 'Conditional', variant: 'ochre' },
  prohibited_incompatible: { label: 'Incompatible', variant: 'danger' },
};

export interface MaterialDnaCardProps {
  candidate: CandidateIntervention;
  className?: string;
}

/** One candidate intervention: overall rule-based score, the seven dimensions, and warnings. */
export const MaterialDnaCard: React.FC<MaterialDnaCardProps> = ({ candidate, className = '' }) => {
  const rec = RECOMMENDATION[candidate.recommendation] ?? { label: humanize(candidate.recommendation), variant: 'neutral' as const };
  const incompatible = candidate.recommendation === 'prohibited_incompatible';

  return (
    <article className={`break-inside-avoid border-t pt-4 ${incompatible ? 'border-danger-500/50' : 'border-ink-900/15'} ${className}`}>
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-ink-900">{humanize(candidate.intervention_material)}</h4>
          <p className="mt-1 font-mono text-xs text-ink-500 tabular-nums">
            Compatibility {candidate.compatibility_score.toFixed(1)} / 100
          </p>
        </div>
        <StatusBadge label={rec.label} variant={rec.variant} />
      </header>

      <dl className="mt-4 space-y-1.5">
        {DIMENSIONS.map(({ key, label, meaning }) => {
          const value = candidate.compatibility_dimensions?.[key];
          if (typeof value !== 'number') return null;
          return (
            <div key={key} className="grid grid-cols-[6.5rem_minmax(0,1fr)_2.5rem] items-center gap-3 text-xs" title={meaning}>
              <dt className="text-ink-600">{label}</dt>
              <dd className="relative h-[5px] bg-ink-900/10" aria-hidden="true">
                <span
                  className={`absolute inset-y-0 left-0 ${value < 4 ? 'bg-danger-500' : value < 7 ? 'bg-ochre-500' : 'bg-jade-500'}`}
                  style={{ width: `${Math.min(10, Math.max(0, value)) * 10}%` }}
                />
              </dd>
              <dd className="text-right font-mono text-ink-900 tabular-nums">
                {value.toFixed(1)}
                <span className="sr-only"> out of 10 for {label.toLowerCase()}</span>
              </dd>
            </div>
          );
        })}
      </dl>

      {candidate.warnings.length > 0 && (
        <ul className="mt-4 space-y-2">
          {candidate.warnings.map((warning) => (
            <li key={warning} className="border-l-2 border-danger-500/60 pl-3 text-xs leading-relaxed text-ink-700">
              {warning}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
};

export default MaterialDnaCard;
