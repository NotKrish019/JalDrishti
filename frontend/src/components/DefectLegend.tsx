import React from 'react';
import { DetectionItem } from '../types';
import { defectColor, humanize } from '../utils/analysis';

export interface DefectLegendProps {
  detections: DetectionItem[];
  visibleClasses: Set<string>;
  onToggleClass: (className: string) => void;
  className?: string;
}

/** Per-class visibility toggles with a colour key and detection count. */
export const DefectLegend: React.FC<DefectLegendProps> = ({ detections, visibleClasses, onToggleClass, className = '' }) => {
  const counts = detections.reduce<Record<string, number>>((acc, d) => {
    acc[d.class_name] = (acc[d.class_name] ?? 0) + 1;
    return acc;
  }, {});
  const classes = Object.keys(counts);

  if (classes.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-2 ${className}`} role="group" aria-label="Show or hide defect classes">
      {classes.map((name) => {
        const on = visibleClasses.has(name);
        return (
          <button
            key={name}
            type="button"
            aria-pressed={on}
            onClick={() => onToggleClass(name)}
            className={`inline-flex h-8 items-center gap-2 rounded-sm border px-3 text-xs transition-colors duration-fast ${
              on ? 'border-ink-900/30 bg-white text-ink-900' : 'border-ink-900/10 bg-transparent text-ink-500 line-through'
            }`}
          >
            <span
              className="h-2.5 w-2.5 rounded-[1px] border"
              style={{ backgroundColor: on ? defectColor(name) : 'transparent', borderColor: defectColor(name) }}
              aria-hidden="true"
            />
            {humanize(name)}
            <span className="font-mono text-ink-500 tabular-nums">{counts[name]}</span>
          </button>
        );
      })}
    </div>
  );
};

export default DefectLegend;
