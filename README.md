# HealChain - Privacy-Preserving Federated Learning Platform

A blockchain-integrated federated learning system that enables privacy-preserving machine learning with fair, transparent reward distribution through smart contracts.

## 🎯 Overview

HealChain combines federated learning with blockchain technology to create a decentralized platform where:
- **Task Publishers** can publish machine learning tasks with escrowed rewards
- **Miners** participate in federated training while keeping their data private
- **Fair Rewards** are distributed based on contribution quality (gradient norms)
- **Transparency** is ensured through cryptographic commitments and on-chain verification

## 🏗️ Architecture

```
HealChain/
├── blockchain/          # Solidity smart contracts (Hardhat)
│   ├── contracts/       # TaskContract, EscrowContract, TaskManager
│   └── deployment/      # Contract addresses and ABIs
├── frontend/            # React + Vite frontend (wagmi Web3)
│   ├── src/
│   │   ├── pages/       # Dashboard, Publish, Mining, Rewards
│   │   ├── components/  # Design system components
│   │   ├── hooks/       # Web3 contract hooks
│   │   └── config/      # Wagmi configuration
│   └── public/          # Contract configs and ABIs
├── federated_layer/     # Python FL components
│   ├── task_publisher/  # Publisher with commit/reveal
│   ├── clients/         # Miner clients
│   └── aggregator/      # Model aggregation
├── integration/         # Backend integration layer
│   ├── sim_server.py    # Flask API server
│   ├── web3_client.py   # Web3 wrapper
│   └── simulation_runner.py  # End-to-end simulation
└── crypto/              # Cryptographic primitives (NDD-FE)
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** v18+ and npm
- **Python** 3.10+ and pip
- **Ganache** or **Hardhat** local blockchain node
- **MetaMask** browser extension
- **IPFS** daemon (optional, for proof storage)

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Deploy Smart Contracts

```bash
# Compile contracts
npx hardhat compile

# Deploy to Ganache (default: http://127.0.0.1:7545, chainId: 5777)
npx hardhat run blockchain/contracts/migrations/deploy_taskmanager.js --network ganache

# Update contract addresses in:
# - blockchain/deployment/contract_config.json (for Python backend)
# - frontend/public/contract-config.json (for frontend)
```

### 3. Start Backend Server

```bash
# Start Flask simulation server (runs on http://127.0.0.1:5000)
python integration/sim_server.py
```

### 4. Start Frontend

```bash
cd frontend
npm run dev
# Opens at http://localhost:3000
```

### 5. Connect Wallet

1. Open MetaMask
2. Add Ganache network:
   - Network Name: Ganache
   - RPC URL: http://127.0.0.1:7545
   - Chain ID: 5777
   - Currency Symbol: ETH
3. Import an account from Ganache (unlocked accounts)
4. Connect wallet in the frontend

## 📖 Usage Guide

### For Task Publishers

1. Navigate to **Dashboard** → Click **"Publish Task"**
2. Fill in task details:
   - Task name and description
   - Dataset type
   - Required accuracy (%)
   - Total reward (ETH)
   - Minimum miners required
3. Click **"Publish Task & Lock Reward"**
   - This creates a commitment hash and locks the reward in escrow
4. Wait for miners to apply
5. When task completes, reveal accuracy and distribute rewards

### For Miners

1. Navigate to **Mining** dashboard
2. View available tasks and your active participation
3. Monitor your contribution score (||Δᵢ||₂)
4. Track training progress and model accuracy
5. View earned rewards in **Rewards** page

### API Endpoints (Backend)

The simulation server exposes:

- `POST /run-simulation` - Start a new simulation run
- `GET /status` - Get current simulation status
- `GET /results` - Get simulation results
- `POST /miner-submit` - Submit miner application
- `GET /get-applicants` - Get list of applicants
- `POST /select-participants` - Select participants for PoS

## 🔧 Configuration

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
- Configured for Ganache (port 7545, chainId 5777)
- Supports Hardhat local (port 8545, chainId 31337)
- Ready for Sepolia testnet

### Backend Configuration

**`blockchain/deployment/contract_config.json`**:
```json
{
  "TaskManager": {
    "address": "0x...",
    "abiFile": "../../artifacts/..."
  },
  "network": {
    "rpcUrl": "http://127.0.0.1:7545",
    "chainId": 5777
  }
}
```

## 🧪 Testing

### Run Contract Tests

```bash
npx hardhat test
```

### Test Frontend

```bash
cd frontend
npm run dev
# Test in browser with MetaMask connected
```

### Test Backend API

```bash
# Start server
python integration/sim_server.py

# In another terminal, test endpoints
curl http://127.0.0.1:5000/status
```

## 🔐 Security Considerations

1. **Commit-Reveal Pattern**: Accuracy requirements are committed before task starts, preventing manipulation
2. **Escrow**: Rewards are locked in smart contract until task completion
3. **Fair Distribution**: Rewards distributed proportionally based on gradient norms (||Δᵢ||₂)
4. **Cryptographic Verification**: All commitments verified on-chain

## 📚 Documentation

- **Frontend Design**: `HealChain_Frontend_Design.md` - Complete design system
- **Implementation Guide**: `HealChain_Frontend_Implementation_Guide.md` - Step-by-step guide
- **Web3 Setup**: `frontend/WEB3_SETUP.md` - Wagmi configuration
- **Responsive Testing**: `frontend/RESPONSIVE_TESTING.md` - Responsive design guide

## 🛠️ Development

### Project Structure

- **Smart Contracts**: Solidity contracts in `blockchain/contracts/`
- **Frontend**: React components using design system in `frontend/src/`
- **Backend**: Python integration layer in `integration/`
- **Federated Learning**: FL components in `federated_layer/`

### Key Technologies

- **Frontend**: React 18, Vite, wagmi v2, viem, ethers.js v6
- **Backend**: Python 3.10+, Flask, web3.py
- **Blockchain**: Solidity 0.8.20, Hardhat
- **Federated Learning**: PyTorch

## 🐛 Troubleshooting

### Frontend Issues

**"Wallet not connecting"**
- Ensure MetaMask is installed and unlocked
- Check network configuration matches Ganache
- Verify chain ID is 5777

**"Contract not found"**
- Verify contract address in `frontend/public/contract-config.json`
- Ensure TaskManager.json ABI file exists in `frontend/public/`
- Check contract is deployed on the correct network

**"Module not found" errors**
- Run `npm install` in `frontend/` directory
- Check Node.js version (v18+)

### Backend Issues

**"RPC connection failed"**
- Ensure Ganache/Hardhat node is running
- Check RPC URL in `blockchain/deployment/contract_config.json`
- Verify port matches (7545 for Ganache)

**"ABI file not found"**
- Run `npx hardhat compile` to generate artifacts
- Check `abiFile` paths in `contract_config.json` are correct

**"Simulation stuck"**
- Check logs in terminal where `sim_server.py` is running
- Verify all required contracts are deployed
- Check `GET /status` endpoint for current state

### IPFS Issues

**"CORS error when uploading"**
- Enable CORS in IPFS daemon (see main README troubleshooting section)
- Or use server-side upload via Python integration

## 🚢 Deployment

### Local Development
- Use Ganache for local blockchain
- Frontend: `npm run dev` (Vite dev server)
- Backend: `python integration/sim_server.py`

### Testnet Deployment
1. Deploy contracts to Sepolia testnet
2. Update contract addresses in config files
3. Update wagmi config for Sepolia
4. Deploy frontend to Vercel/Netlify
5. Update backend RPC URL

### Production
- Use mainnet-compatible network
- Secure all private keys
- Enable HTTPS
- Set up monitoring and logging

## 📝 License

ISC

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📧 Support

For issues and questions, please open an issue on the repository.

---

    
