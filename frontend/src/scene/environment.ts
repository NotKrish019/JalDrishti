import * as THREE from 'three';
import { mergeGeometries, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { COURT_OUTER, SITE } from './siteSpec';
import { DESCENT_HELIX, OPENING } from './cameraPath';
import { SKY } from './atmosphere';
import { createGroundTexture, mulberry32 } from './textures';
import { applyDepthShade } from './materials';
import type { StepwellMaterials } from './stepwell';

/**
 * The heritage site around the stepwell, built procedurally in the stepwell's
 * world coordinates. Art direction follows the reference set (jal1–jal4): a
 * walled court, a colonnaded range with arched openings overlooking the well,
 * a gateway and approach, mature shade trees beyond the walls, and dry,
 * lightly grassed ground. Composition is deliberately restrained: the well
 * first, its enclosure second, the landscape third.
 *
 * Draw calls are kept low: architecture is merged per material, vegetation is
 * one instanced mesh per tree form, and tree shadows are instanced soft decals.
 */

export interface EnvironmentOptions {
  materials: StepwellMaterials;
  anisotropy: number;
  textureSize: number;
  shadows: boolean;
  /** Icosahedron detail for foliage: 2 on capable GPUs, 1 elsewhere. */
  foliageDetail: number;
  /** 0..1 multiplier on the number of distant trees and shrubs. */
  density: number;
}

export interface EnvironmentBuild {
  group: THREE.Group;
  dispose: () => void;
}

/** Azimuth of the opening camera, used to skip planting where it can never be seen. */
const OPENING_AZIMUTH = DESCENT_HELIX.theta0 + OPENING.azimuth;

// --- Noise and terrain ---------------------------------------------------------

const hash2 = (x: number, y: number) => {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return s - Math.floor(s);
};

const vnoise = (x: number, y: number) => {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const xf = x - xi;
  const yf = y - yi;
  const u = xf * xf * (3 - 2 * xf);
  const v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi);
  const b = hash2(xi + 1, yi);
  const c = hash2(xi, yi + 1);
  const d = hash2(xi + 1, yi + 1);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
};

const fbm = (x: number, y: number, octaves = 4) => {
  let sum = 0;
  let amp = 0.5;
  let f = 1;
  for (let i = 0; i < octaves; i += 1) {
    sum += amp * vnoise(x * f, y * f);
    f *= 2.03;
    amp *= 0.5;
  }
  return sum;
};

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/** Ground height. Flat around the enclosure and along the approach; gently rolling beyond; low hills far off. */
export const terrainHeight = (x: number, z: number): number => {
  const r = Math.hypot(x, z);
  let h = (fbm(x * 0.011, z * 0.011) - 0.5) * 5.5 * smooth(COURT_OUTER + 10, COURT_OUTER + 48, r);
  h += fbm(x * 0.0035 + 7.1, z * 0.0035 - 3.4, 3) * 46 * smooth(260, 640, r);
  if (x > 0) h *= smooth(SITE.pathHalfWidth + 2, SITE.pathHalfWidth + 13, Math.abs(z));
  return h - 0.03;
};

// --- Geometry helpers ------------------------------------------------------------

/**
 * World-scaled box-projected UVs: each face takes the two axes it spans, in
 * metres divided by the tile size, so stone courses stay the same size on every element.
 */
const projectUVs = (geo: THREE.BufferGeometry, tileW: number, tileH: number) => {
  const pos = geo.attributes.position as THREE.BufferAttribute;
  const nor = geo.attributes.normal as THREE.BufferAttribute;
  const uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i += 1) {
    const ax = Math.abs(nor.getX(i));
    const ay = Math.abs(nor.getY(i));
    const az = Math.abs(nor.getZ(i));
    const x = pos.getX(i);
    const y = pos.getY(i);
    const z = pos.getZ(i);
    let u: number;
    let v: number;
    if (ay >= ax && ay >= az) {
      u = x / tileW;
      v = z / tileW;
    } else if (ax >= az) {
      u = z / tileW;
      v = y / tileH;
    } else {
      u = x / tileW;
      v = y / tileH;
    }
    uv[i * 2] = u;
    uv[i * 2 + 1] = v;
  }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return geo;
};

/** Ensures a geometry is non-indexed with exactly position/normal/uv, so geometries merge cleanly. */
const normalise = (geo: THREE.BufferGeometry) => {
  const g = geo.index ? geo.toNonIndexed() : geo;
  if (g !== geo) geo.dispose();
  Object.keys(g.attributes).forEach((k) => {
    if (k !== 'position' && k !== 'normal' && k !== 'uv') g.deleteAttribute(k);
  });
  return g;
};

const box = (w: number, h: number, d: number, x: number, y: number, z: number) => {
  const g = new THREE.BoxGeometry(w, h, d);
  g.translate(x, y, z);
  return g;
};

/** Pointed (two-centred) arch outline, as used for gateways and arcades in the region. */
const archPath = (cx: number, y0: number, width: number, height: number) => {
  const b = width / 2;
  const rise = b * 1.15;
  const spring = y0 + height - rise;
  const p = new THREE.Path();
  p.moveTo(cx - b, y0);
  p.lineTo(cx - b, spring);
  p.quadraticCurveTo(cx - b, spring + rise * 0.82, cx, spring + rise);
  p.quadraticCurveTo(cx + b, spring + rise * 0.82, cx + b, spring);
  p.lineTo(cx + b, y0);
  p.closePath();
  return p;
};

/** A wall of width × height pierced by arches, extruded to `depth`, front face at z = 0. */
const arcadedWall = (
  width: number,
  height: number,
  depth: number,
  arches: { cx: number; y0: number; w: number; h: number }[],
) => {
  const shape = new THREE.Shape();
  shape.moveTo(-width / 2, 0);
  shape.lineTo(width / 2, 0);
  shape.lineTo(width / 2, height);
  shape.lineTo(-width / 2, height);
  shape.closePath();
  arches.forEach((a) => shape.holes.push(archPath(a.cx, a.y0, a.w, a.h)));
  const geo = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false, curveSegments: 6 });
  geo.translate(0, 0, -depth);
  return geo;
};

/**
 * A chhatri: raised plinth, four pillars, a projecting chajja, a drum and a
 * shallow dome with a finial. Returned in local coordinates, base at y = 0.
 */
const chhatri = (scale: number) => {
  const s = scale;
  const parts: THREE.BufferGeometry[] = [];
  parts.push(box(3.2 * s, 0.45 * s, 3.2 * s, 0, 0.225 * s, 0));
  const inset = 1.25 * s;
  [-1, 1].forEach((ix) =>
    [-1, 1].forEach((iz) => parts.push(box(0.32 * s, 2.2 * s, 0.32 * s, ix * inset, 0.45 * s + 1.1 * s, iz * inset))),
  );
  parts.push(box(3.9 * s, 0.16 * s, 3.9 * s, 0, 2.73 * s, 0));
  parts.push(box(3.0 * s, 0.34 * s, 3.0 * s, 0, 2.98 * s, 0));
  const drum = new THREE.CylinderGeometry(1.25 * s, 1.3 * s, 0.4 * s, 16, 1);
  drum.translate(0, 3.35 * s, 0);
  parts.push(drum);
  const dome = new THREE.SphereGeometry(1.28 * s, 16, 7, 0, Math.PI * 2, 0, Math.PI / 2);
  dome.scale(1, 1.08, 1);
  dome.translate(0, 3.55 * s, 0);
  parts.push(dome);
  const finial = new THREE.ConeGeometry(0.16 * s, 0.9 * s, 8);
  finial.translate(0, 5.05 * s, 0);
  parts.push(finial);
  const knob = new THREE.SphereGeometry(0.22 * s, 8, 6);
  knob.translate(0, 4.75 * s, 0);
  parts.push(knob);
  return parts.map((p) => projectUVs(normalise(p), 8, 4));
};

const place = (geos: THREE.BufferGeometry[], m: THREE.Matrix4) => geos.map((g) => g.applyMatrix4(m));

/**
 * A horizontal slab following an arc: the annulus sector r0..r1 over polar angles a0..a1,
 * from height y to y + thickness. One continuous piece, so a curved range built from
 * straight segments has no joints in its floors, roof or cornice.
 */
const arcSlab = (r0: number, r1: number, a0: number, a1: number, y: number, thickness: number, segments = 32) => {
  const shape = new THREE.Shape();
  // Shape space (x, y) maps to world (x, -z) after the rotation below.
  for (let i = 0; i <= segments; i += 1) {
    const a = a0 + ((a1 - a0) * i) / segments;
    const pt = [r1 * Math.cos(a), -r1 * Math.sin(a)];
    if (i === 0) shape.moveTo(pt[0], pt[1]);
    else shape.lineTo(pt[0], pt[1]);
  }
  for (let i = segments; i >= 0; i -= 1) {
    const a = a0 + ((a1 - a0) * i) / segments;
    shape.lineTo(r0 * Math.cos(a), -r0 * Math.sin(a));
  }
  shape.closePath();
  const geo = new THREE.ExtrudeGeometry(shape, { depth: thickness, bevelEnabled: false, curveSegments: 1 });
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, y, 0);
  return geo;
};

/** Matrix placing local +z towards the court centre at polar angle `a`, radius `r`, height `y`. */
const facingCentre = (a: number, r: number, y = 0) => {
  const m = new THREE.Matrix4().makeRotationY(Math.atan2(-Math.cos(a), -Math.sin(a)));
  m.setPosition(r * Math.cos(a), y, r * Math.sin(a));
  return m;
};

// --- Vegetation -----------------------------------------------------------------

interface TreeForm {
  trunkHeight: number;
  trunkRadius: number;
  /** Horizontal radius of the crown. */
  crown: number;
  blobs: number;
  /** Crown height relative to its width: < 1 spreading (neem, peepal), > 1 columnar. */
  squash: number;
  dark: string;
  light: string;
  /** Extra thin stems around the main trunk: banyan prop roots, multi-stemmed saplings. */
  stems?: number;
  /** Small leaf clusters budding off each clump; break up the round silhouette. */
  satellites?: number;
  /** Icosahedron detail is quality detail minus this (never below 0). */
  detailDrop?: number;
  /** Visible limbs reaching into the crown (default 6). Distant trees need few. */
  limbs?: number;
}

export const TREE_FORMS: TreeForm[] = [
  // 0 · Banyan / peepal: very broad, low, layered crown with prop roots. Chabutras and focal groves.
  { trunkHeight: 4.2, trunkRadius: 0.75, crown: 7.6, blobs: 22, squash: 0.5, dark: '#1d2716', light: '#566a3b', stems: 5, satellites: 1, detailDrop: 1 },
  // 1 · Neem: dense rounded crown, the common tree of the precinct.
  { trunkHeight: 3.0, trunkRadius: 0.38, crown: 4.4, blobs: 11, squash: 0.74, dark: '#202a17', light: '#56653a', satellites: 1, detailDrop: 1, limbs: 4 },
  // 2 · Sapling / young tree: small, open and lighter in tone.
  { trunkHeight: 1.8, trunkRadius: 0.16, crown: 2.2, blobs: 8, squash: 0.85, dark: '#323d22', light: '#76834c', stems: 1, detailDrop: 1 },
  // 3 · Columnar evergreen (ashoka-like): tall and narrow, gives vertical rhythm among the rounded crowns.
  { trunkHeight: 1.6, trunkRadius: 0.24, crown: 1.9, blobs: 12, squash: 2.6, dark: '#18220f', light: '#46562c', detailDrop: 2, limbs: 2 },
  // 4 · Distant canopy tree: few clumps, lowest detail; read only as massed forest through haze.
  { trunkHeight: 2.6, trunkRadius: 0.3, crown: 4.6, blobs: 9, squash: 0.8, dark: '#212b18', light: '#52603a', detailDrop: 2, limbs: 1 },
];

const colourise = (geo: THREE.BufferGeometry, fn: (i: number, out: THREE.Color) => void) => {
  const count = geo.attributes.position.count;
  const col = new Float32Array(count * 3);
  const c = new THREE.Color();
  for (let i = 0; i < count; i += 1) {
    fn(i, c);
    col.set([c.r, c.g, c.b], i * 3);
  }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return geo;
};

/** A tapered stem between two points, coloured as bark. */
const stem = (from: THREE.Vector3, to: THREE.Vector3, r0: number, r1: number, colour: THREE.Color) => {
  const dir = to.clone().sub(from);
  const len = dir.length();
  const g = new THREE.CylinderGeometry(r1, r0, len, 5, 1, true);
  g.translate(0, len / 2, 0);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize()));
  g.translate(from.x, from.y, from.z);
  return colourise(normalise(g), (_, c) => c.copy(colour));
};

/**
 * One tree: a tapered, slightly leaning trunk, limbs reaching into the crown, and a
 * crown built as a lobed shell of displaced leaf clumps (with smaller satellite
 * clusters), coloured darker inside and beneath, lighter on the sunlit top.
 */
const buildTreeGeometry = (form: TreeForm, seed: number, detail: number) => {
  const rand = mulberry32(seed);
  const parts: THREE.BufferGeometry[] = [];
  const bark = new THREE.Color('#4a3e33');
  const barkLight = new THREE.Color('#6b5c4b');
  const dark = new THREE.Color(form.dark);
  const light = new THREE.Color(form.light);
  const crownH = form.crown * form.squash;
  const crownY = form.trunkHeight + crownH * 0.62;

  const sides = (form.limbs ?? 6) <= 2 ? 5 : 8;
  const trunk = new THREE.CylinderGeometry(form.trunkRadius * 0.55, form.trunkRadius, form.trunkHeight + 0.8, sides, sides === 5 ? 2 : 4, true);
  trunk.translate(0, (form.trunkHeight + 0.8) / 2 - 0.3, 0);
  const tp = trunk.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < tp.count; i += 1) {
    const y = tp.getY(i);
    // lean, plus a flared, buttressed base
    const flare = 1 + Math.max(0, 0.6 - y) * 0.9;
    tp.setXYZ(i, tp.getX(i) * flare + Math.sin(y * 0.9 + seed) * 0.07 * y, y, tp.getZ(i) * flare);
  }
  parts.push(colourise(normalise(trunk), (i, c) => c.copy(bark).lerp(barkLight, (i % 5) / 8)));

  for (let k = 0; k < (form.stems ?? 0); k += 1) {
    const a = rand() * Math.PI * 2;
    const d = form.crown * (0.35 + rand() * 0.35);
    const top = new THREE.Vector3(Math.cos(a) * d, form.trunkHeight + 0.4, Math.sin(a) * d);
    parts.push(stem(new THREE.Vector3(top.x * 1.05, -0.2, top.z * 1.05), top, form.trunkRadius * 0.28, form.trunkRadius * 0.2, bark));
  }

  // Clumps sit mostly in an outer shell, as foliage does on a real crown.
  const blobs: { c: THREE.Vector3; r: number }[] = [];
  for (let b = 0; b < form.blobs; b += 1) {
    const ang = rand() * Math.PI * 2;
    const rad = (0.35 + 0.65 * Math.sqrt(rand())) * form.crown * 0.7;
    const h = (rand() - 0.4) * crownH * 0.75;
    // Taper towards the top so the crown has a dome, not a drum.
    const taper = 1 - Math.max(0, h / (crownH * 0.5)) * 0.45;
    blobs.push({
      c: new THREE.Vector3(Math.cos(ang) * rad * taper, crownY + h, Math.sin(ang) * rad * taper),
      r: form.crown * (0.26 + rand() * 0.16) * Math.min(1, 0.7 + form.squash * 0.25),
    });
  }

  // Limbs from the trunk head towards several clumps.
  const head = new THREE.Vector3(0, form.trunkHeight, 0);
  blobs.slice(0, Math.min(form.limbs ?? 6, form.blobs)).forEach(({ c }) => {
    const to = head.clone().lerp(c, 0.82);
    parts.push(stem(head.clone().setY(head.y - 0.5), to, form.trunkRadius * 0.42, form.trunkRadius * 0.16, bark));
  });

  const centre = new THREE.Vector3(0, crownY, 0);
  const extent = Math.max(form.crown, crownH * 0.6);
  const clump = (c: THREE.Vector3, r: number, bi: number, det: number, tone: number) => {
    let g: THREE.BufferGeometry = new THREE.IcosahedronGeometry(r, det);
    g.deleteAttribute('uv');
    g.deleteAttribute('normal');
    g = mergeVertices(g);
    const p = g.attributes.position as THREE.BufferAttribute;
    const v = new THREE.Vector3();
    const bump = new Float32Array(p.count);
    for (let i = 0; i < p.count; i += 1) {
      v.fromBufferAttribute(p, i);
      const n = v.clone().normalize();
      // Two scales of lumpiness: leaf clusters on top of the clump's overall form.
      const coarse = vnoise(n.x * 2.6 + n.y * 1.7 + bi * 3.1 + seed, n.z * 2.6 - n.y * 1.3);
      const fine = vnoise(n.x * 7.3 + bi * 1.9, n.z * 7.3 + n.y * 5.1 + seed);
      const k = 0.7 + 0.34 * coarse + 0.24 * fine;
      v.multiplyScalar(k);
      v.y *= 0.82;
      v.add(c);
      p.setXYZ(i, v.x, v.y, v.z);
      bump[i] = k;
    }
    g.computeVertexNormals();
    colourise(g, (i, col) => {
      v.fromBufferAttribute(p, i);
      const ny = (g.attributes.normal as THREE.BufferAttribute).getY(i);
      // Inner and underside foliage is in shade; the sun-facing top is lighter;
      // hollows between leaf clusters are darker still.
      const outer = Math.min(1, v.distanceTo(centre) / extent);
      const lit = THREE.MathUtils.clamp(0.1 + ny * 0.42 + outer * 0.42, 0, 1);
      const hollow = THREE.MathUtils.clamp((bump[i] - 0.8) * 2.4, -0.4, 0.3);
      col.copy(dark).lerp(light, THREE.MathUtils.clamp(lit + hollow, 0, 1)).multiplyScalar(tone);
    });
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(p.count * 2), 2));
    parts.push(g.toNonIndexed());
    g.dispose();
  };
  blobs.forEach(({ c, r }, bi) => {
    const tone = 0.82 + rand() * 0.34;
    clump(c, r, bi, detail, tone);
    for (let k = 0; k < (form.satellites ?? 0); k += 1) {
      const out = c.clone().sub(centre).setY(0).normalize();
      const off = new THREE.Vector3(out.x + (rand() - 0.5), rand() * 0.6 - 0.1, out.z + (rand() - 0.5)).normalize();
      clump(c.clone().addScaledVector(off, r * 0.85), r * (0.42 + rand() * 0.15), bi + 50 + k, Math.max(0, detail - 1), tone * 1.04);
    }
  });

  const merged = mergeGeometries(parts, false);
  parts.forEach((g) => g.dispose());
  return merged;
};

/** Low ground-cover clump: grasses and herbs, flattened and a little irregular. */
const buildGroundCoverGeometry = () => {
  let g: THREE.BufferGeometry = new THREE.IcosahedronGeometry(0.5, 0);
  g.deleteAttribute('uv');
  g.deleteAttribute('normal');
  g = mergeVertices(g);
  const p = g.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < p.count; i += 1) {
    const k = 0.75 + 0.5 * hash2(p.getX(i) * 4.1, p.getZ(i) * 3.3 + p.getY(i));
    p.setXYZ(i, p.getX(i) * k * 1.25, Math.max(-0.1, p.getY(i)) * k * 0.45 + 0.04, p.getZ(i) * k * 1.25);
  }
  g.computeVertexNormals();
  const dark = new THREE.Color('#36412a');
  const light = new THREE.Color('#6b7848');
  colourise(g, (i, col) => {
    const ny = (g.attributes.normal as THREE.BufferAttribute).getY(i);
    col.copy(dark).lerp(light, THREE.MathUtils.clamp(0.3 + ny * 0.6, 0, 1));
  });
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(p.count * 2), 2));
  const out = g.toNonIndexed();
  g.dispose();
  return out;
};

const buildShrubGeometry = (detail: number) => {
  const parts: THREE.BufferGeometry[] = [];
  const dark = new THREE.Color('#353d26');
  const light = new THREE.Color('#6f7650');
  [
    [0, 0.55, 0, 0.9],
    [0.7, 0.45, 0.2, 0.7],
    [-0.5, 0.42, -0.4, 0.65],
  ].forEach(([x, y, z, r], bi) => {
    let g: THREE.BufferGeometry = new THREE.IcosahedronGeometry(r, Math.max(0, detail - 2));
    g.deleteAttribute('uv');
    g.deleteAttribute('normal');
    g = mergeVertices(g);
    const p = g.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < p.count; i += 1) {
      const k = 0.8 + 0.3 * hash2(p.getX(i) * 3.1 + bi, p.getZ(i) * 3.7 + p.getY(i));
      p.setXYZ(i, p.getX(i) * k + x, p.getY(i) * k * 0.75 + y, p.getZ(i) * k + z);
    }
    g.computeVertexNormals();
    colourise(g, (i, col) => {
      const ny = (g.attributes.normal as THREE.BufferAttribute).getY(i);
      col.copy(dark).lerp(light, THREE.MathUtils.clamp(0.35 + ny * 0.5, 0, 1));
    });
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(p.count * 2), 2));
    parts.push(g.toNonIndexed());
    g.dispose();
  });
  const merged = mergeGeometries(parts, false);
  parts.forEach((g) => g.dispose());
  return merged;
};

/** Soft radial decal used for tree shadows and contact darkening. */
const createBlobTexture = () => {
  const size = 128;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('2D canvas unavailable');
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.45, 'rgba(255,255,255,0.75)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
};

// --- Build ------------------------------------------------------------------------

export const buildEnvironment = ({
  materials,
  anisotropy,
  textureSize,
  shadows,
  foliageDetail,
  density,
}: EnvironmentOptions): EnvironmentBuild => {
  const group = new THREE.Group();
  group.name = 'heritage-site';
  const disposables: { dispose: () => void }[] = [];
  const track = <T extends { dispose: () => void }>(o: T) => {
    disposables.push(o);
    return o;
  };
  const rand = mulberry32(4021);

  const addMerged = (geos: THREE.BufferGeometry[], material: THREE.Material, name: string, cast = shadows) => {
    if (!geos.length) return;
    const merged = track(mergeGeometries(geos, false));
    geos.forEach((g) => g.dispose());
    const mesh = new THREE.Mesh(merged, material);
    mesh.name = name;
    mesh.castShadow = cast;
    mesh.receiveShadow = shadows;
    group.add(mesh);
  };

  const wallGeos: THREE.BufferGeometry[] = [];
  const trimGeos: THREE.BufferGeometry[] = [];
  const pavingGeos: THREE.BufferGeometry[] = [];
  const shadeGeos: THREE.BufferGeometry[] = [];

  // Recessed interiors read as deep shade behind the arches.
  const shadeMat = track(
    applyDepthShade(
      new THREE.MeshStandardMaterial({
        map: materials.wall.map,
        color: '#7a6a58',
        roughness: 0.95,
        metalness: 0,
        side: THREE.DoubleSide,
      }),
    ),
  );

  // --- Gateway (pol) on the approach axis ----------------------------------------
  {
    const width = 12.4;
    const height = 10.2;
    const depth = 3.4;
    const opening = SITE.gateHalfWidth * 2;
    const r = SITE.courtRadius + SITE.courtWallThickness / 2;
    const m = facingCentre(SITE.gateAngle, r);
    const local: THREE.BufferGeometry[] = [];
    const gate = arcadedWall(width, height, depth, [{ cx: 0, y0: 0, w: opening, h: 7.4 }]);
    gate.translate(0, 0, depth / 2);
    local.push(projectUVs(normalise(gate), 8, 4));
    // Flanking blind niches give the piers depth and scale.
    [-1, 1].forEach((side) => {
      const niche = arcadedWall(1.6, 3.6, 0.4, [{ cx: 0, y0: 0.2, w: 1.0, h: 3.2 }]);
      [depth / 2 + 0.4, -depth / 2].forEach((z) => {
        const n = niche.clone();
        n.translate(side * 4.4, 1.0, z);
        local.push(projectUVs(normalise(n), 8, 4));
      });
      niche.dispose();
    });
    place(local, m).forEach((g) => wallGeos.push(g));

    const trims = [
      box(width + 0.9, 0.26, depth + 0.9, 0, 8.7, 0),
      box(width + 0.4, 0.9, depth + 0.2, 0, height + 0.45, 0),
    ].map((g) => projectUVs(normalise(g), 8, 4));
    // Merlons along the parapet
    for (let i = 0; i < 9; i += 1) {
      const x = -width / 2 + 0.6 + i * ((width - 1.2) / 8);
      [depth / 2, -depth / 2].forEach((z) => trims.push(projectUVs(normalise(box(0.5, 0.6, 0.3, x, height + 1.2, z)), 8, 4)));
    }
    [-4.3, 4.3].forEach((x) => {
      const c = chhatri(0.78);
      c.forEach((g) => g.translate(x, height + 0.9, 0));
      trims.push(...c);
    });
    place(trims, m).forEach((g) => trimGeos.push(g));

    // Sits 5 cm proud of the forecourt paving it overlaps, so the two never z-fight.
    const floor = projectUVs(normalise(box(opening, 0.16, depth, 0, 0.02, 0)), 4, 4);
    place([floor], m).forEach((g) => pavingGeos.push(g));
  }

  // --- Arcaded pavilion range on the far side --------------------------------------
  {
    const { pavilionAngle, pavilionHalfArc, pavilionSegments: n, pavilionDepth: D, pavilionHeight: H } = SITE;
    const Rf = SITE.courtRadius - 0.3;
    const step = (pavilionHalfArc * 2) / n;
    const W = 2 * Rf * Math.sin(step / 2) + 0.05;
    const a0 = pavilionAngle - pavilionHalfArc;
    const a1 = pavilionAngle + pavilionHalfArc;
    /** Exact chord of one segment at radius r: neighbouring pieces meet without gaps or overlaps. */
    const chord = (r: number) => 2 * r * Math.sin(step / 2);
    for (let k = 0; k < n; k += 1) {
      const a = a0 + step * (k + 0.5);
      const m = facingCentre(a, Rf);
      const front: THREE.BufferGeometry[] = [];
      const facade = arcadedWall(W, H, 0.9, [
        { cx: -W / 4, y0: 0, w: 2.3, h: 3.7 },
        { cx: W / 4, y0: 0, w: 2.3, h: 3.7 },
        { cx: -W / 4, y0: 5.3, w: 1.5, h: 2.5 },
        { cx: W / 4, y0: 5.3, w: 1.5, h: 2.5 },
      ]);
      front.push(projectUVs(normalise(facade), 8, 4));
      // Parapet and merlons; local +z points at the court, so the parapet sits at radius Rf - 0.15.
      const pw = chord(Rf - 0.15);
      const trims: THREE.BufferGeometry[] = [box(pw, 0.95, 0.32, 0, H + 0.68, 0.15)];
      for (let i = 0; i < 6; i += 1) trims.push(box(0.42, 0.5, 0.34, -pw / 2 + 0.55 + i * ((pw - 1.1) / 5), H + 1.4, 0.15));
      if (k === 0 || k === n - 1 || k === (n - 1) / 2) {
        const c = chhatri(k === (n - 1) / 2 ? 1.05 : 0.85);
        c.forEach((g) => g.translate(0, H + 0.2, -D / 2));
        trims.push(...c);
      }
      const back = [box(chord(Rf + D), H, 0.8, 0, H / 2, -D)];
      // End walls close the range. They stand 3 cm proud of the facade's end face and their
      // front is recessed 5 cm behind the facade front, so no face of the two is coplanar
      // (coplanar faces z-fight and shimmer as the camera drifts).
      const endWall = (side: number) =>
        box(0.83, H, D - 0.05, side * (W / 2 - 0.4 + 0.015), H / 2, -D / 2 - 0.025);
      if (k === 0) back.push(endWall(-1));
      if (k === n - 1) back.push(endWall(1));
      place(front, m).forEach((g) => wallGeos.push(g));
      place(trims.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => trimGeos.push(g));
      place(back.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => shadeGeos.push(g));
    }
    // Floors, eave, cornice and roof as continuous curved slabs over the whole range.
    // Their top faces sit at distinct heights, so no two surfaces are coplanar.
    shadeGeos.push(projectUVs(normalise(arcSlab(Rf, Rf + D, a0, a1, -0.05, 0.11)), 4, 4));
    shadeGeos.push(projectUVs(normalise(arcSlab(Rf + 0.4, Rf + D, a0, a1, 4.525, 0.35)), 8, 4));
    trimGeos.push(projectUVs(normalise(arcSlab(Rf - 1.0, Rf + 0.1, a0, a1, 4.54, 0.16)), 8, 4));
    wallGeos.push(projectUVs(normalise(arcSlab(Rf - 0.2, Rf + D + 0.4, a0, a1, H - 0.42, 0.44)), 8, 4));
    trimGeos.push(projectUVs(normalise(arcSlab(Rf - 1.0, Rf + 0.3, a0, a1, H - 0.11, 0.32)), 8, 4));

    // Close the hollow ends of the plain court wall where it meets the range.
    [a0, a1].forEach((a) => {
      const cap = box(0.4, SITE.courtWallHeight, SITE.courtWallThickness, 0, SITE.courtWallHeight / 2, 0);
      place([projectUVs(normalise(cap), 8, 4)], facingCentre(a, SITE.courtRadius + SITE.courtWallThickness / 2)).forEach((g) =>
        wallGeos.push(g),
      );
    });
  }

  // --- Approach: forecourt, paved path and kerbs ---------------------------------------
  {
    const start = COURT_OUTER - 0.4;
    const forecourt = projectUVs(normalise(box(14, 0.1, 18, start + 7, 0.0, 0)), 4, 4);
    pavingGeos.push(forecourt);
    const len = SITE.pathLength;
    const w = SITE.pathHalfWidth;
    pavingGeos.push(projectUVs(normalise(box(len, 0.1, w * 2, start + 14 + len / 2, 0.0, 0)), 4, 4));
    [-1, 1].forEach((side) => {
      trimGeos.push(projectUVs(normalise(box(len, 0.22, 0.32, start + 14 + len / 2, 0.06, side * (w + 0.12))), 8, 4));
      trimGeos.push(projectUVs(normalise(box(14, 0.22, 0.32, start + 7, 0.06, side * 9.1)), 8, 4));
    });
  }

  // --- Rubble boundary wall, partly ruined ----------------------------------------------
  {
    const half = SITE.boundaryHalf;
    const segLen = 5.5;
    const sides: [number, number, number, number][] = [
      [-half, -half, half, -half],
      [half, -half, half, half],
      [half, half, -half, half],
      [-half, half, -half, -half],
    ];
    sides.forEach(([x0, z0, x1, z1]) => {
      const len = Math.hypot(x1 - x0, z1 - z0);
      const count = Math.floor(len / segLen);
      for (let i = 0; i < count; i += 1) {
        const t = (i + 0.5) / count;
        const x = x0 + (x1 - x0) * t;
        const z = z0 + (z1 - z0) * t;
        // Gap where the approach path passes through, and a few collapsed stretches.
        if (x > half - 1 && Math.abs(z) < 10) continue;
        if (hash2(i * 1.7, x0 + z0) > 0.86) continue;
        const ruined = hash2(i * 3.3, z1 - x1) > 0.7;
        const h = ruined ? 0.35 + rand() * 0.4 : 1.0 + rand() * 0.45;
        const base = terrainHeight(x, z);
        const along = x1 !== x0;
        const g = box(along ? segLen + 0.05 : 0.9, h + 0.6, along ? 0.9 : segLen + 0.05, x, base + (h + 0.6) / 2 - 0.6, z);
        wallGeos.push(projectUVs(normalise(g), 8, 4));
      }
    });
  }

  // --- The wider precinct: ruins, pavilions and old paths among the trees --------------------
  // Generic forms in the same sandstone language as the stepwell, deliberately not modelled
  // on any particular site. Ruins use a weathered variant of the wall material.
  const ruinGeos: THREE.BufferGeometry[] = [];
  const facingCentreAt = (x: number, z: number, y: number) => facingCentre(Math.atan2(z, x), Math.hypot(x, z), y);
  const polarXZ = (a: number, r: number) => ({ x: r * Math.cos(a), z: r * Math.sin(a) });
  /** Areas kept free of trees: clearings around structures and the line of every path. */
  const keepOut: { x: number; z: number; r: number }[] = [];
  /** Spots for fallen blocks and overgrowth at the foot of ruins. */
  const rubbleAt: { x: number; z: number; r: number }[] = [];

  // Cenotaph group on a raised platform.
  {
    const { x, z } = polarXZ(Math.PI * 0.97, 128);
    const m = facingCentreAt(x, z, terrainHeight(x, z) - 0.4);
    const plinth = [box(19, 2.0, 9, 0, 1.0, 0), box(6, 0.5, 2.2, 0, 0.25, 5.4), box(6, 1.0, 1.1, 0, 0.5, 4.9)];
    place(plinth.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => ruinGeos.push(g));
    [-6, 0, 6].forEach((dx, i) => {
      const c = chhatri(i === 1 ? 1.35 : 1.1);
      c.forEach((g) => g.translate(dx, 2.0, 0));
      place(c, m).forEach((g) => trimGeos.push(g));
    });
    keepOut.push({ x, z, r: 14 });
    rubbleAt.push({ x, z, r: 12 });
  }

  /** A pillared pavilion (baradari) on a plinth, partly fallen: missing columns and a broken roof. */
  const ruinedPavilion = (x: number, z: number, cols: number, rows: number, intact: number, seed: number) => {
    const rnd = mulberry32(seed);
    const bay = 2.6;
    const w = (cols - 1) * bay + 2.4;
    const d = (rows - 1) * bay + 2.4;
    const m = facingCentreAt(x, z, terrainHeight(x, z) - 0.2);
    const parts: THREE.BufferGeometry[] = [box(w + 1.6, 1.0, d + 1.6, 0, 0.5, 0), box(w + 0.6, 0.3, d + 0.6, 0, 1.15, 0)];
    parts.push(box(3, 0.5, 1.2, 0, 0.25, d / 2 + 1.4));
    for (let i = 0; i < cols; i += 1) {
      for (let j = 0; j < rows; j += 1) {
        const cx = -w / 2 + 1.2 + i * bay;
        const cz = -d / 2 + 1.2 + j * bay;
        // Columns under the surviving roof stand; the rest have fallen to stumps.
        const underRoof = i < Math.ceil(cols * 0.6);
        const standing = underRoof || rnd() < intact * 0.4;
        const h = standing ? 3.4 : 0.4 + rnd() * 1.4;
        parts.push(box(0.62, 0.3, 0.62, cx, 1.45, cz));
        parts.push(box(0.42, h, 0.42, cx, 1.3 + h / 2, cz));
        if (standing) parts.push(box(0.7, 0.28, 0.7, cx, 1.3 + h + 0.14, cz));
      }
    }
    // The roof survives over only part of the plan, with its chajja and parapet.
    const span = (Math.ceil(cols * 0.6) - 1) * bay + 2.4;
    const cxRoof = -w / 2 + span / 2;
    parts.push(box(span + 0.8, 0.42, d + 0.8, cxRoof, 4.99, 0));
    parts.push(box(span + 1.4, 0.14, 0.9, cxRoof, 4.75, d / 2 + 0.75));
    parts.push(box(span + 0.8, 0.6, 0.3, cxRoof, 5.5, d / 2 + 0.25));
    place(parts.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => ruinGeos.push(g));
    keepOut.push({ x, z, r: Math.max(w, d) / 2 + 5 });
    rubbleAt.push({ x, z, r: Math.max(w, d) / 2 + 3 });
  };

  /** A broken length of old precinct wall: stepped, uneven top where courses have fallen. */
  const wallFragment = (a: number, r: number, length: number, peak: number, seed: number) => {
    const rnd = mulberry32(seed);
    const { x, z } = polarXZ(a, r);
    const m = facingCentreAt(x, z, terrainHeight(x, z) - 0.3);
    const parts: THREE.BufferGeometry[] = [];
    const segs = Math.max(3, Math.round(length / 1.6));
    for (let i = 0; i < segs; i += 1) {
      const t = (i + 0.5) / segs;
      // Highest near one end, crumbling away towards the other.
      const h = Math.max(0.35, peak * (1 - Math.abs(t - 0.3) * 1.4) * (0.75 + rnd() * 0.35));
      parts.push(box(length / segs + 0.02, h, 0.95, -length / 2 + t * length, h / 2, 0));
    }
    parts.push(box(length + 0.4, 0.3, 1.25, 0, 0.15, 0));
    place(parts.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => ruinGeos.push(g));
    keepOut.push({ x, z, r: length / 2 + 2 });
    rubbleAt.push({ x, z, r: length / 2 + 1.5 });
  };

  const pavA = polarXZ(-1.45, 72);
  ruinedPavilion(pavA.x, pavA.z, 4, 3, 0.7, 211);

  // A small four-pillared stone canopy, intact, on a stepped plinth.
  const pavB = polarXZ(2.6, 66);
  {
    const m = facingCentreAt(pavB.x, pavB.z, terrainHeight(pavB.x, pavB.z) - 0.2);
    const parts = [box(7.5, 0.9, 7.5, 0, 0.45, 0), box(6.4, 0.4, 6.4, 0, 1.1, 0), box(2.8, 0.45, 1.2, 0, 0.22, 4.3)];
    place(parts.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => ruinGeos.push(g));
    const c = chhatri(1.55);
    c.forEach((g) => g.translate(0, 1.3, 0));
    place(c, m).forEach((g) => trimGeos.push(g));
    keepOut.push({ x: pavB.x, z: pavB.z, r: 10 });
    rubbleAt.push({ x: pavB.x, z: pavB.z, r: 6 });
  }

  // A colonnade remnant beside the approach: a row of column stumps, two still carrying a lintel.
  {
    const from = polarXZ(-0.6, 54);
    const to = polarXZ(-0.86, 62);
    const n = 8;
    const rnd = mulberry32(331);
    for (let i = 0; i < n; i += 1) {
      const t = i / (n - 1);
      const x = from.x + (to.x - from.x) * t;
      const z = from.z + (to.z - from.z) * t;
      const h = i === 2 || i === 3 ? 3.6 : 0.5 + rnd() * 1.6;
      const y = terrainHeight(x, z);
      ruinGeos.push(projectUVs(normalise(box(0.9, 0.35, 0.9, x, y + 0.15, z)), 8, 4));
      ruinGeos.push(projectUVs(normalise(box(0.5, h, 0.5, x, y + 0.3 + h / 2, z)), 8, 4));
    }
    const lt = 2.5 / (n - 1);
    const lx = from.x + (to.x - from.x) * lt;
    const lz = from.z + (to.z - from.z) * lt;
    const lintel = box(Math.hypot(to.x - from.x, to.z - from.z) / (n - 1) + 0.9, 0.5, 0.6, 0, 0, 0);
    lintel.rotateY(-Math.atan2(to.z - from.z, to.x - from.x));
    lintel.translate(lx, terrainHeight(lx, lz) + 4.15, lz);
    ruinGeos.push(projectUVs(normalise(lintel), 8, 4));
    keepOut.push({ x: (from.x + to.x) / 2, z: (from.z + to.z) / 2, r: 9 });
    rubbleAt.push({ x: (from.x + to.x) / 2, z: (from.z + to.z) / 2, r: 6 });
  }

  // Fragments of an older inner precinct wall, broken at intervals and half lost in growth.
  [
    [0.42, 60, 10, 1.6],
    [0.95, 64, 13, 2.3],
    [1.55, 60, 9, 1.2],
    [2.15, 61, 12, 2.0],
    [3.05, 63, 14, 2.4],
    [4.55, 60, 11, 1.8],
    [5.25, 62, 9, 1.4],
  ].forEach(([a, r, len, h], i) => wallFragment(a, r, len, h, 400 + i));

  // A ruined arched gateway where an old path leaves the precinct; its parapet has partly fallen.
  const arch = polarXZ(3.55, 88);
  {
    const m = facingCentreAt(arch.x, arch.z, terrainHeight(arch.x, arch.z) - 0.3);
    const gate = arcadedWall(7.5, 6.8, 2.2, [{ cx: 0, y0: 0, w: 3.4, h: 5.2 }]);
    gate.translate(0, 0, 1.1);
    const parts = [projectUVs(normalise(gate), 8, 4), projectUVs(normalise(box(3.2, 1.2, 2.4, -2.1, 7.4, 0)), 8, 4)];
    place(parts, m).forEach((g) => ruinGeos.push(g));
    keepOut.push({ x: arch.x, z: arch.z, r: 7 });
    rubbleAt.push({ x: arch.x, z: arch.z, r: 5 });
  }

  // Background: a pavilion on a terraced mound and a long wall rising above the far canopy.
  {
    const { x, z } = polarXZ(3.95, 185);
    const m = facingCentreAt(x, z, terrainHeight(x, z) - 0.5);
    const parts = [box(26, 4, 20, 0, 2, 0), box(19, 3, 14, 0, 5.5, 0)];
    place(parts.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => ruinGeos.push(g));
    const c = chhatri(2.3);
    c.forEach((g) => g.translate(0, 7, 0));
    place(c, m).forEach((g) => trimGeos.push(g));
    keepOut.push({ x, z, r: 16 });
  }
  {
    const { x, z } = polarXZ(4.4, 215);
    const m = facingCentreAt(x, z, terrainHeight(x, z) - 0.5);
    const parts: THREE.BufferGeometry[] = [box(60, 7, 2.4, 0, 3.5, 0)];
    for (let i = 0; i < 16; i += 1) if (i % 5 !== 3) parts.push(box(1.6, 1.4, 2.6, -28 + i * 3.73, 7.7, 0));
    parts.push(box(6, 11, 6, -30, 5.5, 0), box(6, 9, 6, 30, 4.5, 0));
    place(parts.map((g) => projectUVs(normalise(g), 8, 4)), m).forEach((g) => ruinGeos.push(g));
    keepOut.push({ x, z, r: 6 });
  }

  // --- Old stone paths: two-flag-wide tracks, partly lost under grass ---------------------------
  type Slab = { x: number; z: number; y: number; rot: number; w: number; d: number };
  const slabs: Slab[] = [];
  type P2 = [number, number];
  const bezier = (p0: P2, p1: P2, p2: P2, t: number): P2 => [
    (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
    (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1],
  ];
  const lay = (p0: P2, p1: P2, p2: P2, seed: number) => {
    const rnd = mulberry32(seed);
    const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
    const n = Math.round(len / 0.95);
    for (let i = 0; i <= n; i += 1) {
      const t = i / n;
      const [x, z] = bezier(p0, p1, p2, t);
      const [x2, z2] = bezier(p0, p1, p2, Math.min(1, t + 0.01));
      const dir = Math.atan2(z2 - z, x2 - x);
      if (i % 3 === 0) keepOut.push({ x, z, r: 3.4 });
      [-0.48, 0.48].forEach((side) => {
        // Gaps where turf has grown over the flags.
        if (rnd() < 0.18 + 0.35 * fbm(x * 0.08 + side, z * 0.08)) return;
        const sx = x - Math.sin(dir) * side + (rnd() - 0.5) * 0.12;
        const sz = z + Math.cos(dir) * side + (rnd() - 0.5) * 0.12;
        slabs.push({ x: sx, z: sz, y: terrainHeight(sx, sz) + 0.04, rot: -dir + (rnd() - 0.5) * 0.12, w: 0.86, d: 0.88 + rnd() * 0.12 });
      });
    }
  };
  const onRing = (a: number, r: number): P2 => [r * Math.cos(a), r * Math.sin(a)];
  // Around the enclosure's left flank, in short arcs, then out to the stone canopy. It starts
  // beyond the near side so it never reads as a ring drawn across the foreground.
  {
    const r = COURT_OUTER + 6.5;
    const a0 = 1.2;
    const a1 = 2.45;
    const steps = 3;
    for (let k = 0; k < steps; k += 1) {
      const t0 = a0 + ((a1 - a0) * k) / steps;
      const t1 = a0 + ((a1 - a0) * (k + 1)) / steps;
      lay(onRing(t0, r), onRing((t0 + t1) / 2, r / Math.cos((t1 - t0) / 2)), onRing(t1, r), 500 + k);
    }
    lay(onRing(a1, r), onRing(2.55, 56), [pavB.x, pavB.z], 510);
  }
  // From the forecourt past the colonnade to the ruined pavilion.
  lay([COURT_OUTER + 10, -9.5], [52, -40], [pavA.x + 6, pavA.z + 4], 520);
  // From the stone canopy out through the ruined arch.
  lay([pavB.x - 3, pavB.z - 3], [-74, -6], [arch.x + 2, arch.z + 2], 530);

  // --- Vegetation placement ------------------------------------------------------------------
  type Tree = { x: number; z: number; form: number; scale: number; rot: number; lift?: number };
  const trees: Tree[] = [];
  // Spatial hash so spacing checks stay cheap with several hundred trees.
  const CELL = 8;
  const grid = new Map<string, Tree[]>();
  const nearby = (x: number, z: number, reach: number, fn: (t: Tree) => void) => {
    const span = Math.ceil(reach / CELL);
    const cx = Math.floor(x / CELL);
    const cz = Math.floor(z / CELL);
    for (let i = -span; i <= span; i += 1) for (let j = -span; j <= span; j += 1) grid.get(`${cx + i},${cz + j}`)?.forEach(fn);
  };
  const pushTree = (t: Tree) => {
    trees.push(t);
    const k = `${Math.floor(t.x / CELL)},${Math.floor(t.z / CELL)}`;
    const cell = grid.get(k);
    if (cell) cell.push(t);
    else grid.set(k, [t]);
  };
  const clear = (x: number, z: number, margin: number, spacing: number) => {
    const r = Math.hypot(x, z);
    if (r < COURT_OUTER + margin) return false;
    // keep the approach path and its forecourt open
    if (x > 0 && Math.abs(z) < SITE.pathHalfWidth + 3 + margin * 0.5) return false;
    if (x > COURT_OUTER - 2 && x < COURT_OUTER + 16 && Math.abs(z) < 11) return false;
    // keep the boundary line clear
    const half = SITE.boundaryHalf;
    if (Math.abs(Math.abs(x) - half) < 2.5 && Math.abs(z) < half + 2) return false;
    if (Math.abs(Math.abs(z) - half) < 2.5 && Math.abs(x) < half + 2) return false;
    if (r < 260 && keepOut.some((k) => Math.hypot(k.x - x, k.z - z) < k.r)) return false;
    let ok = true;
    nearby(x, z, spacing, (t) => {
      if (ok && Math.hypot(t.x - x, t.z - z) < spacing) ok = false;
    });
    return ok;
  };
  const addTree = (x: number, z: number, form: number, scale: number, margin = 2) => {
    // Crowns may overlap a little: a continuous canopy, not separate lollipops.
    const spacing = TREE_FORMS[form].crown * scale * (form === 4 ? 0.78 : form === 0 ? 1.1 : 0.85);
    if (!clear(x, z, margin, spacing)) return false;
    pushTree({ x, z, form, scale, rot: rand() * Math.PI * 2 });
    return true;
  };

  // Chabutras: shade trees on raised masonry platforms beside the approach.
  const chabutras = [
    { x: 74, z: -15.5 },
    { x: 128, z: 16 },
  ];
  chabutras.forEach(({ x, z }) => {
    pushTree({ x, z, form: 0, scale: 0.95, rot: rand() * 6.28, lift: 0.95 });
    const base = terrainHeight(x, z);
    const plinth = new THREE.CylinderGeometry(3.6, 3.8, 1.2, 28, 1);
    plinth.translate(x, base + 0.3, z);
    wallGeos.push(projectUVs(normalise(plinth), 8, 4));
    const cap = new THREE.CylinderGeometry(3.75, 3.75, 0.14, 28, 1);
    cap.translate(x, base + 0.95, z);
    trimGeos.push(projectUVs(normalise(cap), 4, 4));
  });

  // A few shade trees inside the court, each on a low square platform, kept
  // clear of the sightline from the opening camera to the well.
  [Math.PI * 0.62, Math.PI * 0.86, Math.PI * 1.62, Math.PI * 1.86].forEach((a) => {
    const r = 32.5;
    const x = r * Math.cos(a);
    const z = r * Math.sin(a);
    pushTree({ x, z, form: 1, scale: 0.95 + rand() * 0.15, rot: rand() * 6.28, lift: 0.5 });
    const plinth = box(3.0, 0.5, 3.0, 0, 0.25, 0);
    plinth.rotateY(-a);
    plinth.translate(x, 0, z);
    trimGeos.push(projectUVs(normalise(plinth), 8, 4));
  });

  // Avenue along the approach: neem, with the occasional columnar tree.
  for (let x = COURT_OUTER + 20; x < 260; x += 11 + rand() * 3) {
    [-1, 1].forEach((side) =>
      addTree(x + rand() * 2, side * (SITE.pathHalfWidth + 5.5 + rand() * 1.5), rand() > 0.8 ? 3 : 1, 0.9 + rand() * 0.25, -1),
    );
  }

  // Old banyans anchor the precinct: large, dominant individuals with their own space.
  [
    [2.2, 76],
    [3.3, 72],
    [-1.0, 88],
    [1.3, 84],
    [4.95, 78],
  ].forEach(([a, r]) => {
    const { x, z } = polarXZ(a, r);
    addTree(x, z, 0, 0.95 + rand() * 0.25, 4);
  });

  // Framing groves in the foreground corners of the opening view. They sit well below the
  // camera's line of sight to the opening (~28 m high at this distance) and thicken the near ground.
  const frame = (a0: number, a1: number, r0: number, r1: number, count: number) => {
    let placed = 0;
    for (let tries = 0; tries < count * 20 && placed < count; tries += 1) {
      const a = a0 + rand() * (a1 - a0);
      const r = r0 + rand() * (r1 - r0);
      const form = [1, 1, 1, 2, 3, 0][Math.floor(rand() * 6)];
      if (addTree(r * Math.cos(a), r * Math.sin(a), form, 0.85 + rand() * 0.35, 9)) placed += 1;
    }
  };
  frame(OPENING_AZIMUTH + 0.35, OPENING_AZIMUTH + 1.2, 52, 96, 34);
  frame(OPENING_AZIMUTH - 1.15, OPENING_AZIMUTH - 0.5, 52, 96, 26);
  // Directly in front of the camera, beyond a glade below the enclosure: tree tops at this
  // range still project below the base of the court wall, so the enclosure stays fully visible.
  frame(OPENING_AZIMUTH - 0.4, OPENING_AZIMUTH + 0.4, 64, 96, 26);

  /**
   * Layered planting. Density follows a slow noise field so the canopy forms groves
   * and glades rather than an even scatter; each ring has its own mix of forms.
   */
  const plant = (r0: number, r1: number, target: number, mix: number[], scale: [number, number], threshold: number) => {
    let placed = 0;
    for (let tries = 0; tries < target * 14 && placed < target; tries += 1) {
      const a = rand() * Math.PI * 2;
      const r = r0 + Math.sqrt(rand()) * (r1 - r0);
      // The opening camera stands at OPENING_AZIMUTH; beyond its position nothing is ever in view.
      const behind = Math.abs(Math.atan2(Math.sin(a - OPENING_AZIMUTH), Math.cos(a - OPENING_AZIMUTH)));
      if (r > 95 && behind < 0.8) continue;
      const x = r * Math.cos(a);
      const z = r * Math.sin(a);
      if (fbm(x * 0.02 + 11, z * 0.02 - 4, 3) < threshold) continue;
      const form = mix[Math.floor(rand() * mix.length)];
      if (addTree(x, z, form, scale[0] + rand() * (scale[1] - scale[0]), 9)) placed += 1;
    }
  };
  // Near belt: the ring just outside the walls stays open; trees close in beyond it.
  plant(COURT_OUTER + 9, 100, Math.round(240 * (0.6 + density * 0.4)), [1, 1, 1, 2, 2, 3, 4], [0.8, 1.2], 0.35);
  // Middle forest: denser, overlapping canopy, mostly the lighter-weight crown.
  plant(100, 240, Math.round(1100 * density), [4, 4, 4, 4, 4, 1, 3], [1.1, 1.6], 0.28);
  // Far canopy mass, seen through haze.
  plant(240, 620, Math.round(900 * density), [4], [1.4, 2.1], 0.25);

  // --- Terrain ----------------------------------------------------------------------------
  {
    const rings = 110;
    const radial = 200;
    const r0 = COURT_OUTER - 0.2;
    const r1 = 980;
    const positions: number[] = [];
    const colours: number[] = [];
    const uvs: number[] = [];
    const indices: number[] = [];
    // An overgrown precinct: grass and herbs over most of the ground, leaf litter
    // and shade-darkened soil under the canopy, bare earth only in worn patches.
    const soil = new THREE.Color('#a89a7c');
    const bare = new THREE.Color('#cbbfa4');
    const trodden = new THREE.Color('#ddd5c3');
    const grass = new THREE.Color('#8b9467');
    const grassDeep = new THREE.Color('#65744c');
    const litter = new THREE.Color('#857553');
    const shade = new THREE.Color('#57533c');
    const c = new THREE.Color();
    const canopyCover = (x: number, z: number) => {
      let best = 0;
      nearby(x, z, 16, (t) => {
        const reach = TREE_FORMS[t.form].crown * t.scale * 1.25;
        const d = Math.hypot(t.x - x, t.z - z);
        if (d < reach) best = Math.max(best, 1 - d / reach);
      });
      return best;
    };
    for (let i = 0; i < rings; i += 1) {
      const r = r0 + (r1 - r0) * Math.pow(i / (rings - 1), 2.3);
      for (let j = 0; j <= radial; j += 1) {
        const a = (j / radial) * Math.PI * 2;
        const x = r * Math.cos(a);
        const z = r * Math.sin(a);
        const y = terrainHeight(x, z);
        positions.push(x, y, z);
        uvs.push(x / 18, z / 18);
        const n1 = fbm(x * 0.03, z * 0.03, 3);
        const n2 = fbm(x * 0.012 + 3, z * 0.012 - 5, 4);
        const n3 = fbm(x * 0.09 - 7, z * 0.09 + 2, 2);
        c.copy(grass).lerp(grassDeep, smooth(0.42, 0.66, n2 + (n3 - 0.5) * 0.3));
        // Patches of soil and, more rarely, bare worn earth.
        c.lerp(soil, smooth(0.48, 0.68, n1) * 0.8);
        // Drifts of fallen leaves well beyond the canopy edge.
        c.lerp(litter, smooth(0.55, 0.75, n3 + (n2 - 0.5) * 0.4) * 0.45);
        c.lerp(bare, smooth(0.66, 0.8, n1 + (n3 - 0.5) * 0.25) * 0.6);
        // Under the canopy: leaf litter, then deep shade towards the trunks.
        const cover = r < 650 ? canopyCover(x, z) : 0;
        c.lerp(litter, smooth(0.0, 0.45, cover) * 0.8);
        c.lerp(shade, smooth(0.45, 1, cover) * 0.6);
        // Far ground reads as continuous forest floor through the haze.
        c.lerp(grassDeep, smooth(220, 520, r) * 0.5);
        // Worn ground at the foot of the enclosure wall.
        c.lerp(trodden, (1 - smooth(COURT_OUTER, COURT_OUTER + 6, r)) * 0.6);
        colours.push(c.r, c.g, c.b);
      }
    }
    const row = radial + 1;
    for (let i = 0; i < rings - 1; i += 1) {
      for (let j = 0; j < radial; j += 1) {
        const a = i * row + j;
        const b = a + row;
        indices.push(a, a + 1, b, b, a + 1, b + 1);
      }
    }
    const geo = track(new THREE.BufferGeometry());
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(colours, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    const groundTex = track(createGroundTexture(31, anisotropy, Math.max(256, textureSize / 2)));
    const mat = track(
      new THREE.MeshStandardMaterial({ map: groundTex, vertexColors: true, roughness: 1, metalness: 0 }),
    );
    // The ground texture is a neutral mid-tone detail layer; vertex colours carry the albedo.
    mat.color.setRGB(1.45, 1.42, 1.4);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.name = 'terrain';
    mesh.receiveShadow = shadows;
    group.add(mesh);
  }

  addMerged(wallGeos, materials.wall, 'site-walls');
  addMerged(trimGeos, materials.trim, 'site-trim');
  addMerged(pavingGeos, materials.paving, 'site-paving');
  addMerged(shadeGeos, shadeMat, 'site-interiors');

  // Weathered stone for the ruins: the same sandstone, greyed and faintly green with age.
  const ruinMat = track(
    applyDepthShade(
      new THREE.MeshStandardMaterial({
        map: materials.wall.map,
        bumpMap: materials.wall.bumpMap,
        bumpScale: 1.4,
        color: '#b9b39a',
        roughness: 0.97,
        metalness: 0,
      }),
    ),
  );
  addMerged(ruinGeos, ruinMat, 'precinct-ruins');

  // --- Trees, shrubs and their shadows -----------------------------------------------------
  const foliageMat = track(new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92, metalness: 0 }));
  const m4 = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const s3 = new THREE.Vector3();
  const p3 = new THREE.Vector3();
  const up = new THREE.Vector3(0, 1, 0);
  const tint = new THREE.Color();
  const instanced: THREE.InstancedMesh[] = [];

  TREE_FORMS.forEach((form, fi) => {
    const list = trees.filter((t) => t.form === fi);
    if (!list.length) return;
    // Detail is set per form: near, characterful trees get finer crowns; the distant canopy is cheapest.
    const geo = track(buildTreeGeometry(form, 97 + fi * 31, Math.max(0, foliageDetail - (form.detailDrop ?? 0) + (fi === 0 ? 1 : 0))));
    const mesh = new THREE.InstancedMesh(geo, foliageMat, list.length);
    list.forEach((t, i) => {
      q.setFromAxisAngle(up, t.rot);
      s3.setScalar(t.scale);
      p3.set(t.x, Math.max(0, terrainHeight(t.x, t.z)) + (t.lift ?? 0), t.z);
      mesh.setMatrixAt(i, m4.compose(p3, q, s3));
      tint.setRGB(0.9 + hash2(t.x, t.z) * 0.2, 0.92 + hash2(t.z, t.x) * 0.16, 0.9 + hash2(t.x + 1, t.z) * 0.12);
      mesh.setColorAt(i, tint);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    mesh.name = `trees-${fi}`;
    mesh.castShadow = false;
    mesh.receiveShadow = false;
    instanced.push(mesh);
    group.add(mesh);
  });

  // Shrubs at the foot of walls, around groves and along the path edge.
  const shrubs: { x: number; z: number; s: number }[] = [];
  const inPavilion = (x: number, z: number) => {
    const da = Math.abs(Math.atan2(Math.sin(Math.atan2(z, x) - SITE.pavilionAngle), Math.cos(Math.atan2(z, x) - SITE.pavilionAngle)));
    return da < SITE.pavilionHalfArc + 0.04 && Math.hypot(x, z) < SITE.courtRadius + SITE.pavilionDepth + 1.5;
  };
  const shrubOk = (x: number, z: number) =>
    Math.hypot(x, z) > COURT_OUTER + 1 &&
    !inPavilion(x, z) &&
    !(x > 0 && Math.abs(z) < SITE.pathHalfWidth + 1.2) &&
    !(x > COURT_OUTER - 2 && x < COURT_OUTER + 16 && Math.abs(z) < 10);
  for (let i = 0; i < 70; i += 1) {
    const a = rand() * Math.PI * 2;
    const r = COURT_OUTER + 1.2 + rand() * 3;
    const x = r * Math.cos(a);
    const z = r * Math.sin(a);
    if (x > 0 && Math.abs(z) < 11) continue;
    if (Math.abs(a - SITE.pavilionAngle) < SITE.pavilionHalfArc + 0.05 && r < COURT_OUTER + SITE.pavilionDepth) continue;
    shrubs.push({ x, z, s: 0.7 + rand() * 0.6 });
  }
  trees.forEach((t) => {
    if (rand() > 0.55 * density + 0.2) return;
    const a = rand() * Math.PI * 2;
    const d = 3 + rand() * 4;
    const x = t.x + Math.cos(a) * d;
    const z = t.z + Math.sin(a) * d;
    if (shrubOk(x, z)) shrubs.push({ x, z, s: 0.6 + rand() * 0.7 });
  });
  // Overgrowth at the foot of ruins and walls, and creeping onto their lower courses.
  rubbleAt.forEach(({ x: cx, z: cz, r }) => {
    for (let k = 0; k < Math.round(r * 2.2); k += 1) {
      const a = rand() * Math.PI * 2;
      const d = r * (0.55 + rand() * 0.6);
      const x = cx + Math.cos(a) * d;
      const z = cz + Math.sin(a) * d;
      if (shrubOk(x, z)) shrubs.push({ x, z, s: 0.5 + rand() * 0.8 });
    }
  });
  // Low scrub scattered through the grassed ground around the site.
  for (let i = 0, tries = 0; i < Math.round(260 * density) && tries < 3000; tries += 1) {
    const a = rand() * Math.PI * 2;
    const r = COURT_OUTER + 6 + Math.pow(rand(), 0.9) * 150;
    const x = r * Math.cos(a);
    const z = r * Math.sin(a);
    if (fbm(x * 0.012 + 3, z * 0.012 - 5, 4) < 0.46 || !shrubOk(x, z)) continue;
    shrubs.push({ x, z, s: 0.35 + rand() * 0.5 });
    i += 1;
  }
  for (let x = COURT_OUTER + 18; x < 220; x += 7 + rand() * 9) {
    shrubs.push({ x, z: (rand() > 0.5 ? 1 : -1) * (SITE.pathHalfWidth + 1.4 + rand()), s: 0.45 + rand() * 0.3 });
  }
  {
    const geo = track(buildShrubGeometry(foliageDetail));
    const mesh = new THREE.InstancedMesh(geo, foliageMat, shrubs.length);
    shrubs.forEach((sh, i) => {
      q.setFromAxisAngle(up, hash2(sh.x, sh.z) * 6.28);
      s3.set(sh.s, sh.s * (0.8 + hash2(sh.z, sh.x) * 0.4), sh.s);
      p3.set(sh.x, terrainHeight(sh.x, sh.z) - 0.1, sh.z);
      mesh.setMatrixAt(i, m4.compose(p3, q, s3));
      tint.setScalar(0.72 + hash2(sh.x + 2, sh.z) * 0.28);
      mesh.setColorAt(i, tint);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    mesh.name = 'shrubs';
    instanced.push(mesh);
    group.add(mesh);
  }

  // Ground cover: grasses and herbs, thickest in clearings and under the canopy edge,
  // never on paths, paving or inside the court.
  {
    const cover: { x: number; z: number; s: number }[] = [];
    const want = Math.round(4500 * (0.4 + density * 0.6));
    const onSlab = (x: number, z: number) => keepOut.some((k) => k.r <= 3.2 && Math.hypot(k.x - x, k.z - z) < 1.6);
    for (let tries = 0; tries < want * 4 && cover.length < want; tries += 1) {
      const a = rand() * Math.PI * 2;
      const r = COURT_OUTER + 1.5 + Math.pow(rand(), 1.6) * 210;
      const x = r * Math.cos(a);
      const z = r * Math.sin(a);
      if (!shrubOk(x, z) || fbm(x * 0.05 + 9, z * 0.05, 2) < 0.36 || onSlab(x, z)) continue;
      cover.push({ x, z, s: 0.5 + rand() * 0.8 });
    }
    const geo = track(buildGroundCoverGeometry());
    const mesh = new THREE.InstancedMesh(geo, foliageMat, cover.length);
    cover.forEach((g, i) => {
      q.setFromAxisAngle(up, hash2(g.z, g.x) * 6.28);
      s3.set(g.s * (0.8 + hash2(g.x, g.z) * 0.6), g.s * (0.6 + hash2(g.x + 3, g.z) * 0.8), g.s);
      p3.set(g.x, terrainHeight(g.x, g.z) - 0.05, g.z);
      mesh.setMatrixAt(i, m4.compose(p3, q, s3));
      // Some clumps are drier and straw-coloured, some lush.
      const dry = hash2(g.x * 0.3, g.z * 0.3);
      tint.setRGB(0.8 + dry * 0.3, 0.82 + dry * 0.16, 0.76 + dry * 0.04);
      mesh.setColorAt(i, tint);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    mesh.name = 'ground-cover';
    instanced.push(mesh);
    group.add(mesh);
  }

  // Path flagstones in the pale paving of the court; fallen blocks in weathered stone.
  {
    const flags = new THREE.InstancedMesh(track(new THREE.BoxGeometry(1, 1, 1)), materials.paving, slabs.length);
    slabs.forEach((sl, i) => {
      q.setFromAxisAngle(up, sl.rot);
      s3.set(sl.w, 0.12, sl.d);
      p3.set(sl.x, sl.y, sl.z);
      flags.setMatrixAt(i, m4.compose(p3, q, s3));
      // Old flags, dulled by weather and lichen, a little different stone to stone.
      tint.setRGB(0.56 + hash2(sl.x, sl.z) * 0.14, 0.57 + hash2(sl.x, sl.z) * 0.14, 0.5 + hash2(sl.x, sl.z) * 0.12);
      flags.setColorAt(i, tint);
    });
    flags.instanceMatrix.needsUpdate = true;
    flags.computeBoundingSphere();
    flags.receiveShadow = shadows;
    flags.name = 'precinct-paths';
    instanced.push(flags);
    group.add(flags);

    const blocks: { x: number; y: number; z: number; rot: number; tilt: number; sx: number; sy: number; sz: number }[] = [];
    rubbleAt.forEach(({ x: cx, z: cz, r }) => {
      for (let k = 0; k < Math.round(r * 0.9); k += 1) {
        const a = rand() * Math.PI * 2;
        const d = r * (0.45 + rand() * 0.55);
        const x = cx + Math.cos(a) * d;
        const z = cz + Math.sin(a) * d;
        const size = 0.5 + rand() * 0.7;
        blocks.push({
          x,
          z,
          y: terrainHeight(x, z) + size * 0.25,
          rot: rand() * 6.28,
          tilt: (rand() - 0.5) * 0.5,
          sx: size * 1.6,
          sy: size * 0.8,
          sz: size,
        });
      }
    });
    const geo = track(new THREE.BoxGeometry(1, 1, 1));
    const mesh = new THREE.InstancedMesh(geo, ruinMat, blocks.length);
    const e = new THREE.Euler();
    blocks.forEach((b, i) => {
      q.setFromEuler(e.set(b.tilt, b.rot, b.tilt * 0.6));
      s3.set(b.sx, b.sy, b.sz);
      p3.set(b.x, b.y, b.z);
      mesh.setMatrixAt(i, m4.compose(p3, q, s3));
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    mesh.receiveShadow = shadows;
    mesh.name = 'fallen-stone';
    instanced.push(mesh);
    group.add(mesh);
  }

  // Tree shadows: soft decals cast away from the sun. Cheaper than extending
  // the shadow map across the landscape, and the sun never moves.
  {
    const tex = track(createBlobTexture());
    const geo = track(new THREE.PlaneGeometry(1, 1));
    geo.rotateX(-Math.PI / 2);
    const mat = track(
      new THREE.MeshBasicMaterial({
        color: '#2b2116',
        map: tex,
        transparent: true,
        // Lighter per tree: under a continuous canopy the decals overlap and accumulate.
        opacity: 0.42,
        depthWrite: false,
        polygonOffset: true,
        polygonOffsetFactor: -2,
        polygonOffsetUnits: -2,
      }),
    );
    const sun = SKY.sunDirection;
    const flat = new THREE.Vector2(-sun.x, -sun.z).normalize();
    const reach = 1 / Math.tan(Math.asin(sun.y));
    const yaw = Math.atan2(-flat.y, flat.x);
    const mesh = new THREE.InstancedMesh(geo, mat, trees.length);
    trees.forEach((t, i) => {
      const form = TREE_FORMS[t.form];
      const h = (form.trunkHeight + form.crown * form.squash * 0.6) * t.scale;
      const d = form.crown * 2 * t.scale;
      const off = h * reach * 0.55;
      const x = t.x + flat.x * off;
      const z = t.z + flat.y * off;
      q.setFromAxisAngle(up, yaw);
      s3.set(d * 1.25 + off * 0.6, 1, d * 0.95);
      p3.set(x, Math.max(0.02, terrainHeight(x, z) + 0.06), z);
      mesh.setMatrixAt(i, m4.compose(p3, q, s3));
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    mesh.renderOrder = 1;
    mesh.name = 'tree-shadows';
    instanced.push(mesh);
    group.add(mesh);
  }

  return {
    group,
    dispose: () => {
      disposables.forEach((d) => d.dispose());
      instanced.forEach((m) => m.dispose());
    },
  };
};
