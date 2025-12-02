// migrations/deploy_taskmanager.cjs
// Deployment script for TaskManager contract (CommonJS version)
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying TaskManager contract with account:", deployer.address);
  console.log("Account balance:", (await ethers.provider.getBalance(deployer.address)).toString());

  // Deploy TaskManager
  const TaskManagerFactory = await ethers.getContractFactory("TaskManager");
  const taskManager = await TaskManagerFactory.deploy();
  await taskManager.waitForDeployment();

  const taskManagerAddress = await taskManager.getAddress();
  console.log("TaskManager deployed to:", taskManagerAddress);

  // Update contract_config.json
  // From migrations/ directory: ../.. goes to blockchain/, then deployment/
  const configPath = path.join(__dirname, "..", "..", "deployment", "contract_config.json");
  
  let config = {};
  try {
    if (fs.existsSync(configPath)) {
      config = JSON.parse(fs.readFileSync(configPath, "utf8"));
    }
  } catch (error) {
    console.warn("Could not read existing config file, creating new one");
  }

  // Add TaskManager to config
  config.TaskManager = {
    address: taskManagerAddress,
    abiFile: "../../artifacts/blockchain/contracts/TaskManager.sol/TaskManager.json"
  };

  // Ensure network config exists
  if (!config.network) {
    config.network = {
      rpcUrl: "http://127.0.0.1:7545",
      chainId: 5777
    };
  }

  // Ensure deployment directory exists
  const deploymentDir = path.dirname(configPath);
  if (!fs.existsSync(deploymentDir)) {
    fs.mkdirSync(deploymentDir, { recursive: true });
  }

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log("Config file updated:", configPath);

  console.log("\n=== Deployment Summary ===");
  console.log("TaskManager Address:", taskManagerAddress);
  console.log("Network:", config.network.rpcUrl);
  console.log("===========================\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

