# FitScout

Private fashion-inspiration inbox for saving image uploads and links in one gallery, then generating outfit ideas based on mood and destination.

## The Light Room (3D doodle)

`/doodle.html` is an immersive drawing room in the spirit of a projection-mapped
gallery installation: you paint trails of light that hang in three-dimensional
space, and the room drifts on its own so the depth you drew becomes visible.

- **Drag** to draw. Speed matters — a fast flick lays its trail further back than
  a slow, deliberate line, so a single gesture has real depth.
- **Scroll** to move the drawing shell nearer or further before you draw, and
  **right-drag** (or **two fingers** on a touch screen) to orbit what you made.
  Pinch or shift-scroll to zoom.
- **Keys**: `C` clear, `Z` undo, `S` save a PNG, `R` recenter, `[` / `]` depth.

Everything renders as camera-facing ribbons through a bloom pass, so a trail
keeps an even thickness however far it drifts, the way projected light does.

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```
