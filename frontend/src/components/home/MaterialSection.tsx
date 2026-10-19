import React, { useEffect, useState } from 'react';
import { SectionIndex } from './SectionIndex';
import { evaluateMaterialCompatibility } from '../../services/api';
import type { CandidateIntervention, CompatibilityDimensions } from '../../types';

const SUBSTRATE = 'hydraulic_lime_mortar';
const CANDIDATES = ['natural_hydraulic_lime_nhl', 'portland_cement_opc'];

const NAMES: Record<string, string> = {
  hydraulic_lime_mortar: 'Traditional hydraulic lime mortar',
  natural_hydraulic_lime_nhl: 'Natural hydraulic lime (NHL)',
  portland_cement_opc: 'Ordinary Portland cement',
};

const DIMENSIONS: { key: keyof CompatibilityDimensions; label: string; note: string }[] = [
  { key: 'mechanical', label: 'Mechanical', note: 'Should a repair be weaker than the stone it joins?' },
  { key: 'moisture', label: 'Moisture', note: 'Can water vapour still leave the wall?' },
  { key: 'thermal', label: 'Thermal', note: 'Do they expand and contract together?' },
  { key: 'chemical', label: 'Chemical', note: 'Will salts or reactions damage the original?' },
  { key: 'reversibility', label: 'Reversibility', note: 'Can it be removed later without harm?' },
  { key: 'heritage', label: 'Heritage', note: 'Is it consistent with how the structure was built?' },
  { key: 'visual', label: 'Visual', note: 'Does it sit quietly beside historic fabric?' },
];

type State =
  | { status: 'loading' }
  | { status: 'ready'; candidates: CandidateIntervention[]; verification: boolean }
  | { status: 'unavailable'; message: string };

const recommendationLabel = (r: CandidateIntervention['recommendation']) =>
  ({
    strongly_recommended: 'Strongly recommended',
    recommended: 'Recommended',
    acceptable_conditional: 'Conditional',
    prohibited_incompatible: 'Incompatible',
  })[r] ?? r;

/**
 * Explains compatibility with a live call to the rule-based engine. When the
 * service is unreachable the dimensions are still explained, with no numbers.
 */
export const MaterialSection: React.FC = () => {
  const [state, setState] = useState<State>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    evaluateMaterialCompatibility(SUBSTRATE, CANDIDATES)
      .then((res) => {
        if (cancelled) return;
        const ordered = CANDIDATES.map((id) =>
          res.candidate_interventions.find((c) => c.intervention_material === id),
        ).filter((c): c is CandidateIntervention => Boolean(c));
        setState({ status: 'ready', candidates: ordered, verification: res.verification_required });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setState({ status: 'unavailable', message: err instanceof Error ? err.message : 'Service unreachable' });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const candidates = state.status === 'ready' ? state.candidates : [];
  const flagged = candidates.find((c) => c.recommendation === 'prohibited_incompatible');

  return (
    <section aria-labelledby="materials-title" className="gutter grain bg-stone-50 py-28 sm:py-36">
      <div className="mx-auto max-w-wide">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <SectionIndex number="05" label="Material compatibility" />
            <h2 id="materials-title" data-reveal="mask" className="mt-10 font-display text-display-md font-medium text-ink-950">
              The right repair is the one the original can live with.
            </h2>
            <p data-reveal className="mt-8 max-w-prose text-base leading-relaxed text-ink-700">
              A conservation repair is judged against the material it touches: its strength, how it handles moisture
              and heat, how it reacts chemically, and whether it can be undone. JalDrishti scores candidate materials
              on seven such dimensions and explains each warning.
            </p>
            <p data-reveal className="mt-6 max-w-prose border-l-2 border-laterite-400 pl-4 text-sm leading-relaxed text-ink-700">
              These are rule-based indications from documented material properties, not laboratory results. The
              original material must be identified on site — for example by petrographic or salt analysis — before any
              recommendation is acted on.
            </p>
          </div>

          <div data-reveal className="lg:col-span-7 lg:pt-4">
            <div className="border border-ink-900/10 bg-white">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink-900/10 px-5 py-4 sm:px-6">
                <div>
                  <p className="eyebrow text-ink-600">Substrate</p>
                  <p className="mt-1 text-sm font-medium text-ink-950">{NAMES[SUBSTRATE]}</p>
                </div>
                <p className="eyebrow inline-flex items-center gap-2 text-ink-600" role="status">
                  <span
                    aria-hidden="true"
                    className={`h-1.5 w-1.5 rounded-full ${
                      state.status === 'ready'
                        ? 'bg-jade-500'
                        : state.status === 'loading'
                          ? 'animate-pulse bg-ochre-500'
                          : 'bg-ink-500'
                    }`}
                  />
                  {state.status === 'ready' && 'Live · rule-based engine'}
                  {state.status === 'loading' && 'Asking the engine…'}
                  {state.status === 'unavailable' && 'Engine unreachable · showing criteria only'}
                </p>
              </div>

              {/* Legend */}
              {candidates.length > 0 && (
                <div className="grid grid-cols-1 gap-px border-b border-ink-900/10 bg-ink-900/10 sm:grid-cols-2">
                  {candidates.map((c, i) => (
                    <div key={c.intervention_material} className="bg-white px-5 py-4 sm:px-6">
                      <p className="flex items-center gap-2 text-sm font-medium text-ink-950">
                        <span
                          aria-hidden="true"
                          className={`h-2.5 w-2.5 ${i === 0 ? 'bg-jade-500' : 'bg-laterite-500'}`}
                        />
                        {NAMES[c.intervention_material] ?? c.intervention_material}
                      </p>
                      <p className="mt-2 flex items-baseline gap-2">
                        <span className="font-display text-4xl font-medium tabular-nums text-ink-950">
                          {Math.round(c.compatibility_score)}
                        </span>
                        <span className="text-xs text-ink-600">/ 100 compatibility</span>
                      </p>
                      <p
                        className={`eyebrow mt-2 ${
                          c.recommendation === 'prohibited_incompatible' ? 'text-danger-500' : 'text-jade-600'
                        }`}
                      >
                        {recommendationLabel(c.recommendation)}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Dimensions */}
              <ul className="divide-y divide-ink-900/10">
                {DIMENSIONS.map((d) => (
                  <li key={d.key} className="grid grid-cols-1 gap-2 px-5 py-4 sm:grid-cols-[9rem_1fr] sm:gap-6 sm:px-6">
                    <div>
                      <p className="text-sm font-medium text-ink-950">{d.label}</p>
                      <p className="mt-0.5 text-xs leading-snug text-ink-600">{d.note}</p>
                    </div>
                    {candidates.length > 0 ? (
                      <div className="flex flex-col justify-center gap-1.5">
                        {candidates.map((c, i) => {
                          const v = c.compatibility_dimensions[d.key];
                          return (
                            <div key={c.intervention_material} className="flex items-center gap-3">
                              <div className="relative h-1.5 flex-1 bg-stone-100">
                                <div
                                  className={`absolute inset-y-0 left-0 ${i === 0 ? 'bg-jade-500' : 'bg-laterite-500'}`}
                                  style={{ width: `${(v / 10) * 100}%` }}
                                />
                              </div>
                              <span className="w-8 text-right font-mono text-xs tabular-nums text-ink-700">
                                {v.toFixed(1)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="flex items-center">
                        <div className="h-1.5 w-full bg-stone-100" aria-hidden="true" />
                      </div>
                    )}
                  </li>
                ))}
              </ul>

              {flagged?.warnings[0] && (
                <div className="border-t border-ink-900/10 bg-danger-100/40 px-5 py-4 sm:px-6">
                  <p className="eyebrow text-danger-700">
                    Engine warning · {NAMES[flagged.intervention_material] ?? flagged.intervention_material}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-ink-800">{flagged.warnings[0]}</p>
                </div>
              )}
              {state.status === 'unavailable' && (
                <p className="border-t border-ink-900/10 px-5 py-4 text-xs text-ink-600 sm:px-6">
                  The compatibility service could not be reached, so no scores are shown. ({state.message})
                </p>
              )}
            </div>
            <p className="mt-3 font-mono text-[11px] tracking-wide text-ink-600">
              Scores 0–10 per dimension from POST /material-compatibility. Verification by a conservation professional
              is always required.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default MaterialSection;
