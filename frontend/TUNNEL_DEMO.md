Expose frontend and local RPC with Cloudflare Tunnel (demo-only)

For short demos you can expose the frontend and your local JSON-RPC using `cloudflared`.

1. Start your local node bound to all interfaces:

```powershell
# Hardhat
npx hardhat node --hostname 0.0.0.0

# or Ganache
ganache --host 0.0.0.0 --port 7545
```

2. Run cloudflared tunnels (frontend and RPC):

```powershell
# Expose frontend dev server
cloudflared tunnel --url http://localhost:3000
# Expose RPC (demo-only; protect this tunnel with Cloudflare Access)
cloudflared tunnel --url http://localhost:7545
```

3. Set `VITE_RPC_URL` in `frontend/.env.local` to the RPC tunnel URL provided by cloudflared.

4. Start the frontend dev server and share the Cloudflare public URL for the frontend.

Security note: do not expose unlocked accounts or private keys via the public RPC. Protect the RPC tunnel using Cloudflare Access or other access control.

Note: If Vite rejects the Cloudflare host with a message about `server.allowedHosts`, the project already includes the host list in `vite.config.js`. After editing `vite.config.js` you must restart the dev server:

```powershell
# Stop the running dev server, then:
cd frontend
npm run dev
```

If you expose a different Cloudflare hostname, add it to the `allowedHosts` array in `frontend/vite.config.js`.
