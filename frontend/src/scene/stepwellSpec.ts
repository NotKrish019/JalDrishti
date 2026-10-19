/**
 * Shared dimensions of the illustrative stepwell. Units are approximately metres.
 *
 * The structure is a composite, not a survey of any real site: a circular,
 * terraced well (after circular stepwells with colonnaded galleries) whose
 * lowest shaft carries carved bands (after the frieze-lined shafts of Gujarat vavs).
 *
 * Section, outer to inner:
 *   ground (y = 0) ─┐ wall 0 at rimRadius
 *                   └─ terrace 1 ─┐ wall 1 at terraceRadius(1)
 *                                 └─ terrace 2 ... ─ terrace N ─┐ shaft
 *                                                               └─ water
 */
export const STEPWELL = {
  rimRadius: 22,
  terraceCount: 9,
  terraceDepth: 1.75, // radial width of each terrace
  tierHeight: 3.2,
  shaftDepth: 3.4, // from the last terrace down to the water surface
  galleryTiers: [2, 4, 6, 8] as readonly number[],
  galleryHeight: 2.35,
} as const;

/** Inner radius of terrace k (k = 0 is the ground rim). */
export const terraceRadius = (k: number): number => STEPWELL.rimRadius - k * STEPWELL.terraceDepth;

/** Floor level of terrace k. */
export const terraceY = (k: number): number => -k * STEPWELL.tierHeight;

export const WATER_Y = terraceY(STEPWELL.terraceCount) - STEPWELL.shaftDepth;
export const WATER_RADIUS = terraceRadius(STEPWELL.terraceCount);

/** Radius of the open void at height y (inside the innermost wall at that level). */
export const voidRadiusAt = (y: number): number => {
  if (y >= 0) return STEPWELL.rimRadius;
  const k = Math.min(STEPWELL.terraceCount, Math.floor(-y / STEPWELL.tierHeight));
  return terraceRadius(k);
};
