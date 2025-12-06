# Frontend-Backend Integration Guide

## Overview

HealChain uses a hybrid architecture where:
- **Frontend** handles UI, wallet connections, and user interactions
- **Backend** (Python Flask server) orchestrates federated learning simulation and blockchain interactions
- **Smart Contracts** handle on-chain escrow, commitments, and reward distribution

## Integration Points

### 1. Task Publishing Flow

**Frontend** (`src/pages/PublishTask.jsx`):
1. User fills form (task name, accuracy, reward, etc.)
2. Form submission should:
   - Generate commitment hash (accuracy + nonce)
   - Call `escrowContract.publishTask()` on-chain (TODO: implement)
   - POST to backend: `POST http://127.0.0.1:5000/run-simulation`

**Backend** (`integration/sim_server.py`):
- Receives POST at `/run-simulation`
- Performs `tpCommit`, `Escrow.deposit`, `startProcessing`
- Waits for miners to apply
- Status changes to `awaiting_selection` when ready

**Integration Status**: ⚠️ **Needs Implementation**
- Frontend form is ready but doesn't call smart contract yet
- Backend endpoint is ready and working
- Need to connect frontend form submission to contract call

### 2. Miner Application Flow

**Frontend** (`components/ClientDashboard.jsx`):
- Miners submit applications via form
- POSTs to: `POST http://127.0.0.1:5000/miner-submit`
- Payload: `{ address, pk, proof_cid, metadata }`

**Backend** (`integration/sim_server.py`):
- Receives at `/miner-submit`
- Stores applicant in `SIM_CONTEXT['applicants']`
- Returns success/error

**Integration Status**: ✅ **Working**
- Fully integrated and tested

### 3. Applicant Selection Flow

**Frontend** (`components/PublisherDashboard.jsx`):
- Polls `/status` endpoint
- When status is `awaiting_selection`:
  - Fetches applicants: `GET http://127.0.0.1:5000/get-applicants`
  - Publisher selects participants
  - POSTs selection: `POST http://127.0.0.1:5000/select-participants`

**Backend** (`integration/sim_server.py`):
- `/get-applicants` returns list of applicants
- `/select-participants` receives selected addresses
- Resumes simulation with selected miners

**Integration Status**: ✅ **Working**
- Fully integrated in PublisherDashboard

### 4. Reward Distribution Flow

**Frontend** (`src/pages/Rewards.jsx`):
- Displays reward history (currently mock data)
- Should call `tpReveal()` and `distributeRewards()` (TODO: implement)

**Backend** (`integration/simulation_runner.py`):
- Performs `publisher.reveal_task()`
- Calls `distributeRewards()` on escrow contract
- Writes results to `simulation_results.json`

**Integration Status**: ⚠️ **Needs Implementation**
- Frontend displays mock data
- Backend performs distribution but frontend doesn't trigger it
- Need to add "Reveal & Distribute" button in Rewards page

## API Endpoints Reference

### Backend Endpoints (Flask Server)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/run-simulation` | POST | Start new simulation | ✅ Working |
| `/status` | GET | Get simulation status | ✅ Working |
| `/results` | GET | Get simulation results | ✅ Working |
| `/miner-submit` | POST | Submit miner application | ✅ Working |
| `/get-applicants` | GET | Get list of applicants | ✅ Working |
| `/select-participants` | POST | Select participants for PoS | ✅ Working |
| `/start-pos` | POST | Start PoS selection | ✅ Working |
| `/debug` | GET | Debug information | ✅ Working |

### Frontend Routes

| Route | Component | Purpose | Status |
|-------|-----------|---------|--------|
| `/` | Dashboard | Landing page | ✅ Complete |
| `/tasks/publish` | PublishTask | Publish new task | ⚠️ Needs contract integration |
| `/mining` | Mining | Miner dashboard | ⚠️ Needs real data |
| `/rewards` | Rewards | Rewards tracking | ⚠️ Needs contract integration |

## Configuration Files

### Frontend Configuration

**`frontend/public/contract-config.json`**:
```json
{
  "TaskManager": {
    "address": "0x..."
  },
  "network": {
    "rpcUrl": "http://127.0.0.1:7545",
    "chainId": 5777
  }
}
```

**`frontend/src/config/wagmi.js`**:
- Wagmi configuration for wallet connections
- Chain definitions (Ganache, Hardhat, Sepolia)

### Backend Configuration

**`blockchain/deployment/contract_config.json`**:
```json
{
  "TaskManager": {
    "address": "0x...",
    "abiFile": "../../artifacts/..."
  },
  "EscrowContract": {
    "address": "0x...",
    "abiFile": "../../artifacts/..."
  },
  "network": {
    "rpcUrl": "http://127.0.0.1:7545",
    "chainId": 5777
  }
}
```

## Data Flow

### Task Publishing
```
User (Frontend) 
  → Fill Form 
  → Generate Commitment 
  → Call escrowContract.publishTask() [TODO]
  → POST /run-simulation
  → Backend performs tpCommit, deposit
  → Status: "running"
```

### Miner Application
```
Miner (Frontend)
  → Submit Application Form
  → POST /miner-submit
  → Backend stores applicant
  → Status: "awaiting_selection"
```

### Participant Selection
```
Publisher (Frontend)
  → Poll /status
  → GET /get-applicants
  → Select participants
  → POST /select-participants
  → Backend resumes simulation
  → Status: "training"
```

### Reward Distribution
```
Publisher (Frontend) [TODO]
  → Click "Reveal & Distribute"
  → Call tpReveal() [TODO]
  → Call distributeRewards() [TODO]
  → Backend completes simulation
  → Status: "completed"
```

## Known Issues & TODOs

### High Priority
1. **PublishTask.jsx**: Implement smart contract call for `publishTask()`
   - Generate commitment hash (accuracy + nonce)
   - Call `escrowContract.publishTask()` with wagmi
   - Save commitment to localStorage
   - Then POST to backend

2. **Rewards.jsx**: Implement reward distribution
   - Add "Reveal & Distribute" button
   - Call `tpReveal()` with stored commitment
   - Call `distributeRewards()` with miner scores
   - Update UI with real data

3. **Mining.jsx**: Fetch real contribution scores
   - Use `useReadContract` to fetch scores from blockchain
   - Display real-time training progress
   - Update metrics with actual data

### Medium Priority
4. **API URL Configuration**: Make backend URL configurable
   - Currently hardcoded to `http://127.0.0.1:5000`
   - Should use environment variable
   - Add to `.env` file

5. **Error Handling**: Improve error messages
   - Network errors
   - Contract call failures
   - Backend API errors

6. **Loading States**: Add loading indicators
   - Contract transaction pending
   - Backend processing
   - Data fetching

### Low Priority
7. **Real-time Updates**: WebSocket for status updates
   - Currently using polling
   - Could use WebSocket for real-time updates

8. **Caching**: Cache contract data
   - Reduce redundant contract calls
   - Cache task lists, scores, etc.

## Testing Integration

### Manual Testing Checklist

1. **Task Publishing**
   - [ ] Fill form in PublishTask page
   - [ ] Submit form (should call contract)
   - [ ] Verify transaction in MetaMask
   - [ ] Check backend receives POST
   - [ ] Verify status changes to "running"

2. **Miner Application**
   - [ ] Submit application in ClientDashboard
   - [ ] Verify POST to /miner-submit succeeds
   - [ ] Check applicant appears in /get-applicants

3. **Participant Selection**
   - [ ] Wait for "awaiting_selection" status
   - [ ] Fetch applicants
   - [ ] Select participants
   - [ ] Submit selection
   - [ ] Verify simulation resumes

4. **Reward Distribution**
   - [ ] Wait for task completion
   - [ ] Click "Reveal & Distribute"
   - [ ] Verify tpReveal transaction
   - [ ] Verify distributeRewards transaction
   - [ ] Check rewards in Rewards page

## Environment Variables

### Frontend (.env)
```
VITE_CHAIN_ID=5777
VITE_RPC_URL=http://127.0.0.1:7545
VITE_API_URL=http://127.0.0.1:5000
```

### Backend (environment or config)
```
RPC_URL=http://127.0.0.1:7545
CHAIN_ID=5777
CONTRACT_CONFIG_PATH=blockchain/deployment/contract_config.json
```

## Troubleshooting

### Frontend can't connect to backend
- Check Flask server is running: `python integration/sim_server.py`
- Verify CORS is enabled in Flask (should be automatic)
- Check firewall isn't blocking port 5000

### Contract calls failing
- Verify wallet is connected
- Check network matches (chainId 5777 for Ganache)
- Ensure contract is deployed
- Check contract address in config files

### Backend can't connect to blockchain
- Verify Ganache/Hardhat node is running
- Check RPC URL in `contract_config.json`
- Ensure contracts are deployed
- Check ABI file paths are correct

---

**Last Updated**: After frontend upgrade completion
**Status**: Core integration working, contract calls need implementation

