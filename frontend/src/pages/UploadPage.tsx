import React, { useEffect, useId, useRef, useState } from 'react';
import { PageContainer } from '../components/PageContainer';
import { UploadZone, SelectedImage } from '../components/UploadZone';
import { ROISelector } from '../components/ROISelector';
import { PipelineStages, PipelineStage, StageStatus } from '../components/PipelineStages';
import { Button } from '../components/Button';
import { Icon } from '../components/Icon';
import {
  AnalysisResultContract,
  AppRoute,
  ImageUploadResult,
  InspectionROI,
  InspectionSession,
  StructureTypology,
} from '../types';
import { ApiError, deleteInspectionImage, submitAnalysisRequest, uploadInspectionImage } from '../services/api';
import { formatBytes } from '../utils/analysis';

export interface UploadPageProps {
  onComplete: (session: InspectionSession) => void;
  onRouteChange: (route: AppRoute) => void;
}

const TYPOLOGIES: { value: StructureTypology; label: string }[] = [
  { value: 'baoli', label: 'Baoli — stepwell' },
  { value: 'bawari', label: 'Bawari — stepped reservoir' },
  { value: 'vav', label: 'Vav — Gujarati stepwell' },
  { value: 'kund', label: 'Kund — stepped tank' },
  { value: 'tank', label: 'Tank' },
  { value: 'other', label: 'Other water structure' },
];

const REGION_SUGGESTIONS = [
  'Delhi NCR',
  'Rajasthan',
  'Gujarat',
  'Haryana',
  'Uttar Pradesh',
  'Madhya Pradesh',
  'Maharashtra',
  'Karnataka',
  'Bihar',
];

interface StageState {
  status: StageStatus;
  progress?: number;
  error?: string;
  code?: number;
}

const errorText = (error: unknown) => (error instanceof Error ? error.message : 'Unexpected error.');

export const UploadPage: React.FC<UploadPageProps> = ({ onComplete, onRouteChange }) => {
  const formId = useId();
  const [selected, setSelected] = useState<SelectedImage | null>(null);
  const [structureType, setStructureType] = useState<StructureTypology>('baoli');
  const [structureName, setStructureName] = useState('');
  const [region, setRegion] = useState('');
  const [notes, setNotes] = useState('');
  const [roiEnabled, setRoiEnabled] = useState(false);
  const [roi, setRoi] = useState<InspectionROI | null>(null);

  const [storage, setStorage] = useState<StageState>({ status: 'pending' });
  const [analysis, setAnalysis] = useState<StageState>({ status: 'pending' });
  const [stored, setStored] = useState<ImageUploadResult | null>(null);
  const [result, setResult] = useState<AnalysisResultContract | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const openFindingsRef = useRef<HTMLButtonElement>(null);
  const statusRef = useRef<HTMLElement>(null);

  const busy = storage.status === 'active' || analysis.status === 'active';
  const fileLocked = busy || stored !== null;

  useEffect(() => {
    if (result) openFindingsRef.current?.focus();
  }, [result]);

  // A failure must not go unseen below the fold.
  const failed = storage.status === 'failed' || analysis.status === 'failed';
  useEffect(() => {
    if (!failed) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    statusRef.current?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'nearest' });
  }, [failed]);

  const resetPipeline = () => {
    setStorage({ status: 'pending' });
    setAnalysis({ status: 'pending' });
    setResult(null);
    setNotice(null);
  };

  const handleSelect = (image: SelectedImage) => {
    if (selected && !result) URL.revokeObjectURL(selected.previewUrl);
    setSelected(image);
    setRoi(null);
    resetPipeline();
  };

  const handleClear = () => {
    if (selected && !result) URL.revokeObjectURL(selected.previewUrl);
    setSelected(null);
    setRoi(null);
    setRoiEnabled(false);
    resetPipeline();
  };

  const runAnalysis = async (image: ImageUploadResult | null) => {
    if (!selected) return;
    setAnalysis({ status: 'active' });
    try {
      const response = await submitAnalysisRequest({
        imageFile: selected.file,
        imageId: image?.image_id,
        structureType,
        structureName: structureName.trim() || undefined,
        region: region.trim() || undefined,
        notes: notes.trim() || undefined,
        roi: roiEnabled && roi && roi.width > 0 ? roi : undefined,
      });
      setResult(response);
      setAnalysis({ status: 'done' });
    } catch (error) {
      setAnalysis({ status: 'failed', error: errorText(error) });
    }
  };

  const runStorage = async () => {
    if (!selected) return;
    setNotice(null);
    setStorage({ status: 'active', progress: 0 });
    setAnalysis({ status: 'pending' });
    try {
      const image = await uploadInspectionImage(
        selected.file,
        { structureType, structureName: structureName.trim() || undefined, notes: notes.trim() || undefined },
        (fraction) => setStorage({ status: 'active', progress: fraction }),
      );
      setStored(image);
      setStorage({ status: 'done' });
      await runAnalysis(image);
    } catch (error) {
      setStorage({
        status: 'failed',
        error: errorText(error),
        code: error instanceof ApiError ? error.statusCode : undefined,
      });
    }
  };

  const handleStart = () => {
    if (stored) {
      void runAnalysis(stored);
    } else {
      void runStorage();
    }
  };

  const handleContinueWithoutStoring = () => {
    setStorage({ status: 'skipped' });
    void runAnalysis(null);
  };

  const handleDeleteStored = async () => {
    if (!stored) return;
    setDeleting(true);
    setNotice(null);
    try {
      await deleteInspectionImage(stored.image_id);
      setStored(null);
      resetPipeline();
      setNotice('The stored image and its metadata record were deleted.');
    } catch (error) {
      setNotice(`Deletion failed: ${errorText(error)}`);
    } finally {
      setDeleting(false);
    }
  };

  const handleOpenFindings = () => {
    if (!result || !selected) return;
    onComplete({
      result,
      provenance: 'live',
      image: stored ?? undefined,
      localPreviewUrl: selected.previewUrl,
    });
  };

  const stages: PipelineStage[] = [
    {
      id: 'store',
      title: 'Store image',
      description: 'Sent to the JalDrishti API, validated, and stored in Cloudinary. Storage alone does not analyse the image.',
      status: storage.status,
      progress: storage.progress,
      activeLabel:
        storage.progress !== undefined && storage.progress >= 1 ? 'Uploaded — waiting for the server to validate and store' : 'Uploading',
      error: storage.error,
      detail:
        storage.status === 'failed' ? (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={handleStart} icon={<Icon name="refresh" className="h-3.5 w-3.5" />}>
              Retry storage
            </Button>
            <Button size="sm" variant="quiet" onClick={handleContinueWithoutStoring}>
              Continue without storing
            </Button>
          </div>
        ) : stored ? (
          <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-[0.8125rem]">
            <dt className="text-ws-faint">Image ID</dt>
            <dd className="truncate font-mono text-ws-text">{stored.image_id}</dd>
            {stored.inspection_id && (
              <>
                <dt className="text-ws-faint">Inspection ID</dt>
                <dd className="truncate font-mono text-ws-text">{stored.inspection_id}</dd>
              </>
            )}
            <dt className="text-ws-faint">Stored</dt>
            <dd className="font-mono tabular-nums text-ws-text">
              {stored.width} × {stored.height} · {stored.format} · {formatBytes(stored.bytes)}
            </dd>
          </dl>
        ) : storage.status === 'skipped' ? (
          <p className="text-[0.8125rem] text-ws-muted">This image was analysed without being stored. It will not appear in inspection history.</p>
        ) : undefined,
    },
    {
      id: 'analyse',
      title: 'Analyse',
      description: 'Vision detection, then rule-based engineering, material compatibility and restoration planning.',
      status: analysis.status,
      activeLabel: 'Waiting for the analysis service to respond',
      error: analysis.error,
      detail:
        analysis.status === 'failed' ? (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={() => void runAnalysis(stored)} icon={<Icon name="refresh" className="h-3.5 w-3.5" />}>
                Retry analysis
              </Button>
            </div>
            <p className="text-[0.8125rem] leading-relaxed text-ws-muted">
              No result was produced. To explore the interface with the labelled development sample instead,{' '}
              <button type="button" className="font-medium text-ws-text underline underline-offset-2" onClick={() => onRouteChange('/analysis')}>
                open the Findings page
              </button>
              .
            </p>
          </div>
        ) : undefined,
    },
    {
      id: 'ready',
      title: 'Results ready',
      description: 'Shown only once the API has returned a complete response.',
      status: result ? 'done' : 'pending',
      detail: result ? (
        <p className="text-[0.8125rem] text-ws-muted">
          {result.vision.detections.length === 0
            ? 'The vision service returned no detections for this image.'
            : `${result.vision.detections.length} detection${result.vision.detections.length === 1 ? '' : 's'} returned.`}
        </p>
      ) : undefined,
    },
  ];

  const startLabel = stored ? 'Analyse stored image' : 'Store and analyse';

  return (
    <PageContainer
      eyebrow="JalDrishti / Inspection"
      title="Inspect a heritage water structure."
      subtitle="Document a traditional water structure through photographs and contextual observations, creating a useful starting point for closer examination — not a diagnosis."
      plate="stepwell-reflection"
      treatment="panel"
      ground="dark"
    >
      <div className="grid gap-x-16 gap-y-12 lg:grid-cols-12">
        <section aria-labelledby={`${formId}-photo`} className="lg:col-span-7">
          <h2 id={`${formId}-photo`} className="mb-5 font-display text-[1.75rem] font-medium leading-tight text-ws-text">
            Photograph
          </h2>

          <UploadZone
            selected={selected}
            onSelect={handleSelect}
            onClear={handleClear}
            locked={fileLocked}
            lockedReason={stored ? 'Stored — delete the stored image to replace it.' : busy ? 'Locked while the pipeline runs.' : undefined}
            previewSlot={
              selected && roiEnabled ? (
                <ROISelector
                  imageSrc={selected.previewUrl}
                  naturalWidth={selected.width}
                  naturalHeight={selected.height}
                  roi={roi}
                  onChangeROI={setRoi}
                />
              ) : undefined
            }
          />

          {selected && (
            <label className="mt-6 flex cursor-pointer items-start gap-3 border-t border-[var(--ws-line-dark)] pt-5">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 accent-ws-moss"
                checked={roiEnabled}
                disabled={busy}
                onChange={(event) => {
                  setRoiEnabled(event.target.checked);
                  if (!event.target.checked) setRoi(null);
                }}
              />
              <span>
                <span className="block text-[0.9375rem] font-medium text-ws-text">Limit analysis to a region (optional)</span>
                <span className="mt-1 block text-[0.8125rem] leading-relaxed text-ws-muted">
                  Off by default — the whole photograph is analysed. If enabled, drag on the image or type pixel values.
                </span>
              </span>
            </label>
          )}
        </section>

        <div className="lg:col-span-5">
          <section aria-labelledby={`${formId}-details`}>
            <h2 id={`${formId}-details`} className="mb-5 font-display text-[1.75rem] font-medium leading-tight text-ws-text">
              About the structure
            </h2>
            <form
              id={formId}
              onSubmit={(event) => {
                event.preventDefault();
                handleStart();
              }}
            >
              <fieldset disabled={busy} className="space-y-5">
                <legend className="sr-only">Structure details</legend>
                <div>
                  <label htmlFor={`${formId}-type`} className="field-label">
                    Typology
                  </label>
                  <select
                    id={`${formId}-type`}
                    className="field"
                    value={structureType}
                    onChange={(event) => setStructureType(event.target.value as StructureTypology)}
                  >
                    {TYPOLOGIES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label htmlFor={`${formId}-name`} className="field-label">
                      Name <span className="text-ws-faint">(optional)</span>
                    </label>
                    <input
                      id={`${formId}-name`}
                      className="field"
                      value={structureName}
                      placeholder="e.g. Agrasen ki Baoli"
                      onChange={(event) => setStructureName(event.target.value)}
                    />
                  </div>
                  <div>
                    <label htmlFor={`${formId}-region`} className="field-label">
                      Region <span className="text-ws-faint">(optional)</span>
                    </label>
                    <input
                      id={`${formId}-region`}
                      className="field"
                      list={`${formId}-regions`}
                      value={region}
                      placeholder="e.g. Delhi NCR"
                      onChange={(event) => setRegion(event.target.value)}
                    />
                    <datalist id={`${formId}-regions`}>
                      {REGION_SUGGESTIONS.map((r) => (
                        <option key={r} value={r} />
                      ))}
                    </datalist>
                  </div>
                </div>
                <div>
                  <label htmlFor={`${formId}-notes`} className="field-label">
                    Field notes <span className="text-ws-faint">(optional)</span>
                  </label>
                  <textarea
                    id={`${formId}-notes`}
                    className="field h-28 resize-y py-2.5 leading-relaxed"
                    value={notes}
                    placeholder="Observed water level, recent repairs, access conditions…"
                    onChange={(event) => setNotes(event.target.value)}
                  />
                </div>
              </fieldset>

              <div className="mt-7 flex flex-wrap items-center gap-x-5 gap-y-3">
                <Button
                  type="submit"
                  size="lg"
                  className="min-w-[13rem]"
                  disabled={!selected || busy || result !== null || (roiEnabled && !roi)}
                  isLoading={busy}
                >
                  {busy ? 'Running…' : startLabel}
                </Button>
                {!selected && <p className="text-[0.8125rem] text-ws-muted">Add a photograph to begin.</p>}
                {roiEnabled && !roi && selected && (
                  <p className="text-[0.8125rem] text-ws-muted">Draw a region on the image, or switch the region option off.</p>
                )}
              </div>
            </form>
          </section>
        </div>
      </div>

      <section ref={statusRef} aria-labelledby={`${formId}-status`} className="mt-14 scroll-mb-8">
        <div className="ws-terrace mb-7 text-ws-sandstone/80" aria-hidden="true">
          <span />
        </div>
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <h2 id={`${formId}-status`} className="font-display text-[1.75rem] font-medium leading-tight text-ws-text">
              Status
            </h2>
            <p className="text-[0.8125rem] text-ws-faint">Storing an image and analysing it are separate steps; each shows the API&rsquo;s real response.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {stored && (
              <Button
                size="sm"
                variant="danger"
                onClick={handleDeleteStored}
                isLoading={deleting}
                disabled={busy}
                icon={<Icon name="trash" className="h-3.5 w-3.5" />}
              >
                Delete stored image
              </Button>
            )}
            {result && (
              <Button ref={openFindingsRef} onClick={handleOpenFindings} size="lg">
                Open findings
                <Icon name="arrowRight" className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        <PipelineStages stages={stages} tone="dark" orientation="horizontal" />
        {notice && (
          <p role="status" className="mt-6 text-[0.8125rem] text-ws-muted">
            {notice}
          </p>
        )}
      </section>

      <section aria-labelledby={`${formId}-limits`} className="mt-20 border-t border-[var(--ws-line-dark)] pt-10">
        <h2 id={`${formId}-limits`} className="font-display text-[1.75rem] font-medium leading-tight text-ws-text">
          What the current pilot can see
        </h2>
        <dl className="mt-6 grid gap-x-12 gap-y-6 text-[0.9375rem] md:grid-cols-3">
          <div>
            <dt className="font-medium text-ws-text">Live detection</dt>
            <dd className="mt-1.5 leading-relaxed text-ws-muted">
              A pilot YOLOv8n crack model. It has not been validated on held-out, human-annotated data, so treat its boxes
              as prompts for review. Other defect classes in the contract are not produced by a trained model.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-ws-text">Image-space only</dt>
            <dd className="mt-1.5 leading-relaxed text-ws-muted">
              Measurements are in pixels of this photograph. Without a calibrated scale they are not physical dimensions.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-ws-text">Better photographs</dt>
            <dd className="mt-1.5 leading-relaxed text-ws-muted">
              Face the wall squarely, use even daylight, keep the surface sharp, and avoid strong shadow across joints.
            </dd>
          </div>
        </dl>
      </section>
    </PageContainer>
  );
};

export default UploadPage;
