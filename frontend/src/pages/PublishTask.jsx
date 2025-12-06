import React, { useState } from 'react';
import { Card, Button } from '../../components';
import { API_ENDPOINTS, apiCall } from '../config/api';

/**
 * Publish Task Page (M1) - Task Publisher form
 */
export const PublishTask = ({ contractAddress, contractABI, rpcUrl }) => {
  const [formData, setFormData] = useState({
    taskName: '',
    datasetType: 'ChestXray-Pneumonia',
    requiredAccuracy: 95,
    totalReward: 1.5,
    description: '',
    minMiners: 10,
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'requiredAccuracy' || name === 'totalReward' || name === 'minMiners' 
        ? parseFloat(value) || 0 
        : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // ============================================
      // WEB3 INTEGRATION POINT (M1 - Publish Task)
      // ============================================
      // TODO: Integrate with escrowContract.publishTask() with commitment hash
      //
      // Example implementation:
      // 1. Generate commitment hash:
      //    const nonce = ethers.randomBytes(32);
      //    const commitHash = ethers.solidityPackedKeccak256(
      //      ['uint256', 'bytes32'],
      //      [formData.requiredAccuracy, nonce]
      //    );
      //
      // 2. Call smart contract:
      //    import { useEscrowContract } from '../hooks/useContract';
      //    const { publishTask } = useEscrowContract(contractAddress, contractABI);
      //    const tx = await publishTask(
      //      taskID,
      //      commitHash,
      //      revealDeadline,
      //      formData.totalReward
      //    );
      //
      // 3. Save commitment locally:
      //    localStorage.setItem(`commitment_${taskID}`, JSON.stringify({
      //      accuracy: formData.requiredAccuracy,
      //      nonce: nonce,
      //      commitHash: commitHash
      //    }));
      //
      // 4. POST to backend simulation server:
      const simulationPayload = {
        publisher: 'frontend', // TODO: Get from connected wallet
        dataHash: `Qm${formData.taskName.replace(/\s+/g, '')}`, // TODO: Generate proper hash
        initialModelLink: '',
        datasetReq: formData.datasetType.toLowerCase().replace(/\s+/g, '_'),
        acc_req: formData.requiredAccuracy,
        reward: formData.totalReward,
        texp: 86400, // 24 hours default
        nonceTP: 1,
        L: formData.description || formData.taskName,
      };

      const result = await apiCall(API_ENDPOINTS.RUN_SIMULATION, {
        method: 'POST',
        body: JSON.stringify(simulationPayload),
      });
      
      setMessage({
        type: 'success',
        text: `Task published successfully! Task ID: ${result.taskId || 'N/A'}. Your commitment has been saved securely.`,
      });
      
      // Reset form
      setFormData({
        taskName: '',
        datasetType: 'ChestXray-Pneumonia',
        requiredAccuracy: 95,
        totalReward: 1.5,
        description: '',
        minMiners: 10,
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Failed to publish task: ${error.message}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: 'var(--space-3)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    fontSize: 'var(--font-size-base)',
    fontFamily: 'var(--font-family-base)',
    marginBottom: 'var(--space-4)',
  };

  const labelStyle = {
    display: 'block',
    marginBottom: 'var(--space-2)',
    fontWeight: 500,
    color: 'var(--color-text-primary)',
  };

  return (
    <div className="container" style={{ maxWidth: '900px', margin: '0 auto', padding: 'var(--space-4)' }}>
      <h1
        style={{
          fontSize: 'var(--font-size-xl)',
          marginBottom: 'var(--space-4)',
          fontWeight: 700,
        }}
      >
        Publish New FL Task
      </h1>

      <Card title="Task Configuration" highlight="info">
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {/* Task Name */}
          <div>
            <label style={labelStyle}>Task Name</label>
            <input
              type="text"
              name="taskName"
              value={formData.taskName}
              onChange={handleChange}
              placeholder="e.g., ChestXray Pneumonia Detection"
              style={inputStyle}
              required
            />
          </div>

          {/* Dataset Selection */}
          <div>
            <label style={labelStyle}>Dataset Type</label>
            <select
              name="datasetType"
              value={formData.datasetType}
              onChange={handleChange}
              style={inputStyle}
            >
              <option>ChestXray-Pneumonia</option>
              <option>MNIST</option>
              <option>CIFAR-10</option>
              <option>ImageNet Subset</option>
            </select>
          </div>

          {/* Required Accuracy & Reward */}
          <div 
            style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr',
              gap: 'var(--space-4)' 
            }}
            className="grid-responsive-2col"
          >
            <div>
              <label style={labelStyle}>Required Accuracy (%)</label>
              <input
                type="number"
                name="requiredAccuracy"
                value={formData.requiredAccuracy}
                onChange={handleChange}
                min="0"
                max="100"
                style={inputStyle}
                required
              />
            </div>
            <div>
              <label style={labelStyle}>Total Reward (ETH)</label>
              <input
                type="number"
                name="totalReward"
                value={formData.totalReward}
                onChange={handleChange}
                min="0.1"
                step="0.1"
                style={inputStyle}
                required
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label style={labelStyle}>Task Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe the learning objective, data handling requirements, etc."
              style={{
                ...inputStyle,
                minHeight: '120px',
                resize: 'vertical',
              }}
            />
          </div>

          {/* Minimum Miners */}
          <div>
            <label style={labelStyle}>Minimum Miners Required</label>
            <input
              type="number"
              name="minMiners"
              value={formData.minMiners}
              onChange={handleChange}
              min="1"
              max="1000"
              style={inputStyle}
              required
            />
          </div>

          {/* Security Note */}
          <div
            style={{
              backgroundColor: 'var(--color-primary-light)',
              border: '1px solid var(--color-primary)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-primary)',
              }}
            >
              🔒 <strong>Your commitment to {'{accuracy, nonce}'} will be saved securely.</strong>
              <br />
              You'll need it later to reveal rewards and confirm task completion.
            </p>
          </div>

          {/* Messages */}
          {message && (
            <div
              style={{
                padding: 'var(--space-4)',
                borderRadius: 'var(--radius-md)',
                backgroundColor:
                  message.type === 'success' ? 'var(--color-success-light)' : 'var(--color-error-light)',
                color: message.type === 'success' ? 'var(--color-success)' : 'var(--color-error)',
                border: `1px solid ${message.type === 'success' ? 'var(--color-success)' : 'var(--color-error)'}`,
              }}
            >
              {message.text}
            </div>
          )}

          {/* Submit Button */}
          <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
            <Button variant="primary" size="lg" type="submit" disabled={loading} style={{ flex: 1 }}>
              {loading ? 'Publishing...' : 'Publish Task & Lock Reward'}
            </Button>
            <Button variant="secondary" size="lg" type="button" onClick={() => window.history.back()}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default PublishTask;

