import { createConfig, http } from 'wagmi';
import { defineChain } from 'viem';
import { injected, metaMask } from 'wagmi/connectors';

/**
 * Wagmi Configuration
 * 
 * Configured for:
 * - Local development (Ganache): http://127.0.0.1:7545 (chainId: 5777)
 * - Hardhat Local: http://127.0.0.1:8545 (chainId: 31337)
 * - Sepolia Testnet: Can be added via environment variables
 */

// Define Ganache chain (matches contract-config.json)
const ganache = defineChain({
  id: 5777,
  name: 'Ganache',
  nativeCurrency: {
    decimals: 18,
    name: 'Ether',
    symbol: 'ETH',
  },
  rpcUrls: {
    default: {
      http: ['http://127.0.0.1:7545'],
    },
  },
});

// Define Hardhat local chain
const hardhat = defineChain({
  id: 31337,
  name: 'Hardhat Local',
  nativeCurrency: {
    decimals: 18,
    name: 'Ether',
    symbol: 'ETH',
  },
  rpcUrls: {
    default: {
      http: ['http://127.0.0.1:8545'],
    },
  },
});

// Sepolia Testnet (for production testing)
const sepolia = defineChain({
  id: 11155111,
  name: 'Sepolia',
  nativeCurrency: {
    decimals: 18,
    name: 'Ether',
    symbol: 'ETH',
  },
  rpcUrls: {
    default: {
      http: ['https://sepolia.infura.io/v3/YOUR_INFURA_KEY'],
    },
  },
});

export const wagmiConfig = createConfig({
  chains: [ganache, hardhat, sepolia],
  connectors: [
    injected(),
    metaMask(),
  ],
  transports: {
    [ganache.id]: http('http://127.0.0.1:7545'),
    [hardhat.id]: http('http://127.0.0.1:8545'),
    [sepolia.id]: http(),
  },
});

// Get the active chain from environment or default to Ganache
export const getActiveChain = () => {
  const chainId = import.meta.env.VITE_CHAIN_ID 
    ? parseInt(import.meta.env.VITE_CHAIN_ID) 
    : 5777; // Default to Ganache (matches contract-config.json)
  
  return wagmiConfig.chains.find((chain) => chain.id === chainId) || ganache;
};

