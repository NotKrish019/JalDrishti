import React, { useId, useRef, useState } from 'react';
import { Icon } from './Icon';
import { ACCEPTED_IMAGE_TYPES, MAX_UPLOAD_BYTES } from '../services/api';
import { formatBytes } from '../utils/analysis';

export interface SelectedImage {
  file: File;
  previewUrl: string;
  width: number;
  height: number;
}

export interface UploadZoneProps {
  selected: SelectedImage | null;
  onSelect: (image: SelectedImage) => void;
  onClear: () => void;
  /** Locks replacement/removal, e.g. while uploading or once the file is stored. */
  locked?: boolean;
  lockedReason?: string;
  /** Replaces the plain preview (used to show the ROI selector). */
  previewSlot?: React.ReactNode;
  className?: string;
}

/** Validates against the same rules the backend enforces, before any bytes are sent. */
const validate = (file: File): string | null => {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return `“${file.name}” is ${file.type || 'an unknown type'}. Use a JPEG, PNG or WebP photograph.`;
  }
  if (file.size === 0) return `“${file.name}” is empty.`;
  if (file.size > MAX_UPLOAD_BYTES) {
    return `“${file.name}” is ${formatBytes(file.size)}. The limit is ${formatBytes(MAX_UPLOAD_BYTES)}.`;
  }
  return null;
};

const readDimensions = (url: string): Promise<{ width: number; height: number }> =>
  new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight });
    img.onerror = () => reject(new Error('decode'));
    img.src = url;
  });

export const UploadZone: React.FC<UploadZoneProps> = ({
  selected,
  onSelect,
  onClear,
  locked = false,
  lockedReason,
  previewSlot,
  className = '',
}) => {
  const inputId = useId();
  const hintId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accept = async (file: File | undefined) => {
    if (!file || locked) return;
    const problem = validate(file);
    if (problem) {
      setError(problem);
      return;
    }
    const url = URL.createObjectURL(file);
    try {
      const { width, height } = await readDimensions(url);
      setError(null);
      onSelect({ file, previewUrl: url, width, height });
    } catch {
      URL.revokeObjectURL(url);
      setError(`“${file.name}” could not be decoded as an image.`);
    }
    if (inputRef.current) inputRef.current.value = '';
  };

  const input = (
    <input
      ref={inputRef}
      id={inputId}
      type="file"
      accept={ACCEPTED_IMAGE_TYPES.join(',')}
      className="peer sr-only"
      aria-describedby={hintId}
      disabled={locked}
      onChange={(event) => accept(event.target.files?.[0])}
    />
  );

  const errorLine = error && (
    <p role="alert" className="mt-3 flex items-start gap-2 text-sm text-laterite-300">
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      {error}
    </p>
  );

  if (selected) {
    return (
      <div className={className}>
        {previewSlot ?? (
          <div key={selected.previewUrl} className="ws-reveal flex items-center justify-center overflow-hidden rounded-[10px] bg-ws-night">
            <img
              src={selected.previewUrl}
              alt={`Preview of ${selected.file.name}`}
              className="block max-h-[32rem] w-auto max-w-full object-contain"
            />
          </div>
        )}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <p className="min-w-0 text-sm">
            <span className="block truncate font-medium text-ws-text">{selected.file.name}</span>
            <span className="font-mono text-xs tabular-nums text-ws-faint">
              {selected.width} × {selected.height} px · {formatBytes(selected.file.size)}
            </span>
          </p>
          {locked ? (
            lockedReason && <p className="text-[0.8125rem] text-ws-muted">{lockedReason}</p>
          ) : (
            <div className="flex items-center gap-1">
              {input}
              <label
                htmlFor={inputId}
                className="inline-flex h-8 cursor-pointer items-center rounded-lg px-3 text-[0.8125rem] font-medium text-ws-text transition-colors duration-fast hover:bg-ws-text/[0.08] peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-ws-moss"
              >
                Replace
              </label>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  onClear();
                }}
                className="inline-flex h-8 items-center gap-1.5 rounded-lg px-3 text-[0.8125rem] font-medium text-ws-muted transition-colors duration-fast hover:bg-ws-text/[0.08] hover:text-ws-text"
              >
                <Icon name="close" className="h-3.5 w-3.5" />
                Remove
              </button>
            </div>
          )}
        </div>
        <p id={hintId} className="sr-only">
          JPEG, PNG or WebP, up to {formatBytes(MAX_UPLOAD_BYTES)}.
        </p>
        {errorLine}
      </div>
    );
  }

  return (
    <div className={className}>
      {input}
      <label
        htmlFor={inputId}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          accept(event.dataTransfer.files?.[0]);
        }}
        className={`group flex cursor-pointer flex-col items-start gap-7 rounded-[14px] p-5 transition-colors duration-base ease-out sm:flex-row sm:items-center sm:gap-10 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-4 peer-focus-visible:outline-ws-moss ${
          dragging ? 'bg-ws-moss/[0.1]' : 'hover:bg-ws-text/[0.03]'
        }`}
      >
        {/* An empty niche: the photograph will be placed into it. */}
        <span aria-hidden="true" className="relative block h-56 w-44 shrink-0 sm:h-64 sm:w-52">
          <svg viewBox="0 0 100 125" preserveAspectRatio="none" className="absolute inset-0 h-full w-full overflow-visible">
            <defs>
              <linearGradient id={`${inputId}-water`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#2f6a5c" stopOpacity="0" />
                <stop offset="1" stopColor="#2f6a5c" stopOpacity={dragging ? 0.85 : 0.55} />
              </linearGradient>
            </defs>
            <path d="M0 125V46C0 22 21 4.5 50 0C79 4.5 100 22 100 46V125Z" fill={`url(#${inputId}-water)`} />
            <path
              d="M0.5 124.5V46C0.5 22 21 5 50 0.8C79 5 99.5 22 99.5 46V124.5"
              fill="none"
              vectorEffect="non-scaling-stroke"
              strokeDasharray="5 5"
              className={`transition-colors duration-base ${dragging ? 'stroke-ws-moss' : 'stroke-ws-text/35 group-hover:stroke-ws-text/60'}`}
              strokeWidth="1.25"
            />
            {[104, 112, 120].map((y, i) => (
              <path key={y} d={`M${10 + i * 4} ${y}H${90 - i * 4}`} vectorEffect="non-scaling-stroke" className="stroke-ws-text/20" strokeWidth="1" />
            ))}
          </svg>
          <span className="absolute inset-x-0 top-[38%] flex justify-center">
            <span
              className={`flex h-11 w-11 items-center justify-center rounded-full border transition-colors duration-base ${
                dragging ? 'border-ws-moss text-ws-moss' : 'border-ws-text/30 text-ws-text group-hover:border-ws-text/60'
              }`}
            >
              <Icon name="upload" className="h-4 w-4" />
            </span>
          </span>
        </span>
        <span className="max-w-[22rem]">
          <span className="block font-display text-[1.875rem] font-medium leading-[1.1] text-ws-text">
            {dragging ? 'Release to place the photograph' : 'Place a photograph in the niche'}
          </span>
          <span className="mt-3 block text-[0.9375rem] leading-relaxed text-ws-muted">
            Drag an image here, or{' '}
            <span className="font-medium text-ws-text underline decoration-ws-text/40 underline-offset-4">choose a file</span>. A
            square-on view of a wall, flight of steps or surface works best.
          </span>
          <span id={hintId} className="mt-4 block text-[0.8125rem] text-ws-faint">
            JPEG, PNG or WebP · up to {formatBytes(MAX_UPLOAD_BYTES)}
          </span>
        </span>
      </label>
      {errorLine}
    </div>
  );
};

export default UploadZone;
