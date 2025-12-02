// TaskContract.test.cjs - Comprehensive tests for TaskContract
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("HealChain Logic Tests (M1, M7)", function () {
    let TaskContract, EscrowContract;
    let taskContract, escrowContract;
    let owner, publisher, miner1, miner2, unauthorized;

    // Helper to compute the Solidity hash locally
    const computeCommitHash = (accReq, nonce) => {
        // Matches the Solidity keccak256(abi.encodePacked(acc_reveal, nonce_TP))
        return ethers.keccak256(ethers.solidityPacked(["uint256", "uint256"], [accReq, nonce]));
    };

    // Helper to compute HASH(score || nonce_i || taskID || pk_j)
    const computeScoreCommit = (score, nonce, taskID, minerAddress) => {
        // Note: score and nonce are uint256. taskID is bytes32. minerAddress is address.
        return ethers.keccak256(ethers.solidityPacked(["uint256", "uint256", "bytes32", "address"], [score, nonce, taskID, minerAddress]));
    };

    before(async function () {
        [owner, publisher, miner1, miner2, unauthorized] = await ethers.getSigners();

        // Deployment and Linking
        TaskContract = await ethers.getContractFactory("TaskContract");
        taskContract = await TaskContract.deploy();
        await taskContract.waitForDeployment();
        
        EscrowContract = await ethers.getContractFactory("EscrowContract");
        escrowContract = await EscrowContract.deploy(await taskContract.getAddress());
        await escrowContract.waitForDeployment();
        
        // Set escrow address in TaskContract (required for access control)
        await taskContract.setEscrowContract(await escrowContract.getAddress());
    });

    it("M1: Should allow the publisher to commit and deposit reward", async function () {
        const taskID = ethers.keccak256(ethers.toUtf8Bytes("task-123"));
        const accReq = 9500; // 95% in basis points (9500/10000)
        const nonceTP = 12345;
        const reward = ethers.parseEther("10");
        const commitHash = computeCommitHash(accReq, nonceTP);

        // 1. Publisher commits to the hash
        await taskContract.connect(publisher).tpCommit(taskID, reward, commitHash);
        
        // 2. Publisher deposits the funds into the Escrow Contract
        await expect(escrowContract.connect(publisher).deposit(taskID, { value: reward }))
            .to.changeEtherBalance(escrowContract, reward);

        const task = await taskContract.tasks(taskID);
        expect(task.commitHash).to.equal(commitHash);
    });

    it("M7: Should allow TP to reveal and fail payment if accuracy is low", async function () {
        // Create a new task for this test
        const taskID = ethers.keccak256(ethers.toUtf8Bytes("task-456"));
        const accReq = 9500; // 95% in basis points (9500/10000)
        const nonceTP = 12345;
        const reward = ethers.parseEther("10");
        const commitHash = computeCommitHash(accReq, nonceTP);
        
        // 1. Publisher commits
        await taskContract.connect(publisher).tpCommit(taskID, reward, commitHash);
        
        // 2. Transition through statuses
        await taskContract.connect(publisher).startProcessing(taskID);
        await taskContract.connect(publisher).markAwaitingVerification(taskID, owner.address);
        
        // 3. Simulate M6: Aggregator publishes the final result (90% = 9000 basis points achieved)
        const participants = [miner1.address, miner2.address];
        const scoreCommits = [
            ethers.keccak256(ethers.toUtf8Bytes("commit1")),
            ethers.keccak256(ethers.toUtf8Bytes("commit2"))
        ];
        const modelHash = ethers.keccak256(ethers.toUtf8Bytes("model-hash"));
        const accCalc = 9000; // 90% in basis points
        
        await taskContract.connect(owner).publishBlock(
            taskID, 
            modelHash, 
            accCalc, 
            owner.address, 
            participants, 
            scoreCommits
        );

        // 4. TP Reveal (M7) - should fail because accCalc (9000) < accReq (9500)
        await taskContract.connect(publisher).tpReveal(taskID, accReq, nonceTP);
        
        const task = await taskContract.tasks(taskID);
        expect(task.status).to.equal(5); // FAILED_ACCURACY (5)
    });
    
    it("M7: Should successfully verify minerRevealScore and update totalScore", async function () {
        // --- SETUP: M1 & M6 Simulation ---
        const taskID = ethers.keccak256(ethers.toUtf8Bytes("task-reveal-test"));
        const reward = ethers.parseEther("50"); 
        const accReq = 9500; // 95% in basis points
        const nonceTP = 98765;
        const commitHash = computeCommitHash(accReq, nonceTP);

        // Miner 1 details (successful submission)
        const score1 = 500; // Scaled score (e.g., 5.0 * 100)
        const nonce1 = 1001; 
        const commit1 = computeScoreCommit(score1, nonce1, taskID, miner1.address);

        // Miner 2 details (successful submission)
        const score2 = 300; 
        const nonce2 = 1002;
        const commit2 = computeScoreCommit(score2, nonce2, taskID, miner2.address);
        
        const participants = [miner1.address, miner2.address];
        const scoreCommits = [commit1, commit2];
        const accCalc = 9600; // 96% in basis points (achieved accuracy > required accuracy)
        const modelHash = ethers.keccak256(ethers.toUtf8Bytes("model-hash-reveal-test"));
        
        // 1. M1: Commit & Deposit
        await taskContract.connect(publisher).tpCommit(taskID, reward, commitHash);
        await escrowContract.connect(publisher).deposit(taskID, { value: reward });
        
        // 2. Transition through statuses
        await taskContract.connect(publisher).startProcessing(taskID);
        await taskContract.connect(publisher).markAwaitingVerification(taskID, owner.address);
        
        // 3. M6: Publish Block (Successful Aggregation)
        await taskContract.connect(owner).publishBlock(
            taskID, 
            modelHash,
            accCalc, 
            owner.address, // Aggregator
            participants, 
            scoreCommits
        );
        
        // 4. M7: TP Reveal (Opens the reveal window)
        await taskContract.connect(publisher).tpReveal(taskID, accReq, nonceTP);

        // --- EXECUTION: Miner Reveals ---
        
        // Miner 1 reveals their score (SUCCESS)
        await taskContract.connect(miner1).minerRevealScore(taskID, score1, nonce1);
        
        // Miner 2 reveals their score (SUCCESS)
        await taskContract.connect(miner2).minerRevealScore(taskID, score2, nonce2);

        // --- VERIFICATION ---
        const task = await taskContract.tasks(taskID);
        
        // Get task data which includes revealed scores
        const taskData = await taskContract.getTaskData(taskID);
        const [publisherAddr, rewardAmount, participantsList, revealedScoresArray, totalRevealedScore, isPaymentEligible] = taskData;
        
        // Check scores and total tally
        // Find miner indices in participants array
        const miner1Index = participantsList.indexOf(miner1.address);
        const miner2Index = participantsList.indexOf(miner2.address);
        
        expect(revealedScoresArray[miner1Index]).to.equal(score1, "Miner 1 score incorrect");
        expect(revealedScoresArray[miner2Index]).to.equal(score2, "Miner 2 score incorrect");
        expect(totalRevealedScore).to.equal(score1 + score2, "Total score tally incorrect");
        
        // Also verify hasRevealedScore mapping
        expect(await taskContract.hasRevealedScore(taskID, miner1.address)).to.be.true;
        expect(await taskContract.hasRevealedScore(taskID, miner2.address)).to.be.true;
    });
    
    it("M7: Should revert on invalid score reveal attempts", async function () {
        const taskID = ethers.keccak256(ethers.toUtf8Bytes("task-revert-test"));
        const reward = ethers.parseEther("10"); 
        const accReq = 8000; // 80% in basis points
        const nonceTP = 11223;
        const commitHash = computeCommitHash(accReq, nonceTP);
        
        const score1 = 100;
        const nonce1 = 2001; 
        const commit1 = computeScoreCommit(score1, nonce1, taskID, miner1.address);
        const modelHash = ethers.keccak256(ethers.toUtf8Bytes("model-hash-revert-test"));
        const accCalc = 8500; // 85% in basis points
        
        // 1. M1 & M6 Setup
        await taskContract.connect(publisher).tpCommit(taskID, reward, commitHash);
        await escrowContract.connect(publisher).deposit(taskID, { value: reward });
        await taskContract.connect(publisher).startProcessing(taskID);
        await taskContract.connect(publisher).markAwaitingVerification(taskID, owner.address);
        await taskContract.connect(owner).publishBlock(
            taskID, 
            modelHash,
            accCalc, 
            owner.address, 
            [miner1.address], 
            [commit1]
        );
        await taskContract.connect(publisher).tpReveal(taskID, accReq, nonceTP);

        // --- TEST FAILURES ---
        
        // 1. Failure: Miner tries to change their score/nonce (Free-Riding attempt)
        await expect(
            taskContract.connect(miner1).minerRevealScore(taskID, score1 + 10, nonce1) // Score change
        ).to.be.revertedWith("Score commit mismatch. Miner is dishonest.");

        // 2. Failure: Miner tries to reveal twice
        await taskContract.connect(miner1).minerRevealScore(taskID, score1, nonce1); // First successful reveal
        await expect(
            taskContract.connect(miner1).minerRevealScore(taskID, score1, nonce1)
        ).to.be.revertedWith("Score already revealed."); // Reverts due to hasRevealedScore check

        // 3. Failure: Unauthorized address tries to reveal a score
        // Create a new task for this test since we already used miner1 above
        const taskID2 = ethers.keccak256(ethers.toUtf8Bytes("task-unauthorized-test"));
        const commitHash2 = computeCommitHash(accReq, nonceTP);
        const commit2_unauth = computeScoreCommit(score1, nonce1, taskID2, miner1.address);
        const modelHash2 = ethers.keccak256(ethers.toUtf8Bytes("model-hash-unauth-test"));
        
        await taskContract.connect(publisher).tpCommit(taskID2, reward, commitHash2);
        await escrowContract.connect(publisher).deposit(taskID2, { value: reward });
        await taskContract.connect(publisher).startProcessing(taskID2);
        await taskContract.connect(publisher).markAwaitingVerification(taskID2, owner.address);
        await taskContract.connect(owner).publishBlock(
            taskID2, 
            modelHash2,
            accCalc, 
            owner.address, 
            [miner1.address], 
            [commit2_unauth]
        );
        await taskContract.connect(publisher).tpReveal(taskID2, accReq, nonceTP);
        
        await expect(
            taskContract.connect(unauthorized).minerRevealScore(taskID2, score1, nonce1)
        ).to.be.revertedWith("Not a valid participant."); 
    });
});

