import React from 'react';
import { MaterialCompatibilityContract } from '../types';
import { OriginTag } from './StatusBadge';
import { humanize } from '../utils/analysis';

export interface WhyThisRecommendationProps {
  material: MaterialCompatibilityContract;
  className?: string;
}

/**
 * The basis for the material recommendations: which original material was
 * assumed, how confident that assumption is, and what must be tested on site.
 */
export const WhyThisRecommendation: React.FC<WhyThisRecommendationProps> = ({ material, className = '' }) => (
  <div className={`rounded-sm border border-ochre-500/30 bg-ochre-100/40 p-5 ${className}`}>
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p className="text-xs text-ink-600">Assumed original material</p>
        <p className="mt-1 text-base font-semibold text-ink-900">{humanize(material.original_material)}</p>
        <p className="mt-1 font-mono text-xs text-ink-600 tabular-nums">
          Assumption confidence {(material.original_material_confidence * 100).toFixed(0)}%
        </p>
      </div>
      {material.verification_required && <OriginTag kind="expert" />}
    </div>

    <p className="mt-4 text-sm leading-relaxed text-ink-700">
      The original material is inferred from the structure type, not identified from the photograph. Compatibility scores
      below hold only if the assumption is confirmed{material.verification_required ? ' by the tests listed' : ''}.
    </p>

    {material.recommended_tests && material.recommended_tests.length > 0 && (
      <div className="mt-4">
        <p className="text-xs font-medium text-ink-900">Recommended confirmation tests</p>
        <ol className="mt-2 space-y-1.5 text-xs leading-relaxed text-ink-700">
          {material.recommended_tests.map((test, i) => (
            <li key={test} className="flex gap-3">
              <span className="font-mono text-ink-500 tabular-nums">{String(i + 1).padStart(2, '0')}</span>
              <span>{test}</span>
            </li>
          ))}
        </ol>
      </div>
    )}
  </div>
);

export default WhyThisRecommendation;
