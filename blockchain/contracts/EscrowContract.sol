// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ITaskContract {
    // Use the new name to explicitly request the full shape including aggregator
    function getTaskDataWithAggregator(bytes32 taskID) external view returns (
        address publisher, 
        address aggregator,
        uint256 rewardAmount, 
        address[] memory participants, 
        uint256[] memory revealedScores, 
        uint256 totalRevealedScore, 
        bool isPaymentEligible
    );
    function setTaskDistributed(bytes32 taskID) external;
}

contract EscrowContract {
    ITaskContract public taskContract;

    mapping(bytes32 => uint256) public escrowBalance;
    
    // Constant for Aggregator Share (e.g., 500 basis points = 5%) [cite: 856]
    uint256 public constant AGGREGATOR_SHARE_BPS = 500; 

    event DepositReceived(bytes32 indexed taskID, address indexed depositor, uint256 amount);
    event RewardsDistributed(bytes32 indexed taskID, uint256 totalDistributed, uint256 aggregatorReward);
    event RefundIssued(bytes32 indexed taskID, address indexed recipient, uint256 amount);

    constructor(address _taskContractAddress) {
        taskContract = ITaskContract(_taskContractAddress);
    }

    // M1: Deposit
    function deposit(bytes32 taskID) public payable {
        require(msg.value > 0, "Deposit must be > 0");
        escrowBalance[taskID] += msg.value;
        emit DepositReceived(taskID, msg.sender, msg.value);
    }

    // M7: Distribute Rewards (Algorithm 7, Function 3)
    function distributeRewards(bytes32 taskID) public {
        (
            address publisher, 
            address aggregator,
            , 
            address[] memory participants, 
            uint256[] memory scores, 
            uint256 totalScore, 
            bool isPaymentEligible
        ) = taskContract.getTaskDataWithAggregator(taskID);

        uint256 rewardPool = escrowBalance[taskID];
        require(rewardPool > 0, "No funds.");

        if (!isPaymentEligible) {
            // Path 3: Accuracy Failed -> Refund Publisher [cite: 576, 924]
            (bool success, ) = publisher.call{value: rewardPool}("");
            require(success, "Refund failed.");
            emit RefundIssued(taskID, publisher, rewardPool);
        } else {
            // Path 1: Success -> Distribute
            uint256 totalDistributed = 0;

            if (totalScore == 0) {
                // Fallback: Equal Distribution [cite: 913]
                require(participants.length > 0, "No participants");
                uint256 equalShare = rewardPool / participants.length;
                for (uint256 i = 0; i < participants.length; i++) {
                    (bool success, ) = participants[i].call{value: equalShare}("");
                    require(success, "Fallback transfer failed.");
                    totalDistributed += equalShare;
                }
                emit RewardsDistributed(taskID, totalDistributed, 0);
            } else {
                // FIX: Calculate Aggregator Share FIRST [cite: 906]
                // If aggregator is not set (zero address), skip aggregator cut
                uint256 aggregatorReward = 0;
                if (aggregator != address(0)) {
                    aggregatorReward = (rewardPool * AGGREGATOR_SHARE_BPS) / 10000;
                }
                
                // Remaining pool for miners [cite: 907]
                uint256 minerPool = rewardPool - aggregatorReward;
                
                // Distribute to Miners
                for (uint256 i = 0; i < participants.length; i++) {
                    if (scores[i] > 0) {
                        // share = (remaining * score) / totalScore [cite: 907]
                        uint256 share = (minerPool * scores[i]) / totalScore;
                        (bool success, ) = participants[i].call{value: share}("");
                        require(success, "Miner transfer failed.");
                        totalDistributed += share;
                    }
                }
                
                // FIX: Pay Aggregator [cite: 911]
                if (aggregatorReward > 0) {
                     (bool successAgg, ) = aggregator.call{value: aggregatorReward}("");
                     require(successAgg, "Aggregator transfer failed.");
                     totalDistributed += aggregatorReward;
                }
                
                // Return dust to publisher
                if (rewardPool > totalDistributed) {
                    uint256 dust = rewardPool - totalDistributed;
                    (bool dustSuccess, ) = publisher.call{value: dust}("");
                    // Note: Dust refund failure is non-critical (dust is typically small)
                    // In production, could emit event if dustSuccess is false
                    dustSuccess; // Silence unused variable warning
                }
                
                emit RewardsDistributed(taskID, totalDistributed, aggregatorReward);
            }
        }
        
        escrowBalance[taskID] = 0;
        taskContract.setTaskDistributed(taskID);
    }
}