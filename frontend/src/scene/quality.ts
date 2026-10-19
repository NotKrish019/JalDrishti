export type QualityTier = 'high' | 'medium' | 'low';

export interface QualitySettings {
  maxPixelRatio: number;
  antialias: boolean;
  shadows: boolean;
  shadowMapSize: number;
  /** Foliage icosahedron detail. */
  foliageDetail: number;
  /** Multiplier on distant trees and shrubs. */
  density: number;
  segments: number;
  textureSize: number;
  dust: number;
}

export const QUALITY: Record<QualityTier, QualitySettings> = {
  high: {
    maxPixelRatio: 2,
    antialias: true,
    shadows: true,
    shadowMapSize: 4096,
    foliageDetail: 2,
    density: 1,
    segments: 160,
    textureSize: 1024,
    dust: 520,
  },
  medium: {
    maxPixelRatio: 1.5,
    antialias: true,
    shadows: true,
    shadowMapSize: 2048,
    foliageDetail: 1,
    density: 0.75,
    segments: 112,
    textureSize: 1024,
    dust: 320,
  },
  low: {
    maxPixelRatio: 1,
    antialias: false,
    shadows: false,
    shadowMapSize: 0,
    foliageDetail: 1,
    density: 0.45,
    segments: 72,
    textureSize: 512,
    dust: 140,
  },
};

/** True when a WebGL context can actually be created. */
export const detectWebGL = (): boolean => {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return false;
    (gl as WebGLRenderingContext).getExtension('WEBGL_lose_context')?.loseContext();
    return true;
  } catch {
    return false;
  }
};

const isSoftwareRenderer = (): boolean => {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') as WebGLRenderingContext | null;
    if (!gl) return true;
    const info = gl.getExtension('WEBGL_debug_renderer_info');
    const renderer = info ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)) : '';
    gl.getExtension('WEBGL_lose_context')?.loseContext();
    return /swiftshader|llvmpipe|software|basic render/i.test(renderer);
  } catch {
    return false;
  }
};

/**
 * Initial tier from coarse device signals. The scene refines this at runtime by
 * lowering its pixel ratio if frame times stay high.
 */
export const pickQualityTier = (): QualityTier => {
  if (isSoftwareRenderer()) return 'low';
  const nav = navigator as Navigator & { deviceMemory?: number };
  const memory = nav.deviceMemory ?? 8;
  const cores = nav.hardwareConcurrency ?? 8;
  const coarse = window.matchMedia('(pointer: coarse)').matches;
  const small = Math.min(window.innerWidth, window.innerHeight) < 600;
  if (memory <= 2 || cores <= 2) return 'low';
  if (coarse || small || memory <= 4 || cores <= 4) return 'medium';
  return 'high';
};
