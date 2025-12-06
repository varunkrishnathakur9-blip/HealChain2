# Web3 Integration Setup Guide

## Part 4: Web3 Integration Complete ✅

The frontend now includes full Web3 integration using wagmi v2.

### Dependencies Added

The following packages have been added to `package.json`:
- `wagmi` - React hooks for Ethereum
- `viem` - TypeScript Ethereum library (required by wagmi)
- `@tanstack/react-query` - Data fetching library (required by wagmi)

### Installation

Run the following command to install the new dependencies:

```bash
cd frontend
npm install
```

### What's Included

1. **Wagmi Configuration** (`src/config/wagmi.js`)
   - Configured for Ganache (port 7545, chainId 5777)
   - Supports Hardhat local (port 8545, chainId 31337)
   - Ready for Sepolia testnet

2. **WalletConnect Component** (`components/WalletConnect.jsx`)
   - Uses wagmi hooks for wallet connection
   - Supports MetaMask and other injected wallets
   - Shows connected address with disconnect option

3. **Contract Hooks** (`src/hooks/useContract.js`)
   - `useContract` - Generic contract interaction hook
   - `useEscrowContract` - For M1 (Publish Task)
   - `useRewardContract` - For M7 (Reward Distribution)

4. **Integration Points**
   - Comments added in pages showing where to integrate contract calls
   - PublishTask.jsx - M1 integration point
   - Mining.jsx - M2-M3 integration point
   - Rewards.jsx - M7 integration point

### Usage Example

```javascript
import { useEscrowContract } from '../hooks/useContract';

function PublishTask() {
  const { publishTask, isPending } = useEscrowContract(contractAddress, contractABI);
  
  const handlePublish = async () => {
    await publishTask(taskID, commitHash, deadline, reward);
  };
  
  return <button onClick={handlePublish} disabled={isPending}>Publish</button>;
}
```

### Environment Variables (Optional)

Create a `.env` file in the `frontend` directory:

```
VITE_CHAIN_ID=5777  # Ganache default
VITE_RPC_URL=http://127.0.0.1:7545
```

### Next Steps

1. Install dependencies: `npm install`
2. Start Ganache or Hardhat local node
3. Deploy contracts and update `public/contract-config.json`
4. Implement contract calls in pages using the integration points
5. Test wallet connection and contract interactions

