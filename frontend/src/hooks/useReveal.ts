import { useEffect, type RefObject } from 'react';

/**
 * Reveals `[data-reveal]` descendants of `root` as they enter the viewport.
 * Content stays visible if this hook never runs (no JS, or reduced motion via CSS).
 */
export const useReveal = (root: RefObject<HTMLElement>) => {
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    el.classList.add('js-reveal');
    const targets = Array.from(el.querySelectorAll<HTMLElement>('[data-reveal]'));
    if (!('IntersectionObserver' in window)) {
      targets.forEach((t) => t.classList.add('is-revealed'));
      return;
    }

    // A fully clip-pathed element never reports as intersecting, so mask
    // reveals are observed through their parent instead.
    const watched = new Map<Element, HTMLElement[]>();
    targets.forEach((t) => {
      const observed = t.dataset.reveal === 'mask' && t.parentElement ? t.parentElement : t;
      watched.set(observed, [...(watched.get(observed) ?? []), t]);
    });

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          watched.get(entry.target)?.forEach((t) => t.classList.add('is-revealed'));
          io.unobserve(entry.target);
        });
      },
      { rootMargin: '0px 0px -10% 0px', threshold: 0.05 },
    );
    watched.forEach((_, observed) => io.observe(observed));
    return () => io.disconnect();
  }, [root]);
};
