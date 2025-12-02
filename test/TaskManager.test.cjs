const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("TaskManager", function () {
  let taskManager;
  let owner;
  let addr1;
  let addr2;

  beforeEach(async function () {
    // Get signers
    [owner, addr1, addr2] = await ethers.getSigners();

    // Deploy TaskManager
    const TaskManager = await ethers.getContractFactory("TaskManager");
    taskManager = await TaskManager.deploy();
    await taskManager.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should deploy successfully", async function () {
      expect(await taskManager.getAddress()).to.be.properAddress;
    });

    it("Should initialize task counter to 0", async function () {
      expect(await taskManager.getTaskIdCounter()).to.equal(0);
    });
  });

  describe("Publishing Tasks", function () {
    it("Should allow any user to publish a task", async function () {
      const dataHash = "QmHash123";
      
      await expect(taskManager.connect(addr1).publishTask(dataHash))
        .to.emit(taskManager, "TaskPublished")
        .withArgs(0, addr1.address, dataHash);

      expect(await taskManager.taskPublisher(0)).to.equal(addr1.address);
      expect(await taskManager.taskDataHash(0)).to.equal(dataHash);
    });

    it("Should increment task counter on each publish", async function () {
      await taskManager.connect(addr1).publishTask("hash1");
      expect(await taskManager.getTaskIdCounter()).to.equal(1);

      await taskManager.connect(addr2).publishTask("hash2");
      expect(await taskManager.getTaskIdCounter()).to.equal(2);
    });

    it("Should emit TaskPublished event with correct parameters", async function () {
      const dataHash = "testHash456";
      
      const tx = await taskManager.connect(owner).publishTask(dataHash);
      const receipt = await tx.wait();
      
      const event = receipt.logs.find(
        log => {
          try {
            const parsed = taskManager.interface.parseLog(log);
            return parsed && parsed.name === "TaskPublished";
          } catch {
            return false;
          }
        }
      );
      
      expect(event).to.not.be.undefined;
      const parsed = taskManager.interface.parseLog(event);
      expect(parsed.args.taskId).to.equal(0);
      expect(parsed.args.publisher).to.equal(owner.address);
      expect(parsed.args.dataHash).to.equal(dataHash);
    });
  });

  describe("Access Control", function () {
    beforeEach(async function () {
      // Publish a task as addr1
      await taskManager.connect(addr1).publishTask("originalHash");
    });

    it("Should allow original publisher to update their task", async function () {
      const newHash = "updatedHash";
      
      await expect(taskManager.connect(addr1).updateTask(0, newHash))
        .to.emit(taskManager, "TaskUpdated")
        .withArgs(0, addr1.address, newHash);

      expect(await taskManager.taskDataHash(0)).to.equal(newHash);
    });

    it("Should prevent non-publisher from updating task", async function () {
      await expect(
        taskManager.connect(addr2).updateTask(0, "maliciousHash")
      ).to.be.revertedWith("TaskManager: Only the task publisher can perform this action");
    });

    it("Should prevent updating non-existent task", async function () {
      await expect(
        taskManager.connect(addr1).updateTask(999, "hash")
      ).to.be.revertedWith("TaskManager: Task does not exist");
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await taskManager.connect(addr1).publishTask("testHash");
    });

    it("Should return correct task info", async function () {
      const [publisher, dataHash] = await taskManager.getTaskInfo(0);
      
      expect(publisher).to.equal(addr1.address);
      expect(dataHash).to.equal("testHash");
    });

    it("Should return true for existing task", async function () {
      expect(await taskManager.taskExists(0)).to.be.true;
    });

    it("Should return false for non-existent task", async function () {
      expect(await taskManager.taskExists(999)).to.be.false;
    });
  });

  describe("Input Validation", function () {
    it("Should reject data hash that is too long", async function () {
      const longHash = "a".repeat(257); // 257 characters
      
      await expect(
        taskManager.connect(addr1).publishTask(longHash)
      ).to.be.revertedWith("TaskManager: Data hash too long");
    });

    it("Should accept empty string as data hash", async function () {
      await expect(taskManager.connect(addr1).publishTask(""))
        .to.emit(taskManager, "TaskPublished");
    });
  });
});

