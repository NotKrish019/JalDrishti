# JalDrishti Frontend

**Owner:** Anika Jain (Frontend) · Team NeuralX
**Stack:** React 18, Vite 5, TypeScript, Tailwind CSS 3, three.js (landing scene only)

---

## 1. What lives here

- **Landing experience** (`/`): a scroll-driven 3D descent into an illustrative circular stepwell. It resolves into the product narrative: engineering, challenge, the See → Understand → Assess → Revive method, live material compatibility and the workspace.
- **Inspection workspace**:
  - `/upload`: upload, Cloudinary storage via the backend, then analysis.
  - `/analysis`: findings.
  - `/report`: printable dossier.
  - `/knowledge`: live IKS knowledge base.

## 2. Setup

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production build
```

The backend (`uvicorn backend.app.main:app --port 8000`) allows `http://localhost:5173` by default (`CORS_ORIGINS`).
`VITE_API_BASE_URL` overrides the API origin.

## 3. Structure

```
src/
├── App.tsx                 # routing (pushState) and inspection session state
├── scene/                  # WebGL only — no React
│   ├── stepwellSpec.ts     # shared dimensions (3D model + section drawing)
│   ├── cameraPath.ts       # helical keyframes + C1 Hermite spline, pure functions
│   ├── stepwell.ts         # procedural geometry (merged + instanced)
│   ├── textures.ts         # procedural canvas textures (no image assets)
│   ├── materials.ts        # depth-shading shader injection
│   ├── atmosphere.ts       # sky, cloud sheets, light shaft, dust
│   ├── water.ts            # water surface shader
│   ├── quality.ts          # WebGL detection and quality tiers
│   └── DescentScene.ts     # renderer lifecycle, damping, adaptive resolution
├── components/
│   ├── HeroScene.tsx       # scroll measurement, overlay copy, fallbacks
│   ├── home/               # landing sections + StepwellSection drawing
│   ├── AppShell.tsx …      # workspace UI
├── hooks/                  # useReducedMotion, useReveal
├── services/api.ts         # all backend calls
└── utils/analysis.ts       # defensive readers for live/fixture payloads
```

## 4. The descent: how it works

- **Scroll model:** native scrolling over a tall section with a sticky canvas. There is no scroll hijacking, Lenis or GSAP. `HeroScene` maps the section's scroll offset to progress `p ∈ [0, 1]`. `DescentScene` eases its camera towards `p` with frame-rate-independent damping, so forward, reverse, fast and jump scrolling all land on the same pose.
- **Camera:** keys are sampled from a helix (`x = r cos θ`, `z = r sin θ`, `y` falling with `s`, 1.3 turns, radius 15.5 → 2.6 m). They are interpolated with non-uniform Catmull-Rom/Hermite tangents, giving continuous velocity without stops at keyframes. `isInsideVoid()` checks clearance against the geometry.
- **Overlay:** chapter opacity is written straight to the DOM from the same `p`, without a React re-render per frame.
- **Rendering cost:**
  - Rendering stops when the hero is off-screen or the tab is hidden.
  - The shadow map is rendered once, since nothing that casts shadows moves.
  - Pixel ratio adapts to measured frame time.
- **Quality tiers:** `high`, `medium` and `low` come from device signals and software-renderer detection. They vary pixel ratio, shadows, cloud layers, noise octaves, segment counts and dust.
- **Fallbacks:**
  - `prefers-reduced-motion` renders one still frame inside the well at normal page height.
  - No WebGL, or a lost context, shows the section drawing with the same headline.
  - "Skip the descent" and the "Start an inspection" CTA are always available.

## 5. Honesty rules enforced in the UI

- **Fixtures** load only on explicit action and are labelled everywhere they appear.
- **Analysis failures** are never replaced by the fixture.
- **Provenance:** each block is tagged *Model output*, *Rule-based engine* or *Requires expert verification*.
- **No model run:** if `vision.processing_metadata.model_version` lacks a YOLO tag, the findings are marked *Not from a trained model* and a warning is shown.
- **Confidence is not severity:** detection confidence and relative extent are shown separately, and pixel measurements are never presented as physical sizes.
- **Credentials:** none in the frontend. Uploads go through `POST /images/upload`.

## 6. Performance notes

- **Landing bundle:** the app shell is about 84 kB gzipped. three.js and the scene come in a lazy chunk of about 141 kB gzipped.
- **Measured** on an Apple M2 (Chrome, ANGLE/Metal, 1440×900, high tier): a steady 60 fps at the opening, mid-descent and water views (frame time p95 ≤ 17.5 ms). Lower-end GPUs have not been measured.

## 7. Known limitations

- The stepwell is a procedural composite, not a survey of any site. The carved frieze is abstract.
- The cloud sea is layered fBm sheets, not volumetric rendering.
- Inspection history is not implemented, so a session lasts only for the page lifetime.
