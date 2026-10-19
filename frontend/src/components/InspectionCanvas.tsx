import React, { useState } from 'react';
import { DetectionItem, ImageDimensions } from '../types';
import { defectColor, humanize } from '../utils/analysis';

export interface InspectionCanvasProps {
  /** Null when the result carries no displayable image; boxes are then drawn on a blank frame. */
  imageSrc: string | null;
  imageDimensions: ImageDimensions;
  detections: DetectionItem[];
  visibleClasses: Set<string>;
  highlighted: number | null;
  onHighlight: (index: number | null) => void;
  className?: string;
}

/**
 * Photograph with detection boxes drawn in the image's own pixel space via an
 * SVG viewBox, so the boxes stay registered at every display size.
 */
export const InspectionCanvas: React.FC<InspectionCanvasProps> = ({
  imageSrc,
  imageDimensions,
  detections,
  visibleClasses,
  highlighted,
  onHighlight,
  className = '',
}) => {
  const [showLabels, setShowLabels] = useState(true);
  const [imageFailed, setImageFailed] = useState(false);
  const { width_pixels: w, height_pixels: h } = imageDimensions;
  const stroke = Math.max(2, Math.round(Math.max(w, h) / 450));
  const fontSize = Math.max(12, Math.round(Math.max(w, h) / 70));
  const visible = detections
    .map((d, index) => ({ d, index }))
    .filter(({ d }) => visibleClasses.has(d.class_name));
  const showImage = imageSrc && !imageFailed;

  return (
    <figure className={`overflow-hidden rounded-sm bg-ws-night ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ws-text/10 px-4 py-2.5">
        <p className="font-mono text-[0.6875rem] uppercase tracking-[0.08em] text-ws-muted tabular-nums">
          {w} × {h} px · {visible.length} of {detections.length} shown
        </p>
        <label className="flex cursor-pointer items-center gap-2 text-xs text-ws-text">
          <input
            type="checkbox"
            className="h-3.5 w-3.5 accent-ws-mist"
            checked={showLabels}
            onChange={(event) => setShowLabels(event.target.checked)}
          />
          Labels
        </label>
      </div>

      <svg
        viewBox={`0 0 ${w} ${h}`}
        className="block h-auto w-full"
        role="img"
        aria-label={`Inspection image with ${visible.length} detection box${visible.length === 1 ? '' : 'es'}`}
        onMouseLeave={() => onHighlight(null)}
      >
        {showImage ? (
          <image href={imageSrc} x="0" y="0" width={w} height={h} preserveAspectRatio="none" onError={() => setImageFailed(true)} />
        ) : (
          <>
            <rect width={w} height={h} fill="#221D17" />
            <text x={w / 2} y={h / 2} textAnchor="middle" fill="#76675A" fontSize={fontSize * 1.2} fontFamily="Instrument Sans, sans-serif">
              Image not available — boxes shown in image coordinates
            </text>
          </>
        )}

        {highlighted !== null && visible.some((v) => v.index === highlighted) && (
          <rect width={w} height={h} fill="rgb(14 12 10 / 0.35)" pointerEvents="none" />
        )}

        {visible.map(({ d, index }) => {
          const [x1, y1, x2, y2] = d.bounding_box;
          const color = defectColor(d.class_name);
          const active = highlighted === index;
          const dimmed = highlighted !== null && !active;
          const label = `${humanize(d.class_name)} · ${(d.confidence * 100).toFixed(0)}%`;
          return (
            <g
              key={index}
              opacity={dimmed ? 0.35 : 1}
              onMouseEnter={() => onHighlight(index)}
              style={{ cursor: 'pointer' }}
            >
              <rect
                x={x1}
                y={y1}
                width={Math.max(1, x2 - x1)}
                height={Math.max(1, y2 - y1)}
                fill={active ? `${color}33` : 'transparent'}
                stroke={color}
                strokeWidth={active ? stroke * 1.8 : stroke}
              />
              {showLabels && (
                <g transform={`translate(${x1}, ${Math.max(0, y1 - fontSize * 1.6)})`}>
                  <rect width={label.length * fontSize * 0.56 + fontSize} height={fontSize * 1.6} fill={color} />
                  <text
                    x={fontSize * 0.5}
                    y={fontSize * 1.12}
                    fontSize={fontSize}
                    fill="#17140F"
                    fontFamily="IBM Plex Mono, monospace"
                  >
                    {label}
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>

      <figcaption className="border-t border-ws-text/10 px-4 py-2.5 text-xs text-ws-muted">
        Boxes mark regions returned by the vision service. Percentages are detection confidence, not severity.
      </figcaption>
    </figure>
  );
};

export default InspectionCanvas;
