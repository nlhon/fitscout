import './style.css'

const DB_NAME = 'fitscout-inbox'
const DB_VERSION = 1
const STORE_NAME = 'inspirations'

let db
let inspirations = []

document.querySelector('#app').innerHTML = `
  <main class="layout">
    <header>
      <p class="eyebrow">Private inbox</p>
      <h1>FitScout Inspiration Agent</h1>
      <p class="subtitle">Save image uploads and links in one place, then generate outfit ideas from your mood and destination.</p>
    </header>

    <section class="panel">
      <h2>Add an image</h2>
      <form id="image-form" class="stack" autocomplete="off">
        <label>
          Image file
          <input id="image-file" name="image" type="file" accept="image/*" required />
        </label>
        <label>
          Notes (optional)
          <input name="note" type="text" maxlength="140" placeholder="e.g. streetwear layers" />
        </label>
        <button type="submit">Save image</button>
      </form>
    </section>

    <section class="panel">
      <h2>Save a link</h2>
      <form id="link-form" class="stack" autocomplete="off">
        <label>
          URL
          <input name="url" type="url" required placeholder="https://..." />
        </label>
        <label>
          Notes (optional)
          <input name="note" type="text" maxlength="140" placeholder="e.g. monochrome tailoring" />
        </label>
        <button type="submit">Save link</button>
      </form>
    </section>

    <section class="panel">
      <h2>Generate outfit</h2>
      <form id="agent-form" class="stack" autocomplete="off">
        <label>
          How are you feeling?
          <input name="mood" type="text" required placeholder="confident, relaxed, bold..." />
        </label>
        <label>
          Where are you going?
          <input name="destination" type="text" required placeholder="brunch, office, concert..." />
        </label>
        <button type="submit">Generate suggestion</button>
      </form>
      <p id="agent-output" class="agent-output">Add a few inspirations, then generate your look.</p>
    </section>

    <section class="panel">
      <div class="gallery-head">
        <h2>Gallery</h2>
        <p id="item-count">0 items</p>
      </div>
      <div id="gallery" class="gallery" aria-live="polite"></div>
    </section>

    <p id="status" class="status" aria-live="polite"></p>
  </main>
`

const imageForm = document.querySelector('#image-form')
const linkForm = document.querySelector('#link-form')
const agentForm = document.querySelector('#agent-form')
const gallery = document.querySelector('#gallery')
const itemCount = document.querySelector('#item-count')
const status = document.querySelector('#status')
const agentOutput = document.querySelector('#agent-output')

init()

async function init() {
  db = await openDatabase()
  await refreshGallery()
}

imageForm.addEventListener('submit', async (event) => {
  event.preventDefault()

  const fileInput = imageForm.querySelector('#image-file')
  const noteInput = imageForm.querySelector('input[name="note"]')
  const file = fileInput.files?.[0]

  if (!file) {
    setStatus('Please choose an image file.')
    return
  }

  const dataUrl = await readFileAsDataUrl(file)

  await saveInspiration({
    type: 'image',
    note: noteInput.value.trim(),
    fileName: file.name,
    mimeType: file.type,
    source: dataUrl,
    createdAt: new Date().toISOString(),
  })

  imageForm.reset()
  setStatus('Image saved to your private inbox.')
  await refreshGallery()
})

linkForm.addEventListener('submit', async (event) => {
  event.preventDefault()

  const formData = new FormData(linkForm)
  const rawUrl = String(formData.get('url') || '').trim()
  const note = String(formData.get('note') || '').trim()

  let normalizedUrl

  try {
    normalizedUrl = new URL(rawUrl).toString()
  } catch {
    setStatus('Please enter a valid URL.')
    return
  }

  await saveInspiration({
    type: 'link',
    note,
    source: normalizedUrl,
    createdAt: new Date().toISOString(),
  })

  linkForm.reset()
  setStatus('Link saved to your private inbox.')
  await refreshGallery()
})

agentForm.addEventListener('submit', (event) => {
  event.preventDefault()

  if (!inspirations.length) {
    agentOutput.textContent = 'No inspirations yet. Save at least one image or link first.'
    return
  }

  const formData = new FormData(agentForm)
  const mood = String(formData.get('mood') || '').trim()
  const destination = String(formData.get('destination') || '').trim()

  const picks = chooseRandom(inspirations, Math.min(3, inspirations.length))
  const details = picks
    .map((item) => {
      if (item.type === 'image') {
        return item.note || item.fileName || 'a saved image'
      }

      return item.note || item.source
    })
    .join(', ')

  agentOutput.textContent = `For a ${mood} vibe at ${destination}, start with pieces inspired by ${details}. Keep the silhouette balanced and finish with one standout accessory.`
})

async function refreshGallery() {
  inspirations = await getInspirations()
  renderGallery(inspirations)
}

function renderGallery(items) {
  itemCount.textContent = `${items.length} item${items.length === 1 ? '' : 's'}`

  if (!items.length) {
    gallery.innerHTML = '<p class="empty">Your gallery is empty. Upload an image or save a link to get started.</p>'
    return
  }

  gallery.innerHTML = items
    .map((item) => {
      if (item.type === 'image') {
        return `
          <article class="card">
            <img src="${item.source}" alt="Saved fashion inspiration" loading="lazy" />
            <div>
              <p class="meta">Image</p>
              <p>${escapeHtml(item.note || item.fileName || 'No notes')}</p>
            </div>
          </article>
        `
      }

      return `
        <article class="card">
          <div>
            <p class="meta">Link</p>
            <p>${escapeHtml(item.note || 'Saved link')}</p>
            <a href="${item.source}" target="_blank" rel="noreferrer">${escapeHtml(item.source)}</a>
          </div>
        </article>
      `
    })
    .join('')
}

function setStatus(message) {
  status.textContent = message
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = window.indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = () => {
      const nextDb = request.result
      if (!nextDb.objectStoreNames.contains(STORE_NAME)) {
        nextDb.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true })
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

function saveInspiration(item) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    tx.objectStore(STORE_NAME).add(item)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

function getInspirations() {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const request = tx.objectStore(STORE_NAME).getAll()

    request.onsuccess = () => {
      const records = [...request.result].sort((a, b) =>
        (b.createdAt || '').localeCompare(a.createdAt || ''),
      )
      resolve(records)
    }

    request.onerror = () => reject(request.error)
  })
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

function chooseRandom(items, count) {
  const shuffled = [...items]

  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }

  return shuffled.slice(0, count)
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}
