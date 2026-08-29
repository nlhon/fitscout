import { defineConfig } from 'vite'
import { fileURLToPath } from 'node:url'

// Two entries: the FitScout inbox and the Light Room drawing experience.
export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        doodle: fileURLToPath(new URL('./doodle.html', import.meta.url)),
      },
    },
  },
})
