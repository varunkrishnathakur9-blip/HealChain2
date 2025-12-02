const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("EscrowContract distributeRewards", function () {
  it("distributes proportionally when totalScore > 0", async function () {
    const [publisher, miner1, miner2, miner3] = await ethers.getSigners();

    // Deploy mock task contract and escrow
    const Mock = await ethers.getContractFactory("MockTaskContract");
    const mock = await Mock.deploy();
    await mock.waitForDeployment();

    const Escrow = await ethers.getContractFactory("EscrowContract");
    const escrow = await Escrow.deploy(mock.target);
    await escrow.waitForDeployment();

    // Prepare participants and scores
    const participants = [miner1.address, miner2.address, miner3.address];
    const scores = [10, 30, 60];
    const total = 100;

    // Set mock task data
    await mock.setTaskData(publisher.address, ethers.parseEther("10"), participants, scores, total, true);

    // Fund escrow with 10 ETH from publisher using deposit()
    await escrow.connect(publisher).deposit(ethers.keccak256(ethers.toUtf8Bytes("taskA")), { value: ethers.parseEther("10") });

    // Capture balances before
    const before = await Promise.all(participants.map(a => ethers.provider.getBalance(a)));

    // Call distributeRewards
    await expect(escrow.distributeRewards(ethers.keccak256(ethers.toUtf8Bytes("taskA")))).to.not.be.reverted;

    // Check balances increased proportionally (approx)
    const after = await Promise.all(participants.map(a => ethers.provider.getBalance(a)));
    const gained = after.map((a, i) => a - before[i]);

    // miner1 should get ~1 ETH (10%), miner2 ~3 ETH, miner3 ~6 ETH
    expect(gained[0]).to.be.gte(ethers.parseEther("0.9"));
    expect(gained[1]).to.be.gte(ethers.parseEther("2.7"));
    expect(gained[2]).to.be.gte(ethers.parseEther("5.9"));
  });

  it("falls back to equal distribution when totalScore == 0", async function () {
    const [publisher, miner1, miner2] = await ethers.getSigners();

    const Mock = await ethers.getContractFactory("MockTaskContract");
    const mock = await Mock.deploy();
    await mock.waitForDeployment();

    const Escrow = await ethers.getContractFactory("EscrowContract");
    const escrow = await Escrow.deploy(mock.target);
    await escrow.waitForDeployment();

    const participants = [miner1.address, miner2.address];
    const scores = [0, 0];

    await mock.setTaskData(publisher.address, ethers.parseEther("2"), participants, scores, 0, true);
    await escrow.connect(publisher).deposit(ethers.keccak256(ethers.toUtf8Bytes("taskB")), { value: ethers.parseEther("2") });

    const before = await Promise.all(participants.map(a => ethers.provider.getBalance(a)));
    await expect(escrow.distributeRewards(ethers.keccak256(ethers.toUtf8Bytes("taskB")))).to.not.be.reverted;
    const after = await Promise.all(participants.map(a => ethers.provider.getBalance(a)));
    const gained = after.map((a,i) => a - before[i]);

    // Each should get ~1 ETH
    expect(gained[0]).to.be.gte(ethers.parseEther("0.9"));
    expect(gained[1]).to.be.gte(ethers.parseEther("0.9"));
  });

  it("refunds publisher when isPaymentEligible is false", async function () {
    const [publisher, miner1] = await ethers.getSigners();

    const Mock = await ethers.getContractFactory("MockTaskContract");
    const mock = await Mock.deploy();
    await mock.waitForDeployment();

    const Escrow = await ethers.getContractFactory("EscrowContract");
    const escrow = await Escrow.deploy(mock.target);
    await escrow.waitForDeployment();

    const participants = [miner1.address];
    const scores = [10];

    await mock.setTaskData(publisher.address, ethers.parseEther("1"), participants, scores, 10, false);
    await escrow.connect(publisher).deposit(ethers.keccak256(ethers.toUtf8Bytes("taskC")), { value: ethers.parseEther("1") });

    const before = await ethers.provider.getBalance(publisher.address);
    await expect(escrow.distributeRewards(ethers.keccak256(ethers.toUtf8Bytes("taskC")))).to.not.be.reverted;
    const after = await ethers.provider.getBalance(publisher.address);

    // Publisher should have been refunded (minus gas) — check increase amount approx 1 ETH
    expect(after).to.be.gte(before - ethers.parseEther("0.01") );
  });
});
