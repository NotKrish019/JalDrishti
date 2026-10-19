import React from 'react';
import { RestorationResultContract, RestorationPhase } from '../types';
import { StatusBadge, BadgeVariant } from './StatusBadge';
import { humanize } from '../utils/analysis';

const PHASES: { id: RestorationPhase; label: string }[] = [
  { id: 'phase_1_immediate_stabilization', label: 'Immediate stabilisation' },
  { id: 'phase_2_hydrological_remediation', label: 'Hydrological remediation' },
  { id: 'phase_3_masonry_and_iks_consolidation', label: 'Masonry and traditional consolidation' },
  { id: 'phase_4_long_term_monitoring', label: 'Long-term monitoring' },
];

const URGENCY: Record<string, BadgeVariant> = {
  immediate: 'danger',
  high: 'ochre',
  medium: 'neutral',
  routine: 'jade',
};

const SEVERITY: Record<string, BadgeVariant> = {
  destructive: 'danger',
  high_risk: 'danger',
  moderate_risk: 'ochre',
};

export interface RestorationRoadmapProps {
  restoration: RestorationResultContract;
  /** Show IKS guidelines and prohibited practices as well as the phased actions. */
  showGuidance?: boolean;
  className?: string;
}

/** Phased conservation considerations from the restoration planner. */
export const RestorationRoadmap: React.FC<RestorationRoadmapProps> = ({ restoration, showGuidance = true, className = '' }) => {
  const actions = [...(restoration.prioritized_actions ?? [])].sort((a, b) => a.step - b.step);
  const knownPhases = new Set(PHASES.map((p) => p.id));
  const phases = [
    ...PHASES,
    ...Array.from(new Set(actions.map((a) => a.phase)))
      .filter((p) => !knownPhases.has(p))
      .map((p) => ({ id: p, label: humanize(p) })),
  ].filter((phase) => actions.some((a) => a.phase === phase.id));

  const iks = restoration.iks_guidelines;

  return (
    <div className={className}>
      <p className="mb-6 text-sm text-ink-700">
        Strategy: <span className="font-medium text-ink-900">{humanize(restoration.restoration_strategy)}</span>
      </p>

      {actions.length === 0 ? (
        <p className="text-sm text-ink-600">The planner returned no prioritised actions.</p>
      ) : (
        <ol className="space-y-10">
          {phases.map((phase, phaseIndex) => (
            <li key={phase.id} className="grid gap-4 md:grid-cols-[12rem_minmax(0,1fr)]">
              <div>
                <p className="font-mono text-xs text-laterite-500 tabular-nums">Phase {phaseIndex + 1}</p>
                <p className="mt-1 font-display text-xl font-medium leading-tight text-ink-900">{phase.label}</p>
              </div>
              <ul className="space-y-4">
                {actions
                  .filter((a) => a.phase === phase.id)
                  .map((action) => (
                    <li key={action.step} className="break-inside-avoid border-t border-ink-900/15 pt-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <h4 className="text-sm font-semibold text-ink-900">
                          <span className="mr-2 font-mono font-normal text-ink-500 tabular-nums">{String(action.step).padStart(2, '0')}</span>
                          {action.action_title}
                        </h4>
                        <StatusBadge label={humanize(action.urgency)} variant={URGENCY[action.urgency] ?? 'neutral'} />
                      </div>
                      <dl className="mt-3 grid gap-x-4 gap-y-2 text-sm sm:grid-cols-[8rem_minmax(0,1fr)]">
                        <dt className="text-xs text-ink-500">Targets</dt>
                        <dd className="text-ink-700">{humanize(action.target_defect)}</dd>
                        <dt className="text-xs text-ink-500">Technique</dt>
                        <dd className="leading-relaxed text-ink-700">{action.recommended_technique}</dd>
                        <dt className="text-xs text-ink-500">Materials</dt>
                        <dd className="leading-relaxed text-ink-700">{action.material_specification}</dd>
                        {action.preconditions && action.preconditions.length > 0 && (
                          <>
                            <dt className="text-xs text-ink-500">Before starting</dt>
                            <dd className="leading-relaxed text-ink-700">{action.preconditions.join(' ')}</dd>
                          </>
                        )}
                      </dl>
                    </li>
                  ))}
              </ul>
            </li>
          ))}
        </ol>
      )}

      {showGuidance && restoration.incompatible_practices?.length > 0 && (
        <div className="mt-12">
          <h3 className="text-sm font-semibold text-ink-900">Practices to avoid</h3>
          <ul className="mt-3 divide-y divide-ink-900/10 border-y border-ink-900/10">
            {restoration.incompatible_practices.map((p) => (
              <li key={p.prohibited_action} className="grid gap-2 py-4 break-inside-avoid md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] md:gap-6">
                <p className="text-sm font-medium text-ink-900">{p.prohibited_action}</p>
                <p className="text-sm leading-relaxed text-ink-700">{p.failure_mechanism}</p>
                <div>
                  <StatusBadge label={humanize(p.severity)} variant={SEVERITY[p.severity] ?? 'neutral'} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {showGuidance && iks && (
        <div className="mt-12 grid gap-8 md:grid-cols-2">
          {iks.traditional_mortar_recipe && (
            <div className="break-inside-avoid">
              <h3 className="text-sm font-semibold text-ink-900">Traditional mortar</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-700">{iks.traditional_mortar_recipe}</p>
            </div>
          )}
          {iks.seasonal_curing_rules && (
            <div className="break-inside-avoid">
              <h3 className="text-sm font-semibold text-ink-900">Seasonal curing</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-700">{iks.seasonal_curing_rules}</p>
            </div>
          )}
          {iks.craftsmanship_references?.length > 0 && (
            <div className="break-inside-avoid md:col-span-2">
              <h3 className="text-sm font-semibold text-ink-900">References cited by the planner</h3>
              <ul className="mt-2 space-y-1.5 text-sm text-ink-700">
                {iks.craftsmanship_references.map((ref) => (
                  <li key={ref} className="flex gap-3">
                    <span className="mt-[9px] h-px w-3 shrink-0 bg-ink-500" aria-hidden="true" />
                    <span>{ref}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RestorationRoadmap;
