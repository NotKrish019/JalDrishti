import React, { useEffect, useId, useRef, useState } from 'react';
import { PageContainer } from '../components/PageContainer';
import { UploadZone, SelectedImage } from '../components/UploadZone';
import { ROISelector } from '../components/ROISelector';
import { PipelineStages, PipelineStage, StageStatus } from '../components/PipelineStages';
import { Button } from '../components/Button';
import { Icon } from '../components/Icon';
import { Section } from '../components/Section';
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

  const busy = storage.status === 'active' || analysis.status === 'active';
  const fileLocked = busy || stored !== null;

  useEffect(() => {
    if (result) openFindingsRef.current?.focus();
  }, [result]);

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
          <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-xs">
            <dt className="text-ink-500">Image ID</dt>
            <dd className="truncate font-mono text-ink-900">{stored.image_id}</dd>
            {stored.inspection_id && (
              <>
                <dt className="text-ink-500">Inspection ID</dt>
                <dd className="truncate font-mono text-ink-900">{stored.inspection_id}</dd>
              </>
            )}
            <dt className="text-ink-500">Stored</dt>
            <dd className="font-mono text-ink-900 tabular-nums">
              {stored.width} × {stored.height} · {stored.format} · {formatBytes(stored.bytes)}
            </dd>
          </dl>
        ) : storage.status === 'skipped' ? (
          <p className="text-xs text-ink-600">This image was analysed without being stored. It will not appear in inspection history.</p>
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
            <p className="text-xs leading-relaxed text-ink-600">
              No result was produced. To explore the interface with the labelled development sample instead,{' '}
              <button type="button" className="font-medium text-ink-900 underline underline-offset-2" onClick={() => onRouteChange('/analysis')}>
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
        <p className="text-xs text-ink-600">
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
      eyebrow="01 — Inspect"
      title="New inspection"
      subtitle="Add a photograph of the structure, describe what it is, and run it through the pipeline. Every stage below reflects a real response from the API."
    >
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-12">
        <div className="lg:col-span-7">
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
            <div className="mt-6 border-t border-ink-900/10 pt-5">
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 accent-jade-600"
                  checked={roiEnabled}
                  disabled={busy}
                  onChange={(event) => {
                    setRoiEnabled(event.target.checked);
                    if (!event.target.checked) setRoi(null);
                  }}
                />
                <span>
                  <span className="block text-sm font-medium text-ink-900">Limit analysis to a region (optional)</span>
                  <span className="mt-0.5 block text-xs leading-relaxed text-ink-600">
                    Off by default — the whole photograph is analysed. If enabled, drag on the image or type pixel values.
                  </span>
                </span>
              </label>
            </div>
          )}
        </div>

        <div className="lg:col-span-5">
          <form
            id={formId}
            onSubmit={(event) => {
              event.preventDefault();
              handleStart();
            }}
            className="space-y-5"
          >
            <fieldset disabled={busy} className="space-y-5">
              <legend className="eyebrow mb-1 text-ink-500">Structure</legend>
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
                    Name <span className="font-normal text-ink-500">(optional)</span>
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
                    Region <span className="font-normal text-ink-500">(optional)</span>
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
                  Field notes <span className="font-normal text-ink-500">(optional)</span>
                </label>
                <textarea
                  id={`${formId}-notes`}
                  className="field h-24 resize-y py-2.5 leading-relaxed"
                  value={notes}
                  placeholder="Observed water level, recent repairs, access conditions…"
                  onChange={(event) => setNotes(event.target.value)}
                />
              </div>
            </fieldset>

            <Button
              type="submit"
              size="lg"
              className="w-full"
              disabled={!selected || busy || result !== null || (roiEnabled && !roi)}
              isLoading={busy}
            >
              {busy ? 'Running…' : startLabel}
            </Button>
            {!selected && <p className="text-xs text-ink-500">Add a photograph to begin.</p>}
            {roiEnabled && !roi && selected && (
              <p className="text-xs text-ink-500">Draw a region on the image, or switch the region option off.</p>
            )}
          </form>

          <div className="mt-8 border-t border-ink-900/10 pt-6">
            <PipelineStages stages={stages} />
          </div>

          {result && (
            <div className="mt-6">
              <Button ref={openFindingsRef} onClick={handleOpenFindings} size="lg" className="w-full">
                Open findings
                <Icon name="arrowRight" className="h-4 w-4" />
              </Button>
            </div>
          )}

          {(stored || notice) && (
            <div className="mt-6 space-y-3 border-t border-ink-900/10 pt-5">
              {notice && (
                <p role="status" className="text-xs text-ink-700">
                  {notice}
                </p>
              )}
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
            </div>
          )}
        </div>
      </div>

      <Section
        index="A"
        title="What the current pilot can see"
        description="So that results are read for what they are."
        className="mt-20"
      >
        <dl className="grid gap-x-10 gap-y-6 text-sm md:grid-cols-3">
          <div>
            <dt className="font-medium text-ink-900">Live detection</dt>
            <dd className="mt-1 leading-relaxed text-ink-600">
              A pilot YOLOv8n model trained for surface cracks. Other defect classes in the contract are not yet produced by a
              trained model.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-ink-900">Image-space only</dt>
            <dd className="mt-1 leading-relaxed text-ink-600">
              Measurements are in pixels of this photograph. Without a calibrated scale they are not physical dimensions.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-ink-900">Better photographs</dt>
            <dd className="mt-1 leading-relaxed text-ink-600">
              Face the wall squarely, use even daylight, keep the surface sharp, and avoid strong shadow across joints.
            </dd>
          </div>
        </dl>
      </Section>
    </PageContainer>
  );
};

export default UploadPage;
