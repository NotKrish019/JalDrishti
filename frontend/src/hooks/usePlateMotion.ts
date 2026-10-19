import { useEffect, type RefObject } from 'react';

/**
 * Depth for a framed photograph: the image drifts slower than the page as it
 * scrolls (parallax inside its frame), and the frame tilts a few degrees
 * towards a fine pointer. Transforms only, written straight to the DOM in a
 * rAF, so nothing re-renders and nothing shifts layout.
 *
 * Off under prefers-reduced-motion; tilt is also off for coarse pointers.
 */
export const usePlateMotion = (
  frame: RefObject<HTMLElement>,
  image: RefObject<HTMLElement>,
  { tilt = true, scale = 1.14 }: { tilt?: boolean; scale?: number } = {},
) => {
  useEffect(() => {
    const f = frame.current;
    const img = image.current;
    if (!f || !img) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reduce.matches) return;
    const fine = tilt && window.matchMedia('(pointer: fine)').matches;

    let raf = 0;
    let tiltX = 0;
    let tiltY = 0;
    let targetX = 0;
    let targetY = 0;

    const render = () => {
      raf = 0;
      const rect = f.getBoundingClientRect();
      // -1 when the frame enters at the bottom, +1 as it leaves at the top.
      const progress = Math.max(-1, Math.min(1, (window.innerHeight / 2 - (rect.top + rect.height / 2)) / window.innerHeight));
      img.style.transform = `translate3d(0, ${(progress * (scale - 1) * 40).toFixed(2)}%, 0) scale(${scale})`;
      if (!tilt) return;
      tiltX += (targetX - tiltX) * 0.18;
      tiltY += (targetY - tiltY) * 0.18;
      f.style.transform = `perspective(1400px) rotateX(${tiltY.toFixed(3)}deg) rotateY(${tiltX.toFixed(3)}deg)`;
      if (Math.abs(targetX - tiltX) > 0.01 || Math.abs(targetY - tiltY) > 0.01) schedule();
    };
    const schedule = () => {
      if (!raf) raf = requestAnimationFrame(render);
    };
    const onMove = (e: PointerEvent) => {
      const rect = f.getBoundingClientRect();
      targetX = ((e.clientX - rect.left) / rect.width - 0.5) * 5;
      targetY = -((e.clientY - rect.top) / rect.height - 0.5) * 4;
      schedule();
    };
    const onLeave = () => {
      targetX = 0;
      targetY = 0;
      schedule();
    };

    schedule();
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    if (fine) {
      f.addEventListener('pointermove', onMove);
      f.addEventListener('pointerleave', onLeave);
    }
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
      f.removeEventListener('pointermove', onMove);
      f.removeEventListener('pointerleave', onLeave);
      img.style.transform = '';
      f.style.transform = '';
    };
  }, [frame, image, tilt, scale]);
};
