import {
  AdditiveBlending,
  Color,
  Mesh,
  PerspectiveCamera,
  PlaneGeometry,
  Scene,
  ShaderMaterial,
  Vector2,
  Vector3,
  WebGLRenderer,
} from 'three'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

import { Environment } from './environment.js'
import { CameraRig } from './camera-rig.js'
import { Stroke } from './strokes.js'

const MAX_STROKES = 140
const BASE_RADIUS = 6.4

export class Sketch {
  constructor(canvas, { reducedMotion = false } = {}) {
    this.canvas = canvas
    this.reducedMotion = reducedMotion
    this.size = new Vector2(canvas.clientWidth || 1, canvas.clientHeight || 1)

    this.renderer = new WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
      // Needed so a still can be lifted out of the canvas on demand.
      preserveDrawingBuffer: true,
    })
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    this.renderer.setSize(this.size.x, this.size.y, false)
    this.renderer.setClearColor(0x000000, 1)

    this.scene = new Scene()
    this.camera = new PerspectiveCamera(46, this.size.x / this.size.y, 0.1, 200)
    this.rig = new CameraRig(this.camera, { radius: BASE_RADIUS, reducedMotion })

    this.environment = new Environment(this.size)

    this.composer = new EffectComposer(this.renderer)
    this.composer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    this.composer.setSize(this.size.x, this.size.y)

    const roomPass = new RenderPass(this.environment.scene, this.environment.camera)
    const strokePass = new RenderPass(this.scene, this.camera)
    // The room has already painted the frame; the strokes composite on top of it.
    strokePass.clear = false
    // Threshold sits above the wall's brightness so only the drawn light blooms;
    // a lower one smears the whole room into a single white haze.
    this.bloom = new UnrealBloomPass(new Vector2(this.size.x, this.size.y), 0.78, 0.45, 0.55)

    this.composer.addPass(roomPass)
    this.composer.addPass(strokePass)
    this.composer.addPass(this.bloom)
    this.composer.addPass(new OutputPass())

    this.strokes = []
    this.active = null
    this.dissolveQueue = []
    this.dissolveTimer = 0

    this.color = '#ffffff'
    this.width = 7.5
    this.depth = BASE_RADIUS
    this.minDepth = BASE_RADIUS - 2.6
    this.maxDepth = BASE_RADIUS + 2.6
    this.depthOffset = 0
    this.targetDepthOffset = 0

    this.pointerNdc = new Vector2(0, 0)
    this.smoothedNdc = new Vector2(0, 0)
    this.lastSampleTime = 0
    this.lastClientPoint = new Vector2(0, 0)

    this.frozenCamera = null
    this.scratch = new Vector3()
    this.rayDir = new Vector3()
    this.point = new Vector3()

    this.cursor = this.createCursor()
    this.scene.add(this.cursor)

    this.time = 0
    this.listeners = { change: [] }
  }

  on(event, handler) {
    this.listeners[event]?.push(handler)
  }

  emit(event, payload) {
    for (const handler of this.listeners[event] || []) handler(payload)
  }

  createCursor() {
    const material = new ShaderMaterial({
      uniforms: {
        uOpacity: { value: 0 },
        uColor: { value: new Color(this.color) },
      },
      vertexShader: /* glsl */ `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: /* glsl */ `
        precision highp float;
        uniform float uOpacity;
        uniform vec3 uColor;
        varying vec2 vUv;
        void main() {
          float d = length(vUv - 0.5) * 2.0;
          float core = exp(-d * d * 30.0);
          float ring = exp(-pow((d - 0.62) * 7.0, 2.0)) * 0.35;
          float a = (core + ring) * uOpacity;
          if (a <= 0.002) discard;
          gl_FragColor = vec4(mix(uColor, vec3(1.0), core) * a, a);
        }
      `,
      transparent: true,
      blending: AdditiveBlending,
      depthWrite: false,
      depthTest: false,
    })

    const mesh = new Mesh(new PlaneGeometry(1, 1), material)
    mesh.frustumCulled = false
    mesh.renderOrder = 3
    mesh.visible = false
    return mesh
  }

  setColor(hex) {
    this.color = hex
    this.cursor.material.uniforms.uColor.value.set(hex)
  }

  setWidth(width) {
    this.width = width
  }

  get depthRatio() {
    return (this.depth - this.minDepth) / (this.maxDepth - this.minDepth)
  }

  nudgeDepth(amount) {
    this.depth = clamp(this.depth + amount, this.minDepth, this.maxDepth)
    this.emit('change')
  }

  zoom(amount) {
    this.rig.zoomBy(amount)
  }

  orbit(dx, dy) {
    this.rig.orbitBy(dx, dy)
  }

  setOrbiting(value) {
    this.rig.orbiting = value
  }

  // Places a pointer sample on the drawing shell: a spherical surface a fixed
  // distance in front of the camera as it stood when the stroke began. Freezing
  // the basis means the ambient drift cannot smear a stroke mid-draw, and the
  // curve stays where the hand put it once the room starts moving again.
  projectToShell(ndcX, ndcY, distance) {
    const cam = this.frozenCamera || this.camera
    this.scratch.set(ndcX, ndcY, 0.5).unproject(cam)
    this.rayDir.copy(this.scratch).sub(cam.position).normalize()
    return this.point.copy(cam.position).addScaledVector(this.rayDir, distance)
  }

  worldPerPixel(distance) {
    const height = 2 * Math.tan((this.camera.fov * Math.PI) / 360) * distance
    return height / Math.max(this.size.y, 1)
  }

  beginStroke(ndcX, ndcY, clientX, clientY, time) {
    this.finishStroke()

    this.frozenCamera = this.camera.clone()
    this.frozenCamera.updateMatrixWorld(true)

    this.smoothedNdc.set(ndcX, ndcY)
    this.pointerNdc.set(ndcX, ndcY)
    this.lastClientPoint.set(clientX, clientY)
    this.lastSampleTime = time
    this.depthOffset = 0
    this.targetDepthOffset = 0

    const stroke = new Stroke({
      color: this.color,
      width: this.width,
      resolution: this.size,
      seed: Math.random(),
    })
    stroke.addPoint(this.projectToShell(ndcX, ndcY, this.depth))

    this.active = stroke
    this.strokes.push(stroke)
    this.scene.add(stroke.mesh)
    this.rig.drawing = true

    this.trimOldStrokes()
    this.emit('change')
  }

  extendStroke(ndcX, ndcY, clientX, clientY, time) {
    const stroke = this.active
    if (!stroke) return

    this.pointerNdc.set(ndcX, ndcY)

    const dt = Math.max(time - this.lastSampleTime, 0.0005)
    const speed = this.lastClientPoint.distanceTo(TEMP_V2.set(clientX, clientY)) / dt
    this.lastClientPoint.set(clientX, clientY)
    this.lastSampleTime = time

    // Speed reads as pressure against the wall: a quick flick lays its trail
    // further back, a slow deliberate line stays close. That is what gives a
    // single gesture genuine depth instead of a flat decal.
    this.targetDepthOffset = clamp(speed / 900, 0, 1) * 1.5
    this.depthOffset += (this.targetDepthOffset - this.depthOffset) * 0.12

    // Smooth the raw pointer so hand jitter does not become visible chatter.
    this.smoothedNdc.x += (ndcX - this.smoothedNdc.x) * 0.3
    this.smoothedNdc.y += (ndcY - this.smoothedNdc.y) * 0.3

    const distance = this.depth + this.depthOffset
    const candidate = this.projectToShell(this.smoothedNdc.x, this.smoothedNdc.y, distance)

    const last = stroke.points[stroke.points.length - 1]
    const minSpacing = this.worldPerPixel(distance) * 2.5
    if (last && last.distanceTo(candidate) < minSpacing) return

    stroke.addPoint(candidate)

    if (stroke.isFull) {
      // Continue seamlessly in a fresh stroke rather than dropping the gesture.
      const carry = candidate.clone()
      this.finishStroke()
      const next = new Stroke({
        color: this.color,
        width: this.width,
        resolution: this.size,
        seed: Math.random(),
      })
      next.addPoint(carry)
      this.active = next
      this.strokes.push(next)
      this.scene.add(next.mesh)
      this.trimOldStrokes()
    }
  }

  finishStroke() {
    if (!this.active) return
    const stroke = this.active
    this.active = null
    this.rig.drawing = false
    this.frozenCamera = null

    if (stroke.count < 2) {
      this.removeStroke(stroke)
    } else {
      stroke.finalize()
    }
    this.emit('change')
  }

  trimOldStrokes() {
    const live = this.strokes.filter((s) => !s.dissolving)
    const excess = live.length - MAX_STROKES
    for (let i = 0; i < excess; i += 1) {
      live[i].startDissolve()
    }
  }

  removeStroke(stroke) {
    const index = this.strokes.indexOf(stroke)
    if (index !== -1) this.strokes.splice(index, 1)
    this.scene.remove(stroke.mesh)
    stroke.dispose()
  }

  undo() {
    for (let i = this.strokes.length - 1; i >= 0; i -= 1) {
      const stroke = this.strokes[i]
      if (!stroke.dissolving && stroke !== this.active) {
        stroke.startDissolve()
        this.emit('change')
        return true
      }
    }
    return false
  }

  clear() {
    this.finishStroke()
    const pending = this.strokes.filter((s) => !s.dissolving)
    if (!pending.length) return false
    // Staggered so the wall empties in a wave rather than blinking out.
    this.dissolveQueue = pending.reverse()
    this.dissolveTimer = 0
    this.emit('change')
    return true
  }

  get strokeCount() {
    return this.strokes.filter((s) => !s.dissolving).length
  }

  resize() {
    const width = this.canvas.clientWidth || window.innerWidth
    const height = this.canvas.clientHeight || window.innerHeight
    this.size.set(width, height)

    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    this.renderer.setSize(width, height, false)
    this.composer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    this.composer.setSize(width, height)
    this.bloom.setSize(width, height)

    this.camera.aspect = width / height
    this.camera.updateProjectionMatrix()

    this.environment.setResolution(width, height)
    for (const stroke of this.strokes) stroke.setResolution(width, height)
  }

  updateCursor(delta) {
    const visible = this.pointerActive
    const distance = this.depth + (this.active ? this.depthOffset : 0)
    const position = this.projectToShell(this.pointerNdc.x, this.pointerNdc.y, distance)

    this.cursor.position.copy(position)
    this.cursor.quaternion.copy(this.camera.quaternion)
    const scale = this.worldPerPixel(distance) * (this.active ? 44 : 62)
    this.cursor.scale.setScalar(scale)

    const target = visible ? (this.active ? 0.9 : 0.42) : 0
    const u = this.cursor.material.uniforms.uOpacity
    u.value += (target - u.value) * Math.min(delta * 8, 1)
    this.cursor.visible = u.value > 0.004
  }

  update(delta) {
    this.time += delta

    if (this.dissolveQueue.length) {
      this.dissolveTimer += delta
      while (this.dissolveQueue.length && this.dissolveTimer > 0.035) {
        this.dissolveTimer -= 0.035
        this.dissolveQueue.pop().startDissolve()
      }
    }

    this.rig.update(delta)

    const motion = this.reducedMotion ? 0.25 : 1
    for (let i = this.strokes.length - 1; i >= 0; i -= 1) {
      const stroke = this.strokes[i]
      if (!stroke.update(this.time, delta, motion)) {
        this.removeStroke(stroke)
        this.emit('change')
      }
    }

    this.environment.setEnergy(this.active ? 1 : this.pointerActive ? 0.34 : 0)
    this.environment.update(this.time, delta)
    this.updateCursor(delta)

    this.composer.render(delta)
  }

  toDataURL() {
    // Re-render immediately before reading so the buffer is guaranteed current.
    this.composer.render(0.016)
    return this.renderer.domElement.toDataURL('image/png')
  }

  dispose() {
    for (const stroke of this.strokes) stroke.dispose()
    this.strokes = []
    this.cursor.geometry.dispose()
    this.cursor.material.dispose()
    this.environment.dispose()
    this.composer.dispose()
    this.renderer.dispose()
  }
}

const TEMP_V2 = new Vector2()

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}
