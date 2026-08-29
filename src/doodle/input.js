// Gesture routing. One pointer draws; a second pointer (or a right/middle drag)
// takes over as orbit + pinch, because moving around the doodle has to stay
// available without ever stealing the primary drag from the drawing hand.

export function bindInput(sketch, canvas, actions) {
  const pointers = new Map()
  let drawingId = null
  let orbitId = null
  let pinchDistance = 0
  let pinchCenter = { x: 0, y: 0 }

  const rect = () => canvas.getBoundingClientRect()

  function toNdc(event, box) {
    return {
      x: ((event.clientX - box.left) / box.width) * 2 - 1,
      y: -(((event.clientY - box.top) / box.height) * 2 - 1),
      u: (event.clientX - box.left) / box.width,
      v: 1 - (event.clientY - box.top) / box.height,
    }
  }

  function now() {
    return performance.now() / 1000
  }

  function beginPinch() {
    const [a, b] = [...pointers.values()]
    pinchDistance = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)
    pinchCenter = { x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2 }
  }

  function onPointerDown(event) {
    canvas.setPointerCapture?.(event.pointerId)
    pointers.set(event.pointerId, { clientX: event.clientX, clientY: event.clientY })

    const box = rect()
    const p = toNdc(event, box)
    sketch.pointerActive = true
    sketch.pointerNdc.set(p.x, p.y)
    sketch.environment.setPointer(p.u, p.v)

    if (pointers.size >= 2) {
      // A second finger converts the gesture into navigation.
      if (drawingId !== null) {
        sketch.finishStroke()
        drawingId = null
      }
      sketch.setOrbiting(true)
      beginPinch()
      return
    }

    const wantsOrbit = event.button === 1 || event.button === 2 || event.shiftKey
    if (wantsOrbit) {
      orbitId = event.pointerId
      sketch.setOrbiting(true)
      return
    }

    drawingId = event.pointerId
    sketch.environment.emitRipple(p.u, p.v, sketch.time)
    sketch.beginStroke(p.x, p.y, event.clientX, event.clientY, now())
    actions.onDrawStart?.()
  }

  function onPointerMove(event) {
    const box = rect()
    const p = toNdc(event, box)

    const tracked = pointers.get(event.pointerId)
    const prev = tracked ? { x: tracked.clientX, y: tracked.clientY } : null
    if (tracked) {
      tracked.clientX = event.clientX
      tracked.clientY = event.clientY
    }

    sketch.pointerActive = true
    sketch.environment.setPointer(p.u, p.v)

    if (pointers.size >= 2) {
      const [a, b] = [...pointers.values()]
      const distance = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)
      const center = { x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2 }

      if (pinchDistance > 0) {
        sketch.zoom((pinchDistance - distance) / 900)
      }
      sketch.orbit(center.x - pinchCenter.x, center.y - pinchCenter.y)

      pinchDistance = distance
      pinchCenter = center
      return
    }

    if (event.pointerId === orbitId && prev) {
      sketch.orbit(event.clientX - prev.x, event.clientY - prev.y)
      return
    }

    if (event.pointerId === drawingId) {
      sketch.pointerNdc.set(p.x, p.y)
      sketch.extendStroke(p.x, p.y, event.clientX, event.clientY, now())
      return
    }

    sketch.pointerNdc.set(p.x, p.y)
  }

  function endPointer(event) {
    pointers.delete(event.pointerId)
    canvas.releasePointerCapture?.(event.pointerId)

    if (event.pointerId === drawingId) {
      sketch.finishStroke()
      drawingId = null
      const box = rect()
      const p = toNdc(event, box)
      sketch.environment.emitRipple(p.u, p.v, sketch.time)
      actions.onDrawEnd?.()
    }

    if (event.pointerId === orbitId) {
      orbitId = null
    }

    if (pointers.size < 2) {
      pinchDistance = 0
    }
    if (pointers.size === 0) {
      sketch.setOrbiting(false)
      if (event.pointerType !== 'mouse') sketch.pointerActive = false
    }
  }

  function onWheel(event) {
    event.preventDefault()
    if (event.shiftKey) {
      sketch.zoom(event.deltaY / 900)
    } else {
      // Unmodified wheel moves the drawing shell nearer or further, which is the
      // one control that makes a doodle occupy space rather than a plane.
      sketch.nudgeDepth(event.deltaY / 420)
    }
  }

  function onKeyDown(event) {
    if (event.target instanceof HTMLElement && /input|textarea|select/i.test(event.target.tagName)) {
      return
    }

    const key = event.key.toLowerCase()
    if ((event.metaKey || event.ctrlKey) && key === 'z') {
      event.preventDefault()
      actions.onUndo?.()
      return
    }
    if (event.metaKey || event.ctrlKey || event.altKey) return

    if (key === 'c') actions.onClear?.()
    else if (key === 'z') actions.onUndo?.()
    else if (key === 's') actions.onSave?.()
    else if (key === 'r') actions.onRecenter?.()
    else if (key === '[') sketch.nudgeDepth(-0.35)
    else if (key === ']') sketch.nudgeDepth(0.35)
    else return

    event.preventDefault()
  }

  canvas.addEventListener('pointerdown', onPointerDown)
  canvas.addEventListener('pointermove', onPointerMove)
  canvas.addEventListener('pointerup', endPointer)
  canvas.addEventListener('pointercancel', endPointer)
  canvas.addEventListener('pointerleave', (event) => {
    if (event.pointerType === 'mouse' && drawingId === null) sketch.pointerActive = false
  })
  canvas.addEventListener('wheel', onWheel, { passive: false })
  canvas.addEventListener('contextmenu', (event) => event.preventDefault())
  window.addEventListener('keydown', onKeyDown)

  return () => {
    canvas.removeEventListener('pointerdown', onPointerDown)
    canvas.removeEventListener('pointermove', onPointerMove)
    canvas.removeEventListener('pointerup', endPointer)
    canvas.removeEventListener('pointercancel', endPointer)
    canvas.removeEventListener('wheel', onWheel)
    window.removeEventListener('keydown', onKeyDown)
  }
}
