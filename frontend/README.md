# JalDrishti Frontend

**Owner:** Anika Jain (Frontend) · Team NeuralX
**Stack:** React 18, Vite 5, TypeScript, Tailwind CSS 3, three.js (landing scene only)

---

## 1. What lives here

- **Landing experience** (`/`): opens with the JalDrishti wordmark over an illustrative stepwell in an old, overgrown heritage precinct (walled court, arcaded pavilion, gateway and approach, surrounded by woodland, ruined pavilions, a colonnade remnant, broken precinct walls, a ruined arch, old flagstone paths and a cenotaph group), then a scroll-driven descent to the water in six chapters. The stepwell is one example; the copy covers India's wider water heritage. It resolves into: the diversity of forms (with honest knowledge-base coverage), why documentation matters, See → Understand → Assess → Revive (with live material compatibility), one platform for different contexts (mission vs. what is built today), our approach and the call to action.
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
│   ├── siteSpec.ts         # layout of the surrounding site (gateway, pavilion, path)
│   ├── environment.ts      # terrain, precinct architecture and ruins, paths, trees, shrubs, ground cover, shadow decals
│   ├── cameraPath.ts       # helical keyframes + C1 Hermite spline, pure functions
│   ├── stepwell.ts         # procedural geometry (merged + instanced)
│   ├── textures.ts         # procedural canvas textures (no image assets)
│   ├── materials.ts        # depth-shading shader injection
│   ├── atmosphere.ts       # sky, light shaft, dust
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
- **Camera:** the path opens on an elevated three-quarter view of the whole site, holds, then swings in to the rim (`p` 0 → 0.3). On wide screens the opening is framed right of centre (film offset); on portrait screens it is lifted (view offset). Both ease out before the rim. The descent keys are sampled from a helix (`x = r cos θ`, `z = r sin θ`, `y` falling with `s`, 1.3 turns, radius 15.5 → 2.6 m). They are interpolated with non-uniform Catmull-Rom/Hermite tangents, giving continuous velocity without stops at keyframes. `isInsideVoid()` checks clearance against the geometry.
- **Overlay:** scroll only sets the camera's target. The scene reports its eased progress each frame (`onProgress`) and chapter opacity is written straight to the DOM from that value, so copy and camera stay in step in both directions (verified: 0 mismatch over ~1,000 frames of wheel and jump scrolling). The scene is created at the measured scroll position (`initialProgress`), so a reload mid-page never flashes the opening pose.
- **Helix entry:** the turn rate ramps up over the first 10% of the spiral instead of starting at full speed, removing the whip at the rim.
- **Debugging:** in development only, the live scene is available as `window.__jdDescent`.
- **Rendering cost:**
  - Rendering stops when the hero is off-screen or the tab is hidden.
  - The shadow map is rendered once, since nothing that casts shadows moves.
  - Pixel ratio adapts to measured frame time.
- **Quality tiers:** `high`, `medium` and `low` come from device signals and software-renderer detection. They vary pixel ratio, shadows, foliage detail, landscape density, segment counts and dust.
- **Fallbacks:**
  - The first paint is `public/hero/opening.jpg`, a still rendered from the scene's own opening view; the canvas cross-fades over it once ready.
  - `prefers-reduced-motion` renders one still frame of the site at normal page height, followed by the six chapters as a readable list.
  - No WebGL, or a lost context, keeps the rendered still (captioned as such) and the same chapter list.
  - "Skip the descent" and the "Start an inspection" CTA are always available.

## 5. Honesty rules enforced in the UI

- **Fixtures** load only on explicit action and are labelled everywhere they appear.
- **Analysis failures** are never replaced by the fixture.
- **Provenance:** each block is tagged *Model output*, *Rule-based engine* or *Requires expert verification*.
- **No model run:** if `vision.processing_metadata.model_version` lacks a YOLO tag, the findings are marked *Not from a trained model* and a warning is shown.
- **Confidence is not severity:** detection confidence and relative extent are shown separately, and pixel measurements are never presented as physical sizes.
- **Credentials:** none in the frontend. Uploads go through `POST /images/upload`.

## 6. Performance notes

- **Landing bundle:** the app shell is about 86 kB gzipped. three.js, the scene and the site come in a lazy chunk of about 157 kB gzipped. The poster still is about 210 kB.
- **Site cost:** architecture is merged per material (ruins share one weathered-stone material), each of the five tree forms is one instanced mesh, as are shrubs, ground cover, path flagstones and fallen blocks; tree shadows are instanced decals (the shadow map covers only the court, gateway and pavilion). Detail drops with distance by form: characterful near trees get finer crowns, the far canopy uses the cheapest form, and nothing is planted in the wedge behind the opening camera. About 25 draw calls per frame.
- **Measured** on an Apple M2 (Chrome, ANGLE/Metal, 1440×900, high tier): a steady 60 fps at the opening, mid-descent and water views, about 1.25M triangles per frame. Lower-end GPUs have not been measured.

## 7. Known limitations

- The stepwell is a procedural composite, not a survey of any site. The carved frieze is abstract.
- The surrounding precinct is also procedural and illustrative: its layout follows the reference images in spirit, not any real monument. Trees are stylised crowns of displaced leaf clumps, not botanical models. Medium and low quality tiers plant fewer distant trees and use coarser crowns; only the high tier has been measured.
- The scene is generated in three.js at load time; no Blender or glTF assets are used.
- Inspection history is not implemented, so a session lasts only for the page lifetime.
