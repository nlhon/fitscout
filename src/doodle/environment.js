import {
  Mesh,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
  ShaderMaterial,
  Vector2,
} from 'three'

// The room: a fullscreen quad standing in for the projected wall. Everything here
// is deliberately dim so the doodle stays the only real light source, and so the
// bloom pass has nothing but the strokes to catch.

const MAX_RIPPLES = 6

const FRAGMENT_SHADER = /* glsl */ `
  precision highp float;

  uniform float uTime;
  uniform vec2 uResolution;
  uniform vec2 uPointer;
  uniform float uEnergy;
  uniform vec3 uRipples[${MAX_RIPPLES}];
  uniform float uReveal;

  varying vec2 vUv;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  void main() {
    float aspect = uResolution.x / uResolution.y;
    vec2 uv = vUv;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    // Off-centre warm wash, as if a single projector sits high and to the left.
    vec2 light = vec2(-0.16, 0.12);
    float d = length(p - light);

    vec3 deep = vec3(0.050, 0.052, 0.062);
    vec3 warm = vec3(0.225, 0.205, 0.183);
    vec3 color = mix(warm, deep, smoothstep(0.05, 1.15, d));

    // Very slow concentric rings drifting outward through the wash.
    float rings = sin(d * 17.0 - uTime * 0.22);
    rings += 0.55 * sin(d * 9.0 + uTime * 0.13);
    color += rings * 0.012 * smoothstep(1.2, 0.15, d);

    // Halo tracking the drawing hand.
    vec2 ph = p - (uPointer - 0.5) * vec2(aspect, 1.0);
    float pd = length(ph);
    color += vec3(0.34, 0.33, 0.31) * exp(-pd * pd * 11.0) * uEnergy * 0.3;
    color += vec3(0.2) * exp(-pow((pd - 0.16) * 12.0, 2.0)) * uEnergy * 0.18;

    // Rings shed on each new contact with the wall.
    for (int i = 0; i < ${MAX_RIPPLES}; i++) {
      vec3 r = uRipples[i];
      float age = uTime - r.z;
      if (r.z <= 0.0 || age < 0.0 || age > 3.0) continue;
      vec2 rp = p - (r.xy - 0.5) * vec2(aspect, 1.0);
      float rd = length(rp);
      float radius = age * 0.42;
      float band = exp(-pow((rd - radius) * 16.0, 2.0));
      color += vec3(0.26, 0.25, 0.24) * band * (1.0 - age / 3.0) * 0.4;
    }

    // Vignette, then a little grain so the flat gradient does not band.
    float vignette = smoothstep(1.5, 0.28, length(p));
    color *= 0.35 + vignette * 0.65;
    color += (hash(uv * uResolution + fract(uTime)) - 0.5) * 0.012;

    // The wall is authored in display values; the composer works in linear
    // space and converts back on output, so undo that conversion here.
    color = pow(max(color, 0.0), vec3(2.2));

    gl_FragColor = vec4(color * uReveal, 1.0);
  }
`

export class Environment {
  constructor(resolution) {
    this.scene = new Scene()
    this.camera = new OrthographicCamera(-1, 1, 1, -1, 0, 1)

    this.ripples = new Array(MAX_RIPPLES)
    for (let i = 0; i < MAX_RIPPLES; i += 1) {
      this.ripples[i] = { x: 0.5, y: 0.5, t: 0 }
    }
    this.rippleCursor = 0
    this.energy = 0
    this.targetEnergy = 0

    this.material = new ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uResolution: { value: new Vector2(resolution.x, resolution.y) },
        uPointer: { value: new Vector2(0.5, 0.5) },
        uEnergy: { value: 0 },
        uReveal: { value: 0 },
        uRipples: { value: new Float32Array(MAX_RIPPLES * 3) },
      },
      vertexShader: /* glsl */ `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = vec4(position.xy, 0.0, 1.0);
        }
      `,
      fragmentShader: FRAGMENT_SHADER,
      depthTest: false,
      depthWrite: false,
    })

    const mesh = new Mesh(new PlaneGeometry(2, 2), this.material)
    mesh.frustumCulled = false
    this.scene.add(mesh)
    this.mesh = mesh
  }

  emitRipple(x, y, time) {
    const slot = this.ripples[this.rippleCursor]
    slot.x = x
    slot.y = y
    slot.t = time
    this.rippleCursor = (this.rippleCursor + 1) % MAX_RIPPLES
  }

  setPointer(x, y) {
    this.material.uniforms.uPointer.value.set(x, y)
  }

  setEnergy(value) {
    this.targetEnergy = value
  }

  setResolution(width, height) {
    this.material.uniforms.uResolution.value.set(width, height)
  }

  update(time, delta) {
    const u = this.material.uniforms
    u.uTime.value = time

    this.energy += (this.targetEnergy - this.energy) * Math.min(delta * 4, 1)
    u.uEnergy.value = this.energy

    u.uReveal.value = Math.min(1, u.uReveal.value + delta * 0.7)

    const data = u.uRipples.value
    for (let i = 0; i < MAX_RIPPLES; i += 1) {
      const r = this.ripples[i]
      data[i * 3] = r.x
      data[i * 3 + 1] = r.y
      data[i * 3 + 2] = r.t
    }
  }

  dispose() {
    this.mesh.geometry.dispose()
    this.material.dispose()
  }
}
