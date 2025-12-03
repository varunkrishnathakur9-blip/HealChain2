import React, { useState } from 'react';
import { ethers } from 'ethers';

const MinerDashboard = ({ contractAddress, contractABI, currentTaskId }) => {
    const [datasetSize, setDatasetSize] = useState('1000');
    const [computePower, setComputePower] = useState('2.5');
    const [status, setStatus] = useState(null);

    const uploadToIPFS = async (payload) => {
        // Use local IPFS HTTP API to add JSON
        const url = 'http://127.0.0.1:5001/api/v0/add';
        const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
        const form = new FormData();
        form.append('file', blob, 'proof.json');

        const res = await fetch(url, { method: 'POST', body: form });
        const text = await res.text();
        // IPFS returns lines of JSON; take last
        const lastLine = text.trim().split('\n').pop();
        const parsed = JSON.parse(lastLine);
        return parsed.Hash || parsed.Name;
    };

    const handleJoinTask = async () => {
        try {
            setStatus('Uploading proof to IPFS...');
            const payload = {
                dataset_size: parseInt(datasetSize, 10),
                compute_power: parseFloat(computePower)
            };
            const cid = await uploadToIPFS(payload);
            setStatus(`Uploaded to IPFS: ${cid}`);

            if (!window.ethereum) {
                setStatus('MetaMask required to call contract');
                return;
            }

            const provider = new ethers.BrowserProvider(window.ethereum);
            const signer = await provider.getSigner();
            const contract = new ethers.Contract(contractAddress, contractABI, signer);

            const tx = await contract.applyForTask(parseInt(currentTaskId, 10), cid);
            setStatus('Submitting on-chain application...');
            await tx.wait();
            setStatus('Applied successfully on-chain.');
        } catch (e) {
            setStatus('Error: ' + e.message);
        }
    };

    return (
        <div style={{ padding: 12 }}>
            <h3>Miner Dashboard</h3>
            <div>
                <label>Dataset Size</label>
                <input value={datasetSize} onChange={e => setDatasetSize(e.target.value)} />
            </div>
            <div>
                <label>Compute Power</label>
                <input value={computePower} onChange={e => setComputePower(e.target.value)} />
            </div>
            <div style={{ marginTop: 8 }}>
                <button onClick={handleJoinTask}>Join Task</button>
            </div>
            {status && <div style={{ marginTop: 8 }}>{status}</div>}
        </div>
    );
};

export default MinerDashboard;
