import React, { useEffect, useState } from 'react';
import PublisherDashboard from './PublisherDashboard.jsx';

const ClientDashboard = ({ user, contractAddress, contractABI }) => {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Prompt user to connect MetaMask on mount for a better UX
    if (typeof window.ethereum !== 'undefined') {
      // Passive: do not request accounts automatically; show button in PublisherDashboard
    }
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h2>Client Dashboard</h2>
      <p>Welcome, <strong>{user?.name || user?.email}</strong></p>

      <div style={{ marginTop: 18 }}>
        <h3>Publish a Task</h3>
        <p>Provide initial model link and dataset requirement to become eligible to publish (as in simulation).</p>
        <PublisherDashboard contractAddress={contractAddress} contractABI={contractABI} />
      </div>
    </div>
  );
};

export default ClientDashboard;
