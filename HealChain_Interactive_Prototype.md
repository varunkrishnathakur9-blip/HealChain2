# HealChain Frontend - Interactive Prototype (Copy-Paste Ready)

## Complete Single-File Prototype

Save this as `index.html` and open in your browser to see the full UI:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HealChain - Privacy-Preserving Federated Learning</title>
    <style>
        :root {
            --color-primary: #0066cc;
            --color-primary-dark: #0052a3;
            --color-primary-light: #e6f0ff;
            --color-success: #22c55e;
            --color-success-light: #dcfce7;
            --color-warning: #f59e0b;
            --color-warning-light: #fef3c7;
            --color-error: #ef4444;
            --color-error-light: #fee2e2;
            --color-bg-primary: #ffffff;
            --color-bg-secondary: #f9fafb;
            --color-bg-tertiary: #f3f4f6;
            --color-text-primary: #1f2937;
            --color-text-secondary: #6b7280;
            --color-text-tertiary: #9ca3af;
            --color-border: #e5e7eb;
            --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-size-sm: 14px;
            --font-size-base: 16px;
            --font-size-lg: 18px;
            --font-size-xl: 20px;
            --font-size-2xl: 24px;
            --font-size-3xl: 32px;
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --space-6: 24px;
            --space-8: 32px;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
            --radius-md: 8px;
            --radius-lg: 12px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--font-family-base);
            background-color: var(--color-bg-secondary);
            color: var(--color-text-primary);
            line-height: 1.6;
        }

        /* Navigation */
        nav {
            background-color: var(--color-bg-primary);
            border-bottom: 1px solid var(--color-border);
            padding: var(--space-4) var(--space-6);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .nav-brand {
            font-size: var(--font-size-2xl);
            font-weight: 700;
            color: var(--color-primary);
        }

        .nav-links {
            display: flex;
            gap: var(--space-6);
            align-items: center;
        }

        .nav-links a {
            color: var(--color-text-secondary);
            text-decoration: none;
            font-size: var(--font-size-sm);
            transition: color 200ms;
        }

        .nav-links a:hover {
            color: var(--color-primary);
        }

        /* Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: var(--space-8);
        }

        /* Hero Section */
        .hero {
            background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-bg-secondary) 100%);
            border-radius: var(--radius-lg);
            padding: var(--space-8);
            margin-bottom: var(--space-8);
            text-align: center;
        }

        .hero h1 {
            font-size: var(--font-size-3xl);
            color: var(--color-primary);
            margin-bottom: var(--space-3);
        }

        .hero p {
            font-size: var(--font-size-lg);
            color: var(--color-text-secondary);
            margin-bottom: var(--space-6);
        }

        .hero-buttons {
            display: flex;
            gap: var(--space-4);
            justify-content: center;
            flex-wrap: wrap;
        }

        /* Buttons */
        button {
            font-family: var(--font-family-base);
            font-size: var(--font-size-base);
            font-weight: 500;
            padding: var(--space-3) var(--space-4);
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: all 200ms ease;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: var(--space-2);
        }

        .btn-primary {
            background-color: var(--color-primary);
            color: white;
            border: 1px solid var(--color-primary);
        }

        .btn-primary:hover {
            background-color: var(--color-primary-dark);
        }

        .btn-secondary {
            background-color: var(--color-bg-secondary);
            color: var(--color-text-primary);
            border: 1px solid var(--color-border);
        }

        .btn-secondary:hover {
            background-color: var(--color-bg-tertiary);
        }

        .btn-outline {
            background-color: transparent;
            color: var(--color-primary);
            border: 2px solid var(--color-primary);
        }

        .btn-outline:hover {
            background-color: var(--color-primary-light);
        }

        /* Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: var(--space-6);
            margin-bottom: var(--space-8);
        }

        /* Cards */
        .card {
            background-color: var(--color-bg-primary);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            box-shadow: var(--shadow-md);
            transition: all 200ms;
        }

        .card:hover {
            box-shadow: var(--shadow-lg);
        }

        .card.highlight-success {
            border-left: 4px solid var(--color-success);
        }

        .card.highlight-info {
            border-left: 4px solid var(--color-primary);
        }

        .card.highlight-warning {
            border-left: 4px solid var(--color-warning);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-3);
        }

        .card-title {
            font-size: var(--font-size-lg);
            font-weight: 600;
            color: var(--color-text-primary);
        }

        .card-subtitle {
            font-size: var(--font-size-sm);
            color: var(--color-text-secondary);
            margin-top: var(--space-2);
        }

        /* Metrics */
        .metric {
            display: flex;
            align-items: center;
            gap: var(--space-4);
            padding: var(--space-4);
            background-color: var(--color-bg-secondary);
            border-radius: var(--radius-md);
        }

        .metric-icon {
            font-size: 24px;
            opacity: 0.7;
        }

        .metric-value {
            font-size: var(--font-size-2xl);
            font-weight: 700;
            color: var(--color-text-primary);
        }

        .metric-label {
            font-size: var(--font-size-sm);
            color: var(--color-text-secondary);
        }

        .metric-change {
            font-size: var(--font-size-sm);
            font-weight: 500;
            margin-left: var(--space-2);
        }

        .metric-change.up {
            color: var(--color-success);
        }

        .metric-change.down {
            color: var(--color-error);
        }

        /* Progress Bar */
        .progress {
            margin-bottom: var(--space-3);
        }

        .progress-label {
            display: flex;
            justify-content: space-between;
            font-size: var(--font-size-sm);
            margin-bottom: var(--space-2);
        }

        .progress-bar {
            height: 8px;
            background-color: var(--color-border);
            border-radius: 99px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background-color: var(--color-primary);
            transition: width 300ms ease;
        }

        .progress-fill.success {
            background-color: var(--color-success);
        }

        /* Badge */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: var(--space-1);
            padding: var(--space-2) var(--space-3);
            border-radius: 99px;
            font-size: var(--font-size-sm);
            font-weight: 500;
        }

        .badge.active {
            background-color: var(--color-success-light);
            color: var(--color-success);
        }

        .badge.pending {
            background-color: var(--color-warning-light);
            color: var(--color-warning);
        }

        .badge.completed {
            background-color: var(--color-success-light);
            color: var(--color-success);
        }

        /* Table */
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: var(--font-size-sm);
        }

        th {
            padding: var(--space-3);
            text-align: left;
            font-weight: 600;
            color: var(--color-text-secondary);
            background-color: var(--color-bg-secondary);
            border-bottom: 2px solid var(--color-border);
        }

        td {
            padding: var(--space-3);
            border-bottom: 1px solid var(--color-border);
        }

        tr:hover {
            background-color: var(--color-bg-secondary);
        }

        /* Form */
        input, select, textarea {
            width: 100%;
            padding: var(--space-3);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            font-family: var(--font-family-base);
            font-size: var(--font-size-base);
            margin-bottom: var(--space-4);
        }

        label {
            display: block;
            margin-bottom: var(--space-2);
            font-weight: 500;
            color: var(--color-text-primary);
        }

        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 2px solid var(--color-border);
            margin-bottom: var(--space-6);
        }

        .tab {
            padding: var(--space-3) var(--space-4);
            cursor: pointer;
            background: none;
            border: none;
            font-size: var(--font-size-base);
            color: var(--color-text-secondary);
            border-bottom: 3px solid transparent;
            transition: all 200ms;
        }

        .tab.active {
            color: var(--color-primary);
            border-bottom-color: var(--color-primary);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: var(--space-4);
            }

            .grid {
                grid-template-columns: 1fr;
            }

            .nav-links {
                flex-wrap: wrap;
                gap: var(--space-2);
            }

            .hero h1 {
                font-size: var(--font-size-2xl);
            }

            .hero-buttons {
                flex-direction: column;
            }

            button {
                width: 100%;
            }
        }

        /* Page Content */
        .page {
            display: none;
        }

        .page.active {
            display: block;
        }

        .section-title {
            font-size: var(--font-size-2xl);
            font-weight: 700;
            margin-bottom: var(--space-2);
        }

        .section-subtitle {
            color: var(--color-text-secondary);
            margin-bottom: var(--space-8);
        }

        /* Alert */
        .alert {
            padding: var(--space-4);
            border-radius: var(--radius-md);
            margin-bottom: var(--space-4);
            border-left: 4px solid;
        }

        .alert.info {
            background-color: var(--color-primary-light);
            border-left-color: var(--color-primary);
            color: var(--color-primary);
        }

        .alert.success {
            background-color: var(--color-success-light);
            border-left-color: var(--color-success);
            color: var(--color-success);
        }

        .alert p {
            margin: 0;
            font-size: var(--font-size-sm);
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: white;
            padding: var(--space-8);
            border-radius: var(--radius-lg);
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav>
        <div class="nav-brand">⛓️ HealChain</div>
        <div class="nav-links">
            <a href="#" onclick="showPage('dashboard')">Dashboard</a>
            <a href="#" onclick="showPage('publish')">Publish Task</a>
            <a href="#" onclick="showPage('mining')">Mining</a>
            <a href="#" onclick="showPage('rewards')">Rewards</a>
            <button class="btn-primary" onclick="connectWallet()">Connect Wallet</button>
        </div>
    </nav>

    <!-- Dashboard Page -->
    <div id="dashboard" class="page active">
        <div class="container">
            <!-- Hero -->
            <div class="hero">
                <h1>Privacy-Preserving Federated Learning</h1>
                <p>Collaborate on machine learning without sharing data. Fair rewards through blockchain.</p>
                <div class="hero-buttons">
                    <button class="btn-primary" onclick="showPage('publish')">Publish Task</button>
                    <button class="btn-outline" onclick="showPage('mining')">Become a Miner</button>
                </div>
            </div>

            <!-- Metrics -->
            <div class="grid">
                <div class="card">
                    <div class="metric">
                        <div class="metric-icon">📋</div>
                        <div>
                            <div class="metric-label">Active Tasks</div>
                            <div class="metric-value">12</div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="metric">
                        <div class="metric-icon">⛏️</div>
                        <div>
                            <div class="metric-label">Registered Miners</div>
                            <div class="metric-value">147</div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="metric">
                        <div class="metric-icon">💰</div>
                        <div>
                            <div class="metric-label">Total Rewards Distributed</div>
                            <div class="metric-value">24.5 ETH</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Tasks -->
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">Recent Tasks</div>
                        <div class="card-subtitle">Latest federated learning tasks on the network</div>
                    </div>
                    <button class="btn-outline">View All →</button>
                </div>

                <div class="grid">
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-3);">
                            <span style="font-weight: 600;">ChestXray-Pneumonia</span>
                            <span class="badge active">🟢 Active</span>
                        </div>
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-3);">
                            Train classification model on medical images
                        </p>
                        <div style="display: flex; justify-content: space-between; font-size: var(--font-size-sm); margin-bottom: var(--space-3);">
                            <span>Reward: <strong>1.5 ETH</strong></span>
                            <span>Miners: <strong>23/30</strong></span>
                        </div>
                        <div class="progress">
                            <div class="progress-label">
                                <span>Accuracy Goal</span>
                                <span>76%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 76%"></div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-3);">
                            <span style="font-weight: 600;">MNIST Classification</span>
                            <span class="badge pending">🟡 Training</span>
                        </div>
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-3);">
                            Digit recognition on handwritten digits
                        </p>
                        <div style="display: flex; justify-content: space-between; font-size: var(--font-size-sm); margin-bottom: var(--space-3);">
                            <span>Reward: <strong>1.0 ETH</strong></span>
                            <span>Miners: <strong>18/25</strong></span>
                        </div>
                        <div class="progress">
                            <div class="progress-label">
                                <span>Accuracy Goal</span>
                                <span>92%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 92%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Publish Task Page -->
    <div id="publish" class="page">
        <div class="container" style="max-width: 900px;">
            <div class="section-title">Publish New FL Task</div>
            <div class="card">
                <form style="display: flex; flex-direction: column; gap: var(--space-6);">
                    <div>
                        <label>Task Name</label>
                        <input type="text" placeholder="e.g., ChestXray Pneumonia Detection">
                    </div>

                    <div>
                        <label>Dataset Type</label>
                        <select>
                            <option>ChestXray-Pneumonia</option>
                            <option>MNIST</option>
                            <option>CIFAR-10</option>
                        </select>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
                        <div>
                            <label>Required Accuracy (%)</label>
                            <input type="number" value="95" min="0" max="100">
                        </div>
                        <div>
                            <label>Total Reward (ETH)</label>
                            <input type="number" value="1.5" min="0.1" step="0.1">
                        </div>
                    </div>

                    <div>
                        <label>Task Description</label>
                        <textarea placeholder="Describe the learning objective..."></textarea>
                    </div>

                    <div class="alert info">
                        <p><strong>🔒 Security Note:</strong> Your commitment will be saved securely. You'll need it to reveal rewards later.</p>
                    </div>

                    <div style="display: flex; gap: var(--space-4);">
                        <button type="submit" class="btn-primary" style="flex: 1;">Publish Task & Lock Reward</button>
                        <button type="button" class="btn-secondary">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Mining Page -->
    <div id="mining" class="page">
        <div class="container">
            <div class="section-title">Mining Dashboard</div>
            <div class="section-subtitle">Your federated learning participation and earnings</div>

            <div class="grid">
                <div class="card">
                    <div class="metric">
                        <div class="metric-icon">⛏️</div>
                        <div>
                            <div class="metric-label">Active Tasks</div>
                            <div class="metric-value">3</div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="metric">
                        <div class="metric-icon">📊</div>
                        <div>
                            <div class="metric-label">Your Score (||Δᵢ||₂)</div>
                            <div style="display: flex; align-items: baseline; gap: var(--space-2);">
                                <div class="metric-value" style="font-size: var(--font-size-xl);">0.8743</div>
                                <span class="metric-change up">↑ 12%</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="metric">
                        <div class="metric-icon">💰</div>
                        <div>
                            <div class="metric-label">Total Earned</div>
                            <div class="metric-value">3.24 ETH</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card highlight-success">
                <div class="card-header">
                    <div>
                        <div class="card-title">Currently Training</div>
                        <div class="card-subtitle">Active federated learning task</div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-6); margin-bottom: var(--space-6);">
                    <div>
                        <h3 style="margin: 0 0 var(--space-2) 0;">ChestXray-Pneumonia</h3>
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-4);">
                            Classification model for pneumonia detection
                        </p>
                        <div class="alert success">
                            <p><strong>Your Contribution Score: 0.8743</strong></p>
                            <div class="progress" style="margin-top: var(--space-2);">
                                <div class="progress-label">
                                    <span>Percentile</span>
                                    <span>87%</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill success" style="width: 87%"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div style="margin-bottom: var(--space-6);">
                            <span style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Round</span>
                            <div style="font-size: var(--font-size-2xl); font-weight: 700;">Round 5/10</div>
                        </div>
                        <div style="margin-bottom: var(--space-6);">
                            <span style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Model Accuracy</span>
                            <div style="font-size: var(--font-size-2xl); font-weight: 700;">94.8%</div>
                            <span style="font-size: var(--font-size-sm); color: var(--color-success);">↑ Target: 95%</span>
                        </div>
                        <span class="badge active">🟢 Training in Progress</span>
                    </div>
                </div>

                <div style="background-color: var(--color-bg-secondary); padding: var(--space-4); border-radius: var(--radius-md);">
                    <p style="font-size: var(--font-size-sm); font-weight: 500; margin: 0 0 var(--space-3) 0;">Training Progress</p>
                    <div class="progress">
                        <div class="progress-label">
                            <span>Epoch 5/10</span>
                            <span>50%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 50%"></div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-3); margin-top: var(--space-4);">
                        <div>
                            <div style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Local Loss</div>
                            <div style="font-size: var(--font-size-lg); font-weight: 700;">0.245</div>
                        </div>
                        <div>
                            <div style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Local Accuracy</div>
                            <div style="font-size: var(--font-size-lg); font-weight: 700;">93.2%</div>
                        </div>
                        <div>
                            <div style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Gradient Norm</div>
                            <div style="font-size: var(--font-size-lg); font-weight: 700;">0.87</div>
                        </div>
                        <div>
                            <div style="font-size: var(--font-size-sm); color: var(--color-text-secondary);">Status</div>
                            <div style="font-size: var(--font-size-lg); font-weight: 700; color: var(--color-success);">✅ Valid</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Rewards Page -->
    <div id="rewards" class="page">
        <div class="container">
            <div class="section-title">Rewards & Earnings</div>

            <div class="grid">
                <div class="card highlight-success">
                    <div style="text-align: center;">
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin: 0 0 var(--space-2) 0;">Total Earned</p>
                        <div style="font-size: var(--font-size-3xl); font-weight: 700; color: var(--color-success); margin: 0 0 var(--space-2) 0;">3.24 Ⓞ</div>
                        <p style="font-size: var(--font-size-sm); color: var(--color-success); margin: 0;">↑ +0.45 ETH this week</p>
                    </div>
                </div>
                <div class="card highlight-info">
                    <div style="text-align: center;">
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin: 0 0 var(--space-2) 0;">Pending Rewards</p>
                        <div style="font-size: var(--font-size-3xl); font-weight: 700; color: var(--color-primary); margin: 0 0 var(--space-2) 0;">0.82 Ⓞ</div>
                        <span class="badge pending">🟡 Reveal Pending</span>
                    </div>
                </div>
                <div class="card highlight-warning">
                    <div style="text-align: center;">
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin: 0 0 var(--space-2) 0;">Fair Share Score</p>
                        <div style="font-size: var(--font-size-3xl); font-weight: 700; color: var(--color-warning); margin: 0 0 var(--space-2) 0;">87%</div>
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin: 0;">Avg: 78%</p>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">Recent Reward Distributions</div>
                        <div class="card-subtitle">Fairness-based reward allocation from completed tasks</div>
                    </div>
                </div>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Your Score (||Δ||₂)</th>
                                <th>Total Score</th>
                                <th>Share (%)</th>
                                <th>Amount (ETH)</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>ChestXray-Pneumonia</strong></td>
                                <td>0.8743</td>
                                <td>23.45</td>
                                <td><strong>3.73%</strong></td>
                                <td style="color: var(--color-success); font-weight: 700;">+0.56 Ⓞ</td>
                                <td><span class="badge completed">✅ Completed</span></td>
                            </tr>
                            <tr>
                                <td><strong>MNIST Classification</strong></td>
                                <td>0.7821</td>
                                <td>18.92</td>
                                <td><strong>4.13%</strong></td>
                                <td style="color: var(--color-success); font-weight: 700;">+0.45 Ⓞ</td>
                                <td><span class="badge completed">✅ Completed</span></td>
                            </tr>
                            <tr>
                                <td><strong>CIFAR-10 Detection</strong></td>
                                <td>0.9124</td>
                                <td>21.34</td>
                                <td><strong>4.27%</strong></td>
                                <td style="color: var(--color-success); font-weight: 700;">+0.64 Ⓞ</td>
                                <td><span class="badge completed">✅ Completed</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-title">How Fairness Works</div>
                <div class="card-subtitle" style="margin-bottom: var(--space-6);">Reward allocation mechanism</div>
                <div class="grid">
                    <div>
                        <h4 style="margin: 0 0 var(--space-2) 0; color: var(--color-primary);">📊 Contribution Scoring</h4>
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin: 0;">
                            Your score is the L2 norm of your gradient: ||Δᵢ||₂<br>
                            Higher quality updates = Higher reward
                        </p>
                    </div>
                    <div>
                        <h4 style="margin: 0 0 var(--space-2) 0; color: var(--color-primary);">⚖️ Proportional Distribution</h4>
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin: 0;">
                            Rewardᵢ = (scoreᵢ / Σ scoreⱼ) × Total<br>
                            Prevents free-riding & rewards quality
                        </p>
                    </div>
                    <div>
                        <h4 style="margin: 0 0 var(--space-2) 0; color: var(--color-primary);">🔐 Cryptographically Verified</h4>
                        <p style="font-size: var(--font-size-sm); color: var(--color-text-secondary); margin: 0;">
                            Scores committed in M3, revealed in M7<br>
                            No tampering possible - blockchain ensures integrity
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function showPage(pageId) {
            // Hide all pages
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            // Show selected page
            document.getElementById(pageId).classList.add('active');
            // Scroll to top
            window.scrollTo(0, 0);
        }

        function connectWallet() {
            alert('In production, this would connect to MetaMask or WalletConnect');
        }
    </script>
</body>
</html>
```

---

## How to Use This Prototype

1. **Save the code above** as `healchain-ui.html`
2. **Open in browser** - Double-click the file or drag it into any browser
3. **Click navigation links** to navigate between pages
4. **No dependencies required** - Pure HTML/CSS/JavaScript

---

## Features Included

✅ **Responsive Design** - Works on mobile, tablet, desktop
✅ **Dark/Light Mode Ready** - CSS variables for easy theming
✅ **Interactive Navigation** - Working tab system
✅ **All Key Pages**:
  - Dashboard (home)
  - Publish Task (M1)
  - Mining Dashboard (M2-M3)
  - Rewards Tracking (M7)

✅ **Components**:
  - Buttons (primary, secondary, outline)
  - Cards (with highlights)
  - Progress bars
  - Badges
  - Tables
  - Forms
  - Metrics display
  - Alerts

---

## Next Steps

1. **Copy this HTML** and open in browser to see it working
2. **Customize colors** by editing CSS variables in the `<style>` tag
3. **Add real data** by replacing hardcoded values with dynamic data
4. **Integrate Web3** by adding ethers.js/wagmi connections
5. **Convert to React** by breaking into components (mentioned in first document)

This is your **production-ready starting point** for the entire frontend! 🚀