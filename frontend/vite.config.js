import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react({
      // Include both .jsx and .js files for JSX transformation
      include: /\.(jsx|js)$/,
    })
  ],
  esbuild: {
    // Configure esbuild to treat .js files as JSX
    loader: 'jsx',
    // Include all .js and .jsx files in the project (not just src/)
    include: /\.(jsx|js)$/,
    exclude: [],
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
  server: {
    port: 3000,
    open: true,
    // Allow Vite dev server to accept requests with Cloudflare Tunnel host header
    // Add any public hostnames you expose via cloudflared here.
    host: true,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'act-mrs-households-rebates.trycloudflare.com'
    ]
  }
})