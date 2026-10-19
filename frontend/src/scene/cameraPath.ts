import { WATER_Y, terraceRadius, terraceY, STEPWELL } from './stepwellSpec';

export type Vec3 = [number, number, number];

export interface CameraKey {
  t: number;
  position: Vec3;
  target: Vec3;
}

export interface CameraPose {
  position: Vec3;
  target: Vec3;
}

const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const easeInOut = (k: number) => k * k * (3 - 2 * k);

/**
 * Scroll-progress milestones. Overlay copy and atmosphere are keyed to the
 * same values so the narrative stays in step with the camera.
 */
export const PHASES = {
  cloudsStart: 0.05,
  cloudsOpen: 0.3,
  descentStart: 0.3,
  descentEnd: 0.86,
  water: 1,
} as const;

/** Helix inside the well: x = r cos θ, z = r sin θ, y falls linearly with s. */
export interface HelixParams {
  turns: number;
  theta0: number;
  radiusStart: number;
  radiusEnd: number;
  yStart: number;
  yEnd: number;
}

export const DESCENT_HELIX: HelixParams = {
  turns: 1.3,
  theta0: Math.PI * 0.25,
  radiusStart: 15.5,
  radiusEnd: 2.6,
  yStart: 3,
  yEnd: WATER_Y + 9.5,
};

export const helixPoint = (h: HelixParams, s: number): CameraPose => {
  const theta = h.theta0 + s * h.turns * Math.PI * 2;
  const r = lerp(h.radiusStart, h.radiusEnd, easeInOut(s));
  const y = lerp(h.yStart, h.yEnd, s);
  // Gaze crosses the void towards the far wall, dropping towards the water as we descend.
  const lookTheta = theta + Math.PI * lerp(0.82, 0.95, s);
  const lookR = lerp(7, 1.2, s);
  const lookDrop = lerp(9, 6.5, s);
  return {
    position: [r * Math.cos(theta), y, r * Math.sin(theta)],
    target: [lookR * Math.cos(lookTheta), y - lookDrop, lookR * Math.sin(lookTheta)],
  };
};

/** Builds the full, deterministic set of camera keys from cloud sea to water. */
export const buildCameraKeys = (): CameraKey[] => {
  const h = DESCENT_HELIX;
  const entry = helixPoint(h, 0);
  const entryTheta = h.theta0;
  const c = Math.cos(entryTheta);
  const s = Math.sin(entryTheta);

  const keys: CameraKey[] = [
    // Above the cloud sea, horizon in the upper third.
    { t: 0, position: [c * 150, 112, s * 150], target: [c * 10, 72, s * 10] },
    { t: 0.08, position: [c * 130, 104, s * 130], target: [c * 6, 52, s * 6] },
    // The clouds part; the opening comes into view below.
    { t: 0.17, position: [c * 84, 76, s * 84], target: [0, 0, 0] },
    { t: 0.25, position: [c * 44, 34, s * 44], target: [-c * 4, -12, -s * 4] },
    // Settling over the rim, just before the turn inwards.
    { t: PHASES.descentStart, position: [c * 24, 12, s * 24], target: [-c * 6, -9, -s * 6] },
  ];

  const helixSamples = 16;
  for (let i = 0; i <= helixSamples; i += 1) {
    const k = i / helixSamples;
    const pose = i === 0 ? entry : helixPoint(h, k);
    keys.push({
      t: lerp(PHASES.descentStart + 0.035, PHASES.descentEnd, k),
      position: pose.position,
      target: pose.target,
    });
  }

  // Final approach: the movement slows and the gaze settles on the water.
  const theta = h.theta0 + h.turns * Math.PI * 2 + 0.35;
  // Framed like a look down a carved shaft: far wall above, water below.
  keys.push({
    t: 0.94,
    position: [3.2 * Math.cos(theta), WATER_Y + 7.6, 3.2 * Math.sin(theta)],
    target: [-1.6 * Math.cos(theta), WATER_Y + 0.4, -1.6 * Math.sin(theta)],
  });
  keys.push({
    t: 1,
    position: [2.8 * Math.cos(theta + 0.12), WATER_Y + 6.6, 2.8 * Math.sin(theta + 0.12)],
    target: [-1.4 * Math.cos(theta + 0.12), WATER_Y, -1.4 * Math.sin(theta + 0.12)],
  });

  return keys;
};

/**
 * Cubic Hermite interpolation with non-uniform Catmull-Rom tangents.
 * C1-continuous across keys, so the camera never pauses at a keyframe.
 */
const hermite = (p0: number, p1: number, m0: number, m1: number, u: number) => {
  const u2 = u * u;
  const u3 = u2 * u;
  return (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1;
};

const tangent = (keys: CameraKey[], i: number, pick: (k: CameraKey) => Vec3, axis: number) => {
  const prev = keys[Math.max(0, i - 1)];
  const next = keys[Math.min(keys.length - 1, i + 1)];
  const dt = next.t - prev.t || 1;
  return (pick(next)[axis] - pick(prev)[axis]) / dt;
};

export const sampleCameraPath = (keys: CameraKey[], progress: number): CameraPose => {
  const t = Math.min(1, Math.max(0, progress));
  let i = 0;
  while (i < keys.length - 2 && keys[i + 1].t < t) i += 1;
  const a = keys[i];
  const b = keys[i + 1];
  const span = b.t - a.t || 1;
  const u = Math.min(1, Math.max(0, (t - a.t) / span));

  const interp = (pick: (k: CameraKey) => Vec3): Vec3 =>
    [0, 1, 2].map((axis) =>
      hermite(
        pick(a)[axis],
        pick(b)[axis],
        tangent(keys, i, pick, axis) * span,
        tangent(keys, i + 1, pick, axis) * span,
        u,
      ),
    ) as Vec3;

  return { position: interp((k) => k.position), target: interp((k) => k.target) };
};

/**
 * Debug/test helper: true when the camera stays inside the open void
 * (with a clearance) whenever it is below ground level.
 */
export const isInsideVoid = (pose: CameraPose, clearance = 1.2): boolean => {
  const [x, y, z] = pose.position;
  if (y >= 0) return true;
  // Conservative: use the inner edge of the terrace below the camera, which also
  // clears any gallery columns standing on that terrace.
  const k = Math.min(STEPWELL.terraceCount, Math.floor(-y / STEPWELL.tierHeight) + 1);
  return y > terraceY(STEPWELL.terraceCount) - STEPWELL.shaftDepth && Math.hypot(x, z) < terraceRadius(k) - clearance;
};
