import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';

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
    const [selectedAggregator, setSelectedAggregator] = useState(null);
    
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
            
            // Extract taskId from event logs
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
                const parsed = contract.interface.parseLog(taskPublishedEvent);
                taskId = parsed.args.taskId.toString();
            }
            
            setSuccess(
                `Task published successfully! Transaction: ${receipt.hash}${taskId ? ` | Task ID: ${taskId}` : ''}`
            );
            setDataHash(''); // Clear input field

            // Trigger backend simulation runner (best-effort)
            try {
                fetch('http://127.0.0.1:5000/run-simulation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        taskId,
                        txHash: receipt.hash,
                        dataHash,
                        initialModelLink,
                        datasetReq,
                        acc_req: accReq,
                        reward: reward,
                        texp: texp,
                        nonceTP: nonceTP,
                        D: datasetReq,
                        L: taskLabel,
                        publisher: currentAccount
                    })
                }).then(r => {
                    if (r.ok) {
                        setSuccess(s => s + ' Simulation started on backend.');
                    } else {
                        setError('Failed to start simulation on backend.');
                    }
                }).catch(e => setError('Failed to contact simulation server: ' + e.message));
            } catch (e) {
                // noop
            }
            setDataHash(''); // Clear input field
            
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

    // --- New: Fetch applicants and run a client-side PoS selection ---
    const fetchApplicants = async (taskId) => {
        if (!contract) return setError('Contract not initialized');
        try {
            setLoading(true);
            setError(null);
            const taskIdInt = parseInt(taskId, 10);
            const events = await contract.queryFilter(contract.filters.MinerApplied(taskIdInt));
            const apps = [];
            for (const ev of events) {
                try {
                    const miner = ev.args.miner;
                    const cid = ev.args.ipfsCid;
                    // fetch metadata from gateway
                    let meta = null;
                    try {
                        const r = await fetch(`http://127.0.0.1:8080/ipfs/${cid}`);
                        meta = await r.json();
                    } catch (e) {
                        meta = null;
                    }
                    apps.push({ miner, cid, meta });
                } catch (e) {
                    // ignore parse errors
                }
            }
            setApplicants(apps);
        } catch (e) {
            setError('Failed to fetch applicants: ' + e.message);
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
                    <button onClick={selectAggregator} style={{ marginLeft: 8 }}>Select Aggregator (PoS)</button>
                </div>
                {applicants && applicants.length > 0 && (
                    <ul>
                        {applicants.map((a, i) => (
                            <li key={i}>{a.miner} - CID: {a.cid} - dataset: {a.meta ? a.meta.dataset_size : 'n/a'}</li>
                        ))}
                    </ul>
                )}
                {selectedAggregator && (
                    <div style={{ marginTop: 8 }}>
                        <strong>Selected Aggregator:</strong> {selectedAggregator.winner.miner} (stake: {selectedAggregator.stake})
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

