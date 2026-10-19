import React, { useRef } from 'react';
import { HeroScene } from '../components/HeroScene';
import {
  ApproachSection,
  ChallengeSection,
  DescentResolution,
  EngineeringStory,
} from '../components/home/StorySections';
import { MaterialSection } from '../components/home/MaterialSection';
import { ClosingSection, ProductSection } from '../components/home/ProductSections';
import { useReveal } from '../hooks/useReveal';
import { AppRoute } from '../types';

export interface HomePageProps {
  onRouteChange: (route: AppRoute) => void;
}

/**
 * Landing narrative: the 3D descent resolves into the water, and the water
 * into the method, the materials and the workspace.
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
        <DescentResolution id="after-descent" />
        <EngineeringStory />
        <ChallengeSection />
        <ApproachSection />
        <MaterialSection />
        <ProductSection onRouteChange={onRouteChange} />
      </main>
      <ClosingSection onRouteChange={onRouteChange} />
    </div>
  );
};

export default HomePage;
