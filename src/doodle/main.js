import './doodle.css'
import { Sketch } from './sketch.js'
import { bindInput } from './input.js'

const LIGHTS = [
  { name: 'White', hex: '#ffffff' },
  { name: 'Ember', hex: '#ffb072' },
  { name: 'Ice', hex: '#8fd8ff' },
  { name: 'Orchid', hex: '#ff8fd0' },
  { name: 'Verdant', hex: '#9dffc0' },
]

const WEIGHTS = [
  { name: 'Fine', width: 4.5, bar: 1 },
  { name: 'Soft', width: 7.5, bar: 3 },
  { name: 'Bold', width: 15, bar: 6 },
]

const canvas = document.querySelector('#stage')
const hud = document.querySelector('#hud')
const fallback = document.querySelector('#fallback')

const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

let sketch
try {
  sketch = new Sketch(canvas, { reducedMotion })
} catch (error) {
  console.error('Light Room could not start:', error)
  fallback.hidden = false
  canvas.hidden = true
}

if (sketch) {
  start(sketch)
}

function start(sketch) {
  hud.hidden = false
  sketch.resize()

  const hint = document.querySelector('#hint')
  const depthFill = document.querySelector('#depth-fill')
  const depthMeter = document.querySelector('#depth-meter')
  const strokeCount = document.querySelector('#stroke-count')
  const undoButton = document.querySelector('#undo')
  const clearButton = document.querySelector('#clear')
  const saveButton = document.querySelector('#save')
  const recenterButton = document.querySelector('#recenter')

  buildSwatches(sketch)
  buildWeights(sketch)

  function refresh() {
    const count = sketch.strokeCount
    strokeCount.textContent = String(count)
    undoButton.disabled = count === 0
    clearButton.disabled = count === 0
    saveButton.disabled = count === 0

    const ratio = sketch.depthRatio
    depthFill.style.width = `${(ratio * 100).toFixed(1)}%`
    // Read out as "near" to "far" so the number means something to a person.
    depthMeter.setAttribute(
      'aria-label',
      `Drawing depth ${Math.round(ratio * 100)} percent, 0 is nearest`,
    )
  }

  sketch.on('change', refresh)
  refresh()

  function fire(button) {
    button.classList.remove('is-firing')
    // Force a reflow so the animation restarts on repeat presses.
    void button.offsetWidth
    button.classList.add('is-firing')
  }

  const actions = {
    onDrawStart() {
      hint.classList.add('is-hidden')
    },
    onDrawEnd: refresh,
    onUndo() {
      if (sketch.undo()) fire(undoButton)
    },
    onClear() {
      if (sketch.clear()) fire(clearButton)
    },
    onRecenter() {
      sketch.rig.recenter()
      fire(recenterButton)
    },
    onSave() {
      if (sketch.strokeCount === 0) return
      fire(saveButton)
      savePng(sketch)
    },
  }

  undoButton.addEventListener('click', actions.onUndo)
  clearButton.addEventListener('click', actions.onClear)
  saveButton.addEventListener('click', actions.onSave)
  recenterButton.addEventListener('click', actions.onRecenter)

  bindInput(sketch, canvas, actions)

  window.addEventListener('resize', () => sketch.resize())
  window.addEventListener('orientationchange', () => sketch.resize())

  canvas.addEventListener('webglcontextlost', (event) => {
    event.preventDefault()
    running = false
    fallback.textContent = 'The graphics context was lost. Reload to reopen the room.'
    fallback.hidden = false
  })

  let running = true
  let last = performance.now()

  document.addEventListener('visibilitychange', () => {
    // Coming back from a hidden tab should not replay a huge delta.
    if (!document.hidden) last = performance.now()
  })

  function frame(now) {
    if (!running) return
    requestAnimationFrame(frame)
    const delta = Math.min((now - last) / 1000, 0.05)
    last = now
    if (document.hidden) return
    sketch.update(delta)
  }

  requestAnimationFrame(frame)
}

function buildSwatches(sketch) {
  const host = document.querySelector('#swatches')
  host.setAttribute('role', 'radiogroup')
  host.setAttribute('aria-label', 'Light colour')

  const buttons = LIGHTS.map((light, index) => {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'swatch'
    button.setAttribute('role', 'radio')
    button.setAttribute('aria-checked', String(index === 0))
    button.setAttribute('aria-label', light.name)
    button.title = light.name
    button.style.color = light.hex

    const dot = document.createElement('i')
    button.append(dot)

    button.addEventListener('click', () => {
      sketch.setColor(light.hex)
      for (const other of buttons) other.setAttribute('aria-checked', String(other === button))
    })

    host.append(button)
    return button
  })
}

function buildWeights(sketch) {
  const host = document.querySelector('#weights')
  host.setAttribute('role', 'radiogroup')
  host.setAttribute('aria-label', 'Line weight')

  const buttons = WEIGHTS.map((weight, index) => {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'weight'
    button.setAttribute('role', 'radio')
    button.setAttribute('aria-checked', String(index === 1))
    button.setAttribute('aria-label', `${weight.name} line`)
    button.title = `${weight.name} line`

    const bar = document.createElement('i')
    bar.style.height = `${weight.bar}px`
    button.append(bar)

    button.addEventListener('click', () => {
      sketch.setWidth(weight.width)
      for (const other of buttons) other.setAttribute('aria-checked', String(other === button))
    })

    host.append(button)
    return button
  })

  sketch.setWidth(WEIGHTS[1].width)
}

function savePng(sketch) {
  const url = sketch.toDataURL()
  const link = document.createElement('a')
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  link.href = url
  link.download = `light-room-${stamp}.png`
  document.body.append(link)
  link.click()
  link.remove()
}
