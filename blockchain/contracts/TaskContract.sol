// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TaskContract {
    // --- Data Structures ---
    enum TaskStatus {
        PUBLISHING, PROCESSING, AWAITING_VERIFICATION, PUBLISHED_ONCHAIN, 
        REWARD_DISTRIBUTED, FAILED_ACCURACY, REJECTED
    }

    // Constants from Algorithm 7
    uint256 public constant SCORE_REVEAL_WINDOW = 24 hours; // [cite: 854]

    struct Task {
        address publisher;             // pkTP (M1)
        uint256 rewardAmount;          // R
        bytes32 commitHash;            // HASH(acc_req || nonce_TP) (M1)
        uint256 accReq;                // Revealed accuracy (M7)
        uint256 accCalc;               // Achieved accuracy (M4/M6)
        TaskStatus status;
        address[] participants;        // Valid miners pk_i (M2)
        bytes32[] scoreCommits;        // HASH(score || nonce_i || taskID || pk_j) (M3/M6)
        mapping(address => uint256) revealedScores; 
        mapping(address => uint256) participantIndex; 
        uint256 totalRevealedScore;
        bool isRevealed;               // Has TP executed tpReveal?
        bool isDistributed;            // Has EscrowContract distributed funds?
        uint256 blockPublishTimestamp; // Timestamp of M6 success
        
        // FIX: Added deadline tracking for Algorithm 7 compliance
        uint256 minersRevealDeadline;  // [cite: 884]
        
        // M6: Evidence fields
        bytes32 modelHash;
        address aggregator;
    }

    // --- Events ---
    event TaskPublished(bytes32 indexed taskID, address indexed publisher, uint256 reward, bytes32 commitHash);
    event TaskStatusChanged(bytes32 indexed taskID, TaskStatus oldStatus, TaskStatus newStatus);
    event BlockPublishedOnChain(bytes32 indexed taskID, bytes32 modelHash, uint256 accCalc, address aggregator);
    event TPRevealed(bytes32 indexed taskID, uint256 accReq, bool paymentEligible);
    event MinerScoreRevealed(bytes32 indexed taskID, address indexed miner, uint256 score);

    mapping(bytes32 => Task) public tasks;
    mapping(bytes32 => mapping(address => bool)) public hasRevealedScore;
    
    address public escrowContractAddress;
    
    // Modifiers
    modifier onlyEscrow() {
        require(msg.sender == escrowContractAddress, "Only escrow contract can call");
        _;
    }
    
    modifier onlyPublisher(bytes32 taskID) {
        require(msg.sender == tasks[taskID].publisher, "Only publisher can call");
        _;
    }
    
    modifier onlyAggregator(bytes32 taskID) {
        require(msg.sender == tasks[taskID].aggregator, "Only aggregator can call");
        _;
    }
    
    function setEscrowContract(address _escrowAddress) external {
        require(escrowContractAddress == address(0), "Escrow address already set");
        require(_escrowAddress != address(0), "Invalid escrow address");
        escrowContractAddress = _escrowAddress;
    }

    // --- Core Verification Logic ---
    
    // M1: TP Commit
    function tpCommit(
        bytes32 taskID, 
        uint256 reward, 
        bytes32 _commitHash
    ) public {
        require(tasks[taskID].publisher == address(0), "Task already exists.");
        require(reward > 0, "Reward must be greater than zero");
        require(_commitHash != bytes32(0), "Invalid commit hash");

        Task storage task = tasks[taskID];
        task.publisher = msg.sender;
        task.rewardAmount = reward;
        task.commitHash = _commitHash;
        task.status = TaskStatus.PUBLISHING;
        task.participants = new address[](0);
        task.scoreCommits = new bytes32[](0);
        
        emit TaskPublished(taskID, msg.sender, reward, _commitHash);
    }
    
    function startProcessing(bytes32 taskID) external onlyPublisher(taskID) {
        Task storage task = tasks[taskID];
        require(task.status == TaskStatus.PUBLISHING, "Invalid status transition");
        task.status = TaskStatus.PROCESSING;
        emit TaskStatusChanged(taskID, TaskStatus.PUBLISHING, TaskStatus.PROCESSING);
    }
    
    function markAwaitingVerification(bytes32 taskID, address _aggregator) external {
        Task storage task = tasks[taskID];
        require(task.status == TaskStatus.PROCESSING, "Invalid status transition");
        require(_aggregator != address(0), "Invalid aggregator address");
        require(msg.sender == task.publisher || msg.sender == _aggregator, "Unauthorized");
        
        TaskStatus oldStatus = task.status;
        task.status = TaskStatus.AWAITING_VERIFICATION;
        task.aggregator = _aggregator;
        emit TaskStatusChanged(taskID, oldStatus, task.status);
    }

    // M6: Aggregator Finalizes the Block
    function publishBlock(
        bytes32 taskID, 
        bytes32 _modelHash,
        uint256 _accCalc,
        address _aggregator,
        address[] memory _participants,
        bytes32[] memory _scoreCommits,
        bytes memory _signature
    ) public onlyAggregator(taskID) {
        Task storage task = tasks[taskID];
        require(task.status == TaskStatus.AWAITING_VERIFICATION, "Task not ready.");
        require(_participants.length == _scoreCommits.length, "Mismatch");

        // Verify aggregator signature over the block fingerprint to ensure
        // the publisher of the block is the expected aggregator.
        // The Aggregator should sign the keccak256(abi.encodePacked(taskID, _modelHash, _accCalc))
        // using the Ethereum Signed Message prefix (\x19Ethereum Signed Message:\n32).
        if (_signature.length != 0) {
            require(_signature.length == 65, "Invalid signature length");
            bytes32 r;
            bytes32 s;
            uint8 v;
            assembly {
                r := mload(add(_signature, 32))
                s := mload(add(_signature, 64))
                v := byte(0, mload(add(_signature, 96)))
            }
            if (v < 27) {
                v += 27;
            }
            require(v == 27 || v == 28, "Invalid v in signature");

            bytes32 blockFingerprint = keccak256(abi.encodePacked(taskID, _modelHash, _accCalc));
            bytes32 ethSignedHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", blockFingerprint));

            address recovered = ecrecover(ethSignedHash, v, r, s);
            // Accept the signed-authority if it matches the declared aggregator,
            // or allow the on-chain transaction sender (msg.sender) when using
            // a node-managed account. This lets deployments use either off-chain
            // signed payloads or direct node-sent transactions from the aggregator.
            if (recovered != _aggregator && msg.sender != _aggregator) {
                revert("Invalid aggregator signature");
            }
        }

        TaskStatus oldStatus = task.status;
        task.status = TaskStatus.PUBLISHED_ONCHAIN;
        task.modelHash = _modelHash;
        task.accCalc = _accCalc;
        task.aggregator = _aggregator;
        task.participants = _participants;
        task.scoreCommits = _scoreCommits;
        task.blockPublishTimestamp = block.timestamp;
        
        for (uint256 i = 0; i < _participants.length; i++) {
            task.participantIndex[_participants[i]] = i;
        }
        
        emit TaskStatusChanged(taskID, oldStatus, task.status);
        emit BlockPublishedOnChain(taskID, _modelHash, _accCalc, _aggregator);
    }

    // M7: TP Reveal (Algorithm 7, Function 1)
    function tpReveal(
        bytes32 taskID, 
        uint256 acc_reveal, 
        uint256 nonce_TP
    ) public onlyPublisher(taskID) {
        Task storage task = tasks[taskID];
        require(task.status == TaskStatus.PUBLISHED_ONCHAIN, "Task not ready.");
        require(!task.isRevealed, "Already revealed");

        // Verify Hash [cite: 875]
        bytes32 computedHash = keccak256(abi.encodePacked(acc_reveal, nonce_TP));
        require(computedHash == task.commitHash, "Commit hash mismatch.");

        bool paymentEligible = (task.accCalc >= acc_reveal);
        task.accReq = acc_reveal;
        task.isRevealed = true;
        
        // FIX: Set the Miner Reveal Deadline [cite: 869]
        task.minersRevealDeadline = block.timestamp + SCORE_REVEAL_WINDOW;

        if (!paymentEligible) {
            TaskStatus oldStatus = task.status;
            task.status = TaskStatus.FAILED_ACCURACY;
            emit TaskStatusChanged(taskID, oldStatus, task.status);
        }
        
        emit TPRevealed(taskID, acc_reveal, paymentEligible);
    }

    // M7: Miner Reveal Score (Algorithm 7, Function 2)
    function minerRevealScore(
        bytes32 taskID, 
        uint256 score, 
        uint256 nonce_i
    ) public {
        Task storage task = tasks[taskID];
        require(task.isRevealed, "TP must reveal first.");
        
        // FIX: Enforce time-bound reveal [cite: 898]
        require(block.timestamp <= task.minersRevealDeadline, "Reveal window closed");
        
        require(!hasRevealedScore[taskID][msg.sender], "Score already revealed.");

        uint256 idx = task.participantIndex[msg.sender];
        require(idx < task.participants.length && task.participants[idx] == msg.sender, "Not a participant.");

        // Verify Hash [cite: 900]
        bytes32 computedCommit = keccak256(abi.encodePacked(score, nonce_i, taskID, msg.sender));
        require(computedCommit == task.scoreCommits[idx], "Score commit mismatch.");

        task.revealedScores[msg.sender] = score;
        task.totalRevealedScore += score;
        hasRevealedScore[taskID][msg.sender] = true;
        
        emit MinerScoreRevealed(taskID, msg.sender, score);
    }
    
    // Getter for Escrow
    function getTaskData(bytes32 taskID) 
        public 
        view 
        returns (
            address publisher, 
            address aggregator, // Added aggregator return
            uint256 rewardAmount, 
            address[] memory participants, 
            uint256[] memory revealedScores, 
            uint256 totalRevealedScore, 
            bool isPaymentEligible
        ) 
    {
        Task storage task = tasks[taskID];
        require(task.isRevealed, "Task not revealed.");
        
        uint256[] memory scores = new uint256[](task.participants.length);
        for (uint256 i = 0; i < task.participants.length; i++) {
            scores[i] = task.revealedScores[task.participants[i]];
        }
        
        return (
            task.publisher, 
            task.aggregator, // FIX: Need this for payment
            task.rewardAmount,
            task.participants, 
            scores, 
            task.totalRevealedScore, 
            (task.status != TaskStatus.FAILED_ACCURACY)
        );
    }
    
    function setTaskDistributed(bytes32 taskID) external onlyEscrow {
        Task storage task = tasks[taskID];
        require(!task.isDistributed, "Already distributed");
        task.status = TaskStatus.REWARD_DISTRIBUTED;
        task.isDistributed = true;
    }
}