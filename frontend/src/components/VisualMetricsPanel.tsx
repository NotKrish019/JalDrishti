import React from 'react';
import { DetectionItem, ScaleReference } from '../types';
import { defectColor, formatNumber, formatPercent, humanize } from '../utils/analysis';

export interface VisualMetricsPanelProps {
  detections: DetectionItem[];
  scaleReference?: ScaleReference;
  highlighted?: number | null;
  onHighlight?: (index: number | null) => void;
  className?: string;
}

const EXTENT_STYLE: Record<string, string> = {
  low: 'text-jade-700',
  moderate: 'text-ochre-700',
  severe: 'text-danger-700',
};

/**
 * Detection inventory exactly as returned. Detection confidence and relative
 * image-space extent are separate columns and are never combined.
 */
export const VisualMetricsPanel: React.FC<VisualMetricsPanelProps> = ({
  detections,
  scaleReference,
  highlighted = null,
  onHighlight,
  className = '',
}) => {
  const calibrated = scaleReference?.calibrated === true && !!scaleReference.pixels_per_millimeter;

  if (detections.length === 0) {
    return (
      <p className={`border-y border-ink-900/10 py-6 text-sm text-ink-700 ${className}`}>
        The vision service returned no detections for this image. This does not mean the structure is free of defects —
        only that none were identified in this photograph by the current model.
      </p>
    );
  }

  return (
    <div className={className}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[46rem] border-collapse text-left text-sm">
          <caption className="sr-only">Detections returned by the vision service</caption>
          <thead>
            <tr className="border-b border-ink-900/20 text-xs text-ink-600">
              <th scope="col" className="py-2.5 pr-4 font-medium">Class</th>
              <th scope="col" className="py-2.5 pr-4 font-medium">Detection confidence</th>
              <th scope="col" className="py-2.5 pr-4 font-medium">Relative extent (image-space)</th>
              <th scope="col" className="py-2.5 pr-4 text-right font-medium">Area (px²)</th>
              <th scope="col" className="py-2.5 pr-4 text-right font-medium">Coverage</th>
              <th scope="col" className="py-2.5 pr-4 text-right font-medium">Components</th>
              <th scope="col" className="py-2.5 text-right font-medium">Length (px)</th>
            </tr>
          </thead>
          <tbody>
            {detections.map((d, index) => (
              <tr
                key={index}
                tabIndex={onHighlight ? 0 : undefined}
                onMouseEnter={() => onHighlight?.(index)}
                onMouseLeave={() => onHighlight?.(null)}
                onFocus={() => onHighlight?.(index)}
                onBlur={() => onHighlight?.(null)}
                className={`border-b border-ink-900/10 transition-colors duration-fast focus:outline-none ${
                  highlighted === index ? 'bg-stone-100' : ''
                }`}
              >
                <th scope="row" className="py-3 pr-4 font-medium text-ink-900">
                  <span className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 shrink-0 rounded-[1px]" style={{ backgroundColor: defectColor(d.class_name) }} aria-hidden="true" />
                    {humanize(d.class_name)}
                  </span>
                </th>
                <td className="py-3 pr-4 font-mono tabular-nums text-ink-900">{formatPercent(d.confidence, 1)}</td>
                <td className={`py-3 pr-4 ${d.relative_severity ? EXTENT_STYLE[d.relative_severity] : 'text-ink-500'}`}>
                  {d.relative_severity ? humanize(d.relative_severity) : 'Not reported'}
                </td>
                <td className="py-3 pr-4 text-right font-mono tabular-nums text-ink-700">{formatNumber(d.pixel_area)}</td>
                <td className="py-3 pr-4 text-right font-mono tabular-nums text-ink-700">{formatPercent(d.coverage_ratio, 2)}</td>
                <td className="py-3 pr-4 text-right font-mono tabular-nums text-ink-700">{d.component_count}</td>
                <td className="py-3 text-right font-mono tabular-nums text-ink-700">
                  {typeof d.total_length_pixels === 'number' ? formatNumber(d.total_length_pixels) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs leading-relaxed text-ink-500">
        {calibrated
          ? `Scale reference supplied: ${scaleReference!.pixels_per_millimeter} px/mm (${scaleReference!.method ?? 'method not stated'}).`
          : 'Image-space measurements; no physical scale was supplied, so pixel values are not physical dimensions.'}{' '}
        “Relative extent” is the vision service’s coverage-based grading, not an engineering severity rating.
      </p>
    </div>
  );
};

export default VisualMetricsPanel;
