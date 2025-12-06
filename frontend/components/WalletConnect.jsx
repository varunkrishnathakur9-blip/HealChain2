import React from 'react';
import { useAccount, useConnect, useDisconnect } from 'wagmi';
import { injected } from 'wagmi/connectors';
import { Button } from './Button';
import { Badge } from './Badge';

/**
 * WalletConnect Component - Web3 wallet connection using wagmi
 * 
 * Supports MetaMask and other injected wallets
 */
export const WalletConnect = ({ className = '' }) => {
  const { address, isConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();

  // Find MetaMask or first injected connector
  const metaMaskConnector = connectors.find(
    (connector) => connector.id === 'injected' || connector.name.toLowerCase().includes('metamask')
  ) || connectors[0];

  if (isConnected && address) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
        }}
        className={className}
      >
        <Badge
          status="active"
          label={`${address.slice(0, 6)}...${address.slice(-4)}`}
          size="sm"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => disconnect()}
        >
          Disconnect
        </Button>
      </div>
    );
  }

  return (
    <Button
      variant="primary"
      size="sm"
      onClick={() => {
        if (metaMaskConnector) {
          connect({ connector: metaMaskConnector });
        } else {
          alert('No wallet found. Please install MetaMask.');
        }
      }}
      disabled={isPending}
      loading={isPending}
      className={className}
    >
      {isPending ? 'Connecting...' : 'Connect Wallet'}
    </Button>
  );
};

export default WalletConnect;

