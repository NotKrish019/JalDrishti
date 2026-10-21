/**
 * Helpers that read analysis payloads defensively. The live `/analyze`
 * response and the development fixture differ slightly in shape; these
 * helpers return only what is actually present and never invent values.
 */

import {
  AnalysisResultContract,
  InspectionSession,
  MetricScore,
  RootCauseItem,
} from '../types';

const isMetric = (value: unknown): value is MetricScore =>
  !!value &&
  typeof value === 'object' &&
  typeof (value as MetricScore).value === 'number' &&
  typeof (value as MetricScore).scale_max === 'number';

/** Accepts a flat MetricScore or `{ score: MetricScore }`; anything else is absent. */
export const readMetric = (value: unknown): MetricScore | null => {
  if (isMetric(value)) return value;
  if (value && typeof value === 'object' && 'score' in value && isMetric((value as { score: unknown }).score)) {
    return (value as { score: MetricScore }).score;
  }
  return null;
};

export interface LabelledMetric {
  key: string;
  label: string;
  metric: MetricScore;
  /** How to read the number: higher is better, or higher means more urgent / more damage. */
  direction: 'higher_better' | 'higher_worse';
}

/** Engineering scores present in the payload, in a stable reading order. */
export const listEngineeringMetrics = (result: AnalysisResultContract): LabelledMetric[] => {
  const candidates: Array<[string, string, unknown, LabelledMetric['direction']]> = [
    ['visual_condition', 'Visual condition', result.visual_condition, 'higher_better'],
    ['water_functionality', 'Water functionality', result.water_functionality, 'higher_better'],
    ['restoration_priority_score', 'Restoration priority', result.restoration_priority_score, 'higher_worse'],
    [
      'visual_crack_burden',
      'Visual crack burden',
      result.visual_crack_burden ?? result.sub_scores?.visual_crack_burden,
      'higher_worse',
    ],
    ['vegetation_intrusion_index', 'Vegetation intrusion', result.sub_scores?.vegetation_intrusion_index, 'higher_worse'],
    ['masonry_integrity_index', 'Masonry integrity', result.sub_scores?.masonry_integrity_index, 'higher_better'],
    [
      'siltation_obstruction_index',
      'Siltation obstruction',
      result.sub_scores?.siltation_obstruction_index,
      'higher_worse',
    ],
  ];

  return candidates.flatMap(([key, label, raw, direction]) => {
    const metric = readMetric(raw);
    return metric ? [{ key, label, metric, direction }] : [];
  });
};

/** Root causes from either the live `{ findings: [...] }` shape or the fixture array. */
export const readRootCauses = (result: AnalysisResultContract): RootCauseItem[] => {
  const raw = result.root_cause as unknown;
  if (Array.isArray(raw)) return raw as RootCauseItem[];
  if (raw && typeof raw === 'object' && Array.isArray((raw as { findings?: unknown }).findings)) {
    return (raw as { findings: RootCauseItem[] }).findings;
  }
  return [];
};

/** Best available image for overlays: stored Cloudinary preview, local file, then a path in the result. */
export const resolveImageSource = (session: InspectionSession): string | null => {
  if (session.image?.preview_url) return session.image.preview_url;
  if (session.localPreviewUrl) return session.localPreviewUrl;
  const first = session.result.structure.source_images?.[0];
  if (first && (/^(https?:|blob:|data:)/.test(first) || first.startsWith('/'))) return first;
  return null;
};

/** `vegetation_root_intrusion` → `Vegetation root intrusion` */
export const humanize = (token: string): string => {
  const text = token.replace(/_/g, ' ').trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const formatPercent = (fraction: number, digits = 1): string => `${(fraction * 100).toFixed(digits)}%`;

export const formatNumber = (value: number, digits = 0): string =>
  value.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });

export const formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

export const formatTimestamp = (iso: string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/** Overlay colours per defect class, drawn from the design palette. */
export const defectColor = (className: string): string => {
  switch (className) {
    case 'crack':
      return '#C0714F'; // laterite-400
    case 'vegetation_root_intrusion':
    case 'biological_growth':
      return '#7FA393'; // jade-300
    case 'spalling':
    case 'stone_dislodgement':
      return '#E0B15F'; // ochre, lightened for contrast on dark imagery
    case 'efflorescence':
      return '#E2D3BA'; // stone-200
    case 'silt_accumulation':
      return '#B8956A'; // stone-400
    default:
      return '#D9997C'; // laterite-300
  }
};

/**
 * True only when the vision service reports a loaded detection model. The
 * backend appends "+fasterrcnn-..." or "+yolov8n-crack" to model_version only when
 * an actual detection model was loaded and ran live inference; otherwise any
 * detections came from demo matches or fallback logic.
 */
export const visionModelRan = (result: AnalysisResultContract): boolean =>
  /(?:fasterrcnn|yolo|rcnn)/i.test(result.vision.processing_metadata?.model_version ?? '');

export const visionOrigin = (session: InspectionSession): 'fixture' | 'model' | 'unverified' =>
  session.provenance === 'fixture' ? 'fixture' : visionModelRan(session.result) ? 'model' : 'unverified';
