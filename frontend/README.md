# HealChain Frontend DApp

React-based frontend for the HealChain Task Publisher Dashboard.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Ensure the following files exist:
   - `public/contract-config.json` - Contract address configuration
   - `public/TaskManager.json` - Contract ABI file

3. Start the development server:
```bash
npm run dev
```

The app will open at `http://localhost:3000`

## Configuration

The app automatically loads:
- Contract address from `public/contract-config.json`
- Contract ABI from `public/TaskManager.json`

## Requirements

- MetaMask browser extension installed
- Ganache or Hardhat node running at `http://127.0.0.1:7545`
- TaskManager contract deployed

## Usage

1. Open the app in your browser
2. Click "Connect Wallet" to connect MetaMask
3. Enter a data hash in the input field
4. Click "Publish Task" to publish a new task to the blockchain

## Troubleshooting

- **"MetaMask not installed"**: Install MetaMask browser extension
- **"Contract not initialized"**: Ensure contract address is correct in config
- **Transaction fails**: Check that you're connected to the correct network (Ganache)
- **ABI not found**: Ensure TaskManager.json is in the public folder

