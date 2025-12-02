// migrations/deploy_taskmanager.js
// Deployment script for TaskManager contract (ESM-compatible)
import hardhat from 'hardhat';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const { ethers } = hardhat;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying TaskManager contract with account:', deployer.address);
  console.log('Account balance:', (await ethers.provider.getBalance(deployer.address)).toString());

  // Deploy TaskManager
  const TaskManagerFactory = await ethers.getContractFactory('TaskManager');
  const taskManager = await TaskManagerFactory.deploy();
  if (typeof taskManager.waitForDeployment === 'function') {
    await taskManager.waitForDeployment();
  }

  const taskManagerAddress = (typeof taskManager.getAddress === 'function')
    ? await taskManager.getAddress()
    : taskManager.address;

  console.log('TaskManager deployed to:', taskManagerAddress);

  // Update contract_config.json
  const configPath = path.join(__dirname, '..', '..', 'deployment', 'contract_config.json');
  let config = {};
  try {
    if (fs.existsSync(configPath)) {
      config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    }
  } catch (error) {
    console.warn('Could not read existing config file, creating new one');
  }

  config.TaskManager = {
    address: taskManagerAddress,
    abiFile: '../../artifacts/blockchain/contracts/TaskManager.sol/TaskManager.json'
  };

  if (!config.network) {
    config.network = { rpcUrl: 'http://127.0.0.1:7545', chainId: 5777 };
  }

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log('Config file updated:', configPath);

  console.log('\n=== Deployment Summary ===');
  console.log('TaskManager Address:', taskManagerAddress);
  console.log('Network:', config.network.rpcUrl);
  console.log('===========================\n');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

