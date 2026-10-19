import React, { useRef } from 'react';
import { ButtonSurfaceContext } from './Button';
import { usePlateMotion } from '../hooks/usePlateMotion';

/**
 * Reference photographs supplied for the internal pages (public/plates/, byte-for-byte
 * copies of the sample images). Captions describe what is visible and never name a
 * site, because the sources and locations have not been confirmed.
 */
export const PLATES = {
  'stepwell-reflection': {
    src: '/plates/stepwell-reflection.jpg',
    w: 735,
    h: 501,
    caption: 'Carved stepwell galleries, reflected in still water',
    focal: '50% 50%',
  },
  'well-octagon': { src: '/plates/well-octagon.jpg', w: 736, h: 552, caption: 'Octagonal stepwell, seen from above', focal: '50% 55%' },
  'tank-mist': { src: '/plates/tank-mist.jpg', w: 736, h: 981, caption: 'Stepped tank in monsoon mist', focal: '45% 52%' },
  'tank-stepped': { src: '/plates/tank-stepped.jpg', w: 672, h: 839, caption: 'Stepped tank, seen from its rim', focal: '50% 48%' },
} as const;

export type PlateName = keyof typeof PLATES;
/**
 * panel  a wide photograph that bleeds to the right edge and dissolves into the
 *        ground, with the title overlapping it (Inspect)
 * arch   the photograph seen through a pointed arch, after the niches of a
 *        stepwell gallery, beside the title (Findings, Knowledge)
 */
export type PlateTreatment = 'panel' | 'arch';

const Caption: React.FC<{ text: string; dark: boolean; className?: string }> = ({ text, dark, className = '' }) => (
  <figcaption className={`flex items-center gap-3 text-[0.8125rem] ${dark ? 'text-ws-faint' : 'text-ink-500'} ${className}`}>
    <span aria-hidden="true" className="h-px w-6 bg-current opacity-60" />
    {text} · reference photograph
  </figcaption>
);

/** Pointed-arch outline, drawn over the masked photograph (same geometry as .ws-arch's mask). */
const ArchOutline: React.FC = () => (
  <svg aria-hidden="true" className="ws-arch-outline" viewBox="0 0 100 125" preserveAspectRatio="none">
    <path d="M0.5 124.5 V46 C0.5 22 21 5 50 0.8 C79 5 99.5 22 99.5 46 V124.5" vectorEffect="non-scaling-stroke" />
  </svg>
);

export const Plate: React.FC<{ name: PlateName; treatment: PlateTreatment; dark: boolean; className?: string }> = ({
  name,
  treatment,
  dark,
  className = '',
}) => {
  const frameRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  usePlateMotion(frameRef, imageRef, { tilt: treatment === 'arch', scale: treatment === 'panel' ? 1.06 : 1.12 });
  const plate = PLATES[name];
  const img = (
    <img
      ref={imageRef}
      src={plate.src}
      width={plate.w}
      height={plate.h}
      alt=""
      decoding="async"
      style={{ objectPosition: plate.focal }}
    />
  );
  if (treatment === 'panel') {
    return (
      <figure className={className}>
        <div ref={frameRef} className="ws-panel ws-unveil" style={{ aspectRatio: `${plate.w} / ${plate.h}` }}>
          {img}
        </div>
        <Caption text={plate.caption} dark={dark} className="mt-4 justify-end px-[var(--gutter)] lg:pl-0" />
      </figure>
    );
  }
  return (
    <figure className={className}>
      <div ref={frameRef} className={`ws-arch ws-unveil ${dark ? 'ws-arch-dark' : 'ws-arch-light'}`}>
        {img}
        <ArchOutline />
      </div>
      <Caption text={plate.caption} dark={dark} className="mt-4 justify-center" />
    </figure>
  );
};

export interface PageContainerProps {
  /** Location label above the title, e.g. "JalDrishti / Inspection". */
  eyebrow?: string;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  /** Secondary line under the subtitle (structure, provenance). */
  meta?: React.ReactNode;
  /** Notice rendered at the top of the body (provenance warnings). */
  banner?: React.ReactNode;
  plate?: PlateName;
  treatment?: PlateTreatment;
  /**
   * One ground for the whole page, header included: dark granite for the working
   * page, warm limestone for results and reading, or a paper document on limestone.
   */
  ground?: 'dark' | 'light' | 'paper';
  width?: 'content' | 'wide';
  children: React.ReactNode;
  className?: string;
}

const WIDTH = { content: 'max-w-content', wide: 'max-w-wide' };

/**
 * Page frame for application routes: an editorial opening composed with a
 * reference photograph, then the body on the same continuous ground — no band,
 * no divider, no wrapper sheet.
 */
export const PageContainer: React.FC<PageContainerProps> = ({
  eyebrow,
  title,
  subtitle,
  actions,
  meta,
  banner,
  plate,
  treatment = 'arch',
  ground = 'light',
  width = 'wide',
  children,
  className = '',
}) => {
  const dark = ground === 'dark';
  const panel = plate && treatment === 'panel';

  const text = (
    <>
      {eyebrow && (
        <p className={`mb-5 flex items-center gap-3 text-[0.875rem] font-medium ${dark ? 'text-ws-sandstone' : 'text-ws-moss-deep'}`}>
          <span aria-hidden="true" className="h-px w-8 bg-current" />
          {eyebrow}
        </p>
      )}
      <h1
        className={`font-display font-medium leading-[0.96] tracking-[-0.018em] ${
          panel ? 'text-[clamp(2.75rem,6vw,5.75rem)]' : 'text-[clamp(2.5rem,5vw,4.5rem)]'
        } ${dark ? 'text-ws-text' : 'text-ink-950'}`}
      >
        {title}
      </h1>
      {subtitle && (
        <div className={`mt-6 max-w-[34rem] text-[1.0625rem] leading-relaxed ${dark ? 'text-ws-muted' : 'text-ink-700'}`}>{subtitle}</div>
      )}
      {meta && <div className="mt-5">{meta}</div>}
      {actions && <div className="mt-8 flex flex-wrap items-center gap-3 print:hidden">{actions}</div>}
    </>
  );

  return (
    <ButtonSurfaceContext.Provider value={dark ? 'dark' : 'light'}>
      <div className={`${dark ? 'ws-dark' : 'ws-light'} ${className}`}>
        {panel ? (
          // Title overlaps the photograph's dark left side; the image bleeds to the right edge.
          <header className="gutter mx-auto w-full max-w-wide pt-8 sm:pt-12 lg:pt-14">
            <div className="grid lg:grid-cols-12">
              <Plate
                name={plate}
                treatment="panel"
                dark={dark}
                className="-mx-[var(--gutter)] lg:col-start-5 lg:col-end-13 lg:row-start-1 lg:mx-0 lg:-mr-[var(--gutter)] print:hidden"
              />
              <div className="ws-rise relative z-[1] mt-8 lg:col-start-1 lg:col-end-8 lg:row-start-1 lg:mt-0 lg:self-end lg:pb-24">
                {text}
              </div>
            </div>
          </header>
        ) : (
          <header className={`gutter mx-auto w-full ${ground === 'paper' ? 'max-w-[64rem] lg:box-content' : WIDTH[width]} pt-12 sm:pt-16`}>
            <div className={`grid gap-x-16 gap-y-10 ${plate ? 'lg:grid-cols-12 lg:items-end' : ''}`}>
              <div className={plate ? 'ws-rise lg:col-span-7 lg:pb-16' : 'ws-rise max-w-[46rem]'}>{text}</div>
              {plate && (
                <Plate
                  name={plate}
                  treatment="arch"
                  dark={dark}
                  className="mx-auto w-full max-w-[22rem] lg:col-span-4 lg:col-start-9 lg:max-w-none print:hidden"
                />
              )}
            </div>
          </header>
        )}

        <div className="gutter mx-auto w-full pb-24 pt-14 sm:pt-16 print:pt-6">
          <div className={`mx-auto w-full ${ground === 'paper' ? 'max-w-[64rem]' : WIDTH[width]}`}>
            {banner && <div className="mb-10">{banner}</div>}
            {ground === 'paper' ? <article className="ws-doc px-6 py-10 sm:px-12 sm:py-14 print:p-0">{children}</article> : children}
          </div>
        </div>
      </div>
    </ButtonSurfaceContext.Provider>
  );
};

export default PageContainer;
