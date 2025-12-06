import React from 'react';
import { Link } from 'react-router-dom';
import { Card, Metric, ProgressBar, Badge, Button } from '../../components';

/**
 * Dashboard Page - Landing page showing network statistics and recent tasks
 */
export const Dashboard = ({ user, contractAddress, contractABI, rpcUrl, chainId }) => {
  // Mock data - replace with real data from contracts/API
  const metrics = {
    activeTasks: 12,
    registeredMiners: 147,
    totalRewards: 24.5,
    avgAccuracy: 94.8,
  };

  const recentTasks = [
    {
      id: 1,
      name: 'ChestXray-Pneumonia',
      description: 'Train classification model on medical images',
      reward: 1.5,
      miners: { current: 23, required: 30 },
      accuracy: 76,
      status: 'active',
    },
    {
      id: 2,
      name: 'MNIST Classification',
      description: 'Digit recognition on handwritten digits',
      reward: 1.0,
      miners: { current: 18, required: 25 },
      accuracy: 92,
      status: 'pending',
    },
  ];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-secondary)' }}>
      {/* Hero Section */}
      <div
        className="container"
        style={{
          background: 'linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-bg-secondary) 100%)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
          textAlign: 'center',
        }}
      >
        <h1
          style={{
            fontSize: 'var(--font-size-2xl)',
            color: 'var(--color-primary)',
            marginBottom: 'var(--space-3)',
            fontWeight: 700,
          }}
        >
          Privacy-Preserving Federated Learning
        </h1>
        <p
          style={{
            fontSize: 'var(--font-size-base)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-4)',
          }}
        >
          Collaborate on machine learning without sharing data. Fair rewards through blockchain.
        </p>
        <div 
          style={{ 
            display: 'flex', 
            gap: 'var(--space-4)', 
            justifyContent: 'center', 
            flexWrap: 'wrap',
          }}
        >
          <Link to="/tasks/publish" style={{ textDecoration: 'none' }}>
            <Button variant="primary" size="lg">
              Publish Task
            </Button>
          </Link>
          <Link to="/mining" style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="lg">
              Become a Miner
            </Button>
          </Link>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="container">
        <div
          className="grid grid-auto-fit"
          style={{
            marginBottom: 'var(--space-8)',
          }}
        >
          <Metric label="Active Tasks" value={metrics.activeTasks} icon="📋" />
          <Metric label="Registered Miners" value={metrics.registeredMiners} icon="⛏️" />
          <Metric label="Total Rewards Distributed" value={metrics.totalRewards} unit="ETH" icon="💰" />
          <Metric label="Average Model Accuracy" value={metrics.avgAccuracy} unit="%" icon="🎯" />
        </div>

        {/* Recent Tasks */}
        <Card
          title="Recent Tasks"
          subtitle="Latest federated learning tasks on the network"
          action={
            <Link to="/tasks">
              <Button variant="outline" size="sm">
                View All →
              </Button>
            </Link>
          }
        >
          <div
            className="grid grid-auto-fit"
            style={{
              gap: 'var(--space-4)',
            }}
          >
            {recentTasks.map((task) => (
              <div
                key={task.id}
                style={{
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4)',
                  transition: 'all 200ms ease',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 'var(--space-3)',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: 'var(--font-size-base)' }}>{task.name}</span>
                  <Badge status={task.status} />
                </div>
                <p
                  style={{
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-secondary)',
                    margin: '0 0 var(--space-3) 0',
                  }}
                >
                  {task.description}
                </p>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: 'var(--font-size-sm)',
                    marginBottom: 'var(--space-3)',
                  }}
                >
                  <span>
                    Reward: <strong>{task.reward} ETH</strong>
                  </span>
                  <span>
                    Miners: <strong>{task.miners.current}/{task.miners.required}</strong>
                  </span>
                </div>
                <ProgressBar value={task.accuracy} label="Accuracy Goal" color="primary" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;

