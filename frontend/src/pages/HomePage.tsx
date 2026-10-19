import React, { useRef } from 'react';
import { HeroScene } from '../components/HeroScene';
import {
  ApproachSection,
  ContextsSection,
  DiversitySection,
  DocumentationSection,
  ReviveSection,
  UnderstandSection,
} from '../components/home/StorySections';
import { MaterialSection } from '../components/home/MaterialSection';
import { ClosingSection, SeeSection } from '../components/home/ProductSections';
import { useReveal } from '../hooks/useReveal';
import { AppRoute } from '../types';

export interface HomePageProps {
  onRouteChange: (route: AppRoute) => void;
}

/**
 * Landing narrative: the brand over one illustrative stepwell, the descent to its
 * water, then the wider story — the diversity of India's water heritage, why
 * documentation matters, SEE → UNDERSTAND → ASSESS → REVIVE, and the difference
 * between the mission and what is built today.
 */
export const HomePage: React.FC<HomePageProps> = ({ onRouteChange }) => {
  const rootRef = useRef<HTMLDivElement>(null);
  useReveal(rootRef);

  return (
    <div ref={rootRef} className="bg-ink-950">
      <a href="#after-descent" className="sr-only-focusable btn-light fixed left-4 top-4 z-toast">
        Skip to content
      </a>
      <main>
        <HeroScene onRouteChange={onRouteChange} nextSectionId="after-descent" />
        <DiversitySection id="after-descent" />
        <DocumentationSection />
        <SeeSection onRouteChange={onRouteChange} />
        <UnderstandSection onRouteChange={onRouteChange} />
        <MaterialSection />
        <ReviveSection />
        <ContextsSection />
        <ApproachSection />
      </main>
      <ClosingSection onRouteChange={onRouteChange} />
    </div>
  );
};

export default HomePage;
