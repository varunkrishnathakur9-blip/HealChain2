import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, Metric, ProgressBar, Badge, Button } from '../../components';
import { API_ENDPOINTS, apiCall } from '../config/api';

/**
 * Dashboard Page - Landing page showing network statistics and recent tasks
 */
export const Dashboard = ({ user, contractAddress, contractABI, rpcUrl, chainId }) => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiCall(API_ENDPOINTS.PUBLISHED_TASKS);
      setTasks(data.tasks || []);
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  const metrics = {
    activeTasks: tasks.length,
    registeredMiners: tasks.reduce((sum, t) => sum + (t.meta?.minMiners || 0), 0) || 0,
    totalRewards: tasks.reduce((sum, t) => sum + (parseFloat(t.meta?.reward) || 0), 0),
    avgAccuracy: tasks.length > 0 
      ? tasks.reduce((sum, t) => sum + (parseFloat(t.meta?.acc_req) || 0), 0) / tasks.length 
      : 0,
  };

  const formatTask = (task) => ({
    id: task.taskId || task.txHash || `task-${task.time}`,
    name: task.meta?.L || task.meta?.datasetReq || 'Untitled Task',
    description: task.meta?.description || `Dataset: ${task.meta?.datasetReq || 'N/A'}`,
    reward: parseFloat(task.meta?.reward) || 0,
    miners: { current: 0, required: task.meta?.minMiners || 10 },
    accuracy: parseFloat(task.meta?.acc_req) || 0,
    status: 'active',
    publisher: task.publisher,
    time: task.time,
  });

  const recentTasks = tasks.slice(-5).reverse().map(formatTask);

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
          <Metric label="Required Miners" value={metrics.registeredMiners} icon="⛏️" />
          <Metric label="Total Rewards" value={metrics.totalRewards.toFixed(2)} unit="ETH" icon="💰" />
          <Metric label="Average Accuracy Req" value={metrics.avgAccuracy.toFixed(1)} unit="%" icon="🎯" />
        </div>

        {/* Recent Tasks */}
        <Card
          title="Recent Tasks"
          subtitle="Latest federated learning tasks on the network"
          action={
            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              <Button variant="outline" size="sm" onClick={fetchTasks} disabled={loading}>
                {loading ? 'Loading...' : 'Refresh'}
              </Button>
              <Link to="/tasks">
                <Button variant="outline" size="sm">
                  View All →
                </Button>
              </Link>
            </div>
          }
        >
          {error && (
            <div style={{ 
              padding: 'var(--space-3)', 
              backgroundColor: 'var(--color-error-light)', 
              color: 'var(--color-error)',
              borderRadius: 'var(--radius-md)',
              marginBottom: 'var(--space-4)'
            }}>
              Failed to load tasks: {error}
            </div>
          )}
          
          {!loading && recentTasks.length === 0 && !error && (
            <div style={{ 
              padding: 'var(--space-6)', 
              textAlign: 'center',
              color: 'var(--color-text-secondary)'
            }}>
              No tasks published yet. Be the first to publish a task!
            </div>
          )}

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
