import React from 'react';
import { Icon } from './Icon';
import { LoadingState } from './LoadingState';

export type StageStatus = 'pending' | 'active' | 'done' | 'failed' | 'skipped';

export interface PipelineStage {
  id: string;
  title: string;
  description: string;
  status: StageStatus;
  /** Real 0–1 progress, only when measurable. */
  progress?: number;
  /** Text shown while active (e.g. what is being waited on). */
  activeLabel?: string;
  /** Actual error message from the backend or network. */
  error?: string;
  /** Extra content, e.g. stored identifiers or recovery actions. */
  detail?: React.ReactNode;
}

const MARKER: Record<StageStatus, string> = {
  pending: 'border-ink-900/20 bg-stone-50 text-ink-500',
  active: 'border-jade-500 bg-stone-50 text-jade-600',
  done: 'border-jade-600 bg-jade-600 text-stone-50',
  failed: 'border-danger-500 bg-danger-500 text-stone-50',
  skipped: 'border-ink-900/20 bg-stone-50 text-ink-500',
};

const STATUS_TEXT: Record<StageStatus, string> = {
  pending: 'Waiting',
  active: 'In progress',
  done: 'Complete',
  failed: 'Failed',
  skipped: 'Skipped',
};

/** Ordered pipeline with states that reflect real request outcomes only. */
export const PipelineStages: React.FC<{ stages: PipelineStage[]; className?: string }> = ({ stages, className = '' }) => (
  <ol className={className} aria-label="Inspection pipeline">
    {stages.map((stage, index) => (
      <li key={stage.id} className="relative flex gap-4 pb-6 last:pb-0">
        {index < stages.length - 1 && (
          <span
            className={`absolute left-[13px] top-8 bottom-1 w-px ${stage.status === 'done' ? 'bg-jade-600' : 'bg-ink-900/15'}`}
            aria-hidden="true"
          />
        )}
        <span
          className={`relative z-[1] flex h-7 w-7 shrink-0 items-center justify-center rounded-full border font-mono text-[0.6875rem] ${MARKER[stage.status]}`}
          aria-hidden="true"
        >
          {stage.status === 'done' ? (
            <Icon name="check" className="h-3.5 w-3.5" />
          ) : stage.status === 'failed' ? (
            <Icon name="close" className="h-3.5 w-3.5" />
          ) : (
            index + 1
          )}
        </span>
        <div className="min-w-0 flex-1 pt-0.5">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3">
            <h3 className={`text-sm font-medium ${stage.status === 'pending' || stage.status === 'skipped' ? 'text-ink-600' : 'text-ink-900'}`}>
              {stage.title}
            </h3>
            <span className="font-mono text-[0.6875rem] uppercase tracking-[0.08em] text-ink-500">
              {STATUS_TEXT[stage.status]}
            </span>
          </div>
          <p className="mt-0.5 text-xs leading-relaxed text-ink-600">{stage.description}</p>

          {stage.status === 'active' && (
            <LoadingState className="mt-3" label={stage.activeLabel ?? stage.title} progress={stage.progress} />
          )}
          {stage.status === 'failed' && stage.error && (
            <p role="alert" className="mt-2 border-l-2 border-danger-500 pl-3 text-sm text-danger-700">
              {stage.error}
            </p>
          )}
          {stage.detail && <div className="mt-3">{stage.detail}</div>}
        </div>
      </li>
    ))}
  </ol>
);

export default PipelineStages;
