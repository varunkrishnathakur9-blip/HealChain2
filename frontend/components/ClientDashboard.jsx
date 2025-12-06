import React, { useEffect, useState } from 'react';
import { API_ENDPOINTS, apiCall } from '../src/config/api';

const ClientDashboard = ({ user, contractAddress, contractABI }) => {
  const [connectedAccount, setConnectedAccount] = useState(null);
  const [pk, setPk] = useState('');
  const [proofCid, setProofCid] = useState('');
  const [proofJson, setProofJson] = useState('');
  const [metadataJson, setMetadataJson] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [publishedTasks, setPublishedTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [viewTask, setViewTask] = useState(null);
  const [taskApplicants, setTaskApplicants] = useState([]);
  const [loadingApplicants, setLoadingApplicants] = useState(false);
  const [posResult, setPosResult] = useState(null);

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

  // Fetch persisted published tasks for publishers/miners to view
  const fetchPublishedTasks = async () => {
    try {
      setLoadingTasks(true);
      const data = await apiCall(API_ENDPOINTS.PUBLISHED_TASKS);
      if (data && data.tasks) setPublishedTasks(data.tasks);
    } catch (e) {
      console.warn('Failed to fetch published tasks', e);
    } finally {
      setLoadingTasks(false);
    }
  };

  // Fetch applicants for the currently open simulation task
  const fetchTaskApplicants = async (taskId) => {
    try {
      setLoadingApplicants(true);
      // The sim server exposes /get-applicants and supports querying by taskId
      const url = taskId ? `${API_ENDPOINTS.GET_APPLICANTS}?taskId=${encodeURIComponent(taskId)}` : API_ENDPOINTS.GET_APPLICANTS;
      const data = await apiCall(url);
      if (data && data.applicants) {
        setTaskApplicants(data.applicants || []);
      } else {
        setTaskApplicants([]);
      }
    } catch (e) {
      console.warn('Failed to fetch applicants', e);
      setTaskApplicants([]);
    } finally {
      setLoadingApplicants(false);
    }
  };

  useEffect(() => {
    fetchPublishedTasks();
    // Refresh when a miner submits or a task is published elsewhere
    const handler = () => fetchPublishedTasks();
    window.addEventListener('miner_submitted', handler);
    window.addEventListener('task_published', handler);
    return () => { window.removeEventListener('miner_submitted', handler); window.removeEventListener('task_published', handler); };
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

    // If user is viewing a particular published task, include taskId so the server
    // can persist this application against the task record for dashboards.
    if (viewTask && (viewTask.taskId || viewTask.dataHash)) {
      payload.taskId = viewTask.taskId || viewTask.dataHash;
    }

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

      {/* Publisher UI removed from Client Dashboard (publisher functions available under Tasks → Publish) */}

      <div style={{ marginTop: 18 }}>
        <h3>Published Tasks</h3>
        <p>See tasks published in the simulation server and apply directly.</p>
        {loadingTasks ? (
          <div>Loading tasks...</div>
        ) : (
          <div>
            {publishedTasks.length === 0 ? (
              <div>No published tasks available.</div>
            ) : (
              <ul>
                {publishedTasks.map((t, i) => (
                  <li key={i} style={{ marginBottom: 12, padding: 8, border: '1px solid #eee' }}>
                    <div><strong>Task ID:</strong> <span style={{ fontFamily: 'monospace' }}>{t.taskId || 'n/a'}</span></div>
                    <div><strong>Data Hash:</strong> {t.dataHash || 'n/a'}</div>
                    <div><strong>Publisher:</strong> {t.publisher || 'n/a'}</div>
                    <div style={{ marginTop: 6 }}>
                      <strong>Reward:</strong> {t.meta && (t.meta.reward || t.meta.reward_R) ? (t.meta.reward || t.meta.reward_R) : 'n/a'} &nbsp; 
                      <strong>Acc Req:</strong> {t.meta && (t.meta.acc_req || t.meta.accReq) ? (t.meta.acc_req || t.meta.accReq) : 'n/a'} &nbsp; 
                      <strong>Texp:</strong> {t.meta && (t.meta.texp || t.meta.Texp) ? (t.meta.texp || t.meta.Texp) : 'n/a'}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <button onClick={() => {
                        // Pre-fill form with dataHash and trigger scroll
                        if (t.dataHash) setProofCid(t.dataHash);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}>Apply / Send Response</button>
                      <button style={{ marginLeft: 8 }} onClick={() => {
                        // Toggle view details panel
                        if (viewTask && viewTask.taskId === t.taskId) {
                          setViewTask(null);
                          setTaskApplicants([]);
                          setPosResult(null);
                        } else {
                          setViewTask(t);
                          // fetch applicants for this task
                          fetchTaskApplicants(t.taskId);
                        }
                      }}>{viewTask && viewTask.taskId === t.taskId ? 'Hide Details' : 'View Details'}</button>
                      <button style={{ marginLeft: 8 }} onClick={() => {
                        // Quick submit example using connectedAccount (if available)
                        const payload = { address: connectedAccount || '0x0', pk: pk || null, proof_cid: t.dataHash || null, metadata: { sourcedFrom: 'publishedTasks' } };
                        // Attach taskId so submissions are persisted to the task record
                        payload.taskId = t.taskId || t.dataHash;
                        apiCall(API_ENDPOINTS.MINER_SUBMIT, { method: 'POST', body: JSON.stringify(payload) })
                          .then(() => { setMessage('Application submitted for task ' + (t.taskId || t.dataHash)); })
                          .catch((e) => { setMessage('Failed to submit: ' + e.message); });
                      }}>Quick Submit</button>
                    </div>
                    {/* Details panel */}
                    {viewTask && viewTask.taskId === t.taskId && (
                      <div style={{ marginTop: 12, padding: 10, background: '#fafafa', border: '1px solid #ddd' }}>
                        <h4>Task Details</h4>
                        <div><strong>Task ID:</strong> <span style={{ fontFamily: 'monospace' }}>{t.taskId}</span></div>
                        <div><strong>Data Hash:</strong> {t.dataHash}</div>
                        <div><strong>Publisher:</strong> {t.publisher}</div>
                        <div style={{ marginTop: 8 }}>
                          <strong>Reward:</strong> {t.meta && (t.meta.reward || t.meta.reward_R) ? (t.meta.reward || t.meta.reward_R) : 'n/a'}<br />
                          <strong>Acc Req:</strong> {t.meta && (t.meta.acc_req || t.meta.accReq) ? (t.meta.acc_req || t.meta.accReq) : 'n/a'}<br />
                          <strong>Texp:</strong> {t.meta && (t.meta.texp || t.meta.Texp) ? (t.meta.texp || t.meta.Texp) : 'n/a'}
                        </div>
                        <div style={{ marginTop: 12 }}>
                          <button onClick={() => fetchTaskApplicants(t.taskId)}>Refresh Applicants</button>
                          <button style={{ marginLeft: 8 }} onClick={async () => {
                            try {
                              setMessage(null);
                              const k = 1; // select 1 aggregator by default
                              const res = await apiCall(API_ENDPOINTS.RUN_POS_SELECTION, { method: 'POST', body: JSON.stringify({ k }) });
                              if (res && res.selected) {
                                setPosResult(res.selected);
                                setMessage('PoS selection started. Selected: ' + res.selected.join(', '));
                              }
                            } catch (e) {
                              setMessage('PoS selection failed: ' + (e && e.message ? e.message : e));
                            }
                          }}>Request PoS Selection</button>
                        </div>

                        <div style={{ marginTop: 12 }}>
                          <h5>Applicants</h5>
                          {loadingApplicants ? (<div>Loading applicants...</div>) : (
                            taskApplicants.length === 0 ? (<div>No applicants yet.</div>) : (
                              <ul>
                                {taskApplicants.map((a, idx) => (
                                  <li key={idx} style={{ marginBottom: 8 }}>
                                    <div><strong>Address:</strong> <span style={{ fontFamily: 'monospace' }}>{a.address}</span></div>
                                    <div><strong>CID:</strong> {a.proof_cid || a.proofCid || 'n/a'}</div>
                                    <div><strong>Meta:</strong> {a.metadata ? JSON.stringify(a.metadata) : (a.meta ? JSON.stringify(a.meta) : 'n/a')}</div>
                                    <div style={{ marginTop: 6 }}>
                                      <button onClick={() => {
                                        // Quick submit on behalf of connectedAccount to simulate miner response
                                        const payload = { address: connectedAccount || '0x0', pk: pk || null, proof_cid: a.proof_cid || a.proofCid || null, metadata: a.metadata || a.meta || {} };
                                        // Include taskId so the applicant is stored against the persisted task
                                        payload.taskId = t.taskId || t.dataHash;
                                        apiCall(API_ENDPOINTS.MINER_SUBMIT, { method: 'POST', body: JSON.stringify(payload) })
                                          .then(() => { setMessage('Application submitted (mirror) for ' + (a.address || 'unknown')); fetchTaskApplicants(t.taskId); })
                                          .catch((e) => setMessage('Failed to submit: ' + e.message));
                                      }}>Send Response</button>
                                    </div>
                                  </li>
                                ))}
                              </ul>
                            )
                          )}
                        </div>
                        {posResult && (
                          <div style={{ marginTop: 12 }}><strong>Selected:</strong> {posResult.join(', ')}</div>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientDashboard;
