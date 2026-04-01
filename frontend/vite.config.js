import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import path from 'node:path'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig({
  base: '/trainingplatform/',
  server: {
    host: '0.0.0.0',
    proxy: {
      '/trainingplatform/docs': {
        bypass(req, res) {
          const filePath = path.resolve(__dirname, '../docs', req.url.replace('/trainingplatform/docs/', ''))
          if (fs.existsSync(filePath)) {
            const fileContent = fs.readFileSync(filePath)
            const ext = path.extname(filePath).toLowerCase()
            if (ext === '.docx') {
              res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            res.setHeader('Content-Disposition', `attachment; filename="${encodeURIComponent(path.basename(filePath))}"`)
            res.end(fileContent)
            return false
          }
        }
      }
    }
  },
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
