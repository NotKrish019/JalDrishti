import * as THREE from 'three';
import { STEPWELL, WATER_Y } from './stepwellSpec';

/**
 * Sky, cloud sea, the light shaft inside the well and suspended dust.
 * Everything here is shader-driven and allocation-free per frame.
 */

const NOISE_GLSL = /* glsl */ `
  float jdHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }
  float jdNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(jdHash(i), jdHash(i + vec2(1.0, 0.0)), u.x),
               mix(jdHash(i + vec2(0.0, 1.0)), jdHash(i + vec2(1.0, 1.0)), u.x), u.y);
  }
  float jdFbm(vec2 p, int octaves) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.8, -0.6, 0.6, 0.8);
    for (int i = 0; i < 6; i++) {
      if (i >= octaves) break;
      v += a * jdNoise(p);
      p = rot * p * 2.03;
      a *= 0.5;
    }
    return v;
  }
`;

export const SKY = {
  zenith: new THREE.Color('#8f9e9f'),
  horizon: new THREE.Color('#e9dcc4'),
  sun: new THREE.Color('#fff1d6'),
  haze: new THREE.Color('#ddd0ba'),
  sunDirection: new THREE.Vector3(0.42, 0.62, 0.66).normalize(),
};

export const createSky = () => {
  const geo = new THREE.SphereGeometry(900, 32, 16);
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    depthTest: false,
    fog: false,
    uniforms: {
      uZenith: { value: SKY.zenith },
      uHorizon: { value: SKY.horizon },
      uSun: { value: SKY.sun },
      uSunDir: { value: SKY.sunDirection },
    },
    vertexShader: /* glsl */ `
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: /* glsl */ `
      uniform vec3 uZenith; uniform vec3 uHorizon; uniform vec3 uSun; uniform vec3 uSunDir;
      varying vec3 vDir;
      void main() {
        float h = clamp(vDir.y, -0.2, 1.0);
        vec3 col = mix(uHorizon, uZenith, pow(smoothstep(-0.05, 0.9, h), 0.6));
        float sun = max(dot(normalize(vDir), uSunDir), 0.0);
        col += uSun * (pow(sun, 24.0) * 0.35 + pow(sun, 4.0) * 0.12);
        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.frustumCulled = false;
  mesh.renderOrder = -10;
  return { mesh, dispose: () => (geo.dispose(), mat.dispose()) };
};

export interface CloudLayers {
  group: THREE.Group;
  /** open: 0 = closed sea of cloud, 1 = fully parted above the opening. */
  update: (time: number, open: number, cameraY: number) => void;
  dispose: () => void;
}

/**
 * Depth-separated horizontal cloud sheets. Each sheet's fBm density is masked
 * by a radial opening centred on the well; the opening widens with scroll.
 * Sheets fade as the camera approaches them, so descending through them
 * reads as passing through mist rather than through a hard plane.
 */
export const createClouds = (layerCount: number, octaves: number): CloudLayers => {
  const group = new THREE.Group();
  group.name = 'clouds';
  const geo = new THREE.PlaneGeometry(1400, 1400, 1, 1);
  geo.rotateX(-Math.PI / 2);
  const materials: THREE.ShaderMaterial[] = [];

  for (let i = 0; i < layerCount; i += 1) {
    const k = layerCount === 1 ? 0 : i / (layerCount - 1);
    const mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
      fog: false,
      uniforms: {
        uTime: { value: 0 },
        uOpen: { value: 0 },
        uSeed: { value: i * 17.31 },
        uScale: { value: 0.0042 + k * 0.0026 },
        uLayerY: { value: 0 },
        uCameraY: { value: 100 },
        uLight: { value: new THREE.Color('#fffaf1') },
        uShade: { value: new THREE.Color('#8d857a') },
        uHaze: { value: SKY.horizon },
        uDensity: { value: 0.97 - k * 0.12 },
      },
      vertexShader: /* glsl */ `
        varying vec3 vWorld;
        void main() {
          vec4 w = modelMatrix * vec4(position, 1.0);
          vWorld = w.xyz;
          gl_Position = projectionMatrix * viewMatrix * w;
        }
      `,
      fragmentShader: /* glsl */ `
        uniform float uTime; uniform float uOpen; uniform float uSeed; uniform float uScale;
        uniform float uLayerY; uniform float uCameraY; uniform float uDensity;
        uniform vec3 uLight; uniform vec3 uShade; uniform vec3 uHaze;
        varying vec3 vWorld;
        ${NOISE_GLSL}
        void main() {
          vec2 p = vWorld.xz * uScale + vec2(uSeed, uSeed * 0.37) + vec2(uTime * 0.006, uTime * 0.0025);
          float n = jdFbm(p, ${octaves});
          float detail = jdFbm(p * 3.1 + 11.0, ${Math.max(2, octaves - 2)});
          float density = smoothstep(0.3, 0.62, n + detail * 0.2) * uDensity;

          // Radial opening above the well, with a ragged noisy edge.
          float dist = length(vWorld.xz);
          float holeR = mix(-30.0, 260.0, uOpen) + (n - 0.5) * 70.0;
          density *= smoothstep(holeR, holeR + 55.0, dist);

          // Fade out near the camera and towards the far horizon.
          density *= smoothstep(1.5, 14.0, abs(uCameraY - uLayerY));
          density *= 1.0 - smoothstep(380.0, 700.0, dist);

          // Sun-side lighting from the noise gradient gives the sheets a sense of volume.
          float lit = jdFbm(p + vec2(0.035, 0.02), ${octaves}) - n;
          vec3 col = mix(uShade, uLight, smoothstep(0.3, 0.85, n + detail * 0.3));
          col += uLight * clamp(lit * 6.0, -0.15, 0.25);
          col = mix(col, uHaze, smoothstep(160.0, 600.0, dist) * 0.85);
          gl_FragColor = vec4(col, density);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }
      `,
    });
    const mesh = new THREE.Mesh(geo, mat);
    const y = 42 + k * 38;
    mesh.position.y = y;
    mat.uniforms.uLayerY.value = y;
    mesh.renderOrder = 5 + (layerCount - i);
    group.add(mesh);
    materials.push(mat);
  }

  return {
    group,
    update: (time, open, cameraY) => {
      group.visible = open < 0.999;
      materials.forEach((m, i) => {
        m.uniforms.uTime.value = time;
        // Upper sheets part slightly before lower ones: layered reveal.
        m.uniforms.uOpen.value = Math.min(1, Math.max(0, open * 1.15 - (materials.length - 1 - i) * 0.05));
        m.uniforms.uCameraY.value = cameraY;
      });
    },
    dispose: () => {
      geo.dispose();
      materials.forEach((m) => m.dispose());
    },
  };
};

/** Soft additive beam falling diagonally into the well from the opening. */
export const createLightShaft = () => {
  const depth = -WATER_Y + 6;
  const geo = new THREE.CylinderGeometry(9, 13, depth, 48, 1, true);
  geo.translate(0, -depth / 2 + 4, 0);
  const mat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uColor: { value: new THREE.Color('#ffe2b0') },
      uIntensity: { value: 0 },
      uTime: { value: 0 },
    },
    vertexShader: /* glsl */ `
      varying vec2 vUv; varying vec3 vNormalV; varying vec3 vViewPos;
      void main() {
        vUv = uv;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vViewPos = mv.xyz;
        vNormalV = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: /* glsl */ `
      uniform vec3 uColor; uniform float uIntensity; uniform float uTime;
      varying vec2 vUv; varying vec3 vNormalV; varying vec3 vViewPos;
      void main() {
        float edge = abs(dot(normalize(-vViewPos), vNormalV));
        float falloff = smoothstep(0.0, 0.25, vUv.y) * smoothstep(1.0, 0.55, vUv.y);
        float streaks = 0.65 + 0.35 * sin(vUv.x * 40.0 + uTime * 0.15) * sin(vUv.x * 13.0);
        float a = pow(edge, 2.5) * falloff * streaks * uIntensity;
        gl_FragColor = vec4(uColor * a, a);
      }
    `,
  });
  const mesh = new THREE.Mesh(geo, mat);
  // Tilt along the sun direction so the beam lands on the far wall.
  mesh.rotation.z = -0.28;
  mesh.rotation.x = 0.16;
  mesh.renderOrder = 20;
  return {
    mesh,
    update: (time: number, intensity: number) => {
      mat.uniforms.uTime.value = time;
      mat.uniforms.uIntensity.value = intensity;
      mesh.visible = intensity > 0.001;
    },
    dispose: () => (geo.dispose(), mat.dispose()),
  };
};

/** Dust motes suspended in the void; they give the descent a sense of parallax and air. */
export const createDust = (count: number) => {
  const positions = new Float32Array(count * 3);
  const seeds = new Float32Array(count);
  let s = 1;
  const rand = () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
  for (let i = 0; i < count; i += 1) {
    const y = WATER_Y + 1 + rand() * (-WATER_Y + 6);
    const maxR = Math.max(4, STEPWELL.rimRadius - (-Math.min(0, y) / STEPWELL.tierHeight) * STEPWELL.terraceDepth - 1.5);
    const r = Math.sqrt(rand()) * maxR;
    const a = rand() * Math.PI * 2;
    positions.set([r * Math.cos(a), y, r * Math.sin(a)], i * 3);
    seeds[i] = rand();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 1));
  const mat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uOpacity: { value: 0 }, uPixelRatio: { value: 1 } },
    vertexShader: /* glsl */ `
      attribute float aSeed; uniform float uTime; uniform float uPixelRatio; varying float vSeed;
      void main() {
        vSeed = aSeed;
        vec3 p = position;
        p.x += sin(uTime * 0.07 + aSeed * 40.0) * 0.6;
        p.y += sin(uTime * 0.05 + aSeed * 90.0) * 0.4;
        p.z += cos(uTime * 0.06 + aSeed * 70.0) * 0.6;
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        gl_PointSize = min(4.0, (1.0 + aSeed * 1.5) * (14.0 / -mv.z)) * uPixelRatio;
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: /* glsl */ `
      uniform float uOpacity; varying float vSeed;
      void main() {
        float d = length(gl_PointCoord - 0.5);
        float a = smoothstep(0.5, 0.0, d) * uOpacity * (0.35 + vSeed * 0.65);
        gl_FragColor = vec4(vec3(1.0, 0.92, 0.78) * a, a);
      }
    `,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  return {
    points,
    update: (time: number, opacity: number, pixelRatio: number) => {
      mat.uniforms.uTime.value = time;
      mat.uniforms.uOpacity.value = opacity;
      mat.uniforms.uPixelRatio.value = pixelRatio;
      points.visible = opacity > 0.001;
    },
    dispose: () => (geo.dispose(), mat.dispose()),
  };
};
