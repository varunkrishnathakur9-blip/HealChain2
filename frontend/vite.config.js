import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [
      react({
        include: /\.(jsx|js)$/,
      })
    ],
    esbuild: {
      loader: 'jsx',
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
      // 1. Expose to network
      host: true, 
      // 2. Add your specific tunnel URL here to allow the host header
      allowedHosts: [
        'localhost',
        '127.0.0.1',
        '.trycloudflare.com' // Allows any Cloudflare quick tunnel subdomain
      ],
      // 3. CRITICAL: Configure HMR for the Tunnel
      hmr: {
        // This ensures the WebSocket connects via the Tunnel URL, not localhost
        clientPort: 443, 
        // Optional: If HMR fails, uncomment line below and paste your tunnel URL
        // host: 'chairs-expires-actively-algorithms.trycloudflare.com', 
      }
    }
  }
})