import React from 'react';
import { SectionIndex } from './SectionIndex';
import { JalDrishtiLogo } from '../JalDrishtiLogo';
import type { AppRoute } from '../../types';

const WORKFLOW = [
  { step: 'Upload', body: 'Add a photograph of the structure, with its typology and location.' },
  { step: 'Store', body: 'The image is validated and stored through the JalDrishti backend on Cloudinary.' },
  { step: 'Analyse', body: 'Vision, engineering rules and the knowledge base run on the stored image.' },
  { step: 'Review', body: 'Findings over the image, indicators with their limits, and material guidance.' },
  { step: 'Dossier', body: 'A printable record of the inspection, flagged for expert verification.' },
];

/** Schematic of the findings workspace: a drawing, not a screenshot, and carries no data. */
const WorkspaceSchematic: React.FC = () => (
  <svg viewBox="0 0 560 360" className="h-auto w-full" role="img" aria-label="Schematic of the findings workspace: an inspection image with outlined regions beside a list of findings.">
    <rect x="0.5" y="0.5" width="559" height="359" fill="none" stroke="currentColor" strokeOpacity="0.25" />
    <rect x="0.5" y="0.5" width="559" height="34" fill="currentColor" fillOpacity="0.05" />
    <circle cx="20" cy="18" r="5" fill="currentColor" fillOpacity="0.35" />
    <rect x="34" y="14" width="80" height="8" fill="currentColor" fillOpacity="0.25" />
    {/* Image pane: coursed masonry */}
    <g transform="translate(20 52)">
      <rect width="330" height="288" fill="currentColor" fillOpacity="0.06" />
      {Array.from({ length: 9 }, (_, r) => (
        <g key={r}>
          <line x1="0" y1={r * 32} x2="330" y2={r * 32} stroke="currentColor" strokeOpacity="0.18" />
          {Array.from({ length: 6 }, (_, c) => (
            <line
              key={c}
              x1={((c * 60 + (r % 2) * 30) % 330) + 10}
              y1={r * 32}
              x2={((c * 60 + (r % 2) * 30) % 330) + 10}
              y2={r * 32 + 32}
              stroke="currentColor"
              strokeOpacity="0.14"
            />
          ))}
        </g>
      ))}
      <path d="M120 70 l14 22 l-6 18 l18 30 l-4 24 l16 26" fill="none" stroke="#C0714F" strokeWidth="2" />
      <rect x="104" y="60" width="72" height="150" fill="none" stroke="#C0714F" strokeWidth="1.5" strokeDasharray="5 4" />
      <rect x="220" y="20" width="90" height="60" fill="none" stroke="#7FA393" strokeWidth="1.5" strokeDasharray="5 4" />
    </g>
    {/* Findings list */}
    <g transform="translate(370 52)">
      {[0, 1, 2, 3].map((i) => (
        <g key={i} transform={`translate(0 ${i * 58})`}>
          <rect width="170" height="48" fill="none" stroke="currentColor" strokeOpacity="0.2" />
          <rect x="10" y="12" width="8" height="8" fill={i === 0 ? '#C0714F' : i === 1 ? '#7FA393' : 'currentColor'} fillOpacity={i > 1 ? 0.3 : 1} />
          <rect x="26" y="12" width={70 - i * 8} height="7" fill="currentColor" fillOpacity="0.4" />
          <rect x="26" y="28" width="120" height="5" fill="currentColor" fillOpacity="0.15" />
        </g>
      ))}
      <rect y="244" width="170" height="44" fill="currentColor" fillOpacity="0.9" />
      <rect x="44" y="263" width="82" height="7" fill="#F7F2E9" fillOpacity="0.85" />
    </g>
  </svg>
);

export const ProductSection: React.FC<{ onRouteChange: (route: AppRoute) => void }> = ({ onRouteChange }) => (
  <section aria-labelledby="product-title" className="gutter bg-jade-800 py-28 text-stone-50 sm:py-36">
    <div className="mx-auto grid max-w-wide grid-cols-1 gap-16 lg:grid-cols-12 lg:gap-10">
      <div className="lg:col-span-5">
        <SectionIndex number="06" label="The inspection workspace" tone="light" />
        <h2 id="product-title" data-reveal="mask" className="mt-10 font-display text-display-md font-medium">
          From a photograph to a conservation dossier.
        </h2>
        <ol className="mt-12 border-t border-stone-50/15">
          {WORKFLOW.map((w, i) => (
            <li
              key={w.step}
              data-reveal
              style={{ '--reveal-delay': `${i * 70}ms` } as React.CSSProperties}
              className="grid grid-cols-[2.5rem_6rem_1fr] items-baseline gap-x-3 border-b border-stone-50/15 py-4 text-sm"
            >
              <span className="eyebrow text-jade-200">{String(i + 1).padStart(2, '0')}</span>
              <span className="font-medium text-stone-50">{w.step}</span>
              <span className="leading-relaxed text-stone-300">{w.body}</span>
            </li>
          ))}
        </ol>
        <div data-reveal className="mt-10 flex flex-wrap gap-3">
          <a
            href="/upload"
            onClick={(e) => {
              e.preventDefault();
              onRouteChange('/upload');
            }}
            className="btn-light"
          >
            Start an inspection
          </a>
          <a
            href="/knowledge"
            onClick={(e) => {
              e.preventDefault();
              onRouteChange('/knowledge');
            }}
            className="btn-ghost-light"
          >
            Explore the knowledge base
          </a>
        </div>
      </div>
      <figure data-reveal className="text-stone-100 lg:col-span-6 lg:col-start-7 lg:pt-20">
        <WorkspaceSchematic />
        <figcaption className="mt-4 font-mono text-[11px] tracking-wide text-stone-300">
          SCHEMATIC · Findings are labelled as model output, rule-based results, or items needing expert verification.
        </figcaption>
      </figure>
    </div>
  </section>
);

export const ClosingSection: React.FC<{ onRouteChange: (route: AppRoute) => void }> = ({ onRouteChange }) => (
  <footer className="gutter bg-ink-950 pb-10 pt-28 text-stone-100 sm:pt-40">
    <div className="mx-auto max-w-wide">
      <p data-reveal className="font-deva text-2xl text-stone-400" lang="hi">
        जल ही जीवन है
      </p>
      <p data-reveal="mask" className="mt-6 max-w-[22ch] font-display text-display-lg font-medium text-stone-50">
        Preserve the original engineering wisdom. Use modern tools to help it last.
      </p>
      <div className="mt-24 grid grid-cols-1 gap-10 border-t border-stone-50/15 pt-10 md:grid-cols-12">
        <div className="md:col-span-5">
          <JalDrishtiLogo tone="light" showDevanagari />
          <p className="mt-6 max-w-[40ch] text-sm leading-relaxed text-stone-400">
            AI-assisted digital conservation for India&rsquo;s traditional water structures. JalDrishti supports — and
            does not replace — assessment by qualified conservation professionals.
          </p>
        </div>
        <nav aria-label="Footer" className="md:col-span-3 md:col-start-7">
          <p className="eyebrow text-stone-500">Product</p>
          <ul className="mt-4 space-y-2 text-sm">
            {(
              [
                ['/upload', 'Start an inspection'],
                ['/analysis', 'Findings'],
                ['/knowledge', 'Knowledge base'],
                ['/report', 'Dossier'],
              ] as [AppRoute, string][]
            ).map(([route, label]) => (
              <li key={route}>
                <a
                  href={route}
                  onClick={(e) => {
                    e.preventDefault();
                    onRouteChange(route);
                  }}
                  className="link-underline text-stone-200 hover:text-stone-50"
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="md:col-span-3">
          <p className="eyebrow text-stone-500">Team</p>
          <p className="mt-4 text-sm text-stone-200">NeuralX</p>
          <p className="mt-1 text-sm text-stone-400">Vision · Engineering &amp; IKS · Backend · Frontend</p>
        </div>
      </div>
      <p className="mt-16 font-mono text-[11px] tracking-wide text-stone-500">
        The stepwell in the opening sequence is an illustrative procedural model, not a survey of a specific site.
      </p>
    </div>
  </footer>
);
