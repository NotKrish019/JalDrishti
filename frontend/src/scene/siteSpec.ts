/**
 * Layout of the heritage site around the stepwell. Units are approximately metres,
 * in the same world coordinates as the stepwell (opening centred on the origin).
 *
 * Angles are polar angles in the ground plane: x = r cos a, z = r sin a.
 * The opening camera looks in from a ≈ π/4, so:
 *   - the arcaded pavilion stands on the far side, facing the viewer (after the
 *     colonnaded range overlooking the well in the jal3 reference);
 *   - the gateway and approach path sit to the front-right, where the path
 *     leads the eye from the corner of the frame to the opening.
 */
export const SITE = {
  courtRadius: 38,
  courtWallHeight: 5.5,
  courtWallThickness: 1.4,

  gateAngle: 0,
  /** Half the clear width of the gateway passage. */
  gateHalfWidth: 2.8,

  pavilionAngle: Math.PI * 1.25,
  /** Half the angular extent of the pavilion range. */
  pavilionHalfArc: 0.62,
  pavilionDepth: 5.4,
  pavilionHeight: 9.6,
  pavilionSegments: 7,

  pathHalfWidth: 2.6,
  pathLength: 320,
  boundaryHalf: 96,
} as const;

export const COURT_OUTER = SITE.courtRadius + SITE.courtWallThickness;

const TAU = Math.PI * 2;
const norm = (a: number) => ((a % TAU) + TAU) % TAU;

/** Angular half-width of the gateway opening in the court wall. */
export const gateHalfAngle = (): number => Math.asin(SITE.gateHalfWidth / SITE.courtRadius);

/** Arcs [start, end] (polar angle, end > start) where the plain court wall stands. */
export const courtWallArcs = (): [number, number][] => {
  const g = gateHalfAngle();
  const p0 = norm(SITE.pavilionAngle - SITE.pavilionHalfArc);
  const p1 = norm(SITE.pavilionAngle + SITE.pavilionHalfArc);
  return [
    [SITE.gateAngle + g, p0],
    [p1, SITE.gateAngle + TAU - g],
  ];
};

/** True when polar angle `a` falls within one of the plain wall arcs. */
export const onCourtWall = (a: number): boolean => {
  const x = norm(a);
  return courtWallArcs().some(([s, e]) => (x >= s && x <= e) || (x + TAU >= s && x + TAU <= e));
};
