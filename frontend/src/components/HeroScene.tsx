import React, { useCallback, useEffect, useRef, useState } from 'react';
import { JalDrishtiLogo } from './JalDrishtiLogo';
import { StepwellSection } from './home/StepwellSection';
import { useReducedMotion } from '../hooks/useReducedMotion';
import type { AppRoute } from '../types';
import type { DescentScene } from '../scene/DescentScene';

export interface HeroSceneProps {
  onRouteChange: (route: AppRoute) => void;
  /** id of the element that follows the descent; used by "skip". */
  nextSectionId: string;
}

type Tone = 'dark' | 'light';

interface Chapter {
  id: string;
  /** progress range over which the chapter is fully visible */
  from: number;
  to: number;
  tone: Tone;
  index?: string;
  title?: string;
  body: string;
}

/**
 * Narrative copy, keyed to the same scroll progress as the camera path.
 * Claims are deliberately general and verifiable.
 */
const CHAPTERS: Chapter[] = [
  {
    id: 'opening',
    from: 0.13,
    to: 0.24,
    tone: 'dark',
    index: 'I — Through the opening',
    body: 'Beneath the haze, a structure cut down through the ground to meet the water.',
  },
  {
    id: 'descent',
    from: 0.34,
    to: 0.46,
    tone: 'light',
    index: 'II — Into the stepwell',
    body: 'For more than a thousand years, communities in western and northern India built stepped wells down to the water table.',
  },
  {
    id: 'terraces',
    from: 0.53,
    to: 0.63,
    tone: 'light',
    index: 'III — Engineering in stone',
    body: 'Terraces and flights of steps let people follow the water as it rose after the monsoon and fell through the dry months.',
  },
  {
    id: 'shade',
    from: 0.69,
    to: 0.79,
    tone: 'light',
    body: 'Depth, shade and heavy masonry kept the lower levels cool — and every course of stone and lime still records how it was built.',
  },
  {
    id: 'water',
    from: 0.86,
    to: 0.93,
    tone: 'light',
    index: 'IV — The water',
    body: 'The water is the reason the structure exists. Conserving one means understanding the other.',
  },
];

const RAIL = [
  { label: 'Above', at: 0 },
  { label: 'Opening', at: 0.2 },
  { label: 'Descent', at: 0.48 },
  { label: 'Water', at: 0.92 },
];

const FADE = 0.035;

const visibility = (p: number, from: number, to: number) => {
  if (p < from - FADE || p > to + FADE) return 0;
  if (p < from) return (p - (from - FADE)) / FADE;
  if (p > to) return 1 - (p - to) / FADE;
  return 1;
};

type Mode = 'loading' | 'immersive' | 'still' | 'fallback';

export const HeroScene: React.FC<HeroSceneProps> = ({ onRouteChange, nextSectionId }) => {
  const reducedMotion = useReducedMotion();
  const sectionRef = useRef<HTMLElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<DescentScene | null>(null);
  const titleRef = useRef<HTMLDivElement>(null);
  const chapterRefs = useRef<(HTMLDivElement | null)[]>([]);
  const railFillRef = useRef<HTMLDivElement>(null);
  const veilRef = useRef<HTMLDivElement>(null);
  const cueRef = useRef<HTMLDivElement>(null);
  const scrimRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<Mode>('loading');
  const [activeRail, setActiveRail] = useState(0);
  // Chrome sits on bright sky first, then on the shadowed well.
  const [chromeTone, setChromeTone] = useState<Tone>('dark');
  const [sceneReady, setSceneReady] = useState(false);

  const tall = mode === 'immersive' || mode === 'loading';
  const darkBackdrop = mode === 'fallback' || mode === 'still';

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
  }, [reducedMotion]);

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

  // --- Scroll → progress → camera + overlay ----------------------------------------
  const applyProgress = useCallback(
    (p: number) => {
      sceneRef.current?.setProgress(mode === 'still' ? 0.62 : p);

      const title = titleRef.current;
      if (title) {
        const t = mode === 'immersive' || mode === 'loading' ? 1 - Math.min(1, Math.max(0, (p - 0.05) / 0.06)) : 1;
        title.style.opacity = String(t);
        title.style.transform = `translate3d(0, ${(1 - t) * -24}px, 0)`;
        title.style.visibility = t <= 0.001 ? 'hidden' : 'visible';
      }
      if (cueRef.current) cueRef.current.style.opacity = String(p < 0.03 ? 1 : Math.max(0, 1 - (p - 0.03) / 0.03));

      CHAPTERS.forEach((c, i) => {
        const el = chapterRefs.current[i];
        if (!el) return;
        const v = mode === 'immersive' ? visibility(p, c.from, c.to) : 0;
        el.style.opacity = String(v);
        el.style.transform = `translate3d(0, ${(1 - v) * 16}px, 0)`;
        el.style.visibility = v <= 0.001 ? 'hidden' : 'visible';
      });

      if (scrimRef.current) {
        const v = mode === 'immersive' ? Math.min(1, Math.max(0, (p - 0.27) / 0.08)) : mode === 'still' ? 1 : 0;
        scrimRef.current.style.opacity = String(v);
      }
      if (railFillRef.current) railFillRef.current.style.transform = `scaleY(${p})`;
      if (veilRef.current) {
        const v = mode === 'immersive' ? Math.min(1, Math.max(0, (p - 0.955) / 0.045)) : 0;
        veilRef.current.style.opacity = String(v);
      }
      let rail = 0;
      RAIL.forEach((r, i) => {
        if (p >= r.at - 0.02) rail = i;
      });
      setActiveRail((prev) => (prev === rail ? prev : rail));
      const tone: Tone = mode === 'fallback' || (mode !== 'still' && p > 0.27) || mode === 'still' ? 'light' : 'dark';
      setChromeTone((prev) => (prev === tone ? prev : tone));
    },
    [mode],
  );

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    let raf = 0;
    let visible = true;

    const measure = () => {
      raf = 0;
      const rect = section.getBoundingClientRect();
      const range = rect.height - window.innerHeight;
      const p = range > 0 ? Math.min(1, Math.max(0, -rect.top / range)) : 0;
      applyProgress(p);
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
  }, [applyProgress, mode, sceneReady]);

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
    if (!section) return;
    const range = section.offsetHeight - window.innerHeight;
    window.scrollTo({ top: section.offsetTop + range * p, behavior: reducedMotion ? 'auto' : 'smooth' });
  };

  const skip = () => {
    const next = document.getElementById(nextSectionId);
    if (!next) return;
    window.scrollTo({ top: next.offsetTop, behavior: 'auto' });
    next.focus({ preventScroll: true });
  };

  const showCanvas = mode === 'loading' || mode === 'immersive' || mode === 'still';

  return (
    <section
      ref={sectionRef}
      aria-label="A descent into an illustrative stepwell"
      className="relative bg-ink-950"
      style={{ height: tall ? 'max(720vh, 4200px)' : '100svh' }}
    >
      <div className="sticky top-0 h-[100svh] w-full overflow-hidden">
        {/* Scene */}
        <canvas
          ref={canvasRef}
          aria-hidden="true"
          className={`absolute inset-0 h-full w-full transition-opacity duration-slow ease-out ${
            showCanvas && sceneReady ? 'opacity-100' : 'opacity-0'
          }`}
        />

        {/* Pre-scene and no-WebGL composition: haze, then the section drawing */}
        <div
          aria-hidden="true"
          className={`absolute inset-0 transition-opacity duration-slow ${sceneReady && showCanvas ? 'opacity-0' : 'opacity-100'}`}
          style={{
            background:
              mode === 'fallback'
                ? 'radial-gradient(120% 80% at 50% 0%, #2a241c 0%, #0E0C0A 70%)'
                : 'linear-gradient(180deg, #8f9e9f 0%, #e9dcc4 55%, #ddd0ba 100%)',
          }}
        >
          {mode === 'fallback' && (
            <StepwellSection
              tone="dark"
              showLabels={false}
              className="absolute -right-[20%] bottom-0 h-[48%] w-auto max-w-none opacity-40 sm:right-0 sm:h-[62%] lg:opacity-60"
            />
          )}
        </div>

        {/* Legibility scrim for light-on-scene copy */}
        <div
          ref={scrimRef}
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            opacity: 0,
            background:
              mode === 'still'
                ? 'linear-gradient(90deg, rgba(14,12,10,0.8) 0%, rgba(14,12,10,0.45) 45%, rgba(14,12,10,0) 75%)'
                : 'radial-gradient(110% 75% at 0% 100%, rgba(14,12,10,0.72) 0%, rgba(14,12,10,0.35) 38%, rgba(14,12,10,0) 70%)',
          }}
        />

        {/* Top bar */}
        <header className="gutter absolute inset-x-0 top-0 z-nav flex h-[var(--nav-h)] items-center justify-between">
          <a
            href="/"
            onClick={(e) => {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: 'auto' });
            }}
            aria-label="JalDrishti home"
          >
            <JalDrishtiLogo tone={chromeTone === 'light' ? 'light' : 'dark'} />
          </a>
          <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
            <button
              type="button"
              onClick={skip}
              className={`hidden h-9 items-center px-3 text-xs font-medium tracking-wide sm:inline-flex ${
                chromeTone === 'light' ? 'text-stone-100 hover:text-stone-50' : 'text-ink-900/80 hover:text-ink-900'
              } link-underline`}
            >
              Skip the descent
            </button>
            <a
              href="/knowledge"
              onClick={(e) => {
                e.preventDefault();
                onRouteChange('/knowledge');
              }}
              className={`hidden h-9 items-center px-3 text-xs font-medium tracking-wide md:inline-flex ${
                chromeTone === 'light' ? 'text-stone-100 hover:text-stone-50' : 'text-ink-900/80 hover:text-ink-900'
              } link-underline`}
            >
              Knowledge
            </a>
            <a
              href="/upload"
              onClick={(e) => {
                e.preventDefault();
                onRouteChange('/upload');
              }}
              className={chromeTone === 'light' ? 'btn-light h-9 px-4 text-xs' : 'btn-primary h-9 px-4 text-xs'}
            >
              Start an inspection
            </a>
          </nav>
        </header>

        {/* Title */}
        <div
          ref={titleRef}
          className="gutter pointer-events-none absolute inset-x-0 top-[18svh] z-content will-change-transform sm:top-[20svh]"
        >
          <div className="mx-auto max-w-wide">
            <p
              className={`eyebrow mb-6 ${darkBackdrop ? 'text-stone-300' : 'text-ink-700'}`}
            >
              <span className="font-deva text-sm normal-case tracking-normal" lang="hi">
                जलदृष्टि
              </span>
              <span className="mx-3 opacity-50">/</span>
              Water heritage intelligence
            </p>
            <h1
              className={`font-display text-display-xl font-medium uppercase ${
                darkBackdrop ? 'text-stone-50' : 'text-ink-950'
              }`}
            >
              JalDrishti
            </h1>
            <p
              className={`mt-6 max-w-[34rem] font-display text-display-sm italic ${
                darkBackdrop ? 'text-stone-100' : 'text-ink-900'
              }`}
            >
              Where India&rsquo;s water wisdom meets modern intelligence.
            </p>
            <p
              className={`mt-4 max-w-[30rem] text-sm leading-relaxed sm:text-base ${
                mode === 'fallback' ? 'text-stone-300' : 'text-ink-700'
              }`}
            >
              Discover the engineering knowledge held in India&rsquo;s traditional water structures — and the tools
              to help conserve it.
            </p>
            {mode !== 'immersive' && mode !== 'loading' && (
              <div className="pointer-events-auto mt-8 flex flex-wrap gap-3">
                <button type="button" onClick={skip} className={darkBackdrop ? 'btn-light' : 'btn-primary'}>
                  Continue
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Chapters */}
        {CHAPTERS.map((c, i) => (
          <div
            key={c.id}
            ref={(el) => (chapterRefs.current[i] = el)}
            className="gutter pointer-events-none absolute inset-x-0 bottom-[14svh] z-content will-change-transform"
            style={{ opacity: 0, visibility: 'hidden' }}
            aria-hidden={mode !== 'immersive'}
          >
            <div className="mx-auto max-w-wide">
              <div className="max-w-[34rem]">
                {c.index && (
                  <p className={`eyebrow mb-4 ${c.tone === 'dark' ? 'text-ink-800' : 'text-stone-200'}`}>{c.index}</p>
                )}
                <p
                  className={`font-display text-display-sm ${
                    c.tone === 'dark' ? 'text-ink-950' : 'text-stone-50 [text-shadow:0_1px_24px_rgba(14,12,10,0.45)]'
                  }`}
                >
                  {c.body}
                </p>
              </div>
            </div>
          </div>
        ))}

        {/* Scroll cue */}
        {tall && (
          <div
            ref={cueRef}
            className="gutter pointer-events-none absolute bottom-8 right-0 z-content hidden items-end gap-3 text-ink-900 sm:flex"
          >
            <span className="eyebrow">Scroll to descend</span>
            <span className="relative block h-12 w-px overflow-hidden bg-ink-900/20">
              <span className="animate-scroll-cue absolute inset-0 bg-ink-900" />
            </span>
          </div>
        )}

        {/* Progress rail */}
        {mode === 'immersive' && (
          <nav
            aria-label="Descent chapters"
            className="absolute right-[var(--gutter)] top-1/2 z-content hidden -translate-y-1/2 md:block"
          >
            <div className="relative flex flex-col gap-7 pr-5">
              <span
                aria-hidden="true"
                className={`absolute right-0 top-1 bottom-1 w-px ${chromeTone === 'light' ? 'bg-stone-50/25' : 'bg-ink-900/20'}`}
              />
              <span
                aria-hidden="true"
                ref={railFillRef}
                className="absolute right-0 top-1 bottom-1 w-px origin-top bg-laterite-400"
                style={{ transform: 'scaleY(0)' }}
              />
              {RAIL.map((r, i) => (
                <button
                  key={r.label}
                  type="button"
                  onClick={() => scrollToProgress(r.at)}
                  aria-current={activeRail === i ? 'step' : undefined}
                  className={`eyebrow text-right transition-colors duration-base ${
                    chromeTone === 'light'
                      ? `[text-shadow:0_1px_12px_rgba(14,12,10,0.5)] ${activeRail === i ? 'text-stone-50' : 'text-stone-50/60 hover:text-stone-50'}`
                      : activeRail === i
                        ? 'text-ink-950'
                        : 'text-ink-900/55 hover:text-ink-950'
                  }`}
                >
                  {String(i + 1).padStart(2, '0')} {r.label}
                </button>
              ))}
            </div>
          </nav>
        )}

        {/* Honest caption */}
        <p
          className="absolute bottom-3 left-[var(--gutter)] z-content mr-24 max-w-[40rem] rounded-sm bg-ink-950/45 px-2 py-1 font-mono text-[10px] leading-snug tracking-wide text-stone-100/85"
        >
          {mode === 'fallback'
            ? 'Section drawing of an illustrative stepwell. The interactive 3D descent needs WebGL.'
            : 'Illustrative composite stepwell, modelled procedurally. Not a survey of a specific site.'}
        </p>

        {/* Water veil: the descent dissolves into the water colour of the next section */}
        <div
          ref={veilRef}
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 z-overlay bg-jade-900"
          style={{ opacity: 0 }}
        />
      </div>
    </section>
  );
};

export default HeroScene;
