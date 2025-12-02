/* Hardhat deploy script (CommonJS): deploy TaskContract and EscrowContract, then update contract_config.json */
const fs = require('fs');
const path = require('path');

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);

  const Task = await ethers.deployContract('TaskContract');
  await Task.waitForDeployment();
  console.log('TaskContract deployed to:', await Task.getAddress());

  const Escrow = await ethers.deployContract('EscrowContract', [await Task.getAddress()]);
  await Escrow.waitForDeployment();
  console.log('EscrowContract deployed to:', await Escrow.getAddress());

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

  config['TaskContract']['address'] = await Task.getAddress();
  config['TaskContract']['abiFile'] = '../../artifacts/blockchain/contracts/TaskContract.sol/TaskContract.json';

  config['EscrowContract']['address'] = await Escrow.getAddress();
  config['EscrowContract']['abiFile'] = '../../artifacts/blockchain/contracts/EscrowContract.sol/EscrowContract.json';

  // Ensure network rpcUrl points to localhost:8545
  config['network'] = config['network'] || {};
  config['network']['rpcUrl'] = config['network']['rpcUrl'] || 'http://127.0.0.1:8545';

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log('Updated contract_config.json with deployed addresses.');

  // Set escrow address in TaskContract (call setEscrowContract)
  const tx = await Task.setEscrowContract(await Escrow.getAddress());
  await tx.wait();
  console.log('TaskContract.setEscrowContract executed.');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
