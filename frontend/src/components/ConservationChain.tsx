import React from 'react';
import { AnalysisResultContract } from '../types';
import { OriginKind, OriginTag } from './StatusBadge';
import { listEngineeringMetrics, readRootCauses } from '../utils/analysis';

export interface ConservationChainProps {
  result: AnalysisResultContract;
  /** Called with a section id when a stage is chosen. */
  onJump?: (sectionId: string) => void;
  /** Development fixture: every stage is labelled as sample data. */
  isFixture?: boolean;
  /** Origin of the vision findings; see utils/analysis.visionOrigin. */
  seeOrigin?: OriginKind;
  className?: string;
}

interface Stage {
  verb: string;
  sectionId: string;
  origin: OriginKind;
  summary: string;
}

/**
 * SEE → UNDERSTAND → ASSESS → REVIVE for one result, summarising only what the
 * payload contains and declaring where each stage's output came from.
 */
export const ConservationChain: React.FC<ConservationChainProps> = ({ result, onJump, isFixture = false, seeOrigin = 'model', className = '' }) => {
  const detections = result.vision.detections.length;
  const metrics = listEngineeringMetrics(result).length;
  const causes = readRootCauses(result).length;
  const actions = result.restoration?.prioritized_actions?.length ?? 0;
  const candidates = result.material?.candidate_interventions?.length ?? 0;

  const stages: Stage[] = [
    {
      verb: 'See',
      sectionId: 'findings',
      origin: seeOrigin,
      summary: detections === 0 ? 'No detections returned' : `${detections} detection${detections === 1 ? '' : 's'}`,
    },
    {
      verb: 'Understand',
      sectionId: 'causes',
      origin: 'rules',
      summary: causes === 0 ? 'No probable causes inferred' : `${causes} probable cause${causes === 1 ? '' : 's'}`,
    },
    {
      verb: 'Assess',
      sectionId: 'assessment',
      origin: 'rules',
      summary: `${metrics} score${metrics === 1 ? '' : 's'} · ${candidates} material${candidates === 1 ? '' : 's'} compared`,
    },
    {
      verb: 'Revive',
      sectionId: 'restoration',
      origin: 'expert',
      summary: actions === 0 ? 'No actions returned' : `${actions} prioritised consideration${actions === 1 ? '' : 's'}`,
    },
  ];

  return (
    <nav aria-label="Result stages" className={className}>
      <ol className="grid grid-cols-2 border-y border-ink-900/15 md:grid-cols-4">
        {stages.map((stage, i) => (
          <li key={stage.verb} className={`min-w-0 ${i > 0 ? 'md:border-l' : ''} ${i % 2 === 1 ? 'border-l' : ''} border-ink-900/15 ${i >= 2 ? 'border-t md:border-t-0' : ''}`}>
            <a
              href={`#${stage.sectionId}`}
              onClick={(event) => {
                if (!onJump) return;
                event.preventDefault();
                onJump(stage.sectionId);
              }}
              className="group flex h-full flex-col gap-3 p-4 transition-colors duration-fast hover:bg-stone-100 sm:p-5"
            >
              <span className="flex items-baseline gap-3">
                <span className="font-mono text-[0.625rem] text-ink-500 tabular-nums">{String(i + 1).padStart(2, '0')}</span>
                <span className="font-display text-xl font-medium uppercase tracking-[0.04em] text-ink-900 sm:text-2xl">{stage.verb}</span>
              </span>
              <span className="text-sm text-ink-700">{stage.summary}</span>
              <span className="mt-auto">
                <OriginTag kind={isFixture ? 'fixture' : stage.origin} />
              </span>
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
};

export default ConservationChain;
