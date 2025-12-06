import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import SignIn from '../components/SignIn.jsx';
import { Nav, WalletConnect } from '../components';
import Dashboard from './pages/Dashboard.jsx';
import PublishTask from './pages/PublishTask.jsx';
import Mining from './pages/Mining.jsx';
import Rewards from './pages/Rewards.jsx';
import { API_ENDPOINTS, apiCall } from './config/api';
// Keep old components for backward compatibility
import ClientDashboard from '../components/ClientDashboard.jsx';
import ParticipantsDashboard from '../components/ParticipantsDashboard.jsx';
import AggregatorDashboard from '../components/AggregatorDashboard.jsx';
import PublisherDashboard from '../components/PublisherDashboard.jsx';

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
    return (
      <div style={{ 
        padding: 'var(--space-8)', 
        textAlign: 'center',
        color: 'var(--color-text-secondary)'
      }}>
        Loading contract configuration...
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-secondary)' }}>
      <Nav walletConnect={<WalletConnect />} />

      <Routes>
        {/* New Design System Routes */}
        <Route path="/" element={<Dashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/tasks/publish" element={<PublishTask contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} />} />
        <Route path="/mining" element={<Mining user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/rewards" element={<Rewards user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/tasks" element={<Dashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        
        {/* Backward Compatibility Routes */}
        <Route path="/client" element={<ClientDashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/participants" element={<ParticipantsDashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/aggregator" element={<AggregatorDashboard user={user} contractAddress={contractAddress} contractABI={contractABI} rpcUrl={rpcUrl} chainId={chainId} />} />
        <Route path="/publish" element={<PublishFlow rpcUrl={rpcUrl} />} />
      </Routes>
    </div>
  );
}

function PublishFlow({ rpcUrl }) {
  const [dataHash, setDataHash] = useState('QmTest');
  const [status, setStatus] = useState('idle');
  const [taskId, setTaskId] = useState('');
  const [applicants, setApplicants] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const publishTask = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const body = { publisher: 'frontend', dataHash, initialModelLink: '', datasetReq: 'sim', acc_req: 85, reward: 1, texp: 60, nonceTP: 1, L: 'label' };
      const resp = await apiCall(API_ENDPOINTS.RUN_SIMULATION, { method: 'POST', body: JSON.stringify(body) });
      if (!resp.ok) throw new Error('Failed to start simulation');
      const j = await resp.json();
      setTaskId(j.taskId || '');
      setStatus('running');
      setMessage('Publish accepted, polling for applicants...');
      // start polling with backoff
      pollStatus();
    } catch (e) {
      setMessage('Publish failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const pollStatus = async () => {
    const start = Date.now();
    const timeout = 120000; // 2 min
    let delay = 1000;
    const maxDelay = 10000;
    const tick = async () => {
      try {
        const s = await apiCall(API_ENDPOINTS.STATUS);
        setStatus(s.status || 'unknown');
        if (s.status === 'awaiting_selection') {
          setMessage('Applicants ready — fetching');
          try {
            const data = await apiCall(API_ENDPOINTS.GET_APPLICANTS);
            if (data && data.applicants) {
              setApplicants(data.applicants || []);
              setMessage('Applicants loaded');
            } else {
              setMessage('No applicants found');
            }
          } catch (e) {
            setMessage('Failed to fetch applicants: ' + e.message);
          }
          return;
        }
        if (s.status === 'failed') {
          setMessage('Simulation failed on server');
          return;
        }
        if (Date.now() - start < timeout) {
          // exponential backoff
          setTimeout(tick, delay);
          delay = Math.min(maxDelay, delay * 2);
        } else {
          setMessage('Timed out waiting for applicants');
        }
      } catch (e) {
        if (Date.now() - start < timeout) {
          setTimeout(tick, delay);
          delay = Math.min(maxDelay, delay * 2);
        } else {
          setMessage('Polling failed: ' + e.message);
        }
      }
    };
    tick();
  };

  const toggleSelect = (addr) => {
    setSelected(prev => prev.includes(addr) ? prev.filter(x => x !== addr) : [...prev, addr]);
  };

  const selectAllToggle = () => {
    if (selected.length === applicants.length) {
      setSelected([]);
    } else {
      setSelected(applicants.map(a => a.address));
    }
  };

  const startPos = async () => {
    if (selected.length === 0) { setMessage('Select at least one participant'); return; }
    setLoading(true);
    setMessage(null);
    try {
      await apiCall(API_ENDPOINTS.START_POS, { method: 'POST', body: JSON.stringify({ selected }) });
      if (!resp.ok) throw new Error('Server rejected start-pos');
      setMessage('PoS started on server');
    } catch (e) {
      setMessage('Failed to start PoS: ' + e.message);
    } finally { setLoading(false); }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Publish Flow</h2>
      <div>
        <label>Data Hash</label>
        <input value={dataHash} onChange={e => setDataHash(e.target.value)} style={{ width: '60%' }} />
        <button onClick={publishTask} disabled={loading} style={{ marginLeft: 8 }}>Publish & Start</button>
      </div>
      <div style={{ marginTop: 12 }}>
        <strong>Status:</strong> {status} {taskId ? `(task ${taskId})` : ''}
      </div>
      <div style={{ marginTop: 12 }}>
        <h4>Applicants</h4>
        <div style={{ marginBottom: 8 }}>
          <button onClick={selectAllToggle} disabled={applicants.length === 0}>{selected.length === applicants.length ? 'Deselect All' : 'Select All'}</button>
        </div>
        {applicants.length === 0 ? (
          <div>No applicants yet. {status === 'awaiting_selection' ? 'Waiting for applicants...' : ''}</div>
        ) : (
          <ul>
            {applicants.map((a, i) => (
              <li key={i}>
                <label style={{ display: 'block', marginBottom: 6 }}>
                  <input type="checkbox" checked={selected.includes(a.address)} onChange={() => toggleSelect(a.address)} />
                  <span style={{ fontFamily: 'monospace', marginLeft: 8 }}>{a.address}</span>
                </label>
                <div style={{ color: '#666', marginLeft: 28 }}>
                  <div><strong>CID:</strong> {a.proof_cid || 'n/a'}</div>
                  <div><strong>Metadata:</strong> {a.metadata ? JSON.stringify(a.metadata) : 'n/a'}</div>
                </div>
              </li>
            ))}
          </ul>
        )}
        <div style={{ marginTop: 8 }}>
          <button onClick={startPos} disabled={loading || applicants.length === 0 || selected.length === 0}>{loading ? 'Starting PoS...' : 'Start PoS (server)'}</button>
        </div>
      </div>
      {message && <div style={{ marginTop: 12 }}>{message}</div>}
    </div>
  );
}

export default App;
