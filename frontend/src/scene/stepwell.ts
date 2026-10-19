import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { STEPWELL, WATER_Y, terraceRadius, terraceY } from './stepwellSpec';
import { createAshlarTextures, createFriezeTextures, createGroundTexture, createPavingTextures } from './textures';
import { createStoneMaterial } from './materials';

export interface StepwellOptions {
  /** Radial segments for circular geometry. */
  segments: number;
  anisotropy: number;
  textureSize: number;
  shadows: boolean;
}

export interface StepwellBuild {
  group: THREE.Group;
  dispose: () => void;
}

const ASHLAR_TILE_M = 8;
const PAVING_TILE_M = 4;
const FRIEZE_TILE_M = 14;
const COURT_RADIUS = 38;
const COURT_WALL_H = 5.5;

const SANDSTONE = ['#c9ad86', '#bfa078', '#d3b991', '#b8966c', '#c4a47c', '#ad8c64'];
const PAVING = ['#c0aa88', '#b9a27f', '#c6b090', '#b49c7a'];

/** Inward-facing wall band. UVs are rescaled so texture density is constant. */
const wallBand = (radius: number, top: number, height: number, segments: number, tileWidth: number, tileHeight: number) => {
  const geo = new THREE.CylinderGeometry(radius, radius, height, segments, 1, true);
  geo.translate(0, top - height / 2, 0);
  const repeatsAround = Math.max(1, Math.round((Math.PI * 2 * radius) / tileWidth));
  const uv = geo.attributes.uv as THREE.BufferAttribute;
  for (let i = 0; i < uv.count; i += 1) {
    uv.setXY(i, uv.getX(i) * repeatsAround, uv.getY(i) * (height / tileHeight));
  }
  return geo;
};

/** Horizontal ring facing up, with world-scaled planar UVs. */
const flatRing = (inner: number, outer: number, y: number, segments: number, tile: number) => {
  const geo = new THREE.RingGeometry(inner, outer, segments, 1);
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, y, 0);
  const pos = geo.attributes.position as THREE.BufferAttribute;
  const uv = geo.attributes.uv as THREE.BufferAttribute;
  for (let i = 0; i < uv.count; i += 1) {
    uv.setXY(i, pos.getX(i) / tile, pos.getZ(i) / tile);
  }
  return geo;
};

const placeInstances = (
  mesh: THREE.InstancedMesh,
  transforms: { x: number; y: number; z: number; rotY: number; sx?: number; sy?: number; sz?: number }[],
) => {
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  const p = new THREE.Vector3();
  const up = new THREE.Vector3(0, 1, 0);
  transforms.forEach((t, i) => {
    q.setFromAxisAngle(up, t.rotY);
    s.set(t.sx ?? 1, t.sy ?? 1, t.sz ?? 1);
    p.set(t.x, t.y, t.z);
    m.compose(p, q, s);
    mesh.setMatrixAt(i, m);
  });
  mesh.instanceMatrix.needsUpdate = true;
  mesh.computeBoundingSphere();
};

export const buildStepwell = ({ segments, anisotropy, textureSize, shadows }: StepwellOptions): StepwellBuild => {
  const group = new THREE.Group();
  group.name = 'stepwell';
  const disposables: { dispose: () => void }[] = [];
  const track = <T extends { dispose: () => void }>(o: T) => {
    disposables.push(o);
    return o;
  };

  // --- Materials -------------------------------------------------------------
  const ashlar = createAshlarTextures(SANDSTONE, 7, anisotropy, textureSize);
  const paving = createPavingTextures(PAVING, 11, anisotropy, textureSize / 2);
  const frieze = createFriezeTextures(23, anisotropy, textureSize);
  const ground = createGroundTexture(31, anisotropy, textureSize / 2);
  [ashlar.map, ashlar.bump, paving.map, paving.bump, frieze.map, frieze.bump, ground].forEach(track);

  const wallMat = track(createStoneMaterial({ map: ashlar.map, bump: ashlar.bump, side: THREE.DoubleSide }));
  const floorMat = track(createStoneMaterial({ map: paving.map, bump: paving.bump, side: THREE.DoubleSide, bumpScale: 1 }));
  const friezeMat = track(
    createStoneMaterial({ map: frieze.map, bump: frieze.bump, side: THREE.DoubleSide, bumpScale: 2.2, roughness: 0.88 }),
  );
  const columnMat = track(createStoneMaterial({ map: ashlar.map, bump: ashlar.bump, color: '#e8dcc8' }));
  const groundMat = track(createStoneMaterial({ map: ground, color: '#cbbfa9', side: THREE.FrontSide }));

  const { terraceCount, tierHeight, galleryTiers, galleryHeight, rimRadius } = STEPWELL;
  const friezeTiers = new Set([terraceCount - 1, terraceCount - 2]);

  // --- Walls, terraces and curbs (merged by material) -----------------------
  const wallGeos: THREE.BufferGeometry[] = [];
  const friezeGeos: THREE.BufferGeometry[] = [];
  const floorGeos: THREE.BufferGeometry[] = [];

  for (let k = 0; k < terraceCount; k += 1) {
    const r = terraceRadius(k);
    const top = terraceY(k);
    const target = friezeTiers.has(k) ? friezeGeos : wallGeos;
    const tileW = friezeTiers.has(k) ? FRIEZE_TILE_M : ASHLAR_TILE_M;
    const tileH = friezeTiers.has(k) ? tierHeight : ASHLAR_TILE_M / 2;
    target.push(wallBand(r, top, tierHeight, segments, tileW, tileH));

    // Terrace floor below this wall
    const nextR = terraceRadius(k + 1);
    floorGeos.push(flatRing(nextR, r, terraceY(k + 1), segments, PAVING_TILE_M));

    // Curb at the lip of each terrace: a strong horizontal course line
    if (k > 0) {
      floorGeos.push(flatRing(r - 0.2, r, top + 0.24, segments, PAVING_TILE_M));
      floorGeos.push(wallBand(r - 0.2, top + 0.24, 0.24, segments, PAVING_TILE_M, PAVING_TILE_M));
    }
  }

  // Well shaft from the lowest terrace down below the water line, carved band
  const shaftR = terraceRadius(terraceCount);
  const shaftTop = terraceY(terraceCount);
  const shaftHeight = shaftTop - (WATER_Y - 2);
  friezeGeos.push(wallBand(shaftR, shaftTop, shaftHeight, segments, FRIEZE_TILE_M * 0.7, shaftHeight));
  floorGeos.push(flatRing(shaftR - 0.25, shaftR, shaftTop + 0.3, segments, PAVING_TILE_M));
  floorGeos.push(wallBand(shaftR - 0.25, shaftTop + 0.3, 0.3, segments, PAVING_TILE_M, PAVING_TILE_M));

  // Gallery roofs (slab + fascia), forming covered arcades over alternate terraces
  galleryTiers.forEach((k) => {
    const inner = terraceRadius(k) + 0.05;
    const outer = terraceRadius(k - 1);
    const y = terraceY(k) + galleryHeight;
    floorGeos.push(flatRing(inner, outer, y, segments, PAVING_TILE_M));
    floorGeos.push(wallBand(inner, y, 0.42, segments, PAVING_TILE_M, PAVING_TILE_M));
  });

  // Paved courtyard around the opening, enclosed by a perimeter wall
  floorGeos.push(flatRing(rimRadius, COURT_RADIUS, 0, segments, PAVING_TILE_M));
  wallGeos.push(wallBand(COURT_RADIUS, COURT_WALL_H, COURT_WALL_H, segments, ASHLAR_TILE_M, ASHLAR_TILE_M / 2));
  wallGeos.push(wallBand(COURT_RADIUS + 1.4, COURT_WALL_H, COURT_WALL_H, segments, ASHLAR_TILE_M, ASHLAR_TILE_M / 2));
  floorGeos.push(flatRing(COURT_RADIUS - 0.2, COURT_RADIUS + 1.6, COURT_WALL_H, segments, PAVING_TILE_M));
  floorGeos.push(flatRing(rimRadius + 0.15, rimRadius + 0.5, 0.92, segments, PAVING_TILE_M));
  floorGeos.push(wallBand(rimRadius + 0.15, 0.92, 0.14, segments, PAVING_TILE_M, PAVING_TILE_M));

  const addMerged = (geos: THREE.BufferGeometry[], material: THREE.Material, name: string) => {
    const merged = track(mergeGeometries(geos, false));
    geos.forEach((g) => g.dispose());
    const mesh = new THREE.Mesh(merged, material);
    mesh.name = name;
    mesh.castShadow = shadows;
    mesh.receiveShadow = shadows;
    group.add(mesh);
    return mesh;
  };
  addMerged(wallGeos, wallMat, 'walls');
  addMerged(friezeGeos, friezeMat, 'frieze');
  addMerged(floorGeos, floorMat, 'terraces');

  // Ground beyond the plaza, fading into haze
  const groundGeo = track(flatRing(COURT_RADIUS + 1.4, 480, -0.02, segments, 18));
  const groundMesh = new THREE.Mesh(groundGeo, groundMat);
  groundMesh.receiveShadow = shadows;
  group.add(groundMesh);

  // --- Gallery columns (instanced: base, shaft, capital) ---------------------
  type T = { x: number; y: number; z: number; rotY: number };
  const shafts: T[] = [];
  const caps: T[] = [];
  galleryTiers.forEach((k) => {
    const r = terraceRadius(k) + 0.45;
    const count = Math.round((Math.PI * 2 * r) / 2.05);
    const floor = terraceY(k);
    for (let i = 0; i < count; i += 1) {
      const a = (i / count) * Math.PI * 2 + k * 0.17;
      const x = r * Math.cos(a);
      const z = r * Math.sin(a);
      const rotY = -a;
      shafts.push({ x, y: floor + galleryHeight / 2, z, rotY });
      caps.push({ x, y: floor + 0.12, z, rotY });
      caps.push({ x, y: floor + galleryHeight - 0.5, z, rotY });
    }
  });
  const courtCount = Math.round((Math.PI * 2 * COURT_RADIUS) / 3.2);
  for (let i = 0; i < courtCount; i += 1) {
    const a = (i / courtCount) * Math.PI * 2;
    const r = COURT_RADIUS - 0.3;
    shafts.push({ x: r * Math.cos(a), y: galleryHeight / 2, z: r * Math.sin(a), rotY: -a });
    caps.push({ x: r * Math.cos(a), y: galleryHeight - 0.12, z: r * Math.sin(a), rotY: -a });
  }
  const shaftGeo = track(new THREE.BoxGeometry(0.4, galleryHeight, 0.4));
  const capGeo = track(new THREE.BoxGeometry(0.66, 0.24, 0.66));
  const shaftMesh = new THREE.InstancedMesh(shaftGeo, columnMat, shafts.length);
  const capMesh = new THREE.InstancedMesh(capGeo, columnMat, caps.length);
  placeInstances(shaftMesh, shafts);
  placeInstances(capMesh, caps);

  // --- Stair flights running tangentially along the walls -------------------
  // Alternate terraces carry three flights each; each terrace's flights are
  // rotated relative to the one above, which reads as a slow spiral from the void.
  const steps: (T & { sy: number })[] = [];
  const stepsPerFlight = 9;
  const rise = tierHeight / stepsPerFlight;
  const tread = 0.42;
  const stairWidth = 1.1;
  for (let k = 1; k <= terraceCount; k += 1) {
    if (galleryTiers.includes(k)) continue;
    const wallR = terraceRadius(k - 1);
    const r = wallR - stairWidth / 2 - 0.02;
    const floor = terraceY(k);
    for (let f = 0; f < 3; f += 1) {
      const start = k * 0.9 + (f * Math.PI * 2) / 3;
      const dir = (k + f) % 2 === 0 ? 1 : -1;
      for (let s = 0; s < stepsPerFlight; s += 1) {
        const a = start + dir * ((s + 0.5) * tread) / r;
        const h = (s + 1) * rise;
        steps.push({ x: r * Math.cos(a), y: floor + h / 2, z: r * Math.sin(a), rotY: -(a + Math.PI / 2), sy: h });
      }
    }
  }
  const stepGeo = track(new THREE.BoxGeometry(tread + 0.02, 1, stairWidth));
  const stepMesh = new THREE.InstancedMesh(stepGeo, floorMat, steps.length);
  placeInstances(stepMesh, steps);

  // --- Rim balustrade --------------------------------------------------------
  const balusters: (T & { sx: number; sz: number })[] = [];
  const balR = rimRadius + 0.32;
  const balCount = Math.round((Math.PI * 2 * balR) / 0.5);
  for (let i = 0; i < balCount; i += 1) {
    const a = (i / balCount) * Math.PI * 2;
    const post = i % 10 === 0;
    balusters.push({
      x: balR * Math.cos(a),
      y: 0.43,
      z: balR * Math.sin(a),
      rotY: -a,
      sx: post ? 2.2 : 1,
      sz: post ? 2.2 : 1,
    });
  }
  const balGeo = track(new THREE.BoxGeometry(0.13, 0.86, 0.13));
  const balMesh = new THREE.InstancedMesh(balGeo, columnMat, balusters.length);
  placeInstances(balMesh, balusters);

  [shaftMesh, capMesh, stepMesh, balMesh].forEach((m) => {
    m.castShadow = shadows;
    m.receiveShadow = shadows;
    group.add(m);
  });

  return {
    group,
    dispose: () => {
      disposables.forEach((d) => d.dispose());
      [shaftMesh, capMesh, stepMesh, balMesh].forEach((m) => m.dispose());
    },
  };
};
