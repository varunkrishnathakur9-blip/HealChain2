import React from 'react';
import { Card, Metric, ProgressBar, Badge } from '../../components';

/**
 * Mining Dashboard (M2-M3) - Miner's training progress and contribution scores
 */
export const Mining = ({ user, contractAddress, contractABI, rpcUrl, chainId }) => {
  // ============================================
  // WEB3 INTEGRATION POINT (M2-M3 - Mining)
  // ============================================
  // TODO: Fetch real contribution scores from blockchain
  //
  // Example implementation:
  // import { useReadContract } from 'wagmi';
  // const { data: contributionScore } = useReadContract({
  //   address: contractAddress,
  //   abi: contractABI,
  //   functionName: 'getMinerScore',
  //   args: [taskId, userAddress],
  // });
  //
  // Mock data - replace with real data from contracts/API
  const metrics = {
    activeTasks: 3,
    score: 0.8743,
    totalEarned: 3.24,
    participationRate: 94,
  };

  const currentTask = {
    name: 'ChestXray-Pneumonia',
    description: 'Classification model for pneumonia detection',
    score: 0.8743,
    percentile: 87,
    round: { current: 5, total: 10 },
    accuracy: 94.8,
    targetAccuracy: 95,
    epoch: { current: 5, total: 10 },
    localLoss: 0.245,
    localAccuracy: 93.2,
    gradientNorm: 0.87,
    status: 'active',
  };

  return (
    <div className="container" style={{ maxWidth: '1200px', margin: '0 auto', padding: 'var(--space-4)' }}>
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <h1
          style={{
            fontSize: 'var(--font-size-xl)',
            marginBottom: 'var(--space-2)',
            fontWeight: 700,
          }}
        >
          Mining Dashboard
        </h1>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Your federated learning participation and earnings
        </p>
      </div>

      {/* Key Metrics */}
      <div
        className="grid grid-auto-fit"
        style={{
          marginBottom: 'var(--space-8)',
        }}
      >
        <Metric label="Active Tasks" value={metrics.activeTasks} icon="⛏️" />
        <Metric
          label="Your Score (||Δᵢ||₂)"
          value={metrics.score}
          icon="📊"
          change={{ value: 12, direction: 'up' }}
        />
        <Metric label="Total Earned" value={metrics.totalEarned} unit="ETH" icon="💰" />
        <Metric label="Participation Rate" value={metrics.participationRate} unit="%" icon="✅" />
      </div>

      {/* Currently Training Card */}
      <Card
        title="Currently Training"
        subtitle="Active federated learning task"
        highlight="success"
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: 'var(--space-6)',
            marginBottom: 'var(--space-6)',
          }}
          className="grid-responsive-2col"
        >
          <div>
            <h3 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--font-size-lg)', fontWeight: 600 }}>
              {currentTask.name}
            </h3>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: '0 0 var(--space-4) 0',
              }}
            >
              {currentTask.description}
            </p>

            <div
              style={{
                padding: 'var(--space-4)',
                backgroundColor: 'var(--color-success-light)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: 'var(--space-2)',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontWeight: 500 }}>Your Contribution Score</span>
                <span style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>
                  {currentTask.score}
                </span>
              </div>
              <ProgressBar value={currentTask.percentile} label="Percentile" color="success" />
            </div>
          </div>

          <div>
            <div style={{ marginBottom: 'var(--space-6)' }}>
              <span
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  display: 'block',
                  marginBottom: 'var(--space-1)',
                }}
              >
                Round
              </span>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700 }}>
                Round {currentTask.round.current} of {currentTask.round.total}
              </div>
            </div>

            <div style={{ marginBottom: 'var(--space-6)' }}>
              <span
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  display: 'block',
                  marginBottom: 'var(--space-1)',
                }}
              >
                Model Accuracy
              </span>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700 }}>
                {currentTask.accuracy}%
              </div>
              <span
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-success)',
                }}
              >
                ↑ Target: {currentTask.targetAccuracy}%
              </span>
            </div>

            <div style={{ marginBottom: 'var(--space-4)' }}>
              <Badge status={currentTask.status} label="Training in Progress" />
            </div>
          </div>
        </div>

        {/* Training Progress */}
        <div
          style={{
            backgroundColor: 'var(--color-bg-secondary)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <p
            style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: 500,
              margin: '0 0 var(--space-3) 0',
            }}
          >
            Training Progress
          </p>
          <ProgressBar
            value={(currentTask.epoch.current / currentTask.epoch.total) * 100}
            label={`Epoch ${currentTask.epoch.current}/${currentTask.epoch.total}`}
            color="primary"
          />
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
              gap: 'var(--space-3)',
              marginTop: 'var(--space-4)',
            }}
          >
            <div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                Local Loss
              </div>
              <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>{currentTask.localLoss}</div>
            </div>
            <div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                Local Accuracy
              </div>
              <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                {currentTask.localAccuracy}%
              </div>
            </div>
            <div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                Gradient Norm
              </div>
              <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                ||Δ|| = {currentTask.gradientNorm}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                Status
              </div>
              <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: 'var(--color-success)' }}>
                ✅ Valid
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Mining;

