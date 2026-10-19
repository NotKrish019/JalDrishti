import * as THREE from 'three';
import { buildCameraKeys, sampleCameraPath, PHASES, type CameraKey } from './cameraPath';
import { buildStepwell } from './stepwell';
import { buildEnvironment } from './environment';
import { createWater } from './water';
import { SKY, createDust, createLightShaft, createSky } from './atmosphere';
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
  /** Scroll progress at creation, so the very first frame is already in the right pose. */
  initialProgress?: number;
  /**
   * Called whenever the camera's eased progress changes. The overlay copy is driven
   * from this, not from raw scroll, so text and camera can never drift apart.
   */
  onProgress?: (progress: number) => void;
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
  // Near/far kept as tight as the scene allows: the closest wall is ~1 m away in
  // the descent and the landscape ends ~1 km out. A wider range z-fights at aerial distances.
  private readonly camera = new THREE.PerspectiveCamera(48, 1, 0.3, 1500);
  private readonly keys: CameraKey[] = buildCameraKeys();
  private lastTime = 0;
  private readonly disposers: (() => void)[] = [];
  private readonly still: boolean;
  private readonly onContextLost?: () => void;
  private readonly onProgress?: (progress: number) => void;
  private reportedProgress = -1;

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
  /** Horizontal framing shift for the opening shot on wide screens (film offset, mm). */
  private heroShift = 0;
  /** Vertical framing lift for the opening shot on portrait screens (fraction of height). */
  private heroLift = 0;
  private lift = 0;
  private viewWidth = 1;
  private viewHeight = 1;

  private readonly tmpTarget = new THREE.Vector3();
  private readonly tmpRight = new THREE.Vector3();
  private readonly tmpUp = new THREE.Vector3();

  constructor({ canvas, tier, still = false, initialProgress, onProgress, onContextLost }: DescentSceneOptions) {
    const q = QUALITY[tier];
    this.still = still;
    this.onContextLost = onContextLost;
    this.onProgress = onProgress;
    if (initialProgress !== undefined) {
      this.progress = this.targetProgress = Math.min(1, Math.max(0, initialProgress));
      this.hasProgress = true;
    }

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
    // Development-only handle for inspecting the live camera and progress from the console or tests.
    if (import.meta.env.DEV) (window as unknown as { __jdDescent?: DescentScene }).__jdDescent = this;

    // Aerial perspective: the wider landscape recedes into warm haze; nothing inside the well is far enough to fog.
    this.scene.fog = new THREE.Fog(SKY.haze, 110, 640);
    this.scene.background = SKY.haze.clone();

    // --- Light ---------------------------------------------------------------
    const hemi = new THREE.HemisphereLight('#f4e8d2', '#3f3125', 1.05);
    const sun = new THREE.DirectionalLight('#ffe6bf', 3.1);
    sun.position.copy(SKY.sunDirection).multiplyScalar(120);
    sun.target.position.set(0, -14, 0);
    if (q.shadows) {
      sun.castShadow = true;
      sun.shadow.mapSize.set(q.shadowMapSize, q.shadowMapSize);
      // Covers the well, the enclosure, the gateway and the pavilion range.
      const cam = sun.shadow.camera as THREE.OrthographicCamera;
      cam.left = -52;
      cam.right = 52;
      cam.top = 52;
      cam.bottom = -52;
      cam.near = 10;
      cam.far = 260;
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

    const site = buildEnvironment({
      materials: stepwell.materials,
      anisotropy,
      textureSize: q.textureSize,
      shadows: q.shadows,
      foliageDetail: q.foliageDetail,
      density: q.density,
    });
    this.scene.add(site.group);
    this.disposers.push(site.dispose);

    this.water = createWater(Math.max(48, q.segments / 2));
    this.scene.add(this.water.mesh);
    this.disposers.push(this.water.dispose);

    this.sky = createSky();
    this.scene.add(this.sky.mesh);
    this.disposers.push(this.sky.dispose);

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
    // On wide screens the opening shot sits right of centre, leaving the left
    // third of the landscape for the introduction. Portrait screens stay centred.
    this.heroShift = aspect > 1.25 ? -Math.min(6.4, (aspect - 1.25) * 16) : 0;
    // On portrait screens the site sits in the upper half, above the introduction.
    this.heroLift = aspect < 0.9 ? 0.21 : 0;
    this.viewWidth = width;
    this.viewHeight = height;
    this.lift = -1;
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
    // Settle exactly on the target rather than creeping towards it forever.
    if (Math.abs(this.targetProgress - this.progress) < 1e-5) this.progress = this.targetProgress;
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

    // The framing shift eases out as the camera turns towards the rim.
    const shift = this.heroShift * (1 - smoothstep(PHASES.siteHold, PHASES.rim, p));
    if (Math.abs(shift - this.camera.filmOffset) > 1e-4) {
      this.camera.filmOffset = shift;
      this.camera.updateProjectionMatrix();
    }
    const lift = this.heroLift * (1 - smoothstep(PHASES.siteHold, PHASES.rim, p));
    if (Math.abs(lift - this.lift) > 1e-4) {
      this.lift = lift;
      if (lift > 0) {
        this.camera.setViewOffset(this.viewWidth, this.viewHeight, 0, this.viewHeight * lift, this.viewWidth, this.viewHeight);
      } else {
        this.camera.clearViewOffset();
      }
    }

    // Atmosphere keyed to the same milestones as the overlay copy.
    this.shaft.update(this.elapsed, smoothstep(0.26, 0.42, p) * (1 - smoothstep(0.84, 0.98, p)) * 0.5);
    this.dust.update(this.elapsed, smoothstep(0.28, 0.42, p) * 0.85, this.pixelRatio);
    this.water.update(this.elapsed, 1);
    this.sky.mesh.position.copy(this.camera.position);

    // Eye adaptation: exposure rises as daylight falls away with depth.
    this.renderer.toneMappingExposure = 1 + smoothstep(0.38, 0.8, p) * 0.4;

    this.renderer.render(this.scene, this.camera);

    if (this.onProgress && Math.abs(p - this.reportedProgress) > 1e-6) {
      this.reportedProgress = p;
      this.onProgress(p);
    }
  }
}
