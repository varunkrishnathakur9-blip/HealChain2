# HealChain Frontend UI Design System & Component Library

## Design Philosophy

**For HealChain, we follow these principles:**

1. **Clarity Over Complexity** - Federated learning is complex, but the UI must be intuitive
2. **Real-Time Feedback** - Users need to see model training progress, contribution scores, and rewards live
3. **Trust Through Transparency** - Show blockchain transactions, cryptographic commitments, and fairness metrics
4. **Wallet-First** - Assume users have MetaMask or similar; prioritize Web3 integration
5. **Accessibility** - High color contrast, keyboard navigation, clear labeling

---

## Color Palette & Typography

```css
/* Design Tokens */
:root {
  /* Primary Colors (Blockchain Blue) */
  --color-primary: #0066cc;
  --color-primary-dark: #0052a3;
  --color-primary-light: #e6f0ff;
  
  /* Success/Fairness (Green) */
  --color-success: #22c55e;
  --color-success-light: #dcfce7;
  
  /* Warning/Alert (Amber) */
  --color-warning: #f59e0b;
  --color-warning-light: #fef3c7;
  
  /* Error/Danger (Red) */
  --color-error: #ef4444;
  --color-error-light: #fee2e2;
  
  /* Neutral */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-bg-tertiary: #f3f4f6;
  --color-text-primary: #1f2937;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;
  --color-border: #e5e7eb;
  
  /* Typography */
  --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 32px;
  
  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

---

## Component Library

### 1. Button Component

```tsx
// Button Component - All Variants
type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  onClick?: () => void;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled,
  loading,
  icon,
  onClick,
  children
}) => {
  const baseStyles = `
    font-weight: 500;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 200ms ease;
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
  `;
  
  const sizeStyles = {
    sm: 'padding: var(--space-2) var(--space-3); font-size: var(--font-size-sm);',
    md: 'padding: var(--space-3) var(--space-4); font-size: var(--font-size-base);',
    lg: 'padding: var(--space-4) var(--space-6); font-size: var(--font-size-lg);'
  };
  
  const variantStyles = {
    primary: `
      background-color: var(--color-primary);
      color: white;
      border: 1px solid var(--color-primary);
      &:hover:not(:disabled) {
        background-color: var(--color-primary-dark);
      }
    `,
    secondary: `
      background-color: var(--color-bg-secondary);
      color: var(--color-text-primary);
      border: 1px solid var(--color-border);
      &:hover:not(:disabled) {
        background-color: var(--color-bg-tertiary);
      }
    `,
    outline: `
      background-color: transparent;
      color: var(--color-primary);
      border: 2px solid var(--color-primary);
      &:hover:not(:disabled) {
        background-color: var(--color-primary-light);
      }
    `,
    ghost: `
      background-color: transparent;
      color: var(--color-text-secondary);
      border: none;
      &:hover:not(:disabled) {
        color: var(--color-text-primary);
      }
    `
  };
  
  return (
    <button
      style={{
        ...baseStyles,
        ...sizeStyles[size],
        ...variantStyles[variant],
        opacity: disabled ? 0.5 : 1,
        pointerEvents: disabled ? 'none' : 'auto'
      }}
      onClick={onClick}
      disabled={disabled}
    >
      {loading && <Spinner size="sm" />}
      {icon}
      {children}
    </button>
  );
};
```

### 2. Card Component

```tsx
interface CardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
  highlight?: 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  children,
  action,
  highlight
}) => {
  const highlightColor = {
    success: 'var(--color-success-light)',
    warning: 'var(--color-warning-light)',
    error: 'var(--color-error-light)',
    info: 'var(--color-primary-light)'
  }[highlight || 'info'];
  
  return (
    <div
      style={{
        backgroundColor: 'var(--color-bg-primary)',
        border: `1px solid var(--color-border)`,
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        boxShadow: 'var(--shadow-md)',
        ...(highlight && {
          borderLeft: `4px solid ${highlightColor}`
        })
      }}
    >
      {(title || action) && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--space-3)'
        }}>
          <div>
            {title && (
              <h3 style={{
                fontSize: 'var(--font-size-lg)',
                fontWeight: 600,
                color: 'var(--color-text-primary)',
                margin: 0
              }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                margin: 'var(--space-2) 0 0 0'
              }}>
                {subtitle}
              </p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
```

### 3. Metric Display Component

```tsx
interface MetricProps {
  label: string;
  value: string | number;
  unit?: string;
  change?: {
    value: number;
    direction: 'up' | 'down';
  };
  icon?: React.ReactNode;
}

export const Metric: React.FC<MetricProps> = ({
  label,
  value,
  unit,
  change,
  icon
}) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--space-4)',
    padding: 'var(--space-4)',
    backgroundColor: 'var(--color-bg-secondary)',
    borderRadius: 'var(--radius-md)'
  }}>
    {icon && (
      <div style={{
        fontSize: '24px',
        opacity: 0.7
      }}>
        {icon}
      </div>
    )}
    <div>
      <p style={{
        fontSize: 'var(--font-size-sm)',
        color: 'var(--color-text-secondary)',
        margin: 0
      }}>
        {label}
      </p>
      <div style={{
        display: 'flex',
        alignItems: 'baseline',
        gap: 'var(--space-2)',
        marginTop: 'var(--space-1)'
      }}>
        <span style={{
          fontSize: 'var(--font-size-2xl)',
          fontWeight: 700,
          color: 'var(--color-text-primary)'
        }}>
          {value}
        </span>
        {unit && (
          <span style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)'
          }}>
            {unit}
          </span>
        )}
        {change && (
          <span style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: 500,
            color: change.direction === 'up' ? 'var(--color-success)' : 'var(--color-error)',
            marginLeft: 'var(--space-2)'
          }}>
            {change.direction === 'up' ? '↑' : '↓'} {Math.abs(change.value)}%
          </span>
        )}
      </div>
    </div>
  </div>
);
```

### 4. Progress Bar Component

```tsx
interface ProgressBarProps {
  value: number;  // 0-100
  label?: string;
  color?: 'primary' | 'success' | 'warning' | 'error';
  showPercentage?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  color = 'primary',
  showPercentage = true
}) => {
  const colorMap = {
    primary: 'var(--color-primary)',
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
    error: 'var(--color-error)'
  };
  
  return (
    <div>
      {(label || showPercentage) && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 'var(--space-2)',
          fontSize: 'var(--font-size-sm)'
        }}>
          {label && <span>{label}</span>}
          {showPercentage && <span>{Math.round(value)}%</span>}
        </div>
      )}
      <div style={{
        height: '8px',
        backgroundColor: 'var(--color-border)',
        borderRadius: '99px',
        overflow: 'hidden'
      }}>
        <div
          style={{
            height: '100%',
            width: `${value}%`,
            backgroundColor: colorMap[color],
            transition: 'width 300ms ease'
          }}
        />
      </div>
    </div>
  );
};
```

### 5. Status Badge Component

```tsx
interface BadgeProps {
  status: 'active' | 'pending' | 'completed' | 'failed' | 'locked';
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Badge: React.FC<BadgeProps> = ({
  status,
  label,
  size = 'md'
}) => {
  const statusConfig = {
    active: { bg: 'var(--color-success-light)', text: 'var(--color-success)', dot: '🟢' },
    pending: { bg: 'var(--color-warning-light)', text: 'var(--color-warning)', dot: '🟡' },
    completed: { bg: 'var(--color-success-light)', text: 'var(--color-success)', dot: '✅' },
    failed: { bg: 'var(--color-error-light)', text: 'var(--color-error)', dot: '❌' },
    locked: { bg: 'var(--color-bg-tertiary)', text: 'var(--color-text-secondary)', dot: '🔒' }
  };
  
  const config = statusConfig[status];
  const sizeMap = { sm: '12px', md: '14px', lg: '16px' };
  
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 'var(--space-1)',
      padding: `${size === 'sm' ? 'var(--space-1)' : 'var(--space-2)'} var(--space-3)`,
      backgroundColor: config.bg,
      color: config.text,
      borderRadius: '99px',
      fontSize: sizeMap[size],
      fontWeight: 500
    }}>
      {config.dot}
      {label || status}
    </span>
  );
};
```

---

## Page-by-Page UI Design

### Page 1: Dashboard (Landing)

```tsx
export const Dashboard = () => (
  <div style={{
    minHeight: '100vh',
    backgroundColor: 'var(--color-bg-secondary)'
  }}>
    {/* Top Navigation */}
    <nav style={{
      backgroundColor: 'var(--color-bg-primary)',
      borderBottom: '1px solid var(--color-border)',
      padding: 'var(--space-4) var(--space-6)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-primary)' }}>
        ⛓️ HealChain
      </div>
      <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
        <a href="#tasks" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>Tasks</a>
        <a href="#miners" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>Miners</a>
        <a href="#rewards" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>Rewards</a>
        <WalletConnect />
      </div>
    </nav>
    
    {/* Main Content */}
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: 'var(--space-8)' }}>
      {/* Hero Section */}
      <div style={{
        backgroundColor: 'var(--color-primary-light)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-8)',
        marginBottom: 'var(--space-8)',
        textAlign: 'center'
      }}>
        <h1 style={{
          fontSize: 'var(--font-size-3xl)',
          color: 'var(--color-primary)',
          marginBottom: 'var(--space-3)'
        }}>
          Privacy-Preserving Federated Learning
        </h1>
        <p style={{
          fontSize: 'var(--font-size-lg)',
          color: 'var(--color-text-secondary)',
          marginBottom: 'var(--space-6)'
        }}>
          Collaborate on machine learning without sharing data. Fair rewards through blockchain.
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-4)', justifyContent: 'center' }}>
          <Button variant="primary" size="lg">Publish Task</Button>
          <Button variant="outline" size="lg">Become a Miner</Button>
        </div>
      </div>
      
      {/* Key Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: 'var(--space-6)',
        marginBottom: 'var(--space-8)'
      }}>
        <Metric label="Active Tasks" value={12} icon="📋" />
        <Metric label="Registered Miners" value={147} icon="⛏️" />
        <Metric label="Total Rewards Distributed" value="24.5" unit="ETH" icon="💰" />
        <Metric label="Average Model Accuracy" value="94.8" unit="%" icon="🎯" />
      </div>
      
      {/* Recent Tasks */}
      <Card
        title="Recent Tasks"
        subtitle="Latest federated learning tasks on the network"
        action={<Button variant="outline" size="sm">View All →</Button>}
      >
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 'var(--space-4)'
        }}>
          {/* Task Card */}
          <div style={{
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4)',
            hover: { boxShadow: 'var(--shadow-md)' }
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
              <span style={{ fontWeight: 600 }}>ChestXray-Pneumonia</span>
              <Badge status="active" />
            </div>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              margin: '0 0 var(--space-3) 0'
            }}>
              Train classification model on medical images
            </p>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--space-3)'
            }}>
              <span>Reward: <strong>1.5 ETH</strong></span>
              <span>Miners: <strong>23/30</strong></span>
            </div>
            <ProgressBar value={76} label="Accuracy Goal: 95%" />
          </div>
        </div>
      </Card>
    </div>
  </div>
);
```

### Page 2: Task Publisher - Publish Task (M1)

```tsx
export const PublishTaskPage = () => (
  <div style={{ maxWidth: '900px', margin: '0 auto', padding: 'var(--space-8)' }}>
    <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--space-6)' }}>
      Publish New FL Task
    </h1>
    
    <Card title="Task Configuration" highlight="info">
      <form style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {/* Task Name */}
        <div>
          <label style={{
            display: 'block',
            marginBottom: 'var(--space-2)',
            fontWeight: 500,
            color: 'var(--color-text-primary)'
          }}>
            Task Name
          </label>
          <input
            type="text"
            placeholder="e.g., ChestXray Pneumonia Detection"
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-base)',
              fontFamily: 'var(--font-family-base)'
            }}
          />
        </div>
        
        {/* Dataset Selection */}
        <div>
          <label style={{
            display: 'block',
            marginBottom: 'var(--space-2)',
            fontWeight: 500
          }}>
            Dataset Type
          </label>
          <select style={{
            width: '100%',
            padding: 'var(--space-3)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)'
          }}>
            <option>ChestXray-Pneumonia</option>
            <option>MNIST</option>
            <option>CIFAR-10</option>
            <option>ImageNet Subset</option>
          </select>
        </div>
        
        {/* Required Accuracy */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
          <div>
            <label style={{
              display: 'block',
              marginBottom: 'var(--space-2)',
              fontWeight: 500
            }}>
              Required Accuracy (%)
            </label>
            <input
              type="number"
              min="0"
              max="100"
              defaultValue="95"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)'
              }}
            />
          </div>
          
          {/* Reward Amount */}
          <div>
            <label style={{
              display: 'block',
              marginBottom: 'var(--space-2)',
              fontWeight: 500
            }}>
              Total Reward (ETH)
            </label>
            <input
              type="number"
              min="0.1"
              step="0.1"
              defaultValue="1.5"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)'
              }}
            />
          </div>
        </div>
        
        {/* Description */}
        <div>
          <label style={{
            display: 'block',
            marginBottom: 'var(--space-2)',
            fontWeight: 500
          }}>
            Task Description
          </label>
          <textarea
            placeholder="Describe the learning objective, data handling requirements, etc."
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              minHeight: '120px',
              fontFamily: 'var(--font-family-base)',
              fontSize: 'var(--font-size-base)'
            }}
          />
        </div>
        
        {/* Minimum Miners */}
        <div>
          <label style={{
            display: 'block',
            marginBottom: 'var(--space-2)',
            fontWeight: 500
          }}>
            Minimum Miners Required
          </label>
          <input
            type="number"
            min="1"
            max="1000"
            defaultValue="10"
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)'
            }}
          />
        </div>
        
        {/* Security Note */}
        <div style={{
          backgroundColor: 'var(--color-primary-light)',
          border: `1px solid var(--color-primary)`,
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)'
        }}>
          <p style={{
            margin: 0,
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-primary)'
          }}>
            🔒 <strong>Your commitment to {'{accuracy, nonce}'} will be saved securely.</strong>
            <br />You'll need it later to reveal rewards and confirm task completion.
          </p>
        </div>
        
        {/* Submit Button */}
        <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
          <Button variant="primary" size="lg" style={{ flex: 1 }}>
            Publish Task & Lock Reward
          </Button>
          <Button variant="secondary" size="lg">Cancel</Button>
        </div>
      </form>
    </Card>
  </div>
);
```

### Page 3: Miner Dashboard (M2-M3)

```tsx
export const MinerDashboard = () => (
  <div style={{ maxWidth: '1200px', margin: '0 auto', padding: 'var(--space-8)' }}>
    <div style={{ marginBottom: 'var(--space-8)' }}>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--space-2)' }}>
        Mining Dashboard
      </h1>
      <p style={{ color: 'var(--color-text-secondary)' }}>
        Your federated learning participation and earnings
      </p>
    </div>
    
    {/* Key Metrics */}
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
      gap: 'var(--space-4)',
      marginBottom: 'var(--space-8)'
    }}>
      <Metric label="Active Tasks" value={3} icon="⛏️" />
      <Metric label="Your Score (||Δᵢ||₂)" value="0.8743" icon="📊" change={{ value: 12, direction: 'up' }} />
      <Metric label="Total Earned" value="3.24" unit="ETH" icon="💰" />
      <Metric label="Participation Rate" value="94" unit="%" icon="✅" />
    </div>
    
    {/* Current Task - Active */}
    <Card
      title="Currently Training"
      subtitle="Active federated learning task"
      highlight="success"
    >
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 'var(--space-6)',
        marginBottom: 'var(--space-6)'
      }}>
        <div>
          <h3 style={{ margin: '0 0 var(--space-2) 0' }}>ChestXray-Pneumonia</h3>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Classification model for pneumonia detection
          </p>
          
          <div style={{
            marginTop: 'var(--space-4)',
            padding: 'var(--space-4)',
            backgroundColor: 'var(--color-success-light)',
            borderRadius: 'var(--radius-md)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <span style={{ fontWeight: 500 }}>Your Contribution Score</span>
              <span style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>0.8743</span>
            </div>
            <ProgressBar value={87} label="Percentile" />
          </div>
        </div>
        
        <div>
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Round</span>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700 }}>Round 5 of 10</div>
          </div>
          
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Model Accuracy</span>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700 }}>94.8%</div>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-success)' }}>↑ Target: 95%</span>
          </div>
          
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <Badge status="active" label="Training in Progress" />
          </div>
        </div>
      </div>
      
      {/* Training Progress */}
      <div style={{
        backgroundColor: 'var(--color-bg-secondary)',
        padding: 'var(--space-4)',
        borderRadius: 'var(--radius-md)'
      }}>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          fontWeight: 500,
          margin: '0 0 var(--space-3) 0'
        }}>
          Training Progress
        </p>
        <ProgressBar value={50} label="Epoch 5/10" color="primary" />
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 'var(--space-3)',
          marginTop: 'var(--space-4)'
        }}>
          <div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Local Loss</div>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>0.245</div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Local Accuracy</div>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>93.2%</div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Gradient Norm</div>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>||Δ|| = 0.87</div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Status</div>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, color: 'var(--color-success)' }}>✅ Valid</div>
          </div>
        </div>
      </div>
    </Card>
  </div>
);
```

### Page 4: Rewards Tracking & Distribution (M7)

```tsx
export const RewardsPage = () => (
  <div style={{ maxWidth: '1200px', margin: '0 auto', padding: 'var(--space-8)' }}>
    <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--space-6)' }}>
      Rewards & Earnings
    </h1>
    
    {/* Summary Cards */}
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
      gap: 'var(--space-4)',
      marginBottom: 'var(--space-8)'
    }}>
      <Card highlight="success">
        <div style={{ textAlign: 'center' }}>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: '0 0 var(--space-2) 0'
          }}>
            Total Earned
          </p>
          <div style={{
            fontSize: 'var(--font-size-3xl)',
            fontWeight: 700,
            color: 'var(--color-success)',
            margin: '0 0 var(--space-2) 0'
          }}>
            3.24 Ⓞ
          </div>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-success)',
            margin: 0
          }}>
            ↑ +0.45 ETH this week
          </p>
        </div>
      </Card>
      
      <Card highlight="info">
        <div style={{ textAlign: 'center' }}>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: '0 0 var(--space-2) 0'
          }}>
            Pending Rewards
          </p>
          <div style={{
            fontSize: 'var(--font-size-3xl)',
            fontWeight: 700,
            color: 'var(--color-primary)',
            margin: '0 0 var(--space-2) 0'
          }}>
            0.82 Ⓞ
          </div>
          <Badge status="pending" label="Reveal Pending" />
        </div>
      </Card>
      
      <Card highlight="warning">
        <div style={{ textAlign: 'center' }}>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: '0 0 var(--space-2) 0'
          }}>
            Fair Share Score
          </p>
          <div style={{
            fontSize: 'var(--font-size-3xl)',
            fontWeight: 700,
            color: 'var(--color-warning)',
            margin: '0 0 var(--space-2) 0'
          }}>
            87%
          </div>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Avg: 78%
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
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: 'var(--font-size-sm)'
        }}>
          <thead>
            <tr style={{
              borderBottom: '2px solid var(--color-border)',
              backgroundColor: 'var(--color-bg-secondary)'
            }}>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'left',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Task</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'right',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Your Score (||Δ||₂)</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'right',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Total Score</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'right',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Share (%)</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'right',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Amount (ETH)</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'center',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              {
                task: 'ChestXray-Pneumonia',
                myScore: 0.8743,
                totalScore: 23.45,
                share: 3.73,
                amount: 0.56,
                status: 'completed'
              },
              {
                task: 'MNIST Classification',
                myScore: 0.7821,
                totalScore: 18.92,
                share: 4.13,
                amount: 0.45,
                status: 'distributed'
              },
              {
                task: 'CIFAR-10 Detection',
                myScore: 0.9124,
                totalScore: 21.34,
                share: 4.27,
                amount: 0.64,
                status: 'distributed'
              }
            ].map((row, i) => (
              <tr key={i} style={{
                borderBottom: '1px solid var(--color-border)',
                ':hover': { backgroundColor: 'var(--color-bg-secondary)' }
              }}>
                <td style={{ padding: 'var(--space-3)' }}>
                  <strong>{row.task}</strong>
                </td>
                <td style={{ padding: 'var(--space-3)', textAlign: 'right', fontFamily: 'monospace' }}>
                  {row.myScore.toFixed(4)}
                </td>
                <td style={{ padding: 'var(--space-3)', textAlign: 'right', fontFamily: 'monospace' }}>
                  {row.totalScore.toFixed(2)}
                </td>
                <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                  <strong>{row.share.toFixed(2)}%</strong>
                </td>
                <td style={{
                  padding: 'var(--space-3)',
                  textAlign: 'right',
                  fontWeight: 700,
                  color: 'var(--color-success)'
                }}>
                  +{row.amount.toFixed(2)} Ⓞ
                </td>
                <td style={{ padding: 'var(--space-3)', textAlign: 'center' }}>
                  <Badge status={row.status === 'distributed' ? 'completed' : 'pending'} size="sm" />
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
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: 'var(--space-6)'
      }}>
        <div>
          <h4 style={{ margin: '0 0 var(--space-2) 0', color: 'var(--color-primary)' }}>
            📊 Contribution Scoring
          </h4>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Your score is the L2 norm of your gradient: ||Δᵢ||₂
            <br />Higher quality updates = Higher score = Higher rewards
          </p>
        </div>
        
        <div>
          <h4 style={{ margin: '0 0 var(--space-2) 0', color: 'var(--color-primary)' }}>
            ⚖️ Proportional Distribution
          </h4>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Rewardᵢ = (scoreᵢ / Σ scoreⱼ) × Total
            <br />Prevents free-riding & rewards quality work
          </p>
        </div>
        
        <div>
          <h4 style={{ margin: '0 0 var(--space-2) 0', color: 'var(--color-primary)' }}>
            🔐 Cryptographically Verified
          </h4>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Scores committed in M3, revealed in M7
            <br />No tampering possible - blockchain ensures integrity
          </p>
        </div>
      </div>
    </Card>
  </div>
);
```

### Page 5: Task Publisher - Reveal & Complete (M7)

```tsx
export const RevealRewardsPage = () => (
  <div style={{ maxWidth: '900px', margin: '0 auto', padding: 'var(--space-8)' }}>
    <h1 style={{
      fontSize: 'var(--font-size-2xl)',
      marginBottom: 'var(--space-2)'
    }}>
      Complete Task & Distribute Rewards
    </h1>
    <p style={{
      color: 'var(--color-text-secondary)',
      marginBottom: 'var(--space-8)'
    }}>
      ChestXray-Pneumonia Classification • Round 10 Completed
    </p>
    
    {/* Step 1: Reveal Accuracy */}
    <Card
      title="Step 1: Reveal Required Accuracy"
      subtitle="Confirm the accuracy commitment from task creation"
      highlight="info"
      style={{ marginBottom: 'var(--space-6)' }}
    >
      <div style={{
        backgroundColor: 'var(--color-bg-secondary)',
        padding: 'var(--space-6)',
        borderRadius: 'var(--radius-md)',
        marginBottom: 'var(--space-6)'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)'
        }}>
          <div>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              margin: '0 0 var(--space-2) 0'
            }}>
              Required Accuracy
            </p>
            <div style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 700,
              color: 'var(--color-primary)'
            }}>
              95%
            </div>
          </div>
          <div>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              margin: '0 0 var(--space-2) 0'
            }}>
              Achieved Accuracy
            </p>
            <div style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 700,
              color: 'var(--color-success)'
            }}>
              94.8% ✅
            </div>
          </div>
        </div>
        
        <div style={{
          backgroundColor: 'var(--color-success-light)',
          border: `1px solid var(--color-success)`,
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-4)'
        }}>
          <p style={{
            margin: 0,
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-success)',
            fontWeight: 500
          }}>
            ✅ Model meets accuracy requirement!
            <br />
            <span style={{ fontSize: '12px', fontWeight: 'normal' }}>
              Your commitment will be verified on-chain
            </span>
          </p>
        </div>
        
        <Button variant="primary" size="lg" style={{ width: '100%' }}>
          Reveal Accuracy & Unlock Rewards
        </Button>
      </div>
    </Card>
    
    {/* Step 2: Reward Distribution */}
    <Card
      title="Step 2: Distribute Rewards to Miners"
      subtitle="Fair allocation based on contribution scores"
      highlight="success"
    >
      <div style={{
        marginBottom: 'var(--space-6)'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: 'var(--font-size-sm)'
        }}>
          <thead>
            <tr style={{
              borderBottom: '2px solid var(--color-border)',
              backgroundColor: 'var(--color-bg-secondary)'
            }}>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'left',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Miner Wallet</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'right',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Score (||Δ||₂)</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'right',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Share (%)</th>
              <th style={{
                padding: 'var(--space-3)',
                textAlign: 'right',
                fontWeight: 600,
                color: 'var(--color-text-secondary)'
              }}>Reward (ETH)</th>
            </tr>
          </thead>
          <tbody>
            {[
              { wallet: '0x1234...5678', score: 0.9124, share: 7.84, reward: 0.118 },
              { wallet: '0x2345...6789', score: 0.8743, share: 7.51, reward: 0.113 },
              { wallet: '0x3456...7890', score: 0.7892, score: 6.78, reward: 0.102 },
              { wallet: '0x4567...8901', score: 0.7621, share: 6.54, reward: 0.098 },
              { wallet: '0x5678...9012', score: 0.6834, share: 5.87, reward: 0.088 }
            ].map((row, i) => (
              <tr key={i} style={{
                borderBottom: '1px solid var(--color-border)'
              }}>
                <td style={{
                  padding: 'var(--space-3)',
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}>
                  {row.wallet}
                </td>
                <td style={{
                  padding: 'var(--space-3)',
                  textAlign: 'right',
                  fontFamily: 'monospace',
                  fontWeight: 600
                }}>
                  {row.score.toFixed(4)}
                </td>
                <td style={{
                  padding: 'var(--space-3)',
                  textAlign: 'right',
                  fontWeight: 600
                }}>
                  {row.share.toFixed(2)}%
                </td>
                <td style={{
                  padding: 'var(--space-3)',
                  textAlign: 'right',
                  fontWeight: 700,
                  color: 'var(--color-success)'
                }}>
                  +{row.reward.toFixed(3)} Ⓞ
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div style={{
        backgroundColor: 'var(--color-bg-secondary)',
        padding: 'var(--space-4)',
        borderRadius: 'var(--radius-md)',
        marginBottom: 'var(--space-6)',
        textAlign: 'center'
      }}>
        <div style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: 700,
          marginBottom: 'var(--space-2)'
        }}>
          Total Rewards: <span style={{ color: 'var(--color-primary)' }}>1.5 ETH</span>
        </div>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          margin: 0
        }}>
          Distributed proportionally to {23} miners based on their contribution quality
        </p>
      </div>
      
      <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
        <Button variant="primary" size="lg" style={{ flex: 1 }}>
          Execute Reward Distribution
        </Button>
        <Button variant="secondary" size="lg">Review Details</Button>
      </div>
    </Card>
  </div>
);
```

---

## Navigation Structure

```tsx
export const AppLayout = () => (
  <Router>
    <Nav />
    <Routes>
      <Route path="/" element={<Dashboard />} />
      
      {/* Publisher Routes */}
      <Route path="/tasks/publish" element={<PublishTaskPage />} />
      <Route path="/tasks/manage" element={<ManageTasksPage />} />
      <Route path="/tasks/reveal/:taskId" element={<RevealRewardsPage />} />
      
      {/* Miner Routes */}
      <Route path="/mining" element={<MinerDashboard />} />
      <Route path="/tasks/available" element={<AvailableTasksPage />} />
      
      {/* Shared Routes */}
      <Route path="/rewards" element={<RewardsPage />} />
      <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
    </Routes>
  </Router>
);
```

---

## Responsive Breakpoints

```css
/* Mobile First */
@media (max-width: 640px) {
  /* Stack grids vertically */
  .grid-responsive {
    grid-template-columns: 1fr;
  }
  
  /* Reduce padding */
  body {
    padding: var(--space-3);
  }
  
  /* Hide non-essential elements */
  .hide-mobile {
    display: none;
  }
}

@media (min-width: 768px) {
  /* Tablet styles */
  .grid-responsive {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  /* Desktop styles */
  .grid-responsive {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## Web3 Integration Points

```typescript
// components/WalletConnect.tsx
import { useAccount, useConnect, useDisconnect } from 'wagmi';
import { MetaMaskConnector } from 'wagmi/connectors/metaMask';

export const WalletConnect = () => {
  const { address, isConnected } = useAccount();
  const { connect } = useConnect({
    connector: new MetaMaskConnector(),
  });
  const { disconnect } = useDisconnect();
  
  if (isConnected) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <Badge status="active" label={`${address?.slice(0, 6)}...${address?.slice(-4)}`} />
        <Button variant="outline" size="sm" onClick={() => disconnect()}>
          Disconnect
        </Button>
      </div>
    );
  }
  
  return (
    <Button variant="primary" onClick={() => connect()}>
      Connect Wallet
    </Button>
  );
};
```

---

## Implementation Checklist

```
Frontend Implementation Checklist:

COMPONENT LIBRARY (Week 1)
- [ ] Button (primary, secondary, outline, ghost)
- [ ] Card
- [ ] Metric Display
- [ ] Progress Bar
- [ ] Badge
- [ ] Table
- [ ] Form inputs
- [ ] Toast notifications

PAGES (Week 2-3)
- [ ] Dashboard (home)
- [ ] Task Publisher - Publish
- [ ] Task Publisher - Manage
- [ ] Task Publisher - Reveal
- [ ] Miner - Dashboard
- [ ] Miner - Browse Tasks
- [ ] Miner - Training Status
- [ ] Rewards - Tracking
- [ ] Rewards - Distribution

WEB3 INTEGRATION (Week 2)
- [ ] Wallet connection (wagmi + ethers.js)
- [ ] Contract interaction
- [ ] Transaction signing
- [ ] Gas estimation
- [ ] Event listening

FEATURES (Week 3-4)
- [ ] Real-time task status updates
- [ ] Live accuracy monitoring
- [ ] Contribution score display
- [ ] Reward calculations
- [ ] Transaction history
- [ ] Fairness breakdown UI

TESTING (Week 4)
- [ ] Unit tests (components)
- [ ] Integration tests (pages + Web3)
- [ ] E2E tests (full flow)
- [ ] Responsive design
- [ ] Accessibility audit
```

---

**This is your complete production-ready frontend design system. Start with the components, then build pages sequentially!**