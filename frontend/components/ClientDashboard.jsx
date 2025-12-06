import React, { useEffect, useState } from 'react';
import PublisherDashboard from './PublisherDashboard.jsx';
import { API_ENDPOINTS, apiCall } from '../src/config/api';

const ClientDashboard = ({ user, contractAddress, contractABI }) => {
  const [connectedAccount, setConnectedAccount] = useState(null);
  const [pk, setPk] = useState('');
  const [proofCid, setProofCid] = useState('');
  const [proofJson, setProofJson] = useState('');
  const [metadataJson, setMetadataJson] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    // If MetaMask is available, try to read the selected account (non-blocking)
    if (typeof window !== 'undefined' && window.ethereum) {
      try {
        window.ethereum.request({ method: 'eth_accounts' }).then((accounts) => {
          if (accounts && accounts.length > 0) setConnectedAccount(accounts[0]);
        }).catch(() => {});
        // Listen for account changes
        window.ethereum.on && window.ethereum.on('accountsChanged', (accounts) => {
          if (accounts && accounts.length > 0) setConnectedAccount(accounts[0]);
          else setConnectedAccount(null);
        });
      } catch (e) {
        // ignore
      }
    }
  }, []);

  const connectWallet = async () => {
    if (!window.ethereum) return setMessage('MetaMask not available');
    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      if (accounts && accounts.length > 0) setConnectedAccount(accounts[0]);
    } catch (e) {
      setMessage('Wallet connection rejected');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);
    if (!connectedAccount) return setMessage('Connect your wallet or provide an address');
    if (!pk && !proofCid && !proofJson && !metadataJson) return setMessage('Provide at least a public key or proof');

    let metadata = null;
    if (metadataJson) {
      try { metadata = JSON.parse(metadataJson); } catch (e) { return setMessage('Invalid metadata JSON'); }
    } else if (proofJson) {
      try { metadata = JSON.parse(proofJson); } catch (e) { return setMessage('Invalid proof JSON'); }
    }

    const payload = {
      address: connectedAccount,
      pk: pk || null,
      proof_cid: proofCid || null,
      metadata: metadata || null
    };

    try {
      setLoading(true);
      // If user provided inline proof JSON but no CID, try uploading to local IPFS API first
      if (!payload.proof_cid && proofJson) {
        try {
          const cid = await uploadProofJsonToIpfs(proofJson);
          if (cid) {
            payload.proof_cid = cid;
          }
        } catch (e) {
          // IPFS upload failed; we'll continue and submit metadata directly
          console.warn('[ClientDashboard] IPFS upload failed, submitting metadata inline', e);
        }
      }

      await apiCall(API_ENDPOINTS.MINER_SUBMIT, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      setMessage('Application submitted successfully (server accepted it).');
      // Clear form inputs (except pk)
      setProofCid('');
      setProofJson('');
      setMetadataJson('');
      // Trigger a global event so PublisherDashboard can refresh applicants
      try {
        window.dispatchEvent(new CustomEvent('miner_submitted', { detail: { address: connectedAccount } }));
      } catch (e) {}
      // Also proactively call /get-applicants to warm the server cache (best-effort)
      try { apiCall(API_ENDPOINTS.GET_APPLICANTS).catch(() => {}); } catch (e) {}
    } catch (err) {
      setMessage('Submission failed: ' + (err && err.message ? err.message : err));
    } finally {
      setLoading(false);
    }
  };


  async function uploadProofJsonToIpfs(proofJsonStr) {
    // Try to upload to local Kubo HTTP API. This requires the local IPFS daemon
    // to allow CORS requests from the browser. If it fails, throw and let caller
    // continue with metadata inline.
    if (!proofJsonStr) throw new Error('No proof JSON to upload');
    const api = 'http://127.0.0.1:5001/api/v0/add';
    try {
      const blob = new Blob([proofJsonStr], { type: 'application/json' });
      const fd = new FormData();
      fd.append('file', blob, 'proof.json');
      const r = await fetch(api, { method: 'POST', body: fd, mode: 'cors' });
      if (!r.ok) throw new Error(`IPFS API error ${r.status}`);
      const text = await r.text();
      // Kubo returns newline-delimited JSON; parse last line
      const lastLine = text.trim().split('\n').filter(Boolean).pop();
      const parsed = JSON.parse(lastLine);
      return parsed.Hash || parsed.Name || null;
    } catch (e) {
      throw e;
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>Client Dashboard</h2>
      <p>Welcome, <strong>{user?.name || user?.email || connectedAccount || 'Miner'}</strong></p>

      <div style={{ marginTop: 18 }}>
        <h3>Miner Application (Submit Capability Proof)</h3>
        <p>Use this form to submit your public key and proof to the simulation server in real-time.</p>
        <div style={{ marginBottom: 8 }}>
          <strong>Wallet:</strong> {connectedAccount ? (<span style={{ fontFamily: 'monospace' }}>{connectedAccount}</span>) : (<button onClick={connectWallet}>Connect Wallet</button>)}
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 720 }}>
          <label>Public Key (pk)</label>
          <input value={pk} onChange={(e) => setPk(e.target.value)} placeholder="optional - miner public key" />

          <label>Proof CID (if you already have an IPFS CID)</label>
          <input value={proofCid} onChange={(e) => setProofCid(e.target.value)} placeholder="Qm... or leave blank" />

          <label>Proof JSON (paste a JSON object for proof; will be stored as metadata)</label>
          <textarea value={proofJson} onChange={(e) => setProofJson(e.target.value)} rows={6} placeholder='{ "miner_name": "miner-1", "compute_power": 3.5 }' />

          <label>Additional Metadata (JSON)</label>
          <textarea value={metadataJson} onChange={(e) => setMetadataJson(e.target.value)} rows={4} placeholder='Optional metadata: dataset_size, model_quality, etc.' />

          <button type="submit" disabled={loading} style={{ padding: 10 }}>{loading ? 'Submitting...' : 'Submit Application'}</button>
        </form>

        {message && (
          <div style={{ marginTop: 12, padding: 10, background: '#f1f1f1' }}>{message}</div>
        )}
      </div>

      <div style={{ marginTop: 18 }}>
        <h3>Publish a Task</h3>
        <p>Provide initial model link and dataset requirement to become eligible to publish (as in simulation).</p>
        <PublisherDashboard contractAddress={contractAddress} contractABI={contractABI} />
      </div>
    </div>
  );
};

export default ClientDashboard;
