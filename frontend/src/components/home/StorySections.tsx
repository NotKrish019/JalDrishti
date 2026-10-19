import React from 'react';
import { SectionIndex } from './SectionIndex';
import { StepwellSection } from './StepwellSection';
import type { AppRoute } from '../../types';

type Navigate = (route: AppRoute) => void;

const routeLink = (onRouteChange: Navigate, route: AppRoute) => ({
  href: route,
  onClick: (e: React.MouseEvent) => {
    e.preventDefault();
    onRouteChange(route);
  },
});

/** SEE → UNDERSTAND → ASSESS → REVIVE: the order the rest of the page follows. */
export const STAGES = [
  { key: 'see', verb: 'See', deva: 'दृष्टि', line: 'Document what is visible.' },
  { key: 'understand', verb: 'Understand', deva: 'बोध', line: 'Recover the context behind it.' },
  { key: 'assess', verb: 'Assess', deva: 'आकलन', line: 'Weigh materials and interventions.' },
  { key: 'revive', verb: 'Revive', deva: 'पुनर्जीवन', line: 'Plan care that can be accounted for.' },
] as const;

/** A short checklist of points, set as a hairline-ruled list. */
export const PointList: React.FC<{ points: string[]; tone?: 'light' | 'dark'; className?: string }> = ({
  points,
  tone = 'dark',
  className = '',
}) => (
  <ul className={`border-t ${tone === 'dark' ? 'border-ink-900/15' : 'border-stone-50/15'} ${className}`}>
    {points.map((p, i) => (
      <li
        key={p}
        data-reveal
        style={{ '--reveal-delay': `${i * 70}ms` } as React.CSSProperties}
        className={`grid grid-cols-[2rem_1fr] gap-x-3 border-b py-3.5 text-[0.9375rem] leading-relaxed ${
          tone === 'dark' ? 'border-ink-900/15 text-ink-800' : 'border-stone-50/15 text-stone-200'
        }`}
      >
        <span className={`eyebrow pt-[0.4rem] ${tone === 'dark' ? 'text-laterite-500' : 'text-jade-200'}`}>
          {String(i + 1).padStart(2, '0')}
        </span>
        <span>{p}</span>
      </li>
    ))}
  </ul>
);

/**
 * Annotated detail of coursed masonry: the kinds of visible signs a site record
 * starts from. A drawing, not a photograph of a particular structure.
 */
const MasonryDetail: React.FC = () => {
  const rows = 7;
  const rowH = 46;
  const w = 520;
  const blocks: { x: number; y: number; bw: number }[] = [];
  let seed = 7;
  const rand = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
  for (let r = 0; r < rows; r += 1) {
    let x = r % 2 ? -40 : -10;
    while (x < w) {
      const bw = 70 + rand() * 60;
      blocks.push({ x, y: r * rowH, bw });
      x += bw;
    }
  }
  const label = (x1: number, y1: number, x2: number, y2: number, text: string, anchor: 'start' | 'end') => (
    <g>
      <path d={`M${x1} ${y1} L${x2} ${y2}`} stroke="rgba(239,230,214,0.55)" strokeWidth="1" fill="none" />
      <circle cx={x1} cy={y1} r="3" fill="#EFE6D6" />
      <text
        x={x2 + (anchor === 'start' ? 8 : -8)}
        y={y2 + 4}
        textAnchor={anchor}
        fontFamily="IBM Plex Mono, monospace"
        fontSize="11.5"
        letterSpacing="0.06em"
        fill="#EFE6D6"
      >
        {text.toUpperCase()}
      </text>
    </g>
  );
  return (
    <svg
      viewBox="-150 -30 820 390"
      className="h-auto w-full"
      role="img"
      aria-label="Annotated drawing of coursed stone masonry showing an open joint, a crack across a block, plant growth in a joint, an earlier cement patch and damp staining near the base."
    >
      <defs>
        <clipPath id="md-clip">
          <rect x="0" y="0" width={w} height={rows * rowH} />
        </clipPath>
        <linearGradient id="md-damp" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0.55" stopColor="#2a3a33" stopOpacity="0" />
          <stop offset="1" stopColor="#2a3a33" stopOpacity="0.55" />
        </linearGradient>
      </defs>
      <g clipPath="url(#md-clip)">
        <rect x="0" y="0" width={w} height={rows * rowH} fill="#5b4a39" />
        {blocks.map((b, i) => (
          <rect
            key={i}
            x={b.x + 3}
            y={b.y + 3}
            width={b.bw - 6}
            height={rowH - 6}
            fill={['#b8956a', '#a98760', '#c2a27a', '#9f7f5a'][i % 4]}
            opacity={0.92}
          />
        ))}
        {/* eroded joint */}
        <rect x="150" y={2 * rowH - 4} width="120" height="8" fill="#2c2219" />
        {/* earlier cementitious patch */}
        <path d="M330 150 l70 -6 l14 40 l-18 34 l-62 4 l-12 -38 z" fill="#8f918c" opacity="0.95" />
        {/* crack */}
        <path
          d="M96 196 l10 14 l-6 12 l14 18 l-4 14 l12 22 l-2 20"
          stroke="#1f1812"
          strokeWidth="2.4"
          fill="none"
          strokeLinejoin="round"
        />
        {/* vegetation in a joint */}
        <g fill="#6f7d4c">
          <ellipse cx="452" cy="88" rx="16" ry="6" transform="rotate(-30 452 88)" />
          <ellipse cx="470" cy="80" rx="14" ry="5" transform="rotate(20 470 80)" />
          <ellipse cx="462" cy="72" rx="12" ry="4.5" transform="rotate(-70 462 72)" />
          <ellipse cx="478" cy="94" rx="12" ry="4.5" transform="rotate(40 478 94)" />
        </g>
        <rect x="0" y="0" width={w} height={rows * rowH} fill="url(#md-damp)" />
      </g>
      <rect x="0" y="0" width={w} height={rows * rowH} fill="none" stroke="rgba(239,230,214,0.3)" />
      {label(200, 2 * rowH, -10, 40, 'Open joint', 'end')}
      {label(108, 250, -10, 250, 'Crack', 'end')}
      {label(462, 82, 545, 30, 'Plant growth', 'start')}
      {label(380, 170, 545, 170, 'Earlier repair', 'start')}
      {label(420, 300, 545, 300, 'Damp staining', 'start')}
    </svg>
  );
};

/** Schematic sections and plans, one per form. Drawings, not surveys; not to scale. */
const TypologyDrawing: React.FC<{ kind: 'stepwell' | 'kund' | 'tank' | 'temple' | 'pond'; className?: string }> = ({
  kind,
  className = '',
}) => {
  const water = '#4F8070';
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.4, strokeLinejoin: 'round' as const };
  return (
    <svg viewBox="0 0 200 110" className={className} aria-hidden="true">
      <path d="M4 30 H196" stroke="currentColor" strokeOpacity="0.3" strokeDasharray="2 4" />
      {kind === 'stepwell' && (
        <g>
          <path {...common} d="M20 30 H44 V42 H56 V54 H66 V66 H74 V78 H82 V100 H118 V78 H126 V66 H134 V54 H144 V42 H156 V30 H180" />
          <rect x="83" y="88" width="34" height="11" fill={water} />
          <path d="M100 30 V22 M94 22 H106" stroke="currentColor" strokeOpacity="0.5" />
        </g>
      )}
      {kind === 'kund' && (
        <g>
          <path d="M10 30 H44 M156 30 H190" stroke="currentColor" strokeWidth="3" strokeOpacity="0.5" />
          <path {...common} d="M44 30 L52 30 L52 38 L60 38 L60 46 L68 46 L68 54 L76 54 L76 62 L84 62 L84 70 L116 70 L116 62 L124 62 L124 54 L132 54 L132 46 L140 46 L140 38 L148 38 L148 30 L156 30" />
          <path d="M77 62 H123 V69 H77 Z" fill={water} />
        </g>
      )}
      {kind === 'tank' && (
        <g>
          <path {...common} d="M6 30 C24 30 30 22 40 22 C50 22 52 34 62 40 C90 52 120 52 150 42 C160 36 164 22 174 22 C184 22 188 30 196 30" />
          <path d="M60 39 C90 50 120 50 152 41 Z" fill={water} />
          <path d="M60 39 H152" stroke={water} />
          <path d="M168 22 v-6 h10 v6" stroke="currentColor" strokeOpacity="0.6" fill="none" />
        </g>
      )}
      {kind === 'temple' && (
        <g transform="translate(100 66)">
          {[38, 30, 22].map((r) => (
            <rect key={r} x={-r * 1.5} y={-r} width={r * 3} height={r * 2} {...common} strokeOpacity={r === 38 ? 1 : 0.55} />
          ))}
          <rect x="-27" y="-18" width="54" height="36" fill={water} opacity="0.85" />
          <rect x="-7" y="-7" width="14" height="14" fill="currentColor" fillOpacity="0.8" />
          <path d="M0 -38 V-46 M0 38 V44" stroke="currentColor" strokeOpacity="0.5" />
        </g>
      )}
      {kind === 'pond' && (
        <g>
          <path {...common} d="M6 30 C40 30 70 34 92 44 C104 50 112 50 120 44 C132 30 140 14 150 14 C160 14 164 30 196 30" />
          <path d="M40 31 C66 33 84 38 96 45 C104 49 112 49 120 44 L126 35 Z" fill={water} opacity="0.9" />
          <path d="M140 18 C144 10 156 10 160 18" stroke="currentColor" strokeOpacity="0.4" fill="none" />
        </g>
      )}
    </svg>
  );
};

const FORMS = [
  {
    kind: 'stepwell' as const,
    name: 'Stepwells',
    terms: 'Baoli · Bawari · Vav',
    body: 'Stepped descents to groundwater, with landings, retaining walls and, in many cases, galleries and a well shaft. The form shown in the opening is one illustrative example.',
    recorded: true,
  },
  {
    kind: 'kund' as const,
    name: 'Kunds',
    terms: 'Kund · Kunda · Kundi',
    body: 'Stepped reservoirs that gather rainwater, often an inverted stepped pyramid with a paved catchment around the rim.',
    recorded: true,
  },
  {
    kind: 'tank' as const,
    name: 'Historic tanks and reservoirs',
    terms: 'Talab · Sagar · Eri',
    body: 'Embanked bodies of water that hold seasonal runoff, from village tanks to larger reservoirs with inlets, sluices and ghats.',
    recorded: false,
  },
  {
    kind: 'temple' as const,
    name: 'Temple tanks',
    terms: 'Kalyani · Pushkarini',
    body: 'Tanks within or beside temple complexes, frequently stepped on every side and bound up with ritual and civic life.',
    recorded: false,
  },
  {
    kind: 'pond' as const,
    name: 'Ponds and regional systems',
    terms: 'Johad · Pond · local terms',
    body: 'Earthen embankments, village ponds and other regional ways of catching, holding and sharing water, each shaped by local terrain and practice.',
    recorded: false,
  },
];

const RecordTag: React.FC<{ recorded: boolean }> = ({ recorded }) => (
  <span className={`eyebrow inline-flex items-center gap-2 ${recorded ? 'text-jade-200' : 'text-stone-400'}`}>
    <span
      aria-hidden="true"
      className={`h-1.5 w-1.5 rounded-full ${recorded ? 'bg-jade-300' : 'border border-stone-400 bg-transparent'}`}
    />
    {recorded ? 'Knowledge records today' : 'Within the intended scope'}
  </span>
);

/** S2 — A diverse water heritage. The descent's water veil resolves into this section. */
export const DiversitySection: React.FC<{ id: string }> = ({ id }) => {
  const [featured, ...rest] = FORMS;
  return (
    <section
      id={id}
      tabIndex={-1}
      aria-labelledby={`${id}-title`}
      className="gutter relative bg-jade-900 pb-28 pt-24 text-stone-50 outline-none sm:pb-36 sm:pt-32"
    >
      <div className="mx-auto max-w-wide">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <SectionIndex label="A diverse water heritage" tone="light" />
          </div>
          <div className="lg:col-span-8">
            <h2 id={`${id}-title`} data-reveal="mask" className="max-w-[18ch] font-display text-display-lg font-medium">
              One heritage. Many forms. Distinct local knowledge.
            </h2>
            <p data-reveal className="mt-8 max-w-[42rem] text-[1.0625rem] leading-relaxed text-stone-200">
              Across India, traditional water structures take many forms. Stepwells, baolis, kunds, tanks, ponds, and
              other regional systems respond to different landscapes, communities, materials, and relationships with
              water. Understanding them requires attention to their individual context.
            </p>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 gap-px bg-stone-50/15 lg:grid-cols-12">
          <article data-reveal className="bg-jade-900 py-10 lg:col-span-5 lg:py-12 lg:pr-12">
            <TypologyDrawing kind={featured.kind} className="h-auto w-full max-w-[28rem] text-stone-100" />
            <p className="eyebrow mt-8 text-stone-400">{featured.terms}</p>
            <h3 className="mt-3 font-display text-display-md font-medium">{featured.name}</h3>
            <p className="mt-4 max-w-[34rem] text-[0.9375rem] leading-relaxed text-stone-300">{featured.body}</p>
            <div className="mt-6">
              <RecordTag recorded={featured.recorded} />
            </div>
          </article>
          <div className="grid grid-cols-1 gap-px bg-stone-50/15 sm:grid-cols-2 lg:col-span-7">
            {rest.map((f, i) => (
              <article
                key={f.kind}
                data-reveal
                style={{ '--reveal-delay': `${i * 80}ms` } as React.CSSProperties}
                className="bg-jade-900 py-8 sm:px-8 lg:py-10"
              >
                <TypologyDrawing kind={f.kind} className="h-auto w-full max-w-[15rem] text-stone-200" />
                <p className="eyebrow mt-6 text-stone-400">{f.terms}</p>
                <h3 className="mt-2 font-display text-2xl font-medium leading-tight">{f.name}</h3>
                <p className="mt-3 text-sm leading-relaxed text-stone-300">{f.body}</p>
                <div className="mt-5">
                  <RecordTag recorded={f.recorded} />
                </div>
              </article>
            ))}
          </div>
        </div>
        <p className="mt-6 max-w-[52rem] font-mono text-[11px] leading-relaxed tracking-wide text-stone-400">
          SCHEMATIC SECTIONS AND PLANS, NOT TO SCALE. Regional names overlap and vary; these are examples, not a
          catalogue. &ldquo;Knowledge records today&rdquo; marks the typologies in JalDrishti&rsquo;s current knowledge
          base (baoli, bawari, kund, vav).
        </p>
      </div>
    </section>
  );
};

/** S3 — Why documentation matters, and the method that follows. */
export const DocumentationSection: React.FC = () => (
  <section aria-labelledby="documentation-title" className="gutter relative bg-ink-900 pb-24 pt-28 text-stone-50 sm:pb-32 sm:pt-36">
    <div className="mx-auto max-w-wide">
      <div className="grid grid-cols-1 gap-14 lg:grid-cols-12 lg:gap-10">
        <div className="lg:col-span-5">
          <SectionIndex label="Why documentation matters" tone="light" />
          <h2 id="documentation-title" data-reveal="mask" className="mt-10 font-display text-display-lg font-medium">
            Every structure tells a different story.
          </h2>
          <p data-reveal className="mt-8 max-w-prose text-[1.0625rem] leading-relaxed text-stone-200">
            Visible deterioration can take many forms: cracks, displaced material, moisture, vegetation, surface loss,
            or signs of earlier intervention. Their significance depends on the structure and the conditions around
            it. Good documentation creates a clearer starting point for investigation and conservation.
          </p>
        </div>
        <figure data-reveal className="lg:col-span-7 lg:pt-6">
          <MasonryDetail />
          <figcaption className="mt-3 font-mono text-[11px] tracking-wide text-stone-300">
            ILLUSTRATIVE DETAIL OF COURSED MASONRY · Visible signs are where a record begins, not where a diagnosis ends.
          </figcaption>
        </figure>
      </div>

      <div className="mt-24 sm:mt-28">
        <p data-reveal className="eyebrow text-jade-200">
          The JalDrishti method · See → Understand → Assess → Revive
        </p>
        <ol className="mt-6 grid grid-cols-2 border-t border-stone-50/20 md:grid-cols-4" aria-label="The JalDrishti method">
          {STAGES.map((s, i) => (
            <li
              key={s.key}
              data-reveal
              style={{ '--reveal-delay': `${i * 90}ms` } as React.CSSProperties}
              className={`relative py-7 pr-4 ${i % 2 ? 'border-l border-stone-50/20 pl-4 md:pl-6' : ''} ${
                i === 2 ? 'border-t border-stone-50/20 md:border-l md:border-t-0 md:pl-6' : ''
              } ${i === 3 ? 'border-t border-stone-50/20 md:border-t-0' : ''}`}
            >
              <span className="eyebrow text-jade-200">{String(i + 1).padStart(2, '0')}</span>
              <span className="mt-3 flex items-baseline gap-3">
                <span className="font-display text-display-sm">{s.verb}</span>
                <span className="font-deva text-sm text-stone-400" lang="hi">
                  {s.deva}
                </span>
              </span>
              <span className="mt-2 block text-sm leading-relaxed text-stone-300">{s.line}</span>
              {i < STAGES.length - 1 && (
                <span aria-hidden="true" className="absolute right-3 top-7 hidden text-stone-400 md:block">
                  →
                </span>
              )}
            </li>
          ))}
        </ol>
      </div>
    </div>
  </section>
);

const TYPOLOGIES = ['Baoli', 'Bawari', 'Kund', 'Vav'];

/** C — UNDERSTAND: the knowledge layer, shown beside a section drawn from the 3D model. */
export const UnderstandSection: React.FC<{ onRouteChange: Navigate }> = ({ onRouteChange }) => (
  <section aria-labelledby="understand-title" className="gutter bg-ink-900 py-28 text-stone-50 sm:py-36">
    <div className="mx-auto max-w-wide">
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <SectionIndex number="02" label="Understand" tone="light" />
        </div>
        <h2
          id="understand-title"
          data-reveal="mask"
          className="max-w-[20ch] font-display text-display-lg font-medium lg:col-span-8"
        >
          Connect what is visible with what is known.
        </h2>
      </div>

      <div className="mt-16 grid grid-cols-1 gap-14 lg:grid-cols-12 lg:gap-10">
        <figure data-reveal className="lg:col-span-7">
          <div
            className="overflow-x-auto border border-stone-50/10 bg-ink-950/40 p-4 sm:p-8"
            tabIndex={0}
            aria-label="Section drawing (scrolls horizontally on small screens)"
          >
            <StepwellSection tone="dark" className="h-auto w-full min-w-[620px] sm:min-w-0" />
          </div>
          <figcaption className="mt-4 flex flex-wrap justify-between gap-2 font-mono text-[11px] tracking-wide text-stone-400">
            <span>SECTION A–A · THE ILLUSTRATIVE STEPWELL FROM THE OPENING, ONE EXAMPLE</span>
            <span>Drawn from the same dimensions as the 3D model. Water levels are indicative.</span>
          </figcaption>
        </figure>

        <div className="lg:col-span-5 lg:pl-6">
          <p data-reveal className="max-w-prose text-[1.0625rem] leading-relaxed text-stone-200">
            Visual observations are only one part of understanding a traditional water structure. Construction
            practices, regional knowledge, historical sources, site context, and material choices can add important
            perspective. JalDrishti aims to connect observations with traceable knowledge while keeping the origin of
            each insight visible.
          </p>
          <PointList
            tone="light"
            className="mt-10"
            points={[
              'Connect observations with relevant documented knowledge.',
              'Preserve provenance and references for knowledge entries.',
              'Distinguish evidence from interpretation.',
              'Make missing information and uncertainty visible.',
            ]}
          />
          <div data-reveal className="mt-10 border border-stone-50/15 p-5">
            <p className="eyebrow text-stone-400">Knowledge records today</p>
            <p className="mt-3 font-display text-2xl text-stone-50">{TYPOLOGIES.join(' · ')}</p>
            <p className="mt-3 text-sm leading-relaxed text-stone-400">
              Each record describes construction, materials and water-management principles, and lists the sources
              its statements rest on. Tanks, temple tanks, ponds and other regional systems are within the intended
              scope but do not yet have records.
            </p>
          </div>
          <a {...routeLink(onRouteChange, '/knowledge')} data-reveal className="btn-ghost-light mt-8">
            Explore knowledge
          </a>
        </div>
      </div>
    </div>
  </section>
);

/** Phases used by the restoration planner (see components/RestorationRoadmap.tsx). */
const ROADMAP = [
  { label: 'Immediate stabilisation', note: 'Make safe what is at risk now, without irreversible work.' },
  { label: 'Hydrological remediation', note: 'Address the water and moisture behind the deterioration.' },
  { label: 'Masonry and traditional consolidation', note: 'Repair in kind, with compatible materials and methods.' },
  { label: 'Long-term monitoring', note: 'Record again, compare, and adjust over time.' },
];

/** E — REVIVE. */
export const ReviveSection: React.FC = () => (
  <section aria-labelledby="revive-title" className="gutter bg-jade-800 py-28 text-stone-50 sm:py-36">
    <div className="mx-auto grid max-w-wide grid-cols-1 gap-16 lg:grid-cols-12 lg:gap-10">
      <div className="lg:col-span-5">
        <SectionIndex number="04" label="Revive" tone="light" />
        <h2 id="revive-title" data-reveal="mask" className="mt-10 font-display text-display-lg font-medium">
          Support conservation that respects original knowledge.
        </h2>
        <p data-reveal className="mt-8 max-w-prose text-[1.0625rem] leading-relaxed text-stone-200">
          Responsible conservation seeks to understand the problem before choosing an intervention. It values the
          original fabric, considers the compatibility of materials and methods, addresses contributing causes where
          established, and records the reasoning behind proposed actions.
        </p>
        <PointList
          tone="light"
          className="mt-10"
          points={[
            'Build a clearer record of observed conditions.',
            'Organise conservation considerations and outstanding questions.',
            'Record proposed actions and their supporting evidence where supported.',
            'Encourage appropriate expert review and ongoing monitoring.',
          ]}
        />
      </div>

      <figure data-reveal className="lg:col-span-6 lg:col-start-7 lg:pt-16">
        <p className="eyebrow text-jade-200">How the planner organises a conservation roadmap</p>
        <ol className="mt-6">
          {ROADMAP.map((r, i) => (
            <li key={r.label} className="relative grid grid-cols-[3rem_1fr] pb-9 last:pb-0">
              {i < ROADMAP.length - 1 && (
                <span aria-hidden="true" className="absolute bottom-0 left-[0.6875rem] top-8 w-px bg-stone-50/20" />
              )}
              <span className="relative flex h-6 w-6 items-center justify-center rounded-full border border-stone-50/40 font-mono text-[10px] text-stone-200">
                {i + 1}
              </span>
              <div>
                <p className="font-display text-2xl leading-tight text-stone-50">{r.label}</p>
                <p className="mt-1.5 text-sm leading-relaxed text-stone-300">{r.note}</p>
              </div>
            </li>
          ))}
        </ol>
        <figcaption className="mt-10 border-l-2 border-jade-300 pl-4 text-sm leading-relaxed text-stone-300">
          Roadmap actions are decision support, not a prescription. Where the planner indicates that structural or
          chemical verification is needed, it says so. Any action should be reviewed by a qualified conservation
          professional; JalDrishti does not certify structural safety.
        </figcaption>
      </figure>
    </div>
  </section>
);

const QUESTIONS = [
  {
    form: 'A stepwell',
    asks: [
      'How do its levels and stairs relate to the water table across the seasons?',
      'Where do landings, galleries or retaining walls show movement or repair?',
    ],
  },
  {
    form: 'A kund',
    asks: ['How does the paved catchment direct runoff into the basin?', 'Are inlets and steps clear of silt and vegetation?'],
  },
  {
    form: 'A historic tank',
    asks: [
      'How do embankments, inlets and outlets behave together?',
      'What has changed in the catchment that feeds it?',
    ],
  },
  {
    form: 'A regional system',
    asks: ['What local knowledge governs its upkeep?', 'Who relies on it today, and how has that use changed?'],
  },
];

const BUILT_TODAY = [
  'A pilot vision model that looks for cracks in inspection photographs',
  'Knowledge records for four typologies: baoli, bawari, kund and vav',
  'Rule-based material-compatibility checks for candidate repair materials',
  'A restoration planner that organises considerations into phases',
];

/** S8 — One platform, different contexts. Separates the mission from the example in the opening. */
export const ContextsSection: React.FC = () => (
  <section aria-labelledby="contexts-title" className="gutter bg-ink-950 py-28 text-stone-50 sm:py-36">
    <div className="mx-auto max-w-wide">
      <SectionIndex label="One platform, different contexts" tone="light" />
      <h2 id="contexts-title" data-reveal="mask" className="mt-10 max-w-[22ch] font-display text-display-lg font-medium">
        Because no two heritage water systems are exactly alike.
      </h2>
      <p data-reveal className="mt-8 max-w-[44rem] text-[1.0625rem] leading-relaxed text-stone-300">
        Different structures call for different questions. A stepped well, a kund, a historic tank, and a regional
        water-management system may differ in form, construction, setting, and function. JalDrishti&rsquo;s broader
        vision is to help bring observations, knowledge, and conservation considerations together without treating
        these structures as interchangeable.
      </p>

      <dl className="mt-20 border-t border-stone-50/15">
        {QUESTIONS.map((q, i) => (
          <div
            key={q.form}
            data-reveal
            style={{ '--reveal-delay': `${i * 70}ms` } as React.CSSProperties}
            className="grid grid-cols-1 gap-4 border-b border-stone-50/15 py-8 md:grid-cols-12 md:gap-10"
          >
            <dt className="font-display text-display-sm italic text-stone-100 md:col-span-4">{q.form} asks&hellip;</dt>
            <dd className="md:col-span-8">
              <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-8">
                {q.asks.map((a) => (
                  <li key={a} className="text-[0.9375rem] leading-relaxed text-stone-300">
                    {a}
                  </li>
                ))}
              </ul>
            </dd>
          </div>
        ))}
      </dl>

      <div data-reveal className="mt-16 grid grid-cols-1 gap-8 border border-stone-50/15 p-6 sm:p-8 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <p className="eyebrow text-jade-200">Where JalDrishti stands today</p>
          <p className="mt-4 text-sm leading-relaxed text-stone-300">
            The mission is wider than what is built. Coverage is still growing, nothing here has been validated across
            every type of structure, and each output is labelled with where it came from.
          </p>
        </div>
        <ul className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2 lg:col-span-8">
          {BUILT_TODAY.map((b) => (
            <li key={b} className="flex gap-3 text-[0.9375rem] leading-relaxed text-stone-100">
              <span aria-hidden="true" className="mt-[0.6rem] h-px w-4 shrink-0 bg-jade-300" />
              {b}
            </li>
          ))}
        </ul>
      </div>
    </div>
  </section>
);

/** F — Our approach. */
export const ApproachSection: React.FC = () => (
  <section aria-labelledby="approach-title" className="gutter grain bg-stone-50 py-28 sm:py-40">
    <div className="mx-auto max-w-content text-center">
      <p data-reveal className="eyebrow text-ink-600">
        Our approach
      </p>
      <h2
        id="approach-title"
        data-reveal="mask"
        className="mx-auto mt-8 max-w-[18ch] font-display text-display-lg font-medium text-ink-950"
      >
        Technology in service of heritage.
      </h2>
      <p data-reveal className="mx-auto mt-8 max-w-[44rem] text-lg leading-relaxed text-ink-700">
        JalDrishti brings modern digital tools into conversation with traditional knowledge. The goal is to help
        conservators, researchers, engineers, craftspeople, and communities document what they observe, understand its
        context, and explore better-informed next steps&mdash;supporting their judgement, never replacing it.
      </p>
    </div>
  </section>
);
