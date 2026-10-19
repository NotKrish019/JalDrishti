import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { JalDrishtiLogo } from './JalDrishtiLogo';
import { useReducedMotion } from '../hooks/useReducedMotion';
import type { AppRoute } from '../types';
import type { DescentScene } from '../scene/DescentScene';

export interface HeroSceneProps {
  onRouteChange: (route: AppRoute) => void;
  /** id of the element that follows the descent; used by "skip". */
  nextSectionId: string;
}

type Align = 'left' | 'right' | 'centre';

interface Chapter {
  id: string;
  /** Scroll-progress range over which the chapter is fully visible. */
  from: number;
  to: number;
  label: string;
  rail: string;
  title: string;
  body: string;
  align: Align;
  /** The closing chapter carries the calls to action. */
  final?: boolean;
}

/**
 * Narrative copy, keyed to the same scroll progress as the camera path
 * (scene/cameraPath.ts): the site overview, the rim, the helix descent, the
 * water. Claims are deliberately general; nothing here describes a real site.
 */
const CHAPTERS: Chapter[] = [
  {
    id: 'place',
    from: 0.075,
    to: 0.15,
    label: '01 / The place',
    rail: 'Place',
    title: 'Water heritage belongs to its landscape.',
    body: 'A stepwell, a kund, a temple tank, a village pond: each sits within its own ground, climate, and community. The stepwell here is one illustrative example. Understanding any of them begins by looking beyond the structure itself.',
    align: 'left',
  },
  {
    id: 'approach',
    from: 0.19,
    to: 0.27,
    label: '02 / The approach',
    rail: 'Approach',
    title: 'Structures, land, and water work together.',
    body: 'Slopes, catchments, approaches, and enclosing walls shape how water arrives, is held, and is reached. The form of each traditional water structure responds to its own setting.',
    align: 'left',
  },
  {
    id: 'descent',
    from: 0.37,
    to: 0.49,
    label: '03 / The descent',
    rail: 'Descent',
    title: 'Documentation begins with context.',
    body: 'Stairs, landings, retaining walls, and changing levels are evidence of how a structure was designed and used. Recording them in context gives every later observation a place to belong.',
    align: 'right',
  },
  {
    id: 'craft',
    from: 0.57,
    to: 0.69,
    label: '04 / The craft',
    rail: 'Craft',
    title: 'Materials need careful interpretation.',
    body: 'Joints, worn surfaces, displaced masonry, and later repairs may each tell a different story. A careful record helps separate what is original, what has changed, and what needs closer study.',
    align: 'left',
  },
  {
    id: 'water',
    from: 0.81,
    to: 0.9,
    label: '05 / The water',
    rail: 'Water',
    title: 'Visible evidence, wider questions.',
    body: 'Moisture, drainage, vegetation, and the surrounding environment influence how historic water structures change over time. A photograph offers clues; understanding causes often needs investigation on site.',
    align: 'right',
  },
  {
    id: 'mission',
    from: 0.95,
    to: 1.01,
    label: '06 / JalDrishti',
    rail: 'Mission',
    title: 'One example. A much wider heritage.',
    body: 'From stepwells and kunds to historic tanks and regional water systems, JalDrishti brings digital documentation, traceable knowledge, and conservation-oriented insight together to support how India\u2019s water heritage is understood and cared for.',
    align: 'centre',
    final: true,
  },
];

const FADE = 0.03;
/** The introduction is fully visible until here, and gone by INTRO_END + FADE. */
const INTRO_END = 0.04;

const visibility = (p: number, from: number, to: number) => {
  if (p < from - FADE || p > to + FADE) return 0;
  if (p < from) return (p - (from - FADE)) / FADE;
  if (p > to) return 1 - (p - to) / FADE;
  return 1;
};

const railIndex = (p: number) => {
  let active = 0;
  CHAPTERS.forEach((c, i) => {
    if (p >= c.from - FADE) active = i;
  });
  return active;
};

const POSTER = '/hero/opening.jpg';

type Mode = 'loading' | 'immersive' | 'still' | 'fallback';

/** Legibility scrim behind each chapter, placed where its copy sits. */
const SCRIM: Record<Align, string> = {
  left: 'radial-gradient(120% 90% at 0% 100%, rgba(18,14,10,0.78) 0%, rgba(18,14,10,0.42) 40%, rgba(18,14,10,0) 72%)',
  right:
    'radial-gradient(120% 90% at 100% 100%, rgba(18,14,10,0.78) 0%, rgba(18,14,10,0.42) 40%, rgba(18,14,10,0) 72%)',
  centre: 'radial-gradient(90% 75% at 50% 55%, rgba(10,22,19,0.82) 0%, rgba(10,22,19,0.55) 45%, rgba(10,22,19,0.15) 100%)',
};

export const HeroScene: React.FC<HeroSceneProps> = ({ onRouteChange, nextSectionId }) => {
  const reducedMotion = useReducedMotion();
  const sectionRef = useRef<HTMLElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<DescentScene | null>(null);
  const introRef = useRef<HTMLDivElement>(null);
  const chapterRefs = useRef<(HTMLDivElement | null)[]>([]);
  const railFillRef = useRef<HTMLSpanElement>(null);
  const veilRef = useRef<HTMLDivElement>(null);
  const cueRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<Mode>('loading');
  const [activeRail, setActiveRail] = useState(0);
  const [sceneReady, setSceneReady] = useState(false);
  // The poster shows the opening view; after a reload deep in the descent it would
  // cross-fade into an unrelated frame, so it is only used near the top.
  const [posterApplies, setPosterApplies] = useState(true);

  const tall = mode === 'immersive' || mode === 'loading';

  /**
   * Scroll progress through the descent. The range is measured against the pinned
   * viewport's own height (100svh), not window.innerHeight, which changes as mobile
   * browser toolbars collapse and would make progress jump.
   */
  const measureProgress = useCallback(() => {
    const section = sectionRef.current;
    const viewport = viewportRef.current;
    if (!section || !viewport) return 0;
    const rect = section.getBoundingClientRect();
    const range = rect.height - viewport.offsetHeight;
    return range > 0 ? Math.min(1, Math.max(0, -rect.top / range)) : 0;
  }, []);

  useLayoutEffect(() => {
    setPosterApplies(measureProgress() < 0.18);
  }, [measureProgress]);

  // Latest overlay writer, called by the scene on every eased camera step.
  const overlayRef = useRef<(p: number) => void>(() => {});

  // --- Create / dispose the WebGL scene -----------------------------------------
  useEffect(() => {
    let disposed = false;
    let scene: DescentScene | null = null;
    const canvas = canvasRef.current;
    if (!canvas) return;

    (async () => {
      const { detectWebGL, pickQualityTier } = await import('../scene/quality');
      if (disposed) return;
      if (!detectWebGL()) {
        setMode('fallback');
        return;
      }
      try {
        const { DescentScene: Scene } = await import('../scene/DescentScene');
        if (disposed) return;
        scene = new Scene({
          canvas,
          tier: pickQualityTier(),
          still: reducedMotion,
          // Start in the pose that matches the current scroll position: no flash of the opening view.
          initialProgress: reducedMotion ? 0 : measureProgress(),
          onProgress: (p) => overlayRef.current(p),
          onContextLost: () => setMode('fallback'),
        });
        sceneRef.current = scene;
        const rect = canvas.getBoundingClientRect();
        scene.resize(rect.width, rect.height);
        setMode(reducedMotion ? 'still' : 'immersive');
        requestAnimationFrame(() => setSceneReady(true));
      } catch (err) {
        console.warn('JalDrishti: 3D scene unavailable, using static fallback.', err);
        setMode('fallback');
      }
    })();

    return () => {
      disposed = true;
      scene?.dispose();
      sceneRef.current = null;
      setSceneReady(false);
    };
  }, [reducedMotion, measureProgress]);

  // --- Resize --------------------------------------------------------------------
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ro = new ResizeObserver(([entry]) => {
      sceneRef.current?.resize(entry.contentRect.width, entry.contentRect.height);
    });
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [mode]);

  // --- Overlay: intro, chapters, rail and veil, all from one progress value ------------
  const applyOverlay = useCallback(
    (p: number) => {
      const immersive = mode === 'immersive' || mode === 'loading';
      const intro = introRef.current;
      if (intro) {
        const t = immersive ? 1 - Math.min(1, Math.max(0, (p - INTRO_END) / FADE)) : 1;
        intro.style.opacity = String(t);
        intro.style.transform = `translate3d(0, ${(1 - t) * -20}px, 0)`;
        intro.style.visibility = t <= 0.001 ? 'hidden' : 'visible';
      }
      if (cueRef.current) cueRef.current.style.opacity = String(Math.max(0, 1 - p / 0.03));

      CHAPTERS.forEach((c, i) => {
        const el = chapterRefs.current[i];
        if (!el) return;
        const v = mode === 'immersive' ? visibility(p, c.from, c.to) : 0;
        el.style.opacity = String(v);
        const copy = el.lastElementChild as HTMLElement | null;
        if (copy) copy.style.transform = `translate3d(0, ${(1 - v) * 18}px, 0)`;
        el.style.visibility = v <= 0.001 ? 'hidden' : 'visible';
      });

      if (railFillRef.current) railFillRef.current.style.transform = `scaleY(${p})`;
      if (veilRef.current) {
        // The descent settles into the colour of the section that follows.
        const v = mode === 'immersive' ? Math.min(1, Math.max(0, (p - 0.965) / 0.035)) * 0.85 : 0;
        veilRef.current.style.opacity = String(v);
      }
      const rail = railIndex(p);
      setActiveRail((prev) => (prev === rail ? prev : rail));
    },
    [mode],
  );
  overlayRef.current = applyOverlay;

  /**
   * Scroll sets the camera's target. When the animated scene is running, the overlay
   * follows the camera's eased progress (via onProgress) so copy and view stay in step
   * in both directions; otherwise it follows scroll directly.
   */
  const applyProgress = useCallback(
    (p: number) => {
      const scene = sceneRef.current;
      if (scene && mode === 'immersive') {
        scene.setProgress(p);
      } else {
        // Without motion the scene holds on the opening view of the whole site.
        scene?.setProgress(0);
        applyOverlay(mode === 'immersive' || mode === 'loading' ? p : 0);
      }
    },
    [applyOverlay, mode],
  );

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    let raf = 0;
    let visible = true;

    const measure = () => {
      raf = 0;
      applyProgress(measureProgress());
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(measure);
    };

    const io = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      const scene = sceneRef.current;
      if (!scene) return;
      if (visible && mode === 'immersive' && !document.hidden) scene.start();
      else scene.stop();
    });
    io.observe(section);

    const onVisibility = () => {
      const scene = sceneRef.current;
      if (!scene) return;
      if (document.hidden || !visible) scene.stop();
      else if (mode === 'immersive') scene.start();
    };

    measure();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [applyProgress, measureProgress, mode, sceneReady]);

  // --- Pointer parallax ---------------------------------------------------------------
  useEffect(() => {
    if (mode !== 'immersive') return;
    const finePointer = window.matchMedia('(pointer: fine)').matches;
    if (!finePointer) return;
    const onMove = (e: PointerEvent) => {
      sceneRef.current?.setPointer((e.clientX / window.innerWidth) * 2 - 1, -((e.clientY / window.innerHeight) * 2 - 1));
    };
    window.addEventListener('pointermove', onMove, { passive: true });
    return () => window.removeEventListener('pointermove', onMove);
  }, [mode]);

  const scrollToProgress = (p: number) => {
    const section = sectionRef.current;
    const viewport = viewportRef.current;
    if (!section || !viewport) return;
    const range = section.offsetHeight - viewport.offsetHeight;
    window.scrollTo({ top: section.offsetTop + range * p, behavior: reducedMotion ? 'auto' : 'smooth' });
  };

  const skip = () => {
    const next = document.getElementById(nextSectionId);
    if (!next) return;
    window.scrollTo({ top: next.offsetTop, behavior: 'auto' });
    next.focus({ preventScroll: true });
  };

  const go = (route: AppRoute) => (e: React.MouseEvent) => {
    e.preventDefault();
    onRouteChange(route);
  };

  const explore = () => {
    if (tall) scrollToProgress((CHAPTERS[0].from + CHAPTERS[0].to) / 2);
    else document.getElementById('descent-chapters')?.scrollIntoView({ behavior: 'auto' });
  };

  const showCanvas = mode === 'loading' || mode === 'immersive' || mode === 'still';
  const canvasVisible = showCanvas && sceneReady;

  return (
    <section
      ref={sectionRef}
      aria-label="JalDrishti: an illustrative descent into one example of India’s water heritage"
      className="relative bg-ink-950"
      style={{ height: tall ? 'max(760vh, 4600px)' : 'auto' }}
    >
      <div ref={viewportRef} className={`${tall ? 'sticky' : 'relative'} top-0 h-[100svh] w-full overflow-hidden`}>
        {/*
          Poster: a rendered still of the same opening view. It is the first thing
          painted, it carries the page while the scene initialises, and it remains as
          the architectural view when WebGL is unavailable.
        */}
        {!posterApplies && mode !== 'fallback' && (
          <div aria-hidden="true" className="absolute inset-0 bg-ink-950" />
        )}
        <img
          src={POSTER}
          alt=""
          aria-hidden="true"
          decoding="async"
          {...{ fetchpriority: 'high' }}
          className={`absolute inset-0 h-full w-full object-cover object-[66%_50%] transition-opacity duration-slow ${
            canvasVisible || (!posterApplies && mode !== 'fallback') ? 'opacity-0' : 'opacity-100'
          }`}
        />

        <canvas
          ref={canvasRef}
          aria-hidden="true"
          className={`absolute inset-0 h-full w-full transition-opacity duration-slow ease-out ${
            canvasVisible ? 'opacity-100' : 'opacity-0'
          }`}
        />

        {/* Top scrim for the navigation */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-32"
          style={{ background: 'linear-gradient(180deg, rgba(18,14,10,0.55) 0%, rgba(18,14,10,0) 100%)' }}
        />

        {/* Top bar */}
        <header className="gutter absolute inset-x-0 top-0 z-nav flex h-[var(--nav-h)] items-center justify-between gap-3">
          <a
            href="/"
            onClick={(e) => {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: 'auto' });
            }}
            aria-label="JalDrishti home"
            className="shrink-0"
          >
            <JalDrishtiLogo tone="light" />
          </a>
          <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
            <button
              type="button"
              onClick={skip}
              className="link-underline inline-flex h-9 items-center px-2 text-xs font-medium tracking-wide text-stone-100 hover:text-stone-50 sm:px-3"
            >
              Skip<span className="hidden sm:inline">&nbsp;the descent</span>
            </button>
            <a
              href="/knowledge"
              onClick={go('/knowledge')}
              className="link-underline hidden h-9 items-center px-3 text-xs font-medium tracking-wide text-stone-100 hover:text-stone-50 sm:inline-flex"
            >
              Knowledge
            </a>
            <a href="/upload" onClick={go('/upload')} className="btn-light h-9 px-3 text-xs sm:px-4">
              <span className="sm:hidden">Inspect</span>
              <span className="hidden sm:inline">Start an inspection</span>
            </a>
          </nav>
        </header>

        {/* Introduction: sits over the landscape to the left of the well */}
        <div
          ref={introRef}
          className="pointer-events-none absolute inset-0 z-content will-change-transform"
          style={{
            background:
              'linear-gradient(90deg, rgba(18,14,10,0.7) 0%, rgba(18,14,10,0.44) 30%, rgba(18,14,10,0) 56%), linear-gradient(0deg, rgba(18,14,10,0.32) 0%, rgba(18,14,10,0) 30%)',
          }}
        >
          <div className="gutter flex h-full flex-col justify-end pb-[9svh] sm:justify-center sm:pb-0">
            <div className="mx-auto w-full max-w-wide">
              <p className="eyebrow mb-4 text-stone-200 [text-shadow:0_1px_12px_rgba(18,14,10,0.6)]">
                <span className="font-deva text-sm normal-case tracking-normal" lang="hi">
                  जलदृष्टि
                </span>
                <span className="mx-3 opacity-60">/</span>
                India&rsquo;s water heritage
              </p>
              <h1 className="text-stone-50">
                <span className="block font-display text-[clamp(2.9rem,8.8vw,8.5rem)] font-medium uppercase leading-[0.88] tracking-[0.01em] [text-shadow:0_2px_36px_rgba(18,14,10,0.5)]">
                  JalDrishti
                </span>
                <span className="mt-5 block max-w-[24ch] font-display text-[clamp(1.6rem,2.7vw,2.6rem)] font-medium italic leading-[1.08] [text-shadow:0_2px_24px_rgba(18,14,10,0.55)]">
                  A deeper understanding of India&rsquo;s water heritage.
                </span>
              </h1>
              <p className="mt-6 max-w-[34rem] text-[0.975rem] leading-relaxed text-stone-100 [text-shadow:0_1px_16px_rgba(18,14,10,0.6)] sm:text-[1.0625rem]">
                From stepwells and kunds to historic tanks and other traditional water systems, India&rsquo;s water
                heritage carries architectural, environmental, and cultural knowledge. JalDrishti brings digital tools
                and traditional knowledge together to support its documentation and conservation.
              </p>
              <div className="pointer-events-auto mt-8 flex flex-wrap gap-3">
                <button type="button" onClick={explore} className="btn-light">
                  Explore JalDrishti
                </button>
                <a href="/upload" onClick={go('/upload')} className="btn-ghost-light backdrop-blur-[2px]">
                  Start an inspection
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Screen-reader version of the narrative; the visual layers below are decorative. */}
        {mode === 'immersive' && (
          <ol className="sr-only">
            {CHAPTERS.map((c) => (
              <li key={c.id}>
                <h2>
                  {c.label}: {c.title}
                </h2>
                <p>{c.body}</p>
              </li>
            ))}
          </ol>
        )}

        {/* Chapters */}
        {CHAPTERS.map((c, i) => (
          <div
            key={c.id}
            ref={(el) => (chapterRefs.current[i] = el)}
            className="pointer-events-none absolute inset-0 z-content"
            style={{ opacity: 0, visibility: 'hidden' }}
            aria-hidden="true"
          >
            <div aria-hidden="true" className="absolute inset-0" style={{ background: SCRIM[c.align] }} />
            <div
              className={`gutter relative flex h-full will-change-transform ${
                c.align === 'centre' ? 'items-center justify-center text-center' : 'items-end pb-[13svh]'
              }`}
            >
              <div
                className={`w-full ${
                  c.align === 'centre'
                    ? 'max-w-[44rem]'
                    : c.align === 'right'
                      ? 'mx-auto max-w-wide md:flex md:justify-end md:pr-44'
                      : 'mx-auto max-w-wide'
                }`}
              >
                <div className={c.align === 'centre' ? '' : 'max-w-[36rem]'}>
                  <p className="eyebrow text-jade-100 [text-shadow:0_1px_12px_rgba(18,14,10,0.6)]">{c.label}</p>
                  <p className="mt-4 font-display text-display-md font-medium text-stone-50 [text-shadow:0_2px_28px_rgba(18,14,10,0.55)]">
                    {c.title}
                  </p>
                  <p
                    className={`mt-5 text-base leading-relaxed text-stone-100 [text-shadow:0_1px_14px_rgba(18,14,10,0.7)] sm:text-[1.0625rem] ${
                      c.align === 'centre' ? 'mx-auto max-w-[36rem]' : ''
                    }`}
                  >
                    {c.body}
                  </p>
                  {c.final && (
                    <div className="pointer-events-auto mt-9 flex flex-wrap justify-center gap-3">
                      <a href="/upload" onClick={go('/upload')} className="btn-light" tabIndex={-1}>
                        Begin an inspection
                      </a>
                      <a href="/knowledge" onClick={go('/knowledge')} className="btn-ghost-light" tabIndex={-1}>
                        Explore knowledge
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Scroll cue */}
        {tall && (
          <div
            ref={cueRef}
            aria-hidden="true"
            className="pointer-events-none absolute bottom-7 left-1/2 z-content hidden -translate-x-1/2 flex-col items-center gap-3 text-stone-100 sm:flex"
          >
            <span className="eyebrow [text-shadow:0_1px_10px_rgba(18,14,10,0.6)]">Scroll to descend</span>
            <span className="relative block h-10 w-px overflow-hidden bg-stone-50/25">
              <span className="animate-scroll-cue absolute inset-0 bg-stone-50" />
            </span>
          </div>
        )}

        {/* Progress rail, with a soft edge scrim so it reads over the sunlit site */}
        {mode === 'immersive' && (
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-y-0 right-0 hidden w-60 md:block"
            style={{ background: 'linear-gradient(270deg, rgba(18,14,10,0.3) 0%, rgba(18,14,10,0) 100%)' }}
          />
        )}
        {mode === 'immersive' && (
          <nav
            aria-label="Descent chapters"
            className="absolute right-[var(--gutter)] top-1/2 z-content hidden -translate-y-1/2 md:block"
          >
            <ol className="relative flex flex-col gap-6 pr-5">
              <span aria-hidden="true" className="absolute bottom-1 right-0 top-1 w-px bg-stone-50/25" />
              <span
                aria-hidden="true"
                ref={railFillRef}
                className="absolute bottom-1 right-0 top-1 w-px origin-top bg-stone-50"
                style={{ transform: 'scaleY(0)' }}
              />
              {CHAPTERS.map((c, i) => (
                <li key={c.id} className="relative text-right">
                  <button
                    type="button"
                    onClick={() => scrollToProgress((c.from + Math.min(1, c.to)) / 2)}
                    aria-current={activeRail === i ? 'step' : undefined}
                    className={`eyebrow inline-flex items-center gap-2 [text-shadow:0_1px_12px_rgba(18,14,10,0.6)] transition-colors duration-base ${
                      activeRail === i ? 'text-stone-50' : 'text-stone-50/55 hover:text-stone-50'
                    }`}
                  >
                    <span className="tabular-nums">{String(i + 1).padStart(2, '0')}</span>
                    <span
                      className={`overflow-hidden whitespace-nowrap transition-[max-width,opacity] duration-base ${
                        activeRail === i ? 'max-w-[10rem] opacity-100' : 'max-w-0 opacity-0 lg:max-w-[10rem] lg:opacity-100'
                      }`}
                    >
                      {c.rail}
                    </span>
                  </button>
                  <span
                    aria-hidden="true"
                    className={`absolute right-[-24px] top-1/2 h-[7px] w-[7px] -translate-y-1/2 rounded-full border transition-colors duration-base ${
                      activeRail === i ? 'border-stone-50 bg-stone-50' : 'border-stone-50/50 bg-ink-950/40'
                    }`}
                  />
                </li>
              ))}
            </ol>
          </nav>
        )}

        {/* Honest caption */}
        <p className="absolute bottom-3 left-[var(--gutter)] z-content mr-24 max-w-[40rem] font-mono text-[10px] leading-snug tracking-wide text-stone-100/80 [text-shadow:0_1px_8px_rgba(18,14,10,0.8)]">
          {mode === 'fallback'
            ? 'Rendered still of an illustrative composite stepwell. The interactive descent needs WebGL.'
            : 'Illustrative composite stepwell, modelled procedurally. Not a survey of a specific site.'}
        </p>

        {/* Water veil: the descent settles into the colour of the next section */}
        <div
          ref={veilRef}
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-jade-900"
          style={{ opacity: 0 }}
        />
      </div>

      {/* Without the animated descent, the same six chapters are read as a page. */}
      {!tall && (
        <div id="descent-chapters" className="gutter bg-ink-950 pb-24 pt-20 text-stone-50 sm:pb-32 sm:pt-28">
          <ol className="mx-auto grid max-w-wide grid-cols-1 gap-x-10 gap-y-14 md:grid-cols-2 lg:grid-cols-3">
            {CHAPTERS.map((c) => (
              <li key={c.id} className="border-t border-stone-50/15 pt-6">
                <p className="eyebrow text-jade-200">{c.label}</p>
                <h2 className="mt-4 font-display text-display-sm font-medium">{c.title}</h2>
                <p className="mt-4 text-sm leading-relaxed text-stone-300">{c.body}</p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
};

export default HeroScene;
