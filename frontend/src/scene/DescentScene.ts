import * as THREE from 'three';
import { buildCameraKeys, sampleCameraPath, PHASES, type CameraKey } from './cameraPath';
import { buildStepwell } from './stepwell';
import { createWater } from './water';
import { SKY, createClouds, createDust, createLightShaft, createSky } from './atmosphere';
import { QUALITY, type QualityTier } from './quality';

const smoothstep = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export interface DescentSceneOptions {
  canvas: HTMLCanvasElement;
  tier: QualityTier;
  /** When true the scene renders single frames on demand and never animates by itself. */
  still?: boolean;
  onContextLost?: () => void;
}

/**
 * The scroll-driven descent. React owns scroll measurement and the DOM overlay;
 * this class owns WebGL: it receives a target progress in [0, 1] and eases the
 * camera along a fixed spline towards it, so forward, reverse and jump
 * scrolling all resolve to the same deterministic pose for a given position.
 */
export class DescentScene {
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(48, 1, 0.1, 2400);
  private readonly keys: CameraKey[] = buildCameraKeys();
  private lastTime = 0;
  private readonly disposers: (() => void)[] = [];
  private readonly still: boolean;
  private readonly onContextLost?: () => void;

  private readonly clouds: ReturnType<typeof createClouds>;
  private readonly water: ReturnType<typeof createWater>;
  private readonly shaft: ReturnType<typeof createLightShaft>;
  private readonly dust: ReturnType<typeof createDust>;
  private readonly sky: ReturnType<typeof createSky>;

  private targetProgress = 0;
  private progress = 0;
  private hasProgress = false;
  private pointerTarget = new THREE.Vector2();
  private pointer = new THREE.Vector2();
  private elapsed = 0;
  private frame = 0;
  private running = false;
  private pixelRatio: number;
  private readonly maxPixelRatio: number;
  private frameTimes: number[] = [];

  private readonly tmpTarget = new THREE.Vector3();
  private readonly tmpRight = new THREE.Vector3();
  private readonly tmpUp = new THREE.Vector3();

  constructor({ canvas, tier, still = false, onContextLost }: DescentSceneOptions) {
    const q = QUALITY[tier];
    this.still = still;
    this.onContextLost = onContextLost;

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: q.antialias,
      powerPreference: 'high-performance',
      alpha: false,
      stencil: false,
    });
    this.maxPixelRatio = Math.min(window.devicePixelRatio || 1, q.maxPixelRatio);
    this.pixelRatio = this.maxPixelRatio;
    this.renderer.setPixelRatio(this.pixelRatio);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1;
    this.renderer.shadowMap.enabled = q.shadows;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    // Geometry and sun never move, so the shadow map is rendered once.
    this.renderer.shadowMap.autoUpdate = false;
    this.renderer.shadowMap.needsUpdate = true;

    canvas.addEventListener('webglcontextlost', this.handleContextLost, false);

    this.scene.fog = new THREE.Fog(SKY.haze, 160, 720);
    this.scene.background = SKY.haze.clone();

    // --- Light ---------------------------------------------------------------
    const hemi = new THREE.HemisphereLight('#f4e8d2', '#3f3125', 1.05);
    const sun = new THREE.DirectionalLight('#ffe6bf', 3.1);
    sun.position.copy(SKY.sunDirection).multiplyScalar(90);
    sun.target.position.set(0, -14, 0);
    if (q.shadows) {
      sun.castShadow = true;
      sun.shadow.mapSize.set(q.shadowMapSize, q.shadowMapSize);
      const cam = sun.shadow.camera as THREE.OrthographicCamera;
      cam.left = -30;
      cam.right = 30;
      cam.top = 30;
      cam.bottom = -30;
      cam.near = 20;
      cam.far = 190;
      sun.shadow.bias = -0.0004;
      sun.shadow.normalBias = 0.05;
    }
    this.scene.add(hemi, sun, sun.target);

    // --- Content -------------------------------------------------------------
    const anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    const stepwell = buildStepwell({
      segments: q.segments,
      anisotropy,
      textureSize: q.textureSize,
      shadows: q.shadows,
    });
    this.scene.add(stepwell.group);
    this.disposers.push(stepwell.dispose);

    this.water = createWater(Math.max(48, q.segments / 2));
    this.scene.add(this.water.mesh);
    this.disposers.push(this.water.dispose);

    this.sky = createSky();
    this.scene.add(this.sky.mesh);
    this.disposers.push(this.sky.dispose);

    this.clouds = createClouds(q.cloudLayers, q.cloudOctaves);
    this.scene.add(this.clouds.group);
    this.disposers.push(this.clouds.dispose);

    this.shaft = createLightShaft();
    this.scene.add(this.shaft.mesh);
    this.disposers.push(this.shaft.dispose);

    this.dust = createDust(q.dust);
    this.scene.add(this.dust.points);
    this.disposers.push(this.dust.dispose);
  }

  /** Normalised scroll progress through the descent. */
  setProgress(value: number) {
    this.targetProgress = Math.min(1, Math.max(0, value));
    if (!this.hasProgress) {
      // First measurement (e.g. reload mid-page): start there rather than flying in.
      this.progress = this.targetProgress;
      this.hasProgress = true;
    }
    if (this.still) this.renderFrame(0);
  }

  /** Pointer in normalised device coordinates (-1..1). */
  setPointer(x: number, y: number) {
    this.pointerTarget.set(x, y);
  }

  resize(width: number, height: number) {
    if (width === 0 || height === 0) return;
    this.renderer.setSize(width, height, false);
    const aspect = width / height;
    this.camera.aspect = aspect;
    // Keep a usable horizontal field of view on portrait screens.
    const baseVFov = 48;
    const minHFov = 64;
    const vFovForH = (2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(minHFov) / 2) / aspect) * 180) / Math.PI;
    this.camera.fov = Math.min(80, Math.max(baseVFov, vFovForH));
    this.camera.updateProjectionMatrix();
    if (this.still || !this.running) this.renderFrame(0);
  }

  start() {
    if (this.running || this.still) return;
    this.running = true;
    this.lastTime = performance.now();
    this.frame = requestAnimationFrame(this.loop);
  }

  stop() {
    this.running = false;
    cancelAnimationFrame(this.frame);
  }

  dispose() {
    this.stop();
    this.renderer.domElement.removeEventListener('webglcontextlost', this.handleContextLost);
    this.disposers.forEach((d) => d());
    this.renderer.dispose();
  }

  private handleContextLost = (event: Event) => {
    event.preventDefault();
    this.stop();
    this.onContextLost?.();
  };

  private loop = (now: number) => {
    if (!this.running) return;
    const dt = Math.min(0.1, Math.max(0, (now - this.lastTime) / 1000));
    this.lastTime = now;
    this.renderFrame(dt);
    this.adaptResolution(dt);
    this.frame = requestAnimationFrame(this.loop);
  };

  private adaptResolution(dt: number) {
    this.frameTimes.push(dt);
    if (this.frameTimes.length < 90) return;
    const avg = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
    this.frameTimes = [];
    if (avg > 1 / 40 && this.pixelRatio > 1) {
      this.pixelRatio = Math.max(1, this.pixelRatio - 0.25);
      this.renderer.setPixelRatio(this.pixelRatio);
    } else if (avg < 1 / 58 && this.pixelRatio < this.maxPixelRatio) {
      this.pixelRatio = Math.min(this.maxPixelRatio, this.pixelRatio + 0.25);
      this.renderer.setPixelRatio(this.pixelRatio);
    }
  }

  private renderFrame(dt: number) {
    this.elapsed += dt;
    // Critically-damped easing towards the scroll target: smooth, frame-rate independent.
    const ease = this.still ? 1 : 1 - Math.exp(-dt * 4.2);
    this.progress += (this.targetProgress - this.progress) * ease;
    this.pointer.lerp(this.pointerTarget, this.still ? 0 : 1 - Math.exp(-dt * 2.5));
    const p = this.progress;

    const pose = sampleCameraPath(this.keys, p);
    this.camera.position.set(pose.position[0], pose.position[1], pose.position[2]);
    this.tmpTarget.set(pose.target[0], pose.target[1], pose.target[2]);

    // Gentle pointer parallax and an almost imperceptible idle drift.
    this.camera.lookAt(this.tmpTarget);
    this.tmpRight.setFromMatrixColumn(this.camera.matrixWorld, 0);
    this.tmpUp.setFromMatrixColumn(this.camera.matrixWorld, 1);
    const drift = this.still ? 0 : Math.sin(this.elapsed * 0.21) * 0.12;
    this.tmpTarget
      .addScaledVector(this.tmpRight, this.pointer.x * 1.1 + drift)
      .addScaledVector(this.tmpUp, this.pointer.y * 0.7);
    this.camera.lookAt(this.tmpTarget);

    // Atmosphere keyed to the same milestones as the overlay copy.
    const open = smoothstep(PHASES.cloudsStart, PHASES.cloudsOpen, p);
    this.clouds.update(this.elapsed, open, this.camera.position.y);
    this.shaft.update(this.elapsed, smoothstep(0.26, 0.42, p) * (1 - smoothstep(0.84, 0.98, p)) * 0.5);
    this.dust.update(this.elapsed, smoothstep(0.28, 0.42, p) * 0.85, this.pixelRatio);
    this.water.update(this.elapsed, 1);
    this.sky.mesh.position.copy(this.camera.position);

    // Eye adaptation: exposure rises as daylight falls away with depth.
    this.renderer.toneMappingExposure = 1 + smoothstep(0.38, 0.8, p) * 0.4;

    this.renderer.render(this.scene, this.camera);
  }
}
