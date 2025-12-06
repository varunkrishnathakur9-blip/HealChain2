# HealChain Frontend

Modern React frontend for HealChain - a privacy-preserving federated learning platform with blockchain-based fair payments.

## 🎨 Features

- **Professional Design System**: Complete UI component library with consistent styling
- **Web3 Integration**: wagmi v2 + viem for seamless wallet connections
- **Responsive**: Works perfectly on mobile, tablet, and desktop
- **Four Main Pages**:
  - **Dashboard**: Network statistics and recent tasks
  - **Publish Task**: Create new federated learning tasks with escrow
  - **Mining Dashboard**: Track training progress and contribution scores
  - **Rewards**: View earnings and fairness breakdown

## 🚀 Quick Start

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## 📦 Dependencies

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **wagmi v2** - Web3 React hooks
- **viem** - TypeScript Ethereum library
- **ethers.js v6** - Ethereum utilities
- **react-router-dom** - Client-side routing

## ⚙️ Configuration

### Contract Configuration

**`public/contract-config.json`**:
```json
{
  "TaskManager": {
    "address": "0x..."
  },
  "network": {
    "rpcUrl": "http://127.0.0.1:7545",
    "chainId": 5777
  }
}
```

### Wagmi Configuration

**`src/config/wagmi.js`**:
- Configured for Ganache (port 7545, chainId 5777)
- Supports Hardhat local (port 8545, chainId 31337)
- Ready for Sepolia testnet

### Environment Variables

Create `.env` file (optional):
```
VITE_CHAIN_ID=5777
VITE_RPC_URL=http://127.0.0.1:7545
```

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── pages/           # Main application pages
│   │   ├── Dashboard.jsx
│   │   ├── PublishTask.jsx
│   │   ├── Mining.jsx
│   │   └── Rewards.jsx
│   ├── components/      # Design system components
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── Badge.jsx
│   │   ├── ProgressBar.jsx
│   │   ├── Metric.jsx
│   │   ├── Nav.jsx
│   │   └── WalletConnect.jsx
│   ├── hooks/          # Custom React hooks
│   │   └── useContract.js
│   ├── config/          # Configuration files
│   │   └── wagmi.js
│   ├── index.css        # Design tokens and global styles
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Entry point
├── public/              # Static assets
│   ├── contract-config.json
│   └── TaskManager.json
└── package.json
```

## 🎨 Design System

The frontend uses a comprehensive design system with:

- **Design Tokens**: CSS variables for colors, spacing, typography
- **Components**: Reusable UI components (Button, Card, Badge, etc.)
- **Responsive Breakpoints**: Mobile (≤640px), Tablet (641-1024px), Desktop (≥1025px)
- **Accessibility**: WCAG AA compliant with proper focus states

See `HealChain_Frontend_Design.md` for complete design documentation.

## 🔌 Web3 Integration

### Wallet Connection

The `WalletConnect` component uses wagmi hooks:
- `useAccount()` - Get connected account
- `useConnect()` - Connect wallet
- `useDisconnect()` - Disconnect wallet

### Contract Interactions

Use the custom hooks in `src/hooks/useContract.js`:

```javascript
import { useEscrowContract } from '../hooks/useContract';

function PublishTask() {
  const { publishTask, isPending } = useEscrowContract(address, abi);
  
  const handlePublish = async () => {
    await publishTask(taskID, commitHash, deadline, reward);
  };
}
```

See `WEB3_SETUP.md` for detailed Web3 setup guide.

## 📱 Responsive Design

The frontend is fully responsive:
- **Mobile**: Single column layouts, hamburger menu
- **Tablet**: 2-column grids
- **Desktop**: 3-column grids, full navigation

See `RESPONSIVE_TESTING.md` for testing checklist.

## 🧪 Testing

### Manual Testing

1. **Wallet Connection**: Test MetaMask connection
2. **Navigation**: Test all routes
3. **Forms**: Test form validation and submission
4. **Responsive**: Test on different screen sizes
5. **Web3**: Test contract interactions

### Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## 🐛 Troubleshooting

**"Module not found" errors**
- Run `npm install` to install dependencies
- Check Node.js version (v18+)

**"Wallet not connecting"**
- Ensure MetaMask is installed
- Check network configuration
- Verify chain ID matches Ganache (5777)

**"Contract not found"**
- Verify contract address in `public/contract-config.json`
- Ensure ABI file exists in `public/TaskManager.json`
- Check contract is deployed

**Port conflicts**
- Vite will use next available port if 3000 is in use
- Check terminal output for actual URL

## 📚 Additional Documentation

- **Design System**: `../HealChain_Frontend_Design.md`
- **Implementation Guide**: `../HealChain_Frontend_Implementation_Guide.md`
- **Web3 Setup**: `WEB3_SETUP.md`
- **Responsive Testing**: `RESPONSIVE_TESTING.md`

## 🚀 Deployment

### Build

```bash
npm run build
```

Outputs to `dist/` directory.

### Deploy to Vercel/Netlify

1. Connect your repository
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Deploy!

### Environment Variables

Set in deployment platform:
- `VITE_CHAIN_ID` - Chain ID for wagmi
- `VITE_RPC_URL` - RPC endpoint URL

---

**Built with React + Vite + wagmi for HealChain**

