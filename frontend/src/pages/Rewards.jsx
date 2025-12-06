import React from 'react';
import { Card, Badge } from '../../components';

/**
 * Rewards Page (M7) - Rewards tracking and distribution
 */
export const Rewards = ({ user, contractAddress, contractABI, rpcUrl, chainId }) => {
  // ============================================
  // WEB3 INTEGRATION POINT (M7 - Rewards)
  // ============================================
  // TODO: Integrate reward distribution functions
  //
  // Example implementation:
  // import { useRewardContract } from '../hooks/useContract';
  // const { tpReveal, distributeRewards } = useRewardContract(contractAddress, contractABI);
  //
  // For TP Reveal:
  // const handleReveal = async () => {
  //   const commitment = JSON.parse(localStorage.getItem(`commitment_${taskID}`));
  //   await tpReveal(taskID, commitment.accuracy, commitment.nonce, commitment.commitHash);
  // };
  //
  // For Reward Distribution:
  // const handleDistribute = async () => {
  //   await distributeRewards(taskID, minerAddresses, scores);
  // };
  //
  // Mock data - replace with real data from contracts/API
  const summary = {
    totalEarned: 3.24,
    pendingRewards: 0.82,
    fairShareScore: 87,
    avgFairShare: 78,
  };

  const rewardHistory = [
    {
      task: 'ChestXray-Pneumonia',
      myScore: 0.8743,
      totalScore: 23.45,
      share: 3.73,
      amount: 0.56,
      status: 'completed',
    },
    {
      task: 'MNIST Classification',
      myScore: 0.7821,
      totalScore: 18.92,
      share: 4.13,
      amount: 0.45,
      status: 'distributed',
    },
    {
      task: 'CIFAR-10 Detection',
      myScore: 0.9124,
      totalScore: 21.34,
      share: 4.27,
      amount: 0.64,
      status: 'distributed',
    },
  ];

  return (
    <div className="container" style={{ maxWidth: '1200px', margin: '0 auto', padding: 'var(--space-4)' }}>
      <h1
        style={{
          fontSize: 'var(--font-size-xl)',
          marginBottom: 'var(--space-4)',
          fontWeight: 700,
        }}
      >
        Rewards & Earnings
      </h1>

      {/* Summary Cards */}
      <div
        className="grid grid-auto-fit"
        style={{
          marginBottom: 'var(--space-8)',
        }}
      >
        <Card highlight="success">
          <div style={{ textAlign: 'center' }}>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: '0 0 var(--space-2) 0',
              }}
            >
              Total Earned
            </p>
            <div
              style={{
                fontSize: 'var(--font-size-3xl)',
                fontWeight: 700,
                color: 'var(--color-success)',
                margin: '0 0 var(--space-2) 0',
              }}
            >
              {summary.totalEarned} Ⓞ
            </div>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-success)',
                margin: 0,
              }}
            >
              ↑ +0.45 ETH this week
            </p>
          </div>
        </Card>

        <Card highlight="info">
          <div style={{ textAlign: 'center' }}>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: '0 0 var(--space-2) 0',
              }}
            >
              Pending Rewards
            </p>
            <div
              style={{
                fontSize: 'var(--font-size-3xl)',
                fontWeight: 700,
                color: 'var(--color-primary)',
                margin: '0 0 var(--space-2) 0',
              }}
            >
              {summary.pendingRewards} Ⓞ
            </div>
            <Badge status="pending" label="Reveal Pending" />
          </div>
        </Card>

        <Card highlight="warning">
          <div style={{ textAlign: 'center' }}>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: '0 0 var(--space-2) 0',
              }}
            >
              Fair Share Score
            </p>
            <div
              style={{
                fontSize: 'var(--font-size-3xl)',
                fontWeight: 700,
                color: 'var(--color-warning)',
                margin: '0 0 var(--space-2) 0',
              }}
            >
              {summary.fairShareScore}%
            </div>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: 0,
              }}
            >
              Avg: {summary.avgFairShare}%
            </p>
          </div>
        </Card>
      </div>

      {/* Reward Distribution Table */}
      <Card
        title="Recent Reward Distributions"
        subtitle="Fairness-based reward allocation from completed tasks"
      >
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: '2px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-secondary)',
                }}
              >
                <th
                  style={{
                    padding: 'var(--space-3)',
                    textAlign: 'left',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Task
                </th>
                <th
                  style={{
                    padding: 'var(--space-3)',
                    textAlign: 'right',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Your Score (||Δ||₂)
                </th>
                <th
                  style={{
                    padding: 'var(--space-3)',
                    textAlign: 'right',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Total Score
                </th>
                <th
                  style={{
                    padding: 'var(--space-3)',
                    textAlign: 'right',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Share (%)
                </th>
                <th
                  style={{
                    padding: 'var(--space-3)',
                    textAlign: 'right',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Amount (ETH)
                </th>
                <th
                  style={{
                    padding: 'var(--space-3)',
                    textAlign: 'center',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {rewardHistory.map((row, i) => (
                <tr
                  key={i}
                  style={{
                    borderBottom: '1px solid var(--color-border)',
                    transition: 'background-color 200ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-bg-secondary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <td style={{ padding: 'var(--space-3)' }} data-label="Task">
                    <strong>{row.task}</strong>
                  </td>
                  <td
                    style={{
                      padding: 'var(--space-3)',
                      textAlign: 'right',
                      fontFamily: 'monospace',
                    }}
                    data-label="Your Score"
                  >
                    {row.myScore.toFixed(4)}
                  </td>
                  <td
                    style={{
                      padding: 'var(--space-3)',
                      textAlign: 'right',
                      fontFamily: 'monospace',
                    }}
                    data-label="Total Score"
                  >
                    {row.totalScore.toFixed(2)}
                  </td>
                  <td style={{ padding: 'var(--space-3)', textAlign: 'right' }} data-label="Share">
                    <strong>{row.share.toFixed(2)}%</strong>
                  </td>
                  <td
                    style={{
                      padding: 'var(--space-3)',
                      textAlign: 'right',
                      fontWeight: 700,
                      color: 'var(--color-success)',
                    }}
                    data-label="Amount"
                  >
                    +{row.amount.toFixed(2)} Ⓞ
                  </td>
                  <td style={{ padding: 'var(--space-3)', textAlign: 'center' }} data-label="Status">
                    <Badge
                      status={row.status === 'distributed' ? 'completed' : 'pending'}
                      size="sm"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Fairness Explanation */}
      <Card
        title="How Fairness Works"
        subtitle="Reward allocation mechanism"
        highlight="info"
        style={{ marginTop: 'var(--space-8)' }}
      >
        <div
          className="grid grid-auto-fit"
          style={{
            gap: 'var(--space-6)',
          }}
        >
          <div>
            <h4
              style={{
                margin: '0 0 var(--space-2) 0',
                color: 'var(--color-primary)',
                fontSize: 'var(--font-size-base)',
                fontWeight: 600,
              }}
            >
              📊 Contribution Scoring
            </h4>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: 0,
              }}
            >
              Your score is the L2 norm of your gradient: ||Δᵢ||₂
              <br />
              Higher quality updates = Higher score = Higher rewards
            </p>
          </div>

          <div>
            <h4
              style={{
                margin: '0 0 var(--space-2) 0',
                color: 'var(--color-primary)',
                fontSize: 'var(--font-size-base)',
                fontWeight: 600,
              }}
            >
              ⚖️ Proportional Distribution
            </h4>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: 0,
              }}
            >
              Rewardᵢ = (scoreᵢ / Σ scoreⱼ) × Total
              <br />
              Prevents free-riding & rewards quality work
            </p>
          </div>

          <div>
            <h4
              style={{
                margin: '0 0 var(--space-2) 0',
                color: 'var(--color-primary)',
                fontSize: 'var(--font-size-base)',
                fontWeight: 600,
              }}
            >
              🔐 Cryptographically Verified
            </h4>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: 0,
              }}
            >
              Scores committed in M3, revealed in M7
              <br />
              No tampering possible - blockchain ensures integrity
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Rewards;

