import * as THREE from 'three';
import { WATER_Y } from './stepwellSpec';

/**
 * Shared depth-shading uniforms. Light inside a stepwell falls off with depth
 * long before any geometric shadowing does; this approximates that bounce-light
 * loss and the cool, damp tint of the lowest courses.
 */
export const depthShadeUniforms = {
  uDepthTop: { value: 2.0 },
  uDepthBottom: { value: WATER_Y - 1 },
  uDeepTint: { value: new THREE.Color('#1f2a24') },
  uDeepStrength: { value: 0.78 },
};

export const applyDepthShade = (material: THREE.MeshStandardMaterial): THREE.MeshStandardMaterial => {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, depthShadeUniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying float vJdWorldY;')
      .replace(
        '#include <project_vertex>',
        `#include <project_vertex>
        vec4 jdWorld = vec4(transformed, 1.0);
        #ifdef USE_INSTANCING
          jdWorld = instanceMatrix * jdWorld;
        #endif
        vJdWorldY = (modelMatrix * jdWorld).y;`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
        varying float vJdWorldY;
        uniform float uDepthTop;
        uniform float uDepthBottom;
        uniform vec3 uDeepTint;
        uniform float uDeepStrength;`,
      )
      .replace(
        '#include <tonemapping_fragment>',
        `float jdDepth = 1.0 - smoothstep(uDepthBottom, uDepthTop, vJdWorldY);
        jdDepth = pow(jdDepth, 1.35) * uDeepStrength;
        gl_FragColor.rgb = mix(gl_FragColor.rgb, gl_FragColor.rgb * uDeepTint * 2.2, jdDepth);
        #include <tonemapping_fragment>`,
      );
  };
  // Same program for every material using the shading: cache key must be stable.
  material.customProgramCacheKey = () => 'jd-depth-shade';
  return material;
};

export interface StoneMaterialOptions {
  map: THREE.Texture;
  bump?: THREE.Texture;
  bumpScale?: number;
  color?: THREE.ColorRepresentation;
  side?: THREE.Side;
  roughness?: number;
}

export const createStoneMaterial = ({
  map,
  bump,
  bumpScale = 1.4,
  color = '#ffffff',
  side = THREE.FrontSide,
  roughness = 0.92,
}: StoneMaterialOptions) =>
  applyDepthShade(
    new THREE.MeshStandardMaterial({
      map,
      bumpMap: bump ?? null,
      bumpScale,
      color,
      roughness,
      metalness: 0,
      side,
    }),
  );
