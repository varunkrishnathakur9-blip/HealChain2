# HealChain — Project Overview, Setup and Run Guide

This README documents how to set up and run the HealChain repository locally, including the frontend, local blockchain artifacts, and the Python-driven end-to-end simulation (Option B: backend-driven commit/reveal). It also explains where integration points live and provides troubleshooting tips.

## What this repo contains (high level)
- `blockchain/` — Solidity contracts, Hardhat build artifacts and deployment information
- `federated_layer/` — federated learning components (publisher, miners, aggregator)
- `integration/` — Python integration layer (Web3 client wrapper, simulation runner, sim server, listener)
- `frontend/` — React + Vite frontend where publishers & participants interact
- `crypto/` — cryptographic primitives (NDD-FE and related code)

## Design & Integration Summary
- Frontend publishes a minimal Task with `TaskManager.publishTask(dataHash)` and receives a `TaskPublished` event.
- Option B (default implemented): Backend (Python) performs commit/reveal, escrow deposit and the full simulation flow. The frontend only triggers the on-chain minimal publish and then POSTs the full publish parameters to the local simulation server (`/run-simulation`).
- The `integration/listener.py` can also listen to `TaskPublished` events and forward them to the sim server automatically.
- The Python `simulation_runner.py` coordinates publisher/miners/aggregator and writes `simulation_results.json` on completion.

## Important files and responsibilities
- `integration/simulation_runner.py` — orchestrates the full simulation (M1..M7). It depends on `integration/web3_client.py` and `federated_layer/task_publisher/publisher.py`.
- `integration/web3_client.py` — web3 wrapper; loads contracts from `blockchain/deployment/contract_config.json` and exposes `send_transaction(...)` and `call_view_function(...)` helpers. It has a mock mode when RPC is unavailable.
- `integration/sim_server.py` — lightweight Flask server exposing `POST /run-simulation`, `GET /status`, `GET /results` for frontend/listener to trigger runs and retrieve results.
- `integration/listener.py` — web3.py-based event listener that forwards `TaskPublished` events to the sim server.
- `federated_layer/task_publisher/publisher.py` — implements commit/reveal and PoS selection steps; this is where the TP (`tpCommit`, `tpReveal`) calls are made by the backend.
- `frontend/components/PublisherDashboard.jsx` — UI to publish tasks via MetaMask and POST the full publish parameters to the sim server after the on-chain `publishTask` transaction confirms.
- `frontend/public/contract-config.json` — frontend TaskManager address and RPC network.
- `blockchain/deployment/contract_config.json` — Python integration’s contract addresses and ABI paths (TaskContract, EscrowContract, TaskManager).

## Prerequisites
- Node.js (recommended v18+ or v20+), npm
- Python 3.10+ (the repo used Python 3.14 in logs but 3.10+ is typical) and `pip`
- A local Ethereum JSON-RPC (Ganache or Hardhat node). By default the code expects `http://127.0.0.1:7545`.
- MetaMask browser extension (for frontend testing)

## Quick setup (Windows PowerShell commands)
Run these from the project root (`C:\Users\Lenovo\Desktop\healchain2\HealChain`):

1) Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

2) Compile / Deploy contracts (Hardhat)

If you haven't compiled and deployed the contracts, do this next (from the project root):

```powershell
# compile
npx hardhat compile

# Deploy to local network (example script for TaskManager)
# Adjust scripts and network as needed (Ganache or Hardhat node)
npx hardhat run blockchain/contracts/migrations/deploy_taskmanager.js --network ganache
```

3) Start the local simulation server (backend API)

```powershell
# From project root
python integration\\sim_server.py
```

4) (Optional) Start the event listener

```powershell
# From project root
python integration\\listener.py
# or provide contract address / RPC override:
# python integration\\listener.py 0xYourTaskManagerAddress http://127.0.0.1:7545
```

5) Start the frontend

```powershell
cd frontend
npm install
npm run dev
# Open http://localhost:3000/ in your browser
```

6) Open MetaMask, connect the same local RPC network (e.g., Ganache / Hardhat), and import an unlocked account if needed.

7) (Optional demo) Expose frontend and local RPC with Cloudflare Tunnel

If you want to share your local frontend and JSON-RPC for a short demo, you can use Cloudflare Tunnel (`cloudflared`). This is a convenience for demos only — do not expose unlocked accounts or private keys.

```powershell
# Start your local node bound to all interfaces (so cloudflared can reach it)
# Hardhat
npx hardhat node --hostname 0.0.0.0
# or Ganache
ganache --host 0.0.0.0 --port 7545

# Start the frontend (dev server)
cd frontend
npm run dev

# In another terminal: expose frontend
cloudflared tunnel --url http://localhost:3000

# And expose RPC (demo-only; protect this tunnel with Cloudflare Access)
cloudflared tunnel --url http://localhost:7545
```

After `cloudflared` prints the public URLs, set the tunneled RPC URL in `frontend/.env.local` as `VITE_RPC_URL` (the frontend will prefer this env var). Example file `frontend/.env.local`:

```
VITE_RPC_URL="https://your-rpc-subdomain.trycloudflare.com"
```

Notes:
- Restart the Vite dev server after changing `vite.config.js` or `.env.local` so the new settings take effect.
- If the Cloudflare hostname is rejected by Vite with an error about `server.allowedHosts`, add the Cloudflare host to `frontend/vite.config.js` `server.allowedHosts` (the project already includes an example entry) and restart the dev server.
- Protect the RPC tunnel with Cloudflare Access or other access control if you intend to share it beyond a trusted demo audience.

## How to run a Task (Option B - backend-driven)
1. In the frontend Publisher dashboard (`/`), connect MetaMask and publish a task (supply a `dataHash`). This calls `TaskManager.publishTask(dataHash)` on-chain.
2. After transaction confirmation the frontend will POST the full publish parameters to `http://127.0.0.1:5000/run-simulation` (the sim server). Alternatively, the `integration/listener.py` will automatically forward `TaskPublished` events to the sim server.
3. The sim server launches the `run_healchain_simulation(...)` function in a background thread. The Python `TaskPublisher.publish_task()` method performs `tpCommit`, `Escrow.deposit`, and `startProcessing`. Later the sim will call `publisher.reveal_task(...)` and miners' reveals and then call `distributeRewards` on the escrow contract.
4. When the run completes, the runner writes `simulation_results.json` at the project root. You can fetch results from the sim server:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/results' -Method Get
```

## Key Integration Notes / Observations
- Contracts used by the Python runner: `TaskContract` and `EscrowContract` — these must be deployed and referenced in `blockchain/deployment/contract_config.json` with correct `address` and `abiFile` paths.
- Frontend uses `TaskManager` (a minimal publisher contract) and has its ABI in `frontend/public/TaskManager.json` and `frontend/public/contract-config.json` with the `TaskManager` address.
- The backend Web3 client (`integration/web3_client.py`) expects `contract_config.json` in `blockchain/deployment` to reference ABI file paths relative to that directory. Ensure the `abiFile` paths are valid (they typically point to `../../artifacts/...`).
- If you want the frontend to call `tpCommit`/`tpReveal` or interact with `TaskContract`/`EscrowContract` directly, copy the respective ABI JSONs from `blockchain/artifacts/...` into `frontend/public/` and add the addresses in `frontend/public/contract-config.json`.

## Troubleshooting & FAQ
- ModuleNotFoundError when launching `integration/sim_server.py`: Start the script from the project root so imports resolve, or ensure the project root is on `PYTHONPATH`. The sim server includes logic to add the project root to `sys.path` to help threaded imports.
- Listener fails with web3.py version mismatch (error like `object has no attribute '_get_event_signature'`): This repo was developed across web3.py versions; update `integration/listener.py` to use the event API compatible with your installed `web3` (v5 vs v6 differences). A safe approach is to avoid calling private methods like `_get_event_signature()` and rely on `contract.events.TaskPublished.create_filter(...)` and parsing `event['args']`.
- ABI file not found: If `integration/web3_client.py` errors about missing ABI for `TaskContract` or `EscrowContract`, ensure `blockchain/deployment/contract_config.json` has correct `abiFile` pointing to `artifacts/...` and that the artifacts exist (run `npx hardhat compile`).
- Port conflicts for frontend: Vite will pick the next available port if 3000 is in use. Check terminal output for the actual URL.
- Simulation takes long or appears stuck: The simulation runner performs training and aggregation loops that can be time-consuming; check logs in the terminal where `integration/sim_server.py` is running. The sim server exposes `GET /status` for quick status checks.

## Useful Commands (copyable)
```powershell
# From project root
python -m pip install -r requirements.txt
python integration\\sim_server.py
python integration\\listener.py
cd frontend; npm install; npm run dev

# Trigger a smoke run (example POST)
python -c "import requests; print(requests.post('http://127.0.0.1:5000/run-simulation', json={'publisher':'0x0','dataHash':'QmTest','initialModelLink':'ipfs://init','datasetReq':'chest_xray','acc_req':85,'reward':1,'texp':60,'nonceTP':1,'L':'label'}).status_code)"

# Check sim status
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/status' -Method Get
# Get results
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/results' -Method Get
```

## Recommended next improvements
- Stabilize `integration/listener.py` for web3.py v6 compatibility (avoid private API calls).
- Make sure all ABIs referenced in `blockchain/deployment/contract_config.json` exist in `blockchain/artifacts`. If you prefer a single source for frontend ABIs, copy required ABI JSONs to `frontend/public/`.
- Add a small README in `frontend/` documenting how the frontend uses `frontend/public/contract-config.json` and what ABIs it expects.
- Add CI-style smoke tests that POST to `/run-simulation` and assert `simulation_results.json` is created (use a mocked web3 client in CI).

---
If you'd like, I can now:
- Fix `integration/listener.py` to be compatible with your installed `web3` version and restart the listener, or
- Copy required ABIs into `frontend/public/` and update the frontend `contract-config.json` so the UI can interact directly with `TaskContract`/`EscrowContract` if you want that behavior, or
- Finalize this README with additional screenshots and commands tailored to your local environment.


Notes
- Tests use the in-repo Hardhat configuration and expect `blockchain/contracts/*.sol` to contain the contracts.
- If you see large dependency installations, that's normal for Hardhat + toolbox.
# HealChain

Project scaffold for HealChain: a federated learning system integrated with blockchain for task publishing, escrow, and miner incentives.

Repository structure (scaffolded):
````
HealChain/
├── blockchain/
│   ├── contracts/
│   │   ├── EscrowContract.sol
│   │   ├── TaskContract.sol
│   │   └── migrations/
│   ├── deployment/
│   └── tests/
│
├── crypto/
│   ├── ndd_fe.py
│   └── dgc.py
│
├── federated_layer/
│   ├── models/
│   │   └── image_detector.py
│   ├── clients/
│   │   └── miner.py
│   ├── aggregator/
│   │   └── aggregator.py
│   └── task_publisher/
│       └── publisher.py
│
├── integration/
│   ├── web3_client.py
│   └── simulation_runner.py
│
├── data/
│   └── chest_xray_dataset/
│
├── requirements.txt
└── README.md
````
Next steps:
- Implement contract tests and deployment scripts
- Fill in crypto primitives in `crypto/`
- Implement model training and aggregation logic
- Wire integration scripts to the contracts using `web3_client.py`

