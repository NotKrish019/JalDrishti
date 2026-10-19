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

type Tone = 'light' | 'dark';

const MARKER: Record<Tone, Record<StageStatus, string>> = {
  light: {
    pending: 'border-ink-900/20 bg-ws-paper text-ink-500',
    active: 'border-ws-jade bg-ws-paper text-ws-jade',
    done: 'border-ws-jade bg-ws-jade text-ws-text',
    failed: 'border-danger-500 bg-danger-500 text-stone-50',
    skipped: 'border-ink-900/20 bg-ws-paper text-ink-500',
  },
  dark: {
    pending: 'border-ws-text/25 bg-ws-stone text-ws-faint',
    active: 'border-ws-moss bg-ws-stone text-ws-moss',
    done: 'border-ws-jade-light bg-ws-jade-light text-ws-stone',
    failed: 'border-laterite-300 bg-laterite-300 text-ws-stone',
    skipped: 'border-ws-text/25 bg-ws-stone text-ws-faint',
  },
};

const TEXT: Record<Tone, { title: string; quiet: string; body: string; status: Record<StageStatus, string>; rail: string; railDone: string; error: string }> = {
  light: {
    title: 'text-ink-900',
    quiet: 'text-ink-600',
    body: 'text-ink-600',
    status: { pending: 'text-ink-500', active: 'text-ws-jade', done: 'text-ws-jade', failed: 'text-danger-700', skipped: 'text-ink-500' },
    rail: 'bg-ink-900/15',
    railDone: 'bg-ws-jade',
    error: 'border-danger-500 text-danger-700',
  },
  dark: {
    title: 'text-ws-text',
    quiet: 'text-ws-muted',
    body: 'text-ws-faint',
    status: { pending: 'text-ws-faint', active: 'text-ws-moss', done: 'text-ws-jade-light', failed: 'text-laterite-300', skipped: 'text-ws-faint' },
    rail: 'bg-ws-text/15',
    railDone: 'bg-ws-jade-light',
    error: 'border-laterite-300 text-laterite-300',
  },
};

const STATUS_TEXT: Record<StageStatus, string> = {
  pending: 'Waiting',
  active: 'In progress',
  done: 'Complete',
  failed: 'Failed',
  skipped: 'Skipped',
};

/** Ordered pipeline with states that reflect real request outcomes only. */
export const PipelineStages: React.FC<{
  stages: PipelineStage[];
  className?: string;
  tone?: Tone;
  /** Side by side from md up (stacked below), for full-width status strips. */
  orientation?: 'vertical' | 'horizontal';
}> = ({ stages, className = '', tone = 'light', orientation = 'vertical' }) => {
  const t = TEXT[tone];
  const horizontal = orientation === 'horizontal';
  return (
    <ol className={`${horizontal ? 'grid gap-x-10 md:grid-cols-3' : ''} ${className}`} aria-label="Inspection pipeline">
      {stages.map((stage, index) => (
        <li key={stage.id} className={`relative flex gap-4 pb-6 last:pb-0 ${horizontal ? 'md:pb-0' : ''}`}>
          {index < stages.length - 1 && (
            <span
              className={`absolute bottom-1 left-[11px] top-7 w-px ${horizontal ? 'md:hidden' : ''} ${stage.status === 'done' ? t.railDone : t.rail}`}
              aria-hidden="true"
            />
          )}
          <span
            className={`relative z-[1] flex h-6 w-6 shrink-0 items-center justify-center rounded-full border font-mono text-[0.6875rem] ${MARKER[tone][stage.status]}`}
            aria-hidden="true"
          >
            {stage.status === 'done' ? (
              <Icon name="check" className="h-3 w-3" />
            ) : stage.status === 'failed' ? (
              <Icon name="close" className="h-3 w-3" />
            ) : (
              index + 1
            )}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline justify-between gap-x-3">
              <h3 className={`text-[0.9375rem] font-medium ${stage.status === 'pending' || stage.status === 'skipped' ? t.quiet : t.title}`}>
                {stage.title}
              </h3>
              <span className={`text-[0.8125rem] ${t.status[stage.status]}`}>{STATUS_TEXT[stage.status]}</span>
            </div>
            <p className={`mt-1 text-[0.8125rem] leading-relaxed ${t.body}`}>{stage.description}</p>

            {stage.status === 'active' && (
              <LoadingState className={`mt-3 ${t.quiet}`} label={stage.activeLabel ?? stage.title} progress={stage.progress} />
            )}
            {stage.status === 'failed' && stage.error && (
              <p role="alert" className={`mt-2 border-l-2 pl-3 text-sm ${t.error}`}>
                {stage.error}
              </p>
            )}
            {stage.detail && <div className="mt-3">{stage.detail}</div>}
          </div>
        </li>
      ))}
    </ol>
  );
};

export default PipelineStages;
