import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, Navigate } from 'react-router-dom';
import SignIn from '../components/SignIn.jsx';
import ClientDashboard from '../components/ClientDashboard.jsx';
import ParticipantsDashboard from '../components/ParticipantsDashboard.jsx';
import AggregatorDashboard from '../components/AggregatorDashboard.jsx';

// Loads contract config (contract-config.json) and TaskManager ABI from public
async function loadContractConfig() {
  let address = null;
  let abi = null;
  let rpcUrl = null;
  let chainId = null;
  try {
    const resp = await fetch('/contract-config.json');
    if (resp.ok) {
      const cfg = await resp.json();
      if (cfg.TaskManager && cfg.TaskManager.address) address = cfg.TaskManager.address;
      if (cfg.network) {
        rpcUrl = cfg.network.rpcUrl;
        chainId = cfg.network.chainId;
      }
    }
  } catch (e) {
    console.warn('Failed to load contract-config.json', e);
  }

  try {
    const abiResp = await fetch('/TaskManager.json');
    if (abiResp.ok) {
      const abiData = await abiResp.json();
      abi = abiData.abi;
    }
  } catch (e) {
    console.warn('Failed to load TaskManager.json', e);
  }

  return { address, abi, rpcUrl, chainId };
}

function App() {
  const [user, setUser] = useState(null);
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [contractAddress, setContractAddress] = useState(null);
  const [contractABI, setContractABI] = useState(null);
  const [rpcUrl, setRpcUrl] = useState(null);
  const [chainId, setChainId] = useState(null);

  const handleSignIn = (profile) => {
    setUser(profile);
  };

  useEffect(() => {
    if (!user) return;
    let mounted = true;
    setLoadingConfig(true);
    loadContractConfig().then(({ address, abi, rpcUrl: cfgRpcUrl, chainId: cfgChainId }) => {
      const envRpc = (import.meta.env && import.meta.env.VITE_RPC_URL) ? String(import.meta.env.VITE_RPC_URL).trim() : null;
      if (!mounted) return;
      setContractAddress(address);
      setContractABI(abi);
      setRpcUrl(envRpc || cfgRpcUrl || null);
      setChainId(cfgChainId || null);
    }).finally(() => {
      if (mounted) setLoadingConfig(false);
    });
    return () => { mounted = false; };
  }, [user]);

  if (!user) {
    return <SignIn onSignIn={handleSignIn} />;
  }

  if (loadingConfig) {
    return (<div style={{ padding: 24 }}>Loading contract configuration...</div>);
  }

  return (
    <div>
      <nav style={{ padding: 12, background: '#222', color: '#fff' }}>
        <Link to="/client" style={{ color: '#fff', marginRight: 12 }}>Client</Link>
        <Link to="/participants" style={{ color: '#fff', marginRight: 12 }}>Participants</Link>
        <Link to="/aggregator" style={{ color: '#fff', marginRight: 12 }}>Aggregator</Link>
        <span style={{ float: 'right' }}>{user.name || user.email}</span>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/client" replace />} />
        <Route path="/client" element={<ClientDashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/participants" element={<ParticipantsDashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/aggregator" element={<AggregatorDashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
      </Routes>
    </div>
  );
}

export default App;
