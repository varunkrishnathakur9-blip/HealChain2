import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { API_ENDPOINTS, apiCall } from '../src/config/api';

/**
 * @component PublisherDashboard
 * @description React component for publishing tasks to the TaskManager smart contract.
 *              Connects to MetaMask using ethers.js v6 and provides a UI for task publishing.
 * 
 * @requires ethers.js v6
 * @requires MetaMask browser extension
 * 
 * @example
 * // Usage in your React app:
 * import PublisherDashboard from './components/PublisherDashboard';
 * 
 * function App() {
 *   return <PublisherDashboard contractAddress="0x..." />;
 * }
 */
const PublisherDashboard = ({ contractAddress, contractABI }) => {
    // --- State Management ---
    
    /// @notice Current connected wallet address
    const [currentAccount, setCurrentAccount] = useState(null);
    
    /// @notice Loading state for async operations
    const [loading, setLoading] = useState(false);
    
    /// @notice Error message state
    const [error, setError] = useState(null);
    
    /// @notice Success message state
    const [success, setSuccess] = useState(null);
    
    /// @notice Input field for data hash
    const [dataHash, setDataHash] = useState('');
    /// @notice Input for initial model link (for eligibility)
    const [initialModelLink, setInitialModelLink] = useState('');
    /// @notice Input for dataset requirement / accuracy requirement
    const [datasetReq, setDatasetReq] = useState('');
    /// @notice Input for target accuracy percent
    const [accReq, setAccReq] = useState('85.0');
    /// @notice Input for reward (ETH)
    const [reward, setReward] = useState('10.0');
    /// @notice Input for expiration (seconds)
    const [texp, setTexp] = useState('86400');
    /// @notice Optional nonce for TP
    const [nonceTP, setNonceTP] = useState('');
    /// @notice Task label / model link
    const [taskLabel, setTaskLabel] = useState('');
    
    /// @notice Ethers provider instance
    const [provider, setProvider] = useState(null);
    
    /// @notice Ethers signer instance
    const [signer, setSigner] = useState(null);
    
    /// @notice Contract instance
    const [contract, setContract] = useState(null);
    const [applicants, setApplicants] = useState([]);
    const [selectedApplicants, setSelectedApplicants] = useState([]);
    const [simStatus, setSimStatus] = useState(null);
    
    const [selectedAggregator, setSelectedAggregator] = useState(null);
    const [taskContractAddr, setTaskContractAddr] = useState('');
    const [taskContractABIJSON, setTaskContractABIJSON] = useState(null);
    const [taskIdBytes32, setTaskIdBytes32] = useState('');
    const [lastPublishedTaskId, setLastPublishedTaskId] = useState(null);
    
    // --- Effects ---
    
    /**
     * @effect Initialize connection to MetaMask on component mount
     */
    useEffect(() => {
        // Check if MetaMask is installed
        if (typeof window.ethereum !== 'undefined') {
            initializeProvider();
            // Listen for account changes
            window.ethereum.on('accountsChanged', handleAccountsChanged);
            // Listen for chain changes
            window.ethereum.on('chainChanged', () => {
                window.location.reload();
            });
        } else {
            setError('MetaMask is not installed. Please install MetaMask to use this application.');
        }
        
        // Cleanup listeners on unmount
        return () => {
            if (window.ethereum) {
                window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
            }
        };
    }, []);
    
    /**
     * @effect Initialize contract instance when provider and signer are ready
     */
    useEffect(() => {
        if (provider && signer && contractAddress && contractABI) {
            try {
                const contractInstance = new ethers.Contract(
                    contractAddress,
                    contractABI,
                    signer
                );
                setContract(contractInstance);
            } catch (err) {
                setError(`Failed to initialize contract: ${err.message}`);
            }
        }
    }, [provider, signer, contractAddress, contractABI]);
    
    // --- Helper Functions ---
    
    /**
     * @notice Initialize ethers provider from MetaMask
     */
    const initializeProvider = async () => {
        try {
            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });
            
            if (accounts.length > 0) {
                // Create provider and signer
                const web3Provider = new ethers.BrowserProvider(window.ethereum);
                const web3Signer = await web3Provider.getSigner();
                
                setProvider(web3Provider);
                setSigner(web3Signer);
                setCurrentAccount(accounts[0]);
            }
        } catch (err) {
            setError(`Failed to connect to MetaMask: ${err.message}`);
        }
    };
    
    /**
     * @notice Handle account changes in MetaMask
     * @param accounts Array of connected accounts
     */
    const handleAccountsChanged = async (accounts) => {
        if (accounts.length === 0) {
            // User disconnected MetaMask
            setCurrentAccount(null);
            setProvider(null);
            setSigner(null);
            setContract(null);
        } else {
            // User switched accounts
            setCurrentAccount(accounts[0]);
            if (window.ethereum) {
                const web3Provider = new ethers.BrowserProvider(window.ethereum);
                const web3Signer = await web3Provider.getSigner();
                setSigner(web3Signer);
                
                if (contractABI) {
                    const contractInstance = new ethers.Contract(
                        contractAddress,
                        contractABI,
                        web3Signer
                    );
                    setContract(contractInstance);
                }
            }
        }
    };
    
    /**
     * @notice Connect to MetaMask wallet
     */
    const connectWallet = async () => {
        if (typeof window.ethereum !== 'undefined') {
            try {
                setLoading(true);
                setError(null);
                await initializeProvider();
            } catch (err) {
                setError(`Connection failed: ${err.message}`);
            } finally {
                setLoading(false);
            }
        } else {
            setError('MetaMask is not installed. Please install MetaMask to use this application.');
        }
    };
    
    /**
     * @notice Publish a new task to the blockchain
     * @param event Form submit event
     */
    const handlePublishTask = async (event) => {
        event.preventDefault();
        
        if (!contract) {
            setError('Contract not initialized. Please connect your wallet first.');
            return;
        }
        
        if (!dataHash.trim()) {
            setError('Please enter a data hash.');
            return;
        }
        
        try {
            setLoading(true);
            setError(null);
            setSuccess(null);
            
            // Call the publishTask function
            const tx = await contract.publishTask(dataHash);
            
            // Wait for transaction confirmation
            const receipt = await tx.wait();
            
            // Extract taskId from event logs (robust parsing + fallback)
            const taskPublishedEvent = receipt.logs.find(
                log => {
                    try {
                        const parsed = contract.interface.parseLog(log);
                        return parsed && parsed.name === 'TaskPublished';
                    } catch {
                        return false;
                    }
                }
            );

            let taskId = null;
            if (taskPublishedEvent) {
                try {
                    const parsed = contract.interface.parseLog(taskPublishedEvent);
                    taskId = parsed.args && parsed.args.taskId ? parsed.args.taskId.toString() : null;
                } catch (e) {
                    taskId = null;
                }
            }

            // Fallback: derive from counter if available on contract
            if (!taskId && contract && typeof contract.getTaskIdCounter === 'function') {
                try {
                    const counter = await contract.getTaskIdCounter();
                    const asBigInt = typeof counter === 'bigint' ? counter : BigInt(counter.toString());
                    const derived = asBigInt - BigInt(1);
                    if (derived >= 0) taskId = derived.toString();
                } catch (e) {
                    // ignore
                }
            }

            if (taskId) setLastPublishedTaskId(taskId);

            setSuccess(
                `Task published successfully! Transaction: ${receipt.hash}${taskId ? ` | Task ID: ${taskId}` : ''}`
            );
            setDataHash(''); // Clear input field

            // Try to automatically start the backend simulation (best-effort).
            // If the sim server isn't running, this will fail gracefully and
            // the publisher can still start it manually via the UI.
            try {
                const simBody = {
                    publisher: currentAccount,
                    dataHash: dataHash,
                    initialModelLink: initialModelLink,
                    datasetReq: datasetReq,
                    acc_req: parseFloat(accReq) || 85,
                    reward: parseFloat(reward) || 1,
                    texp: parseInt(texp) || 86400,
                    nonceTP: nonceTP || 0,
                    L: taskLabel || '',
                    taskId: taskId || null
                };

                apiCall(API_ENDPOINTS.RUN_SIMULATION, {
                    method: 'POST',
                    body: JSON.stringify(simBody)
                }).then(() => {
                    setSuccess(prev => prev + ' — Simulation started on backend.');
                }).catch((e) => {
                    // likely no sim server running; tell the user how to start it
                    setError('Could not reach local simulation server. Start it with `python integration\\sim_server.py` or use the listener.');
                });

            // Broadcast the published task to other frontend components (dashboards)
            try {
                const detail = { taskId: taskId || null, dataHash: dataHash, publisher: currentAccount };
                window.dispatchEvent(new CustomEvent('task_published', { detail }));
            } catch (e) {
                // ignore dispatch errors
            }
            } catch (e) {
                // swallow any errors from the best-effort call
            }
            
        } catch (err) {
            // Handle user rejection
            if (err.code === 4001) {
                setError('Transaction was rejected by user.');
            } else {
                setError(`Failed to publish task: ${err.message}`);
            }
        } finally {
            setLoading(false);
        }
    };

    // Explicitly start the backend simulation for a published task
    const startSimulation = async (taskId) => {
        if (!taskId) return setError('Task ID required to start simulation');
        try {
            setLoading(true);
            setError(null);
            await apiCall(API_ENDPOINTS.RUN_SIMULATION, {
                method: 'POST',
                body: JSON.stringify({ taskId })
            });
            setSuccess('Simulation started on backend.');
        } catch (e) {
            setError('Failed to start simulation on backend: ' + e.message);
        } finally {
            setLoading(false);
        }
    };

    // --- New: Fetch applicants and run a client-side PoS selection ---
    const fetchApplicants = async (taskId) => {
        if (!contract) return setError('Contract not initialized');
        try {
            setLoading(true);
            setError(null);

            // First try to fetch applicants from the local sim server (preferred)
            try {
                const data = await apiCall(API_ENDPOINTS.GET_APPLICANTS);
                if (data && data.applicants) {
                    // Normalize applicants into { miner, cid, meta }
                    const apps = data.applicants.map(a => ({
                        miner: a.address,
                        cid: a.proof_cid,
                        meta: a.metadata
                    }));
                    setApplicants(apps);
                    return;
                }
            } catch (e) {
                // If sim server not available or returns non-OK, fall back to on-chain logs
            }

            // Fallback: query on-chain MinerApplied events using provider.getLogs
            if (!provider) return setError('Provider not initialized for on-chain fallback');
            const taskIdStr = taskId.toString();
            const signature = 'MinerApplied(uint256,address,string)';
            const topic0 = ethers.keccak256(ethers.toUtf8Bytes(signature));
            const logs = await provider.getLogs({ address: contractAddress, topics: [topic0] });
            const apps = [];
            for (const log of logs) {
                try {
                    const parsed = contract.interface.parseLog(log);
                    const args = parsed.args || {};
                    const evTaskId = args.taskId ? args.taskId.toString() : (args[0] ? args[0].toString() : null);
                    if (evTaskId !== taskIdStr) continue;
                    const miner = args.miner || args[1];
                    const cid = args.ipfsCid || args[2];
                    let meta = null;
                    if (cid) {
                        try {
                            const r = await fetch(`http://127.0.0.1:8080/ipfs/${cid}`);
                            if (r.ok) meta = await r.json();
                        } catch (e) { meta = null }
                    }
                    apps.push({ miner, cid, meta });
                } catch (e) {
                    // ignore parse errors for unrelated logs
                }
            }
            setApplicants(apps);
        } catch (e) {
            setError('Failed to fetch applicants: ' + (e && e.message ? e.message : e));
        } finally {
            setLoading(false);
        }
    };

    const selectAggregator = async () => {
        if (!applicants || applicants.length === 0) return setError('No applicants to select from');
        // Compute stakes (try to use tokenContract if available, otherwise random)
        const stakes = [];
        for (const a of applicants) {
            let stake = Math.floor(Math.random() * 1000) + 100; // fallback
            stakes.push(stake);
        }
        const total = stakes.reduce((s, v) => s + v, 0);
        const probs = stakes.map(s => s / total);
        // Weighted random
        const r = Math.random();
        let acc = 0;
        let idx = 0;
        for (let i = 0; i < probs.length; i++) {
            acc += probs[i];
            if (r <= acc) { idx = i; break; }
        }
        const winner = applicants[idx];
        setSelectedAggregator({ winner, stake: stakes[idx] });
    };

    // Poll sim server status and auto-fetch applicants when awaiting_selection
    useEffect(() => {
        let stopped = false;
        const id = setInterval(async () => {
            try {
                const data = await apiCall(API_ENDPOINTS.STATUS);
                if (stopped) return;
                setSimStatus(data.status);
                // When awaiting_selection, attempt to fetch applicants each poll
                if (data.status === 'awaiting_selection') {
                    const tmInput = document.getElementById('fetchTaskId');
                    const tmVal = tmInput ? tmInput.value : null;
                    fetchApplicants(tmVal || '');
                }
            } catch (e) {
                // ignore polling errors (sim server may be offline)
            }
        }, 2000);
        return () => { stopped = true; clearInterval(id); };
    }, []);

    // Listen for miner submissions from other components (ClientDashboard)
    useEffect(() => {
        const handler = (ev) => {
            try {
                const tmInput = document.getElementById('fetchTaskId');
                const tmVal = tmInput ? tmInput.value : null;
                // call fetchApplicants to refresh list immediately
                fetchApplicants(tmVal || '');
            } catch (e) {
                // ignore
            }
        };
        window.addEventListener('miner_submitted', handler);
        return () => window.removeEventListener('miner_submitted', handler);
    }, []);
    
    // --- Render ---
    
    return (
        <div style={styles.container}>
            <h2 style={styles.title}>Task Publisher Dashboard</h2>
            
            {/* Connection Status */}
            {!currentAccount ? (
                <div style={styles.section}>
                    <p style={styles.infoText}>
                        Connect your MetaMask wallet to publish tasks.
                    </p>
                    <button
                        onClick={connectWallet}
                        disabled={loading}
                        style={styles.button}
                    >
                        {loading ? 'Connecting...' : 'Connect Wallet'}
                    </button>
                </div>
            ) : (
                <div style={styles.section}>
                            <p style={styles.connectedText}>
                                Connected: <strong>{currentAccount}</strong>
                            </p>
                            <div style={{ marginTop: 8 }}>
                                <strong>Sim Server Status:</strong> {simStatus || 'unknown'} {simStatus === 'awaiting_selection' && <span style={{ marginLeft: 8 }}>⏳ Waiting for publisher selection</span>}
                            </div>
                    
                    {/* Publish Task Form */}
                    <form onSubmit={handlePublishTask} style={styles.form}>
                        <div style={styles.formGroup}>
                            <label htmlFor="dataHash" style={styles.label}>
                                Data Hash:
                            </label>
                            <input
                                type="text"
                                id="dataHash"
                                value={dataHash}
                                onChange={(e) => setDataHash(e.target.value)}
                                placeholder="Enter task data hash"
                                style={styles.input}
                                disabled={loading}
                            />
                        </div>
                        <div style={styles.formGroup}>
                            <label htmlFor="initialModelLink" style={styles.label}>Initial Model Link:</label>
                            <input
                                type="text"
                                id="initialModelLink"
                                value={initialModelLink}
                                onChange={(e) => setInitialModelLink(e.target.value)}
                                placeholder="e.g. https://.../model.zip"
                                style={styles.input}
                                disabled={loading}
                            />
                        </div>

                        <div style={styles.formGroup}>
                            <label htmlFor="datasetReq" style={styles.label}>Dataset / Accuracy Requirement:</label>
                            <input
                                type="text"
                                id="datasetReq"
                                value={datasetReq}
                                onChange={(e) => setDatasetReq(e.target.value)}
                                placeholder="e.g. accuracy>=0.85 or dataset_name"
                                style={styles.input}
                                disabled={loading}
                            />
                        </div>
                        <div style={styles.formGroup}>
                            <label htmlFor="accReq" style={styles.label}>Target Accuracy (%)</label>
                            <input type="text" id="accReq" value={accReq} onChange={(e) => setAccReq(e.target.value)} placeholder="85.0" style={styles.input} disabled={loading} />
                        </div>

                        <div style={styles.formGroup}>
                            <label htmlFor="reward" style={styles.label}>Reward (ETH)</label>
                            <input type="text" id="reward" value={reward} onChange={(e) => setReward(e.target.value)} placeholder="10.0" style={styles.input} disabled={loading} />
                        </div>

                        <div style={styles.formGroup}>
                            <label htmlFor="texp" style={styles.label}>Texp (seconds)</label>
                            <input type="text" id="texp" value={texp} onChange={(e) => setTexp(e.target.value)} placeholder="86400" style={styles.input} disabled={loading} />
                        </div>

                        <div style={styles.formGroup}>
                            <label htmlFor="nonceTP" style={styles.label}>Nonce (optional)</label>
                            <input type="text" id="nonceTP" value={nonceTP} onChange={(e) => setNonceTP(e.target.value)} placeholder="random or integer" style={styles.input} disabled={loading} />
                        </div>

                        <div style={styles.formGroup}>
                            <label htmlFor="taskLabel" style={styles.label}>Task Label / Model Link (L)</label>
                            <input type="text" id="taskLabel" value={taskLabel} onChange={(e) => setTaskLabel(e.target.value)} placeholder="classification or https://..." style={styles.input} disabled={loading} />
                        </div>
                        
                        <button
                            type="submit"
                            disabled={loading || !dataHash.trim()}
                            style={{
                                ...styles.button,
                                ...styles.primaryButton,
                                opacity: (loading || !dataHash.trim()) ? 0.6 : 1
                            }}
                        >
                            {loading ? 'Publishing...' : 'Publish Task'}
                        </button>
                    </form>
                </div>
            )}
            
            {/* Error Message */}
            {error && (
                <div style={styles.errorBox}>
                    <strong>Error:</strong> {error}
                </div>
            )}
            
            {/* Success Message */}
            {success && (
                <div style={styles.successBox}>
                    <strong>Success:</strong> {success}
                </div>
            )}
            {/* Applicants Section */}
            <div style={{ marginTop: 16 }}>
                <h4>Applicants</h4>
                <div style={{ marginBottom: 8 }}>
                    <input id="fetchTaskId" placeholder="Task ID" style={styles.input} />
                    <button onClick={() => {
                        const taskId = document.getElementById('fetchTaskId').value;
                        fetchApplicants(taskId);
                    }}>Fetch Applicants</button>
                    <button onClick={async () => {
                        // Trigger server-side PoS/resume using the selected applicants
                        if (!selectedApplicants || selectedApplicants.length === 0) {
                            setError('No applicants selected. Please select participants first.');
                            return;
                        }
                        try {
                            setLoading(true);
                            setError(null);
                            await apiCall(API_ENDPOINTS.SELECT_PARTICIPANTS, {
                                method: 'POST',
                                body: JSON.stringify({ selected: selectedApplicants })
                            });
                            setSuccess('PoS triggered on server — simulation resumed.');
                        } catch (e) {
                            setError('Failed to trigger PoS: ' + (e && e.message ? e.message : e));
                        } finally {
                            setLoading(false);
                        }
                    }} style={{ marginLeft: 8 }}>Select Aggregator (PoS)</button>
                </div>
                {applicants && applicants.length > 0 && (
                    <div>
                        <p style={{ marginBottom: 8 }}>Select which applicants should participate in the PoS selection:</p>
                        <ul>
                            {applicants.map((a, i) => {
                                const minerAddr = a.miner && a.miner.address ? a.miner.address : a.miner;
                                const checked = selectedApplicants.includes(minerAddr);
                                return (
                                    <li key={i} style={{ marginBottom: 6 }}>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <input type="checkbox" checked={checked} onChange={() => {
                                                if (checked) {
                                                    setSelectedApplicants(prev => prev.filter(x => x !== minerAddr));
                                                } else {
                                                    setSelectedApplicants(prev => [...prev, minerAddr]);
                                                }
                                            }} />
                                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                <span style={{ fontFamily: 'monospace' }}>{minerAddr}</span>
                                                <span style={{ color: '#666', marginTop: 4 }}>CID: {a.cid || 'n/a'}</span>
                                                <span style={{ color: '#666', marginTop: 4 }}>Metadata: {a.meta ? JSON.stringify(a.meta) : (a.metadata ? JSON.stringify(a.metadata) : 'n/a')}</span>
                                            </div>
                                        </label>
                                    </li>
                                );
                            })}
                        </ul>

                        <div style={{ marginTop: 8 }}>
                            <button onClick={async () => {
                                // Submit selected participants to sim server
                                if (!selectedApplicants || selectedApplicants.length === 0) {
                                    setError('No applicants selected. Choose at least one participant.');
                                    return;
                                }
                                try {
                                    setLoading(true);
                                    setError(null);
                                    await apiCall(API_ENDPOINTS.SELECT_PARTICIPANTS, {
                                        method: 'POST',
                                        body: JSON.stringify({ selected: selectedApplicants })
                                    });
                                    setSuccess('Selection submitted — simulation will resume with chosen participants.');
                                } catch (e) {
                                    setError('Failed to submit selection: ' + (e && e.message ? e.message : e));
                                } finally {
                                    setLoading(false);
                                }
                            }} style={{ ...styles.button, backgroundColor: '#17a2b8' }} disabled={loading}>
                                {loading ? 'Submitting...' : 'Confirm Selection & Resume Simulation'}
                            </button>
                        </div>
                    </div>
                )}
                {selectedAggregator && (
                    <div style={{ marginTop: 8 }}>
                        <strong>Selected Aggregator:</strong> {selectedAggregator.winner.miner} (stake: {selectedAggregator.stake})
                        <div style={{ marginTop: 8 }}>
                            <label style={{ display: 'block', marginBottom: 6 }}>TaskContract TaskID (bytes32, optional):</label>
                            <input style={{ padding: '6px', width: '100%' }} placeholder="0x... or leave blank to derive from TaskManager ID" value={taskIdBytes32} onChange={(e) => setTaskIdBytes32(e.target.value)} />
                        </div>
                        <div style={{ marginTop: 8 }}>
                            <label style={{ display: 'block', marginBottom: 6 }}>TaskContract Address (optional):</label>
                            <input style={{ padding: '6px', width: '100%' }} placeholder="0x... (or leave blank to fetch /TaskContract.json)" value={taskContractAddr} onChange={(e) => setTaskContractAddr(e.target.value)} />
                        </div>
                        <div style={{ marginTop: 8 }}>
                            <button onClick={async () => {
                                try {
                                    setLoading(true);
                                    setError(null);
                                    // attempt to load ABI from public if not provided
                                    let abi = taskContractABIJSON;
                                    if (!abi) {
                                        try {
                                            const r = await fetch('/TaskContract.json');
                                            if (r.ok) {
                                                const json = await r.json();
                                                abi = json.abi || json;
                                                setTaskContractABIJSON(abi);
                                            }
                                        } catch (e) {
                                            // ignore
                                        }
                                    }

                                    const addr = taskContractAddr || (window && window.contractConfig && window.contractConfig.TaskContract && window.contractConfig.TaskContract.address) || null;
                                    if (!addr) return setError('TaskContract address not provided. Set it in the input or put /TaskContract.json in frontend/public.');
                                    if (!abi) return setError('TaskContract ABI not available. Place TaskContract.json (with ABI) in frontend/public.');
                                    if (!signer) return setError('Wallet not connected');

                                    // derive bytes32 taskID if user didn't supply
                                    let tid = taskIdBytes32;
                                    if (!tid) {
                                        // try to derive from the TaskManager numeric id input field on the page
                                        const tmInput = document.getElementById('fetchTaskId');
                                        if (!tmInput) return setError('No Task ID available to derive bytes32. Please paste bytes32 into the input.');
                                        const tmVal = tmInput.value;
                                        if (!tmVal) return setError('Provide Task ID or bytes32 TaskContract ID');
                                        try {
                                            const big = BigInt(tmVal);
                                            tid = ethers.hexZeroPad(ethers.toBeHex(big), 32);
                                        } catch (e) {
                                            return setError('Failed to derive bytes32 from TaskManager task id. Provide bytes32 manually.');
                                        }
                                    }

                                    const taskContract = new ethers.Contract(addr, abi, signer);
                                    const tx = await taskContract.markAwaitingVerification(tid, selectedAggregator.winner.miner);
                                    await tx.wait();
                                    setSuccess('markAwaitingVerification tx sent: ' + tx.hash);
                                } catch (e) {
                                    setError('Failed to call markAwaitingVerification: ' + (e && e.message ? e.message : e));
                                } finally {
                                    setLoading(false);
                                }
                            }} style={{ marginTop: 8 }}>Register Aggregator On-Chain</button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- Styles ---
const styles = {
    container: {
        maxWidth: '600px',
        margin: '0 auto',
        padding: '20px',
        fontFamily: 'Arial, sans-serif'
    },
    title: {
        textAlign: 'center',
        color: '#333',
        marginBottom: '30px'
    },
    section: {
        marginBottom: '20px',
        padding: '20px',
        border: '1px solid #ddd',
        borderRadius: '8px',
        backgroundColor: '#f9f9f9'
    },
    infoText: {
        marginBottom: '15px',
        color: '#666'
    },
    connectedText: {
        marginBottom: '20px',
        color: '#28a745',
        fontSize: '14px'
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '15px'
    },
    formGroup: {
        display: 'flex',
        flexDirection: 'column',
        gap: '5px'
    },
    label: {
        fontWeight: 'bold',
        color: '#333'
    },
    input: {
        padding: '10px',
        border: '1px solid #ddd',
        borderRadius: '4px',
        fontSize: '14px'
    },
    button: {
        padding: '12px 24px',
        fontSize: '16px',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        backgroundColor: '#007bff',
        color: 'white',
        fontWeight: 'bold',
        transition: 'background-color 0.3s'
    },
    primaryButton: {
        backgroundColor: '#28a745'
    },
    errorBox: {
        padding: '15px',
        marginTop: '20px',
        backgroundColor: '#f8d7da',
        color: '#721c24',
        border: '1px solid #f5c6cb',
        borderRadius: '4px'
    },
    successBox: {
        padding: '15px',
        marginTop: '20px',
        backgroundColor: '#d4edda',
        color: '#155724',
        border: '1px solid #c3e6cb',
        borderRadius: '4px'
    }
};

export default PublisherDashboard;

