// migrations/deploy.js
// ESM-compatible deployment script for TaskContract and EscrowContract
import hardhat from 'hardhat';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const { ethers } = hardhat;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with the account:', deployer.address);

  // 1. Deploy TaskContract first
  const TaskContractFactory = await ethers.getContractFactory('TaskContract');
  const taskContract = await TaskContractFactory.deploy();
  if (typeof taskContract.waitForDeployment === 'function') {
    await taskContract.waitForDeployment();
  }

  const taskContractAddress = (typeof taskContract.getAddress === 'function')
    ? await taskContract.getAddress()
    : taskContract.address;
  console.log('TaskContract deployed to:', taskContractAddress);

  // 2. Deploy EscrowContract, passing the TaskContract address
  const EscrowContractFactory = await ethers.getContractFactory('EscrowContract');
  const escrowContract = await EscrowContractFactory.deploy(taskContractAddress);
  if (typeof escrowContract.waitForDeployment === 'function') {
    await escrowContract.waitForDeployment();
  }

  const escrowContractAddress = (typeof escrowContract.getAddress === 'function')
    ? await escrowContract.getAddress()
    : escrowContract.address;
  console.log('EscrowContract deployed to:', escrowContractAddress);

  // 3. Set the Escrow Contract address in the TaskContract (required for access control)
  console.log('Setting EscrowContract address in TaskContract...');
  const setEscrowTx = await taskContract.setEscrowContract(escrowContractAddress);
  await setEscrowTx.wait();
  console.log('EscrowContract address set successfully');

  // 4. Save addresses to config file (optional - for Python integration)
  // Migrations live in blockchain/contracts/migrations, but deployment config lives in blockchain/deployment
  const configPath = path.join(__dirname, '..', '..', 'deployment', 'contract_config.json');
  try {
    // ensure deployment directory exists
    const deploymentDir = path.dirname(configPath);
    if (!fs.existsSync(deploymentDir)) {
      fs.mkdirSync(deploymentDir, { recursive: true });
    }

    let config = {};
    try {
      config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } catch (e) {
      // file may not exist yet; start with empty config
      config = {};
    }

    if (!config.TaskContract) config.TaskContract = {};
    if (!config.EscrowContract) config.EscrowContract = {};
    config.TaskContract.address = taskContractAddress;
    config.EscrowContract.address = escrowContractAddress;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    console.log('Config file updated:', configPath);
  } catch (error) {
    console.warn('Could not update config file:', error.message);
  }

  console.log('\n=== Deployment Summary ===');
  console.log('TaskContract:', taskContractAddress);
  console.log('EscrowContract:', escrowContractAddress);
  console.log('========================\n');

  return { taskContractAddress, escrowContractAddress };
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

// To run this: npx hardhat run blockchain/contracts/migrations/deploy.js