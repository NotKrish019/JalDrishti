import React, { useRef, useState } from 'react';
import { InspectionROI } from '../types';

export interface ROISelectorProps {
  imageSrc: string;
  /** Natural pixel size of the image; the ROI is expressed in these pixels. */
  naturalWidth: number;
  naturalHeight: number;
  roi: InspectionROI | null;
  onChangeROI: (roi: InspectionROI | null) => void;
  className?: string;
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/**
 * Optional inspection region. Drawn with the pointer, or typed as pixel values
 * for keyboard users. Output is in image pixels [x, y, width, height].
 */
export const ROISelector: React.FC<ROISelectorProps> = ({
  imageSrc,
  naturalWidth,
  naturalHeight,
  roi,
  onChangeROI,
  className = '',
}) => {
  const frameRef = useRef<HTMLDivElement>(null);
  const [anchor, setAnchor] = useState<{ x: number; y: number } | null>(null);

  const toImagePixels = (event: React.PointerEvent) => {
    const rect = frameRef.current!.getBoundingClientRect();
    return {
      x: clamp(((event.clientX - rect.left) / rect.width) * naturalWidth, 0, naturalWidth),
      y: clamp(((event.clientY - rect.top) / rect.height) * naturalHeight, 0, naturalHeight),
    };
  };

  const handlePointerDown = (event: React.PointerEvent) => {
    if (event.button !== 0) return;
    (event.target as Element).setPointerCapture(event.pointerId);
    const point = toImagePixels(event);
    setAnchor(point);
    onChangeROI({ x: point.x, y: point.y, width: 0, height: 0, isNormalized: false });
  };

  const handlePointerMove = (event: React.PointerEvent) => {
    if (!anchor) return;
    const point = toImagePixels(event);
    onChangeROI({
      x: Math.min(anchor.x, point.x),
      y: Math.min(anchor.y, point.y),
      width: Math.abs(point.x - anchor.x),
      height: Math.abs(point.y - anchor.y),
      isNormalized: false,
    });
  };

  const handlePointerUp = () => {
    setAnchor(null);
    if (roi && (roi.width < 8 || roi.height < 8)) onChangeROI(null);
  };

  const updateField = (key: 'x' | 'y' | 'width' | 'height', value: number) => {
    const base = roi ?? { x: 0, y: 0, width: naturalWidth, height: naturalHeight, isNormalized: false };
    const next = { ...base, [key]: Number.isFinite(value) ? Math.max(0, value) : 0, isNormalized: false };
    next.x = clamp(next.x, 0, naturalWidth - 1);
    next.y = clamp(next.y, 0, naturalHeight - 1);
    next.width = clamp(next.width, 1, naturalWidth - next.x);
    next.height = clamp(next.height, 1, naturalHeight - next.y);
    onChangeROI(next);
  };

  const pct = (v: number, total: number) => `${(v / total) * 100}%`;

  return (
    <div className={className}>
      <div
        ref={frameRef}
        className="relative cursor-crosshair touch-none select-none overflow-hidden rounded-[10px] bg-ws-night"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      >
        <img src={imageSrc} alt="" className="block h-auto w-full" draggable={false} />
        {roi && roi.width > 0 && (
          <>
            {/* Dim everything outside the region */}
            <div
              className="pointer-events-none absolute border border-ws-text"
              style={{
                left: pct(roi.x, naturalWidth),
                top: pct(roi.y, naturalHeight),
                width: pct(roi.width, naturalWidth),
                height: pct(roi.height, naturalHeight),
                boxShadow: '0 0 0 9999px rgb(14 12 10 / 0.55)',
              }}
            />
          </>
        )}
      </div>

      <fieldset className="mt-3">
        <legend className="mb-2 text-[0.8125rem] text-ws-muted">
          Region in image pixels ({naturalWidth} × {naturalHeight})
        </legend>
        <div className="grid grid-cols-4 gap-2">
          {(['x', 'y', 'width', 'height'] as const).map((key) => (
            <label key={key} className="block">
              <span className="mb-1 block font-mono text-[0.6875rem] text-ws-faint">{key}</span>
              <input
                type="number"
                inputMode="numeric"
                min={0}
                className="field h-9 px-2 font-mono tabular-nums"
                value={roi ? Math.round(roi[key]) : ''}
                placeholder="—"
                onChange={(event) => updateField(key, Number(event.target.value))}
              />
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  );
};

export default ROISelector;
