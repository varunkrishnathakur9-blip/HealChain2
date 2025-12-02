/* Hardhat deploy script: deploy TaskContract and EscrowContract, then update contract_config.json */
import hardhat from 'hardhat';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const { ethers } = hardhat;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);

  const TaskFactory = await ethers.getContractFactory('TaskContract');
  const Task = await TaskFactory.deploy();
  if (typeof Task.waitForDeployment === 'function') await Task.waitForDeployment();
  const taskAddress = (typeof Task.getAddress === 'function') ? await Task.getAddress() : Task.address;
  console.log('TaskContract deployed to:', taskAddress);

  const EscrowFactory = await ethers.getContractFactory('EscrowContract');
  const Escrow = await EscrowFactory.deploy(taskAddress);
  if (typeof Escrow.waitForDeployment === 'function') await Escrow.waitForDeployment();
  const escrowAddress = (typeof Escrow.getAddress === 'function') ? await Escrow.getAddress() : Escrow.address;
  console.log('EscrowContract deployed to:', escrowAddress);

  // Update contract_config.json
  const configPath = path.join(__dirname, '..', 'blockchain', 'deployment', 'contract_config.json');
  let config = {};
  try {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (e) {
    console.warn('Could not read existing contract_config.json, creating new one');
  }

  config['TaskContract'] = config['TaskContract'] || {};
  config['EscrowContract'] = config['EscrowContract'] || {};

  config['TaskContract']['address'] = taskAddress;
  config['TaskContract']['abiFile'] = '../../artifacts/blockchain/contracts/TaskContract.sol/TaskContract.json';

  config['EscrowContract']['address'] = escrowAddress;
  config['EscrowContract']['abiFile'] = '../../artifacts/blockchain/contracts/EscrowContract.sol/EscrowContract.json';

  // Ensure network rpcUrl points to localhost:8545
  config['network'] = config['network'] || {};
  config['network']['rpcUrl'] = config['network']['rpcUrl'] || 'http://127.0.0.1:8545';

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log('Updated contract_config.json with deployed addresses.');

  // Set escrow address in TaskContract (call setEscrowContract)
  const tx = await Task.setEscrowContract(escrowAddress);
  await tx.wait();
  console.log('TaskContract.setEscrowContract executed.');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
