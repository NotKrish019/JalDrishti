import * as THREE from 'three';
import { STEPWELL, WATER_RADIUS, WATER_Y } from './stepwellSpec';

/**
 * Still well water. Surface normals come from a few analytic sine swells plus
 * occasional ripple rings; colour is a deep jade body mixed with a Fresnel
 * reflection of what the surface can actually see from the bottom of the well:
 * the bright disc of sky through the rim, and shadowed stone everywhere else.
 */
export const createWater = (segments: number) => {
  const geo = new THREE.CircleGeometry(WATER_RADIUS + 0.2, segments);
  geo.rotateX(-Math.PI / 2);

  // Half-angle of the sky aperture seen from the water centre: the rim is the tightest edge.
  const rimHeight = -WATER_Y;
  const openingCos = Math.cos(Math.atan(STEPWELL.rimRadius / rimHeight));

  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uDeep: { value: new THREE.Color('#0b1d18') },
      uBody: { value: new THREE.Color('#1d4338') },
      uSky: { value: new THREE.Color('#c9c2ae') },
      uStone: { value: new THREE.Color('#5a4635') },
      uOpeningCos: { value: openingCos },
      uRadius: { value: WATER_RADIUS },
      uCalm: { value: 1 },
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
      uniform float uTime; uniform vec3 uDeep; uniform vec3 uBody; uniform vec3 uSky; uniform vec3 uStone;
      uniform float uOpeningCos; uniform float uRadius; uniform float uCalm;
      varying vec3 vWorld;

      vec2 swell(vec2 p, vec2 dir, float freq, float amp, float speed) {
        float ph = dot(p, dir) * freq + uTime * speed;
        return dir * freq * amp * cos(ph);
      }

      void main() {
        vec2 p = vWorld.xz;
        vec2 g = vec2(0.0);
        g += swell(p, normalize(vec2(1.0, 0.3)), 1.3, 0.006, 0.5);
        g += swell(p, normalize(vec2(-0.4, 1.0)), 2.4, 0.004, 0.75);
        g += swell(p, normalize(vec2(0.7, -0.8)), 4.6, 0.0025, 1.1);
        g += swell(p, normalize(vec2(-0.9, -0.2)), 8.3, 0.0014, 1.6);

        // Occasional ripple rings — a drip from the shaft, a leaf landing.
        for (int i = 0; i < 3; i++) {
          float fi = float(i);
          float phase = uTime * 0.09 + fi * 0.37;
          float cycle = floor(phase);
          float age = fract(phase);
          vec2 c = vec2(sin(cycle * 12.9 + fi * 3.1), cos(cycle * 7.3 + fi * 1.7)) * uRadius * 0.55;
          vec2 d = p - c;
          float dist = length(d) + 1e-4;
          float front = age * 7.0;
          float ring = sin((dist - front) * 7.0) * exp(-abs(dist - front) * 2.2) * (1.0 - age);
          g += (d / dist) * ring * 0.035;
        }
        g *= uCalm;

        vec3 N = normalize(vec3(-g.x, 1.0, -g.y));
        vec3 V = normalize(cameraPosition - vWorld);
        float fres = 0.02 + 0.98 * pow(1.0 - max(dot(N, V), 0.0), 5.0);
        vec3 R = reflect(-V, N);

        float sky = smoothstep(uOpeningCos - 0.035, uOpeningCos + 0.035, R.y);
        vec3 refl = mix(uStone * mix(0.35, 1.0, smoothstep(0.1, 0.8, R.y)), uSky, sky);

        float r = length(p) / uRadius;
        vec3 body = mix(uBody, uDeep, smoothstep(0.15, 1.0, r) * 0.85);
        // Faint suspended-silt scatter
        body += vec3(0.02, 0.035, 0.028) * (1.0 - r);

        float reflWeight = max(fres, sky * 0.1);
        vec3 col = mix(body, refl, clamp(reflWeight, 0.0, 0.9));
        // Dark meniscus against the shaft wall
        col *= mix(1.0, 0.55, smoothstep(0.88, 1.0, r));

        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.y = WATER_Y;
  mesh.name = 'water';

  return {
    mesh,
    update: (time: number, calm: number) => {
      mat.uniforms.uTime.value = time;
      mat.uniforms.uCalm.value = calm;
    },
    dispose: () => (geo.dispose(), mat.dispose()),
  };
};
