import { Spherical, Vector3 } from 'three'

// Custom orbit rig rather than OrbitControls: drawing owns the primary drag, so
// orbiting is a secondary gesture, and the camera has to drift on its own when
// nobody is touching it — that idle drift is what turns a flat-looking scribble
// into something visibly suspended in space.

const IDLE_DELAY = 2.6

export class CameraRig {
  constructor(camera, { radius = 6.4, reducedMotion = false } = {}) {
    this.camera = camera
    this.target = new Vector3(0, 0, 0)
    this.spherical = new Spherical(radius, Math.PI / 2, 0)
    this.goal = this.spherical.clone()
    this.baseRadius = radius
    this.reducedMotion = reducedMotion

    this.idleFor = 0
    this.drift = 0
    this.driftPhase = Math.random() * Math.PI * 2
    this.orbiting = false
    this.drawing = false

    this.minRadius = radius * 0.55
    this.maxRadius = radius * 1.9
    this.minPhi = 0.35
    this.maxPhi = Math.PI - 0.35

    this.apply()
  }

  get position() {
    return this.camera.position
  }

  orbitBy(dx, dy) {
    this.goal.theta -= dx * 0.0042
    this.goal.phi = clamp(this.goal.phi - dy * 0.0042, this.minPhi, this.maxPhi)
    this.wake()
  }

  zoomBy(amount) {
    this.goal.radius = clamp(this.goal.radius * (1 + amount), this.minRadius, this.maxRadius)
    this.wake()
  }

  wake() {
    this.idleFor = 0
  }

  recenter() {
    this.goal.theta = 0
    this.goal.phi = Math.PI / 2
    this.goal.radius = this.baseRadius
    this.drift = 0
    this.wake()
  }

  update(delta) {
    const active = this.orbiting || this.drawing

    if (active) {
      this.idleFor = 0
    } else {
      this.idleFor += delta
    }

    // Ease the autonomous drift in only after the room has been left alone, and
    // ease it back out the moment somebody starts drawing again.
    const wants = !active && this.idleFor > IDLE_DELAY && !this.reducedMotion ? 1 : 0
    this.drift += (wants - this.drift) * Math.min(delta * 1.4, 1)

    if (this.drift > 0.001) {
      this.driftPhase += delta * 0.28
      this.goal.theta += delta * 0.048 * this.drift
      this.goal.phi = clamp(
        this.goal.phi + Math.sin(this.driftPhase) * delta * 0.05 * this.drift,
        this.minPhi,
        this.maxPhi,
      )
    }

    const ease = Math.min(delta * 3.4, 1)
    this.spherical.theta += (this.goal.theta - this.spherical.theta) * ease
    this.spherical.phi += (this.goal.phi - this.spherical.phi) * ease
    this.spherical.radius += (this.goal.radius - this.spherical.radius) * ease

    this.apply()
  }

  apply() {
    this.camera.position.setFromSpherical(this.spherical).add(this.target)
    this.camera.lookAt(this.target)
    this.camera.updateMatrixWorld()
  }
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}
