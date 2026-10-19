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
    <p role="alert" className="mt-3 flex items-start gap-2 text-sm text-danger-700">
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      {error}
    </p>
  );

  if (selected) {
    return (
      <div className={className}>
        {previewSlot ?? (
          <div className="flex items-center justify-center bg-ink-900">
            <img
              src={selected.previewUrl}
              alt={`Preview of ${selected.file.name}`}
              className="block max-h-[34rem] w-auto max-w-full object-contain"
            />
          </div>
        )}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p className="min-w-0 text-sm">
            <span className="block truncate font-medium text-ink-900">{selected.file.name}</span>
            <span className="font-mono text-xs text-ink-500 tabular-nums">
              {selected.width} × {selected.height} px · {formatBytes(selected.file.size)}
            </span>
          </p>
          {locked ? (
            lockedReason && <p className="text-xs text-ink-500">{lockedReason}</p>
          ) : (
            <div className="flex items-center gap-2">
              {input}
              <label
                htmlFor={inputId}
                className="inline-flex h-8 cursor-pointer items-center rounded-sm border border-ink-900/25 px-3 text-xs font-medium text-ink-900 transition-colors duration-fast hover:border-ink-900 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-laterite-400"
              >
                Replace
              </label>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  onClear();
                }}
                className="inline-flex h-8 items-center gap-1.5 rounded-sm px-3 text-xs font-medium text-ink-600 transition-colors duration-fast hover:bg-ink-900/[0.05] hover:text-ink-900"
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
        className={`group flex aspect-[4/3] cursor-pointer flex-col items-start justify-end border p-6 transition-colors duration-base ease-out sm:aspect-[16/10] sm:p-10 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-4 peer-focus-visible:outline-laterite-400 ${
          dragging ? 'border-jade-500 bg-jade-50' : 'border-ink-900/20 bg-white hover:border-ink-900/50'
        }`}
      >
        <span
          className={`mb-auto flex h-12 w-12 items-center justify-center rounded-full border transition-colors duration-base ${
            dragging ? 'border-jade-500 text-jade-600' : 'border-ink-900/20 text-ink-700 group-hover:border-ink-900'
          }`}
        >
          <Icon name="upload" className="h-5 w-5" />
        </span>
        <span className="font-display text-display-sm font-medium text-ink-900">
          {dragging ? 'Release to add the photograph' : 'Drop a photograph of the structure'}
        </span>
        <span className="mt-2 text-sm text-ink-600">
          or <span className="font-medium text-ink-900 underline decoration-ink-900/30 underline-offset-4">choose a file</span>
        </span>
        <span id={hintId} className="mt-6 font-mono text-[0.6875rem] uppercase tracking-[0.08em] text-ink-500">
          JPEG · PNG · WebP — up to {formatBytes(MAX_UPLOAD_BYTES)}
        </span>
      </label>
      {errorLine}
    </div>
  );
};

export default UploadZone;
