import React, { useEffect, useMemo, useState } from 'react';
import { PageContainer } from '../components/PageContainer';
import { Section } from '../components/Section';
import { Button } from '../components/Button';
import { Icon } from '../components/Icon';
import { EmptyState } from '../components/EmptyState';
import { InspectionCanvas } from '../components/InspectionCanvas';
import { DefectLegend } from '../components/DefectLegend';
import { VisualMetricsPanel } from '../components/VisualMetricsPanel';
import { ScoreCard } from '../components/ScoreCard';
import { ConservationChain } from '../components/ConservationChain';
import { RootCauseAnalysisCard } from '../components/RootCauseAnalysisCard';
import { MaterialDnaCard } from '../components/MaterialDnaCard';
import { WhyThisRecommendation } from '../components/WhyThisRecommendation';
import { RestorationRoadmap } from '../components/RestorationRoadmap';
import { ProvenanceBanner } from '../components/ProvenanceBanner';
import { OriginTag } from '../components/StatusBadge';
import { AppRoute, InspectionSession } from '../types';
import { humanize, listEngineeringMetrics, readRootCauses, resolveImageSource, visionOrigin } from '../utils/analysis';

export interface AnalysisPageProps {
  session: InspectionSession | null;
  onRouteChange: (route: AppRoute) => void;
  onLoadFixture: () => void;
}

const scrollToSection = (id: string) => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.getElementById(id)?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
};

export const AnalysisPage: React.FC<AnalysisPageProps> = ({ session, onRouteChange, onLoadFixture }) => {
  const detections = session?.result.vision.detections ?? [];
  const classKey = detections.map((d) => d.class_name).join('|');
  const [visibleClasses, setVisibleClasses] = useState<Set<string>>(() => new Set(detections.map((d) => d.class_name)));
  const [highlighted, setHighlighted] = useState<number | null>(null);

  // Reset toggles when a different result is loaded.
  useEffect(() => {
    setVisibleClasses(new Set(detections.map((d) => d.class_name)));
    setHighlighted(null);
  }, [classKey, session?.result.metadata.created_at]);

  const metrics = useMemo(() => (session ? listEngineeringMetrics(session.result) : []), [session]);
  const causes = useMemo(() => (session ? readRootCauses(session.result) : []), [session]);

  if (!session) {
    return (
      <PageContainer
        eyebrow="JalDrishti / Findings"
        title="Findings"
        subtitle="Detections, engineering scores and conservation considerations for one inspection."
        plate="well-octagon"
        treatment="panel"
        ground="dark"
      >
        <EmptyState
          title="No inspection loaded"
          description={
            <>
              <p>Run a photograph through the pipeline to see its findings here.</p>
              <p className="mt-2">
                To review the interface without the backend, you can open the development sample. It is a fixed fixture,
                clearly labelled, and is not the result of any analysis.
              </p>
            </>
          }
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
  const imageSrc = resolveImageSource(session);
  const title = result.structure.name || `Unnamed ${humanize(result.structure.type).toLowerCase()}`;

  const toggleClass = (name: string) =>
    setVisibleClasses((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });

  return (
    <PageContainer
      eyebrow="JalDrishti / Findings"
      title={title}
      subtitle={
        <>
          {humanize(result.structure.type)}
          {result.structure.region ? ` · ${result.structure.region}` : ''}
        </>
      }
      plate="well-octagon"
      treatment="panel"
      ground="dark"
      actions={
        <>
          <Button variant="secondary" onClick={() => onRouteChange('/upload')}>
            New inspection
          </Button>
          <Button onClick={() => onRouteChange('/report')} icon={<Icon name="arrowRight" className="h-4 w-4" />} className="flex-row-reverse">
            Open report
          </Button>
        </>
      }
      banner={<ProvenanceBanner session={session} />}
    >
      <ConservationChain
        result={result}
        onJump={scrollToSection}
        isFixture={session.provenance === 'fixture'}
        seeOrigin={visionOrigin(session) === 'unverified' ? 'unverified' : 'model'}
        className="mb-14"
      />

      <div className="space-y-16">
        <Section
          id="findings"
          index="01"
          title="Visual findings"
          description="Regions identified in the photograph."
          aside={<OriginTag kind={visionOrigin(session)} />}
        >
          <div className="grid gap-6 lg:grid-cols-[minmax(0,44rem)_minmax(0,1fr)] lg:items-start">
            <InspectionCanvas
              imageSrc={imageSrc}
              imageDimensions={result.vision.image_dimensions}
              detections={detections}
              visibleClasses={visibleClasses}
              highlighted={highlighted}
              onHighlight={setHighlighted}
            />
            <div className="space-y-4 text-sm leading-relaxed text-ink-700">
              <DefectLegend detections={detections} visibleClasses={visibleClasses} onToggleClass={toggleClass} />
              <p>
                {detections.length === 0
                  ? 'No regions were returned for this photograph.'
                  : `${detections.length} region${detections.length === 1 ? '' : 's'} returned. Use the toggles to isolate a class; hover a box or a table row to link them.`}
              </p>
              <p className="text-xs text-ink-500">
                Detection confidence is the model’s certainty that a region belongs to a class. It says nothing about how
                serious the defect is.
              </p>
            </div>
          </div>
          <VisualMetricsPanel
            className="mt-8"
            detections={detections}
            scaleReference={result.vision.scale_reference}
            highlighted={highlighted}
            onHighlight={setHighlighted}
          />
        </Section>

        <Section
          id="causes"
          index="02"
          title="Probable causes"
          description="Inferred by deterministic rules from the findings above. Hypotheses to check on site, not diagnoses."
          aside={<OriginTag kind={session.provenance === 'fixture' ? 'fixture' : 'rules'} />}
        >
          <RootCauseAnalysisCard causes={causes} />
        </Section>

        <Section
          id="assessment"
          index="03"
          title="Engineering assessment"
          description="Scores calculated by rule from image-space evidence. They describe what is visible, not structural safety."
          aside={<OriginTag kind={session.provenance === 'fixture' ? 'fixture' : 'rules'} />}
        >
          {metrics.length === 0 ? (
            <p className="text-sm text-ink-600">The response contained no engineering scores.</p>
          ) : (
            <div className="grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
              {metrics.map((m) => (
                <ScoreCard key={m.key} label={m.label} metric={m.metric} direction={m.direction} />
              ))}
            </div>
          )}
        </Section>

        <Section
          id="materials"
          index="04"
          title="Material compatibility"
          description="How candidate repair materials compare with the assumed original, across seven dimensions scored 0–10."
          aside={
            <>
              <OriginTag kind={session.provenance === 'fixture' ? 'fixture' : 'rules'} />
              {result.material.verification_required && <OriginTag kind="expert" />}
            </>
          }
        >
          <div className="grid gap-10 lg:grid-cols-12">
            <WhyThisRecommendation material={result.material} className="lg:col-span-4 lg:self-start" />
            <div className="grid gap-x-8 gap-y-8 md:grid-cols-2 lg:col-span-8">
              {result.material.candidate_interventions.map((c) => (
                <MaterialDnaCard key={c.intervention_material} candidate={c} />
              ))}
            </div>
          </div>
        </Section>

        <Section
          id="restoration"
          index="05"
          title="Conservation considerations"
          description="A phased starting point for planning. Every action requires review by a qualified conservation engineer before work begins."
          aside={
            <>
              <OriginTag kind={session.provenance === 'fixture' ? 'fixture' : 'rules'} />
              <OriginTag kind="expert" />
            </>
          }
        >
          <RestorationRoadmap restoration={result.restoration} />
        </Section>
      </div>
    </PageContainer>
  );
};

export default AnalysisPage;
