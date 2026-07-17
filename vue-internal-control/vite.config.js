import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createInternalControlPayload } from './dev-internal-control-api.js'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'internal-control-local-api',
      configureServer(server) {
        server.middlewares.use('/api/internal-control-data', async (req, res, next) => {
          try {
            const requestUrl = new URL(req.url || '/', 'http://127.0.0.1')
            const productId = requestUrl.searchParams.get('product') || 'gy'
            const tradeDate = requestUrl.searchParams.get('date') || ''
            const payload = await createInternalControlPayload({
              projectRoot: server.config.root,
              productId,
              tradeDate,
            })
            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json; charset=utf-8')
            res.end(JSON.stringify(payload))
          } catch (error) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json; charset=utf-8')
            res.end(JSON.stringify({
              error: error instanceof Error ? error.message : '本地接口处理失败',
            }))
          }
        })
      },
    },
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
