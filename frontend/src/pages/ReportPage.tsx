import React, { useMemo } from 'react';
import { PageContainer } from '../components/PageContainer';
import { Section } from '../components/Section';
import { Button } from '../components/Button';
import { Icon } from '../components/Icon';
import { EmptyState } from '../components/EmptyState';
import { InspectionCanvas } from '../components/InspectionCanvas';
import { VisualMetricsPanel } from '../components/VisualMetricsPanel';
import { ScoreCard } from '../components/ScoreCard';
import { RootCauseAnalysisCard } from '../components/RootCauseAnalysisCard';
import { MaterialDnaCard } from '../components/MaterialDnaCard';
import { WhyThisRecommendation } from '../components/WhyThisRecommendation';
import { RestorationRoadmap } from '../components/RestorationRoadmap';
import { ProvenanceBanner } from '../components/ProvenanceBanner';
import { OriginTag } from '../components/StatusBadge';
import { AppRoute, InspectionSession } from '../types';
import { formatTimestamp, humanize, listEngineeringMetrics, readRootCauses, resolveImageSource, visionOrigin } from '../utils/analysis';

export interface ReportPageProps {
  session: InspectionSession | null;
  onRouteChange: (route: AppRoute) => void;
  onLoadFixture: () => void;
}

const noop = () => undefined;

/** Printable conservation dossier for the current session. */
export const ReportPage: React.FC<ReportPageProps> = ({ session, onRouteChange, onLoadFixture }) => {
  const metrics = useMemo(() => (session ? listEngineeringMetrics(session.result) : []), [session]);
  const causes = useMemo(() => (session ? readRootCauses(session.result) : []), [session]);
  const allClasses = useMemo(
    () => new Set(session?.result.vision.detections.map((d) => d.class_name) ?? []),
    [session],
  );

  if (!session) {
    return (
      <PageContainer
        eyebrow="JalDrishti / Report"
        title="Conservation dossier"
        subtitle="A printable record of one inspection."
        plate="tank-stepped"
        treatment="panel"
        ground="dark"
      >
        <EmptyState
          title="Nothing to report yet"
          description="A dossier is assembled from a completed inspection. Run one first, or open the labelled development sample to preview the layout."
          actions={
            <>
              <Button onClick={() => onRouteChange('/upload')} icon={<Icon name="upload" className="h-4 w-4" />}>
                Start an inspection
              </Button>
              <Button variant="secondary" onClick={onLoadFixture}>
                View development sample
              </Button>
            </>
          }
        />
      </PageContainer>
    );
  }

  const { result } = session;
  const isFixture = session.provenance === 'fixture';
  const rulesOrigin = isFixture ? 'fixture' : 'rules';
  const disclaimer =
    'This dossier summarises photographic evidence and rule-based assessments. It does not certify structural safety and does not replace on-site investigation by qualified conservation engineers. Material recommendations depend on laboratory confirmation of the original material.';

  return (
    <div className="relative">
      {isFixture && (
        <div
          aria-hidden="true"
          className="pointer-events-none fixed inset-0 z-[1] flex items-center justify-center overflow-hidden print:absolute"
        >
          <span className="-rotate-[24deg] whitespace-nowrap font-display text-[12vw] font-medium uppercase tracking-[0.1em] text-ochre-500/[0.07] print:text-ochre-500/15">
            Development sample
          </span>
        </div>
      )}

      <PageContainer
        eyebrow="JalDrishti / Report"
        title="Conservation dossier"
        subtitle={
          <>
            {result.structure.name || `Unnamed ${humanize(result.structure.type).toLowerCase()}`} ·{' '}
            {humanize(result.structure.type)}
            {result.structure.region ? ` · ${result.structure.region}` : ''}
          </>
        }
        actions={
          <>
            <Button variant="secondary" onClick={() => onRouteChange('/analysis')} icon={<Icon name="arrowLeft" className="h-4 w-4" />}>
              Findings
            </Button>
            <Button onClick={() => window.print()} icon={<Icon name="printer" className="h-4 w-4" />}>
              Print / save as PDF
            </Button>
          </>
        }
        banner={<ProvenanceBanner session={session} />}
        plate="tank-stepped"
        treatment="panel"
        ground="dark"
        className="relative z-[2]"
      >
        <div className="space-y-14 print:space-y-10">
          <Section index="01" title="Record" rule={false}>
            <dl className="grid gap-x-10 gap-y-4 text-sm sm:grid-cols-2 lg:grid-cols-3">
              {[
                ['Structure', result.structure.name || 'Not named'],
                ['Typology', humanize(result.structure.type)],
                ['Region', result.structure.region || 'Not stated'],
                ['Generated', formatTimestamp(result.metadata.created_at)],
                ['Pipeline status', humanize(result.metadata.pipeline_status)],
                ['Vision model', result.vision.processing_metadata?.model_version ?? 'Not reported'],
                ['Image ID', session.image?.image_id ?? 'Not stored'],
                ['Inspection ID', session.image?.inspection_id ?? '—'],
                ['Source', isFixture ? 'Development fixture (not an inspection)' : 'JalDrishti API response'],
              ].map(([label, value]) => (
                <div key={label} className="border-t border-ink-900/10 pt-2">
                  <dt className="text-xs text-ink-500">{label}</dt>
                  <dd className="mt-0.5 break-words font-medium text-ink-900">{value}</dd>
                </div>
              ))}
            </dl>
          </Section>

          <Section index="02" title="Visual findings" aside={<OriginTag kind={visionOrigin(session)} />}>
            <div className="grid gap-8 lg:grid-cols-12 print:block">
              <div className="min-w-0 lg:col-span-6 print:mb-6 print:max-w-[60%]">
                <InspectionCanvas
                  imageSrc={resolveImageSource(session)}
                  imageDimensions={result.vision.image_dimensions}
                  detections={result.vision.detections}
                  visibleClasses={allClasses}
                  highlighted={null}
                  onHighlight={noop}
                />
              </div>
              <div className="min-w-0 lg:col-span-6">
                <VisualMetricsPanel detections={result.vision.detections} scaleReference={result.vision.scale_reference} />
              </div>
            </div>
          </Section>

          <Section index="03" title="Engineering assessment" aside={<OriginTag kind={rulesOrigin} />}>
            {metrics.length === 0 ? (
              <p className="text-sm text-ink-600">The response contained no engineering scores.</p>
            ) : (
              <div className="grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 print:grid-cols-2">
                {metrics.map((m) => (
                  <ScoreCard key={m.key} label={m.label} metric={m.metric} direction={m.direction} className="break-inside-avoid" />
                ))}
              </div>
            )}
          </Section>

          <Section index="04" title="Probable causes" aside={<OriginTag kind={rulesOrigin} />}>
            <RootCauseAnalysisCard causes={causes} />
          </Section>

          <Section
            index="05"
            title="Material compatibility"
            aside={
              <>
                <OriginTag kind={rulesOrigin} />
                {result.material.verification_required && <OriginTag kind="expert" />}
              </>
            }
          >
            <WhyThisRecommendation material={result.material} className="mb-8 break-inside-avoid" />
            <div className="grid gap-x-8 gap-y-8 md:grid-cols-2">
              {result.material.candidate_interventions.map((c) => (
                <MaterialDnaCard key={c.intervention_material} candidate={c} />
              ))}
            </div>
          </Section>

          <Section
            index="06"
            title="Conservation considerations"
            aside={
              <>
                <OriginTag kind={rulesOrigin} />
                <OriginTag kind="expert" />
              </>
            }
          >
            <RestorationRoadmap restoration={result.restoration} />
          </Section>

          <section className="rule break-inside-avoid pt-6">
            <h2 className="eyebrow text-ink-500">Limitations</h2>
            <p className="mt-3 max-w-prose text-sm leading-relaxed text-ink-700">{disclaimer}</p>
            {isFixture && (
              <p className="mt-3 max-w-prose text-sm font-semibold text-ochre-700">
                This document was generated from the development sample and describes no real structure.
              </p>
            )}
            <p className="mt-6 font-mono text-[0.6875rem] text-ink-500">JalDrishti · Team NeuralX</p>
          </section>
        </div>
      </PageContainer>
    </div>
  );
};

export default ReportPage;
