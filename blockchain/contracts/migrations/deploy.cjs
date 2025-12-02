// migrations/deploy.cjs
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  // 1. Deploy TaskContract first
  const TaskContractFactory = await ethers.getContractFactory("TaskContract");
  const taskContract = await TaskContractFactory.deploy();
  await taskContract.waitForDeployment();

  const taskContractAddress = await taskContract.getAddress();
  console.log("TaskContract deployed to:", taskContractAddress);

  // 2. Deploy EscrowContract, passing the TaskContract address
  const EscrowContractFactory = await ethers.getContractFactory("EscrowContract");
  const escrowContract = await EscrowContractFactory.deploy(taskContractAddress);
  await escrowContract.waitForDeployment();

  const escrowContractAddress = await escrowContract.getAddress();
  console.log("EscrowContract deployed to:", escrowContractAddress);

  // 3. Set the Escrow Contract address in the TaskContract (required for access control)
  console.log("Setting EscrowContract address in TaskContract...");
  const setEscrowTx = await taskContract.setEscrowContract(escrowContractAddress);
  await setEscrowTx.wait();
  console.log("EscrowContract address set successfully");

  // 4. Save addresses to config file (optional - for Python integration)
  const configPath = path.join(__dirname, "..", "..", "deployment", "contract_config.json");
  
  try {
    const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
    config.TaskContract.address = taskContractAddress;
    config.EscrowContract.address = escrowContractAddress;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    console.log("Config file updated:", configPath);
  } catch (error) {
    console.warn("Could not update config file:", error.message);
  }

  console.log("\n=== Deployment Summary ===");
  console.log("TaskContract:", taskContractAddress);
  console.log("EscrowContract:", escrowContractAddress);
  console.log("========================\n");

  return { taskContractAddress, escrowContractAddress };
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

// To run this: npx hardhat run blockchain/migrations/deploy.js