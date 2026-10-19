import React from 'react';
import { SectionIndex } from './SectionIndex';
import { StepwellSection } from './StepwellSection';

export const STAGES = [
  {
    key: 'see',
    verb: 'See',
    deva: 'दृष्टि',
    summary: 'Inspect photographs for visible deterioration.',
    detail:
      'A pilot YOLOv8n model looks for cracks in each inspection photograph. Findings are returned with detection confidence and image-space measurements — never with a physical scale the photograph cannot support.',
    status: 'Pilot model · cracks in live analysis',
  },
  {
    key: 'understand',
    verb: 'Understand',
    deva: 'बोध',
    summary: 'Connect the structure to how it was built.',
    detail:
      'Curated records for four typologies — baoli, bawari, kund and vav — describe their construction, materials and water-management principles, with the sources each statement rests on.',
    status: 'Curated knowledge base · cited sources',
  },
  {
    key: 'assess',
    verb: 'Assess',
    deva: 'आकलन',
    summary: 'Turn observations into explainable indicators.',
    detail:
      'Rule-based condition and water-functionality indices are calculated from the findings. Every value carries its method, a confidence, and the limitations that apply to it.',
    status: 'Deterministic rules · stated limitations',
  },
  {
    key: 'revive',
    verb: 'Revive',
    deva: 'पुनर्जीवन',
    summary: 'Prioritise conservation, with compatible materials.',
    detail:
      'A phased conservation roadmap, material compatibility across seven dimensions, and the practices to avoid. Every recommendation is marked as needing verification by a qualified conservation professional.',
    status: 'Decision support · expert verification required',
  },
] as const;

/** The water veil resolves into this: the turn from observing to conserving. */
export const DescentResolution: React.FC<{ id: string }> = ({ id }) => (
  <section
    id={id}
    tabIndex={-1}
    aria-labelledby={`${id}-title`}
    className="gutter relative bg-jade-900 pb-28 pt-24 text-stone-50 outline-none sm:pb-36 sm:pt-32"
  >
    <div className="mx-auto max-w-wide">
      <SectionIndex number="01" label="From water to work" tone="light" />
      <h2
        id={`${id}-title`}
        data-reveal="mask"
        className="mt-10 max-w-[18ch] font-display text-display-lg font-medium"
      >
        We do not just observe these structures. We help understand, assess and conserve them.
      </h2>
      <ol className="mt-16 grid grid-cols-2 border-t border-stone-50/15 sm:grid-cols-4" aria-label="The JalDrishti method">
        {STAGES.map((s, i) => (
          <li
            key={s.key}
            data-reveal
            style={{ '--reveal-delay': `${i * 90}ms` } as React.CSSProperties}
            className={`border-stone-50/15 py-6 pr-4 ${i % 2 ? 'border-l pl-4 sm:pl-6' : ''} ${i === 2 ? 'border-l-0 sm:border-l sm:pl-6' : ''} ${i > 1 ? 'border-t sm:border-t-0' : ''}`}
          >
            <span className="eyebrow text-jade-200">{String(i + 1).padStart(2, '0')}</span>
            <span className="mt-3 block font-display text-display-sm">{s.verb}</span>
            <span className="mt-2 block text-sm leading-relaxed text-stone-300">{s.summary}</span>
          </li>
        ))}
      </ol>
    </div>
  </section>
);

const ANNOTATIONS = [
  {
    title: 'Built to the water table',
    body: 'A stepwell is excavated until it meets groundwater. Its depth is set by hydrology, not by ornament.',
  },
  {
    title: 'Steps that follow the seasons',
    body: 'Terraces and flights give access at every level, because the water stands high after the monsoon and low in the dry months.',
  },
  {
    title: 'Local stone, lime and craft',
    body: 'Walls are typically coursed stone or brick set in lime-based mortars — materials that breathe, flex and can be repaired in kind.',
  },
];

export const EngineeringStory: React.FC = () => (
  <section aria-labelledby="engineering-title" className="gutter grain bg-stone-50 py-28 sm:py-36">
    <div className="mx-auto grid max-w-wide grid-cols-1 gap-16 lg:grid-cols-12 lg:gap-10">
      <div className="lg:col-span-5">
        <SectionIndex number="02" label="The engineering" />
        <h2 id="engineering-title" data-reveal="mask" className="mt-10 font-display text-display-md font-medium text-ink-950">
          Not monuments that hold water — water systems that became monuments.
        </h2>
        <p data-reveal className="mt-8 max-w-prose text-base leading-relaxed text-ink-700">
          Traditional water structures were purpose-built systems. Their form answers practical questions: how deep
          the water lies, how far it moves through the year, what the local ground and materials allow, and how people
          reach it safely.
        </p>
        <dl className="mt-12 space-y-8">
          {ANNOTATIONS.map((a, i) => (
            <div
              key={a.title}
              data-reveal
              style={{ '--reveal-delay': `${i * 80}ms` } as React.CSSProperties}
              className="grid grid-cols-[2.5rem_1fr] gap-x-4 border-t border-ink-900/15 pt-5"
            >
              <dt className="contents">
                <span className="eyebrow pt-1 text-laterite-500">{String.fromCharCode(65 + i)}</span>
                <span className="font-display text-2xl font-medium text-ink-950">{a.title}</span>
              </dt>
              <dd className="col-start-2 mt-2 text-sm leading-relaxed text-ink-700">{a.body}</dd>
            </div>
          ))}
        </dl>
      </div>
      <figure data-reveal className="lg:col-span-7 lg:pt-24">
        <div
          className="overflow-x-auto border border-ink-900/10 bg-stone-100/60 p-4 sm:p-8"
          tabIndex={0}
          aria-label="Section drawing (scrolls horizontally on small screens)"
        >
          <StepwellSection className="h-auto w-full min-w-[620px] sm:min-w-0" />
        </div>
        <figcaption className="mt-4 flex flex-wrap justify-between gap-2 font-mono text-[11px] tracking-wide text-ink-600">
          <span>SECTION A–A · ILLUSTRATIVE CIRCULAR STEPWELL</span>
          <span>Drawn from the same dimensions as the 3D model above. Water levels are indicative.</span>
        </figcaption>
      </figure>
    </div>
  </section>
);

const CHALLENGES = [
  {
    title: 'Evidence is scattered',
    body: 'Condition is recorded in photographs on phones and in site notes, rarely in a form that can be compared over time.',
  },
  {
    title: 'Knowledge is fragmented',
    body: 'How a structure was built lives in texts, surveys and the memory of craftspeople — seldom beside the evidence of its decay.',
  },
  {
    title: 'Repairs can do harm',
    body: 'Hard, impermeable modern materials applied to historic lime masonry can trap moisture and accelerate the damage they were meant to fix.',
  },
];

export const ChallengeSection: React.FC = () => (
  <section aria-labelledby="challenge-title" className="gutter bg-stone-100 py-28 sm:py-36">
    <div className="mx-auto max-w-wide">
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <SectionIndex number="03" label="The challenge" />
        </div>
        <h2 id="challenge-title" data-reveal="mask" className="font-display text-display-md font-medium text-ink-950 lg:col-span-8">
          Conservation decisions depend on bringing three things together that usually live apart.
        </h2>
      </div>
      <ol className="mt-20 grid grid-cols-1 border-t border-ink-900/20 md:grid-cols-3">
        {CHALLENGES.map((c, i) => (
          <li
            key={c.title}
            data-reveal
            style={{ '--reveal-delay': `${i * 100}ms` } as React.CSSProperties}
            className={`py-10 md:px-8 ${i ? 'border-t border-ink-900/20 md:border-l md:border-t-0' : 'md:pl-0'}`}
          >
            <span className="font-display text-6xl font-normal italic text-stone-400">{['i', 'ii', 'iii'][i]}</span>
            <h3 className="mt-6 text-lg font-semibold text-ink-950">{c.title}</h3>
            <p className="mt-3 max-w-[34ch] text-sm leading-relaxed text-ink-700">{c.body}</p>
          </li>
        ))}
      </ol>
    </div>
  </section>
);

export const ApproachSection: React.FC = () => (
  <section aria-labelledby="approach-title" className="gutter bg-ink-900 py-28 text-stone-50 sm:py-36">
    <div className="mx-auto max-w-wide">
      <SectionIndex number="04" label="The JalDrishti approach" tone="light" />
      <h2 id="approach-title" data-reveal="mask" className="mt-10 max-w-[20ch] font-display text-display-md font-medium">
        See, understand, assess, revive — each step stated with what it can and cannot tell you.
      </h2>

      <div className="mt-20">
        {STAGES.map((s, i) => (
          <article
            key={s.key}
            data-reveal
            className="grid grid-cols-1 gap-6 border-t border-stone-50/15 py-12 md:grid-cols-12 md:gap-10 md:py-16"
          >
            <div className="md:col-span-5">
              <div className="flex items-baseline gap-5">
                <span className="eyebrow text-stone-400">{String(i + 1).padStart(2, '0')}</span>
                <h3 className="font-display text-display-lg font-medium">{s.verb}</h3>
              </div>
              <p className="mt-2 pl-[2.4rem] font-deva text-lg text-stone-400" lang="hi">
                {s.deva}
              </p>
            </div>
            <div className="md:col-span-6 md:col-start-7">
              <p className="text-lg text-stone-100">{s.summary}</p>
              <p className="mt-4 text-sm leading-relaxed text-stone-300">{s.detail}</p>
              <p className="eyebrow mt-6 inline-flex items-center gap-2 text-jade-200">
                <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-jade-300" />
                {s.status}
              </p>
            </div>
          </article>
        ))}
      </div>
    </div>
  </section>
);
