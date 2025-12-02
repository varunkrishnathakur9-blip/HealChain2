// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Updated interface to match the TaskContract return values from the previous step
interface ITaskContract {
    function getTaskData(bytes32 taskID) external view returns (
        address publisher, 
        address aggregator, // Added aggregator to match real contract
        uint256 rewardAmount, 
        address[] memory participants, 
        uint256[] memory revealedScores, 
        uint256 totalRevealedScore, 
        bool isPaymentEligible
    );
    function setTaskDistributed(bytes32 taskID) external;
}

contract MockTaskContract is ITaskContract {
    address public publisher;
    address public aggregator; // State variable for aggregator
    uint256 public rewardAmount;
    address[] public participants;
    uint256[] public revealedScores;
    uint256 public totalRevealedScore;
    bool public isPaymentEligible;
    bool public distributedCalled = false;

    // Updated setter to include _aggregator
    function setTaskData(
        address _publisher,
        address _aggregator, // New argument
        uint256 _rewardAmount,
        address[] memory _participants,
        uint256[] memory _revealedScores,
        uint256 _totalRevealedScore,
        bool _isPaymentEligible
    ) public {
        publisher = _publisher;
        aggregator = _aggregator; // Set the aggregator
        rewardAmount = _rewardAmount;
        
        delete participants;
        delete revealedScores;
        
        for (uint i = 0; i < _participants.length; i++) {
            participants.push(_participants[i]);
            revealedScores.push(_revealedScores[i]);
        }
        
        totalRevealedScore = _totalRevealedScore;
        isPaymentEligible = _isPaymentEligible;
        distributedCalled = false; // Reset for new test
    }

    // Updated getter to return the aggregator address
    function getTaskData(bytes32) external view override returns (
        address, address, uint256, address[] memory, uint256[] memory, uint256, bool
    ) {
        return (
            publisher, 
            aggregator, // Return aggregator
            rewardAmount, 
            participants, 
            revealedScores, 
            totalRevealedScore, 
            isPaymentEligible
        );
    }

    function setTaskDistributed(bytes32) external override {
        distributedCalled = true;
    }
}