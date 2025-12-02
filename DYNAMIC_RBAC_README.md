# Dynamic Role-Based Access Control (RBAC) System

This document describes the Dynamic RBAC system implementation for the HealChain project, where privileges are resource-specific. Any user can be a "Task Publisher," but only the specific address that published a task has write privileges for that specific task ID.

## 📁 Files Created

### 1. Smart Contract: `TaskManager.sol`
**Location:** `HealChain/blockchain/contracts/TaskManager.sol`

**Features:**
- `publishTask(string memory dataHash)` - Publishes a new task and returns a unique taskId
- `updateTask(uint256 taskId, string memory newDataHash)` - Updates a task (only by original publisher)
- `onlyTaskPublisher(uint256 taskId)` - Access control modifier
- Ownership mapping: `mapping(uint256 => address) public taskPublisher`
- Follows Checks-Effects-Interactions pattern for security

**Events:**
- `TaskPublished(uint256 indexed taskId, address indexed publisher, string dataHash)`
- `TaskUpdated(uint256 indexed taskId, address indexed publisher, string newDataHash)`

### 2. React Frontend: `PublisherDashboard.js`
**Location:** `HealChain/frontend/components/PublisherDashboard.js`

**Features:**
- MetaMask integration using ethers.js v6
- Connect wallet functionality
- Publish task form with data hash input
- Real-time transaction status and error handling
- Account change detection

**Usage:**
```jsx
import PublisherDashboard from './components/PublisherDashboard';
import TaskManagerABI from '../artifacts/blockchain/contracts/TaskManager.sol/TaskManager.json';

function App() {
  return (
    <PublisherDashboard 
      contractAddress="0x..." 
      contractABI={TaskManagerABI.abi} 
    />
  );
}
```

### 3. Python Event Listener: `listener.py`
**Location:** `HealChain/integration/listener.py`

**Features:**
- Infinite loop listener for `TaskPublished` events
- Extracts `taskId`, `publisher`, and `dataHash` from event logs
- Integration point for triggering HealChain algorithms
- Automatic config file loading
- Error handling and retry logic

## 🚀 Setup Instructions

### 1. Deploy the Smart Contract

```bash
# Compile the contract
cd HealChain
npx hardhat compile

# Deploy to local network (Ganache/Hardhat)
npx hardhat run blockchain/contracts/migrations/deploy_taskmanager.js --network ganache
```

The deployment script will automatically update `blockchain/deployment/contract_config.json` with the contract address.

### 2. Set Up React Frontend

**Prerequisites:**
- Node.js and npm installed
- React project initialized
- MetaMask browser extension

**Install Dependencies:**
```bash
npm install ethers@^6.15.0
```

**Integration Steps:**
1. Copy `PublisherDashboard.js` to your React components directory
2. Import the contract ABI from the artifacts folder:
   ```javascript
   import TaskManagerABI from '../artifacts/blockchain/contracts/TaskManager.sol/TaskManager.json';
   ```
3. Use the component in your app:
   ```jsx
   <PublisherDashboard 
     contractAddress="0x..." // From deployment
     contractABI={TaskManagerABI.abi}
   />
   ```

### 3. Run the Python Event Listener

**Prerequisites:**
- Python 3.7+
- Local Ganache node running at `http://127.0.0.1:7545`
- TaskManager contract deployed

**Run the Listener:**
```bash
cd HealChain
python integration/listener.py
```

The listener will:
- Connect to the blockchain
- Load contract address and ABI from config
- Start monitoring for `TaskPublished` events
- Display event details when detected
- Provide integration point for HealChain algorithms

## 🔧 Configuration

### Contract Configuration
The contract address and ABI path are stored in:
```
HealChain/blockchain/deployment/contract_config.json
```

Example structure:
```json
{
  "TaskManager": {
    "address": "0x...",
    "abiFile": "../../artifacts/blockchain/contracts/TaskManager.sol/TaskManager.json"
  },
  "network": {
    "rpcUrl": "http://127.0.0.1:7545",
    "chainId": 5777
  }
}
```

### Python Listener Configuration
Edit `listener.py` to customize:
- `RPC_URL`: Blockchain RPC endpoint (default: `http://127.0.0.1:7545`)
- `poll_interval`: Seconds between block polling (default: 2)
- `from_block`: Starting block number (default: `'latest'`)

## 🔐 Security Features

1. **Access Control**: Only the original publisher can update their task
2. **Checks-Effects-Interactions**: Contract follows CEI pattern to prevent reentrancy
3. **Input Validation**: Data hash length validation
4. **Event Logging**: All state changes are logged as events

## 📝 Integration with HealChain Backend

The Python listener includes a clearly marked integration point where you can trigger your existing HealChain algorithms:

```python
# In listener.py, _process_event method:

# ============================================================
# INTEGRATION POINT: Trigger External HealChain Algorithms
# ============================================================
# 
# from federated_layer.task_publisher.publisher import process_task
# from federated_layer.aggregator.aggregator import start_aggregation
# 
# process_task(
#     task_id=task_id,
#     publisher_address=publisher,
#     data_hash=data_hash,
#     block_number=block_number
# )
```

## 🧪 Testing

### Test the Smart Contract
```bash
# Run Hardhat tests
npx hardhat test
```

### Test the Frontend
1. Start your React development server
2. Connect MetaMask to your local network (Ganache)
3. Import a test account from Ganache into MetaMask
4. Use the dashboard to publish a task

### Test the Event Listener
1. Start Ganache
2. Deploy the contract
3. Run the listener: `python integration/listener.py`
4. Publish a task from the frontend
5. Verify the event is detected and logged

## 📚 API Reference

### Smart Contract Functions

#### `publishTask(string memory dataHash) → uint256`
Publishes a new task and returns the assigned taskId.

**Parameters:**
- `dataHash`: Hash of the task data (string, max 256 bytes)

**Returns:**
- `taskId`: Unique identifier for the published task

**Events:**
- Emits `TaskPublished(taskId, msg.sender, dataHash)`

#### `updateTask(uint256 taskId, string memory newDataHash)`
Updates an existing task's data hash. Only callable by the original publisher.

**Parameters:**
- `taskId`: The task ID to update
- `newDataHash`: New data hash for the task

**Modifiers:**
- `onlyTaskPublisher(taskId)`: Ensures only the original publisher can update

**Events:**
- Emits `TaskUpdated(taskId, msg.sender, newDataHash)`

#### `getTaskInfo(uint256 taskId) → (address publisher, string dataHash)`
View function to get task information.

**Returns:**
- `publisher`: Address that published the task
- `dataHash`: Data hash associated with the task

## 🐛 Troubleshooting

### Frontend Issues
- **MetaMask not connecting**: Ensure MetaMask is installed and unlocked
- **Transaction fails**: Check network connection and account balance
- **Contract not found**: Verify contract address and ABI are correct

### Python Listener Issues
- **Connection failed**: Ensure Ganache is running at the configured RPC URL
- **Contract not found**: Verify contract address in config file
- **ABI file not found**: Run `npx hardhat compile` to generate artifacts

### Contract Deployment Issues
- **Insufficient funds**: Ensure deployer account has enough ETH
- **Network mismatch**: Verify network configuration in `hardhat.config.js`

## 📄 License

MIT License - See project root for details.

