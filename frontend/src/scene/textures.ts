import * as THREE from 'three';

/**
 * Procedural canvas textures. Generated once at start-up (a few ms each), so the
 * scene needs no downloaded image assets and has nothing to license.
 */

/** Small deterministic PRNG so the masonry pattern is identical on every load. */
const mulberry32 = (seed: number) => () => {
  let t = (seed += 0x6d2b79f5);
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const makeCanvas = (w: number, h: number) => {
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('2D canvas unavailable');
  return { canvas, ctx };
};

const speckle = (ctx: CanvasRenderingContext2D, w: number, h: number, rand: () => number, count: number, alpha: number) => {
  for (let i = 0; i < count; i += 1) {
    const v = rand();
    ctx.fillStyle = v > 0.5 ? `rgba(255,248,235,${alpha * rand()})` : `rgba(40,28,18,${alpha * rand()})`;
    const s = 1 + rand() * 2;
    ctx.fillRect(rand() * w, rand() * h, s, s);
  }
};

const finish = (canvas: HTMLCanvasElement, srgb: boolean, anisotropy: number) => {
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = anisotropy;
  tex.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  tex.needsUpdate = true;
  return tex;
};

export interface MasonryTextures {
  map: THREE.Texture;
  bump: THREE.Texture;
}

/**
 * Coursed ashlar: horizontal courses of dressed blocks with lime joints.
 * One texture tile represents roughly 8 m × 4 m of wall.
 */
export const createAshlarTextures = (
  palette: string[],
  seed: number,
  anisotropy: number,
  size = 1024,
): MasonryTextures => {
  const rand = mulberry32(seed);
  const w = size;
  const h = size / 2;
  const { canvas: c, ctx } = makeCanvas(w, h);
  const { canvas: bc, ctx: bctx } = makeCanvas(w, h);

  ctx.fillStyle = '#b9a07d';
  ctx.fillRect(0, 0, w, h);
  bctx.fillStyle = '#202020';
  bctx.fillRect(0, 0, w, h);

  const courses = 8;
  const courseH = h / courses;
  const joint = Math.max(2, size / 400);

  for (let row = 0; row < courses; row += 1) {
    let x = -rand() * 120;
    const y = row * courseH;
    while (x < w) {
      const bw = (0.09 + rand() * 0.12) * w;
      const tone = palette[Math.floor(rand() * palette.length)];
      ctx.fillStyle = tone;
      ctx.fillRect(x + joint, y + joint, bw - joint * 2, courseH - joint * 2);
      // Weathering: darker lower edge, lighter upper arris.
      const g = ctx.createLinearGradient(0, y, 0, y + courseH);
      g.addColorStop(0, 'rgba(255,245,225,0.10)');
      g.addColorStop(0.7, 'rgba(0,0,0,0)');
      g.addColorStop(1, 'rgba(40,25,10,0.22)');
      ctx.fillStyle = g;
      ctx.fillRect(x + joint, y + joint, bw - joint * 2, courseH - joint * 2);

      const b = 170 + Math.floor(rand() * 60);
      bctx.fillStyle = `rgb(${b},${b},${b})`;
      bctx.fillRect(x + joint, y + joint, bw - joint * 2, courseH - joint * 2);

      // Wrap blocks that cross the right edge so the texture tiles seamlessly.
      if (x + bw > w) {
        ctx.fillStyle = tone;
        ctx.fillRect(x - w + joint, y + joint, bw - joint * 2, courseH - joint * 2);
        bctx.fillStyle = `rgb(${b},${b},${b})`;
        bctx.fillRect(x - w + joint, y + joint, bw - joint * 2, courseH - joint * 2);
      }
      x += bw;
    }
  }

  speckle(ctx, w, h, rand, size * 14, 0.22);

  // Damp staining near the base of each tile — water marks on stepwell walls.
  const stain = ctx.createLinearGradient(0, h * 0.7, 0, h);
  stain.addColorStop(0, 'rgba(30,40,30,0)');
  stain.addColorStop(1, 'rgba(30,40,30,0.18)');
  ctx.fillStyle = stain;
  ctx.fillRect(0, 0, w, h);

  return { map: finish(c, true, anisotropy), bump: finish(bc, false, anisotropy) };
};

/** Square paving slabs for terrace floors and the ground plaza. */
export const createPavingTextures = (palette: string[], seed: number, anisotropy: number, size = 512): MasonryTextures => {
  const rand = mulberry32(seed);
  const { canvas: c, ctx } = makeCanvas(size, size);
  const { canvas: bc, ctx: bctx } = makeCanvas(size, size);
  ctx.fillStyle = '#9b8566';
  ctx.fillRect(0, 0, size, size);
  bctx.fillStyle = '#222';
  bctx.fillRect(0, 0, size, size);
  const n = 6;
  const cell = size / n;
  const joint = 2;
  for (let i = 0; i < n; i += 1) {
    for (let j = 0; j < n; j += 1) {
      ctx.fillStyle = palette[Math.floor(rand() * palette.length)];
      ctx.fillRect(i * cell + joint, j * cell + joint, cell - joint * 2, cell - joint * 2);
      const b = 170 + Math.floor(rand() * 60);
      bctx.fillStyle = `rgb(${b},${b},${b})`;
      bctx.fillRect(i * cell + joint, j * cell + joint, cell - joint * 2, cell - joint * 2);
    }
  }
  speckle(ctx, size, size, rand, size * 10, 0.25);
  return { map: finish(c, true, anisotropy), bump: finish(bc, false, anisotropy) };
};

/**
 * Carved band for the deep shaft: a moulded cornice, then a row of arched niches
 * with abstract relief panels, then a lotus-petal moulding. Deliberately abstract —
 * it suggests carved stone without imitating specific sculpture.
 */
export const createFriezeTextures = (seed: number, anisotropy: number, size = 1024): MasonryTextures => {
  const rand = mulberry32(seed);
  const w = size;
  const h = size / 2;
  const { canvas: c, ctx } = makeCanvas(w, h);
  const { canvas: bc, ctx: bctx } = makeCanvas(w, h);

  const base = '#8a5a3e';
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, w, h);
  bctx.fillStyle = '#808080';
  bctx.fillRect(0, 0, w, h);

  const band = (y: number, bh: number, light: string, b: number) => {
    ctx.fillStyle = light;
    ctx.fillRect(0, y, w, bh);
    bctx.fillStyle = `rgb(${b},${b},${b})`;
    bctx.fillRect(0, y, w, bh);
  };

  // Cornice mouldings
  band(0, h * 0.04, '#a5714f', 220);
  band(h * 0.05, h * 0.02, '#6b4430', 60);
  band(h * 0.08, h * 0.05, '#9c6a49', 200);

  // Niches
  const niches = 12;
  const nw = w / niches;
  const top = h * 0.16;
  const bottom = h * 0.66;
  for (let i = 0; i < niches; i += 1) {
    const x = i * nw;
    // pilaster
    ctx.fillStyle = '#a06e4c';
    ctx.fillRect(x, top, nw * 0.14, bottom - top);
    bctx.fillStyle = '#d0d0d0';
    bctx.fillRect(x, top, nw * 0.14, bottom - top);
    // recess with an arched head
    const rx = x + nw * 0.22;
    const rw = nw * 0.7;
    ctx.fillStyle = '#4a2e20';
    bctx.fillStyle = '#303030';
    for (const [g, fill] of [
      [ctx, '#4a2e20'],
      [bctx, '#303030'],
    ] as const) {
      g.fillStyle = fill;
      g.beginPath();
      g.moveTo(rx, bottom);
      g.lineTo(rx, top + rw * 0.45);
      g.quadraticCurveTo(rx + rw / 2, top - rw * 0.1, rx + rw, top + rw * 0.45);
      g.lineTo(rx + rw, bottom);
      g.closePath();
      g.fill();
    }
    // relief panel inside the niche: a lit vertical form
    const fx = rx + rw * 0.3;
    const fw = rw * 0.4;
    const fy = top + rw * 0.5 + rand() * 4;
    const grad = ctx.createLinearGradient(fx, 0, fx + fw, 0);
    grad.addColorStop(0, '#b98762');
    grad.addColorStop(1, '#6e4631');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.ellipse(fx + fw / 2, fy + fw * 0.35, fw * 0.32, fw * 0.36, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(fx, fy + fw * 0.7, fw, bottom - fy - fw * 0.9);
    bctx.fillStyle = '#e0e0e0';
    bctx.beginPath();
    bctx.ellipse(fx + fw / 2, fy + fw * 0.35, fw * 0.32, fw * 0.36, 0, 0, Math.PI * 2);
    bctx.fill();
    bctx.fillRect(fx, fy + fw * 0.7, fw, bottom - fy - fw * 0.9);
  }

  // Sill and petal moulding
  band(bottom, h * 0.04, '#a5714f', 220);
  const petals = 48;
  const pw = w / petals;
  for (let i = 0; i < petals; i += 1) {
    for (const [g, light, dark] of [
      [ctx, '#9e6b4a', '#5e3b29'],
      [bctx, '#d8d8d8', '#404040'],
    ] as const) {
      g.fillStyle = dark;
      g.fillRect(i * pw, bottom + h * 0.05, pw, h * 0.09);
      g.fillStyle = light;
      g.beginPath();
      g.ellipse(i * pw + pw / 2, bottom + h * 0.095, pw * 0.38, h * 0.042, 0, 0, Math.PI * 2);
      g.fill();
    }
  }
  band(bottom + h * 0.15, h * 0.03, '#6b4430', 70);
  // Plain coursed stone below
  for (let row = 0; row < 3; row += 1) {
    const y = bottom + h * 0.19 + row * h * 0.05;
    band(y, h * 0.045, row % 2 ? '#8f5e41' : '#966447', 170);
  }

  speckle(ctx, w, h, rand, size * 16, 0.25);
  return { map: finish(c, true, anisotropy), bump: finish(bc, false, anisotropy) };
};

/** Low-frequency value noise used by the sky-facing ground plane. */
export const createGroundTexture = (seed: number, anisotropy: number, size = 512): THREE.Texture => {
  const rand = mulberry32(seed);
  const { canvas, ctx } = makeCanvas(size, size);
  ctx.fillStyle = '#a99c86';
  ctx.fillRect(0, 0, size, size);
  for (let i = 0; i < 900; i += 1) {
    const r = 6 + rand() * 40;
    const x = rand() * size;
    const y = rand() * size;
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    const tone = rand() > 0.5 ? '196,184,160' : '120,108,90';
    g.addColorStop(0, `rgba(${tone},0.18)`);
    g.addColorStop(1, `rgba(${tone},0)`);
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  speckle(ctx, size, size, rand, size * 20, 0.3);
  return finish(canvas, true, anisotropy);
};
