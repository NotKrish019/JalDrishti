import React from 'react';
import { InspectionSession } from '../types';
import { Icon } from './Icon';
import { formatTimestamp, visionModelRan } from '../utils/analysis';

/** States plainly whether the result is a live API response or the development sample. */
export const ProvenanceBanner: React.FC<{ session: InspectionSession }> = ({ session }) => {
  const { result } = session;

  if (session.provenance === 'fixture') {
    return (
      <div role="note" className="flex gap-3 rounded-sm border border-ochre-500/50 bg-ochre-100 px-4 py-3.5 text-sm text-ochre-700 print:border-2">
        <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          <strong className="font-semibold">Development sample — not a real inspection.</strong> These values are a fixed
          fixture bundled with the frontend for interface review. They were not produced by the model or the engines.
        </p>
      </div>
    );
  }

  const model = result.vision.processing_metadata?.model_version;
  const latency = result.vision.processing_metadata?.inference_latency_ms;

  const meta = (
    <div role="note" className="flex flex-wrap items-center gap-x-6 gap-y-1 border-y border-ink-900/10 py-3 font-mono text-[0.6875rem] uppercase tracking-[0.06em] text-ink-600">
      <span className="flex items-center gap-2 text-jade-700">
        <span className="h-1.5 w-1.5 rounded-full bg-jade-500" aria-hidden="true" />
        Returned by the JalDrishti API
      </span>
      <span>{formatTimestamp(result.metadata.created_at)}</span>
      {model && <span>Model {model}</span>}
      {typeof latency === 'number' && <span className="tabular-nums">Vision {latency.toFixed(0)} ms</span>}
      <span>Pipeline {result.metadata.pipeline_status}</span>
      {session.image ? <span className="normal-case">Image {session.image.image_id}</span> : <span>Image not stored</span>}
    </div>
  );

  if (visionModelRan(result)) return meta;

  return (
    <div className="space-y-3">
      <div role="alert" className="flex gap-3 rounded-sm border border-ochre-500/50 bg-ochre-100 px-4 py-3.5 text-sm text-ochre-700 print:border-2">
        <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          <strong className="font-semibold">The vision model did not run for this analysis.</strong> The API did not
          report a loaded detection model, so the regions below come from precomputed demo results or the vision
          service&rsquo;s fallback logic — not from live inference on this photograph. Do not rely on them, or on the
          scores and recommendations derived from them.
        </p>
      </div>
      {meta}
    </div>
  );
};

export default ProvenanceBanner;
