import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  Color,
  DoubleSide,
  Mesh,
  ShaderMaterial,
  Vector2,
} from 'three'

// A stroke is a screen-space-expanded ribbon: the polyline the pointer traced is
// duplicated into two vertices per point, and the vertex shader pushes them apart
// along the screen-space normal of the segment. That keeps the light trail an even
// thickness no matter how far away it drifts, the way projected light behaves.

const MAX_POINTS = 1400
const FLOATS_PER_POINT = 2

const VERTEX_SHADER = /* glsl */ `
  attribute vec3 aPrev;
  attribute vec3 aNext;
  attribute float aSide;
  attribute float aIndex;

  uniform vec2 uResolution;
  uniform float uWidth;
  uniform float uTime;
  uniform float uSeed;
  uniform float uWobble;
  uniform float uCount;

  varying float vSide;
  varying float vProgress;

  // Slow three-axis drift so a finished doodle keeps breathing instead of
  // hanging in space like dead geometry.
  vec3 warp(vec3 p) {
    float t = uTime * 0.35 + uSeed;
    return p + vec3(
      sin(t + p.y * 0.55),
      sin(t * 1.13 + p.z * 0.55),
      sin(t * 0.87 + p.x * 0.55)
    ) * uWobble;
  }

  vec2 toScreen(vec4 clip, float aspect) {
    vec2 s = clip.xy / max(clip.w, 0.0001);
    s.x *= aspect;
    return s;
  }

  void main() {
    float aspect = uResolution.x / uResolution.y;
    mat4 mvp = projectionMatrix * modelViewMatrix;

    vec4 current = mvp * vec4(warp(position), 1.0);
    vec4 prev = mvp * vec4(warp(aPrev), 1.0);
    vec4 next = mvp * vec4(warp(aNext), 1.0);

    vec2 currentS = toScreen(current, aspect);
    vec2 prevS = toScreen(prev, aspect);
    vec2 nextS = toScreen(next, aspect);

    vec2 dirA = currentS - prevS;
    vec2 dirB = nextS - currentS;
    float lenA = length(dirA);
    float lenB = length(dirB);

    vec2 dir;
    if (lenA < 0.00001 && lenB < 0.00001) {
      dir = vec2(1.0, 0.0);
    } else if (lenA < 0.00001) {
      dir = dirB / lenB;
    } else if (lenB < 0.00001) {
      dir = dirA / lenA;
    } else {
      dir = normalize(dirA / lenA + dirB / lenB);
    }

    vec2 normal = vec2(-dir.y, dir.x);
    normal.x /= aspect;

    // uWidth is in device-independent pixels; convert to clip space.
    float halfWidth = uWidth / uResolution.y;

    vProgress = aIndex / max(uCount - 1.0, 1.0);
    vSide = aSide;

    current.xy += normal * aSide * halfWidth * current.w;
    gl_Position = current;
  }
`

const FRAGMENT_SHADER = /* glsl */ `
  precision highp float;

  uniform vec3 uColor;
  uniform float uOpacity;
  uniform float uDissolve;
  uniform float uHeadGlow;
  uniform float uTime;
  uniform float uSeed;

  varying float vSide;
  varying float vProgress;

  void main() {
    float d = abs(vSide);

    // Neon-tube profile: a solid lit core that fills the ribbon and softens only
    // at the very edge, wrapped in a wide haze for the bloom pass to pick up.
    float core = smoothstep(1.0, 0.5, d);
    float halo = exp(-d * d * 3.0) * 0.22;

    float alpha = core + halo;

    // Taper both ends so a trail resolves to a point instead of a cut ribbon.
    alpha *= smoothstep(0.0, 0.012, vProgress);
    alpha *= smoothstep(1.0, 0.975, vProgress);

    // Erase front travels from the tail to the tip when the piece is cleared.
    float cut = 1.0 - uDissolve;
    float erased = smoothstep(cut, cut + 0.1, vProgress);
    float flare = exp(-pow((vProgress - cut) * 26.0, 2.0)) * step(0.001, cut) * uDissolve;
    alpha *= erased;

    // A brighter bead sits at the tip while the trail is still being drawn,
    // then fades once the hand lifts.
    float head = exp(-pow((vProgress - 1.0) * 10.0, 2.0)) * uHeadGlow;

    // Slow shimmer travelling along the trail, like light down a fibre.
    float shimmer = 0.08 * sin(vProgress * 22.0 - uTime * 1.6 + uSeed * 6.28);

    // Keep a hot centre without washing the hue out entirely, or every colour
    // reads as plain white once the core is lit.
    vec3 color = mix(uColor, vec3(1.0), core * 0.6 + head * 0.4);
    float intensity = (alpha + flare * 0.6) * (1.0 + head * 0.7 + shimmer) * uOpacity * 1.35;

    if (intensity <= 0.002) discard;

    // Additive blending multiplies by source alpha, so the trail carries its
    // brightness in rgb alone — squaring it here would gut the softer haze.
    gl_FragColor = vec4(color * intensity, 1.0);
  }
`

export class Stroke {
  constructor({ color, width, resolution, seed = Math.random() }) {
    this.points = []
    this.count = 0
    this.capacity = MAX_POINTS
    this.finished = false
    this.dissolving = false
    this.dissolve = 1
    this.opacity = 0
    this.targetOpacity = 1
    this.headGlow = 1

    this.positions = new Float32Array(this.capacity * FLOATS_PER_POINT * 3)
    this.prev = new Float32Array(this.capacity * FLOATS_PER_POINT * 3)
    this.next = new Float32Array(this.capacity * FLOATS_PER_POINT * 3)
    this.side = new Float32Array(this.capacity * FLOATS_PER_POINT)
    this.indices = new Float32Array(this.capacity * FLOATS_PER_POINT)

    for (let i = 0; i < this.capacity; i += 1) {
      this.side[i * 2] = 1
      this.side[i * 2 + 1] = -1
      this.indices[i * 2] = i
      this.indices[i * 2 + 1] = i
    }

    const elements = new Uint32Array((this.capacity - 1) * 6)
    for (let i = 0; i < this.capacity - 1; i += 1) {
      const a = i * 2
      elements.set([a, a + 1, a + 2, a + 2, a + 1, a + 3], i * 6)
    }

    this.geometry = new BufferGeometry()
    this.geometry.setAttribute('position', new BufferAttribute(this.positions, 3))
    this.geometry.setAttribute('aPrev', new BufferAttribute(this.prev, 3))
    this.geometry.setAttribute('aNext', new BufferAttribute(this.next, 3))
    this.geometry.setAttribute('aSide', new BufferAttribute(this.side, 1))
    this.geometry.setAttribute('aIndex', new BufferAttribute(this.indices, 1))
    this.geometry.setIndex(new BufferAttribute(elements, 1))
    this.geometry.setDrawRange(0, 0)
    // The ribbon is built in the shader, so three cannot derive useful bounds.
    this.geometry.boundingSphere = null
    this.geometry.frustumCulled = false

    this.material = new ShaderMaterial({
      uniforms: {
        uResolution: { value: new Vector2(resolution.x, resolution.y) },
        uWidth: { value: width },
        uColor: { value: new Color(color) },
        uOpacity: { value: 0 },
        uDissolve: { value: 1 },
        uHeadGlow: { value: 1 },
        uCount: { value: 1 },
        uTime: { value: 0 },
        uSeed: { value: seed },
        uWobble: { value: 0 },
      },
      vertexShader: VERTEX_SHADER,
      fragmentShader: FRAGMENT_SHADER,
      transparent: true,
      blending: AdditiveBlending,
      depthWrite: false,
      side: DoubleSide,
    })

    this.mesh = new Mesh(this.geometry, this.material)
    this.mesh.frustumCulled = false
    this.mesh.renderOrder = 2
  }

  get isFull() {
    return this.count >= this.capacity
  }

  addPoint(point) {
    if (this.isFull || this.finished) return

    const i = this.count
    const base = i * 6

    for (let v = 0; v < 2; v += 1) {
      const o = base + v * 3
      this.positions[o] = point.x
      this.positions[o + 1] = point.y
      this.positions[o + 2] = point.z
    }

    // The first point has no predecessor and the newest has no successor yet;
    // both point at themselves until a neighbour shows up.
    const prevIndex = i > 0 ? i - 1 : i
    this.copyPoint(this.prev, i, prevIndex)
    this.copyPoint(this.next, i, i)

    if (i > 0) {
      this.copyPoint(this.next, i - 1, i)
    }

    this.points.push(point.clone())
    this.count += 1

    this.geometry.setDrawRange(0, Math.max(this.count - 1, 0) * 6)
    this.material.uniforms.uCount.value = this.count

    this.geometry.attributes.position.needsUpdate = true
    this.geometry.attributes.aPrev.needsUpdate = true
    this.geometry.attributes.aNext.needsUpdate = true
  }

  copyPoint(target, at, from) {
    const src = from * 6
    const dst = at * 6
    for (let v = 0; v < 2; v += 1) {
      target[dst + v * 3] = this.positions[src]
      target[dst + v * 3 + 1] = this.positions[src + 1]
      target[dst + v * 3 + 2] = this.positions[src + 2]
    }
  }

  // Once the pointer lifts, swap the pre-allocated buffers for exact-size ones so
  // a long session does not hold hundreds of mostly-empty megabytes on the GPU.
  finalize() {
    if (this.finished) return
    this.finished = true

    const points = this.count
    if (points < 2) {
      this.geometry.setDrawRange(0, 0)
      return
    }

    const verts = points * 2
    const trimmed = new BufferGeometry()
    trimmed.setAttribute('position', new BufferAttribute(this.positions.slice(0, verts * 3), 3))
    trimmed.setAttribute('aPrev', new BufferAttribute(this.prev.slice(0, verts * 3), 3))
    trimmed.setAttribute('aNext', new BufferAttribute(this.next.slice(0, verts * 3), 3))
    trimmed.setAttribute('aSide', new BufferAttribute(this.side.slice(0, verts), 1))
    trimmed.setAttribute('aIndex', new BufferAttribute(this.indices.slice(0, verts), 1))

    const elements = new Uint32Array((points - 1) * 6)
    for (let i = 0; i < points - 1; i += 1) {
      const a = i * 2
      elements.set([a, a + 1, a + 2, a + 2, a + 1, a + 3], i * 6)
    }
    trimmed.setIndex(new BufferAttribute(elements, 1))
    trimmed.boundingSphere = null

    this.geometry.dispose()
    this.geometry = trimmed
    this.mesh.geometry = trimmed

    this.positions = null
    this.prev = null
    this.next = null
    this.side = null
    this.indices = null

  }

  startDissolve() {
    this.dissolving = true
  }

  setResolution(width, height) {
    this.material.uniforms.uResolution.value.set(width, height)
  }

  // Returns false once the stroke has finished dissolving and can be removed.
  update(time, delta, motion) {
    const u = this.material.uniforms
    u.uTime.value = time
    u.uWobble.value = 0.014 * motion

    this.opacity += (this.targetOpacity - this.opacity) * Math.min(delta * 9, 1)
    u.uOpacity.value = this.opacity

    // The tip bead burns while drawing and decays over ~0.4s after release.
    this.headGlow += ((this.finished ? 0 : 1) - this.headGlow) * Math.min(delta * 7, 1)
    u.uHeadGlow.value = this.headGlow

    if (this.dissolving) {
      this.dissolve = Math.max(0, this.dissolve - delta * 0.9)
      u.uDissolve.value = this.dissolve
      if (this.dissolve <= 0) return false
    }

    return true
  }

  dispose() {
    this.geometry.dispose()
    this.material.dispose()
  }
}
