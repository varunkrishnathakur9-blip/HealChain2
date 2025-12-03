// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TaskManager
 * @notice Dynamic Role-Based Access Control system where privileges are resource-specific.
 *         Any user can be a "Task Publisher," but only the specific address that published
 *         a task has write privileges for that specific task ID.
 * @dev Follows Checks-Effects-Interactions pattern for security
 */
contract TaskManager {
    // --- State Variables ---
    
    /// @notice Counter for task IDs, auto-increments on each publish
    uint256 private _taskIdCounter;
    
    /// @notice Mapping from taskId to the address that published it (owner)
    /// @dev taskId => publisher address
    mapping(uint256 => address) public taskPublisher;
    
    /// @notice Mapping from taskId to data hash
    /// @dev taskId => dataHash (stored as string hash)
    mapping(uint256 => string) public taskDataHash;
    
    // --- Events ---
    
    /**
     * @notice Emitted when a new task is published
     * @param taskId The unique identifier for the task
     * @param publisher The address that published the task
     * @param dataHash The hash of the task data
     */
    event TaskPublished(
        uint256 indexed taskId,
        address indexed publisher,
        string dataHash
    );
    
    /**
     * @notice Emitted when a task is updated
     * @param taskId The unique identifier for the task
     * @param publisher The address that updated the task
     * @param newDataHash The new hash of the task data
     */
    event TaskUpdated(
        uint256 indexed taskId,
        address indexed publisher,
        string newDataHash
    );

    /**
     * @notice Emitted when a miner applies for a task with an IPFS proof
     */
    event MinerApplied(
        uint256 indexed taskId,
        address indexed miner,
        string ipfsCid
    );

    // --- Miner Applications ---
    struct MinerApplication {
        address miner;
        string ipfsCid;
        uint256 stake;
    }

    // taskId => applications
    mapping(uint256 => MinerApplication[]) public taskApplications;
    
    // --- Modifiers ---
    
    /**
     * @notice Restricts access to only the original publisher of a specific task
     * @param taskId The task ID to check ownership for
     * @dev Reverts if the caller is not the original publisher
     */
    modifier onlyTaskPublisher(uint256 taskId) {
        require(
            taskPublisher[taskId] != address(0),
            "TaskManager: Task does not exist"
        );
        require(
            msg.sender == taskPublisher[taskId],
            "TaskManager: Only the task publisher can perform this action"
        );
        _;
    }
    
    // --- Functions ---
    
    /**
     * @notice Publishes a new task with the given data hash
     * @param dataHash The hash of the task data (string format)
     * @return taskId The unique identifier assigned to the newly published task
     * @dev Increments taskId counter and stores ownership mapping
     *      Follows Checks-Effects-Interactions pattern:
     *      1. Checks: Validate input (implicit - string can be empty but that's acceptable)
     *      2. Effects: Update state (counter, mappings)
     *      3. Interactions: Emit event
     */
    function publishTask(string memory dataHash) public returns (uint256) {
        // CHECKS: Input validation (string can be empty, but we ensure it's not too large)
        require(
            bytes(dataHash).length <= 256,
            "TaskManager: Data hash too long"
        );
        
        // EFFECTS: Update state variables
        uint256 newTaskId = _taskIdCounter;
        _taskIdCounter++; // Increment before assignment to start from 0
        
        taskPublisher[newTaskId] = msg.sender;
        taskDataHash[newTaskId] = dataHash;
        
        // INTERACTIONS: Emit event
        emit TaskPublished(newTaskId, msg.sender, dataHash);
        
        return newTaskId;
    }
    
    /**
     * @notice Updates an existing task's data hash (demonstration of access control)
     * @param taskId The task ID to update
     * @param newDataHash The new data hash for the task
     * @dev Only the original publisher can update their task
     *      This function demonstrates the security of the onlyTaskPublisher modifier
     */
    function updateTask(uint256 taskId, string memory newDataHash) 
        public 
        onlyTaskPublisher(taskId) 
    {
        // CHECKS: Input validation
        require(
            bytes(newDataHash).length <= 256,
            "TaskManager: Data hash too long"
        );
        
        // EFFECTS: Update state
        taskDataHash[taskId] = newDataHash;
        
        // INTERACTIONS: Emit event
        emit TaskUpdated(taskId, msg.sender, newDataHash);
    }

    /**
     * @notice Apply for a published task by providing an IPFS CID that contains miner capability proof
     * @param taskId The task to apply for
     * @param ipfsCid CID string pointing to JSON metadata uploaded to IPFS
     */
    function applyForTask(uint256 taskId, string memory ipfsCid) public {
        require(taskExists(taskId), "TaskManager: Task does not exist");
        require(bytes(ipfsCid).length > 0, "TaskManager: ipfsCid required");

        // For simplicity, stake is set to 0 here; off-chain or another contract can set/verify stake
        MinerApplication memory app = MinerApplication({
            miner: msg.sender,
            ipfsCid: ipfsCid,
            stake: 0
        });

        taskApplications[taskId].push(app);
        emit MinerApplied(taskId, msg.sender, ipfsCid);
    }
    
    // --- View Functions ---
    
    /**
     * @notice Gets the current task ID counter
     * @return The next task ID that will be assigned
     */
    function getTaskIdCounter() public view returns (uint256) {
        return _taskIdCounter;
    }
    
    /**
     * @notice Checks if a task exists
     * @param taskId The task ID to check
     * @return True if the task exists, false otherwise
     */
    function taskExists(uint256 taskId) public view returns (bool) {
        return taskPublisher[taskId] != address(0);
    }
    
    /**
     * @notice Gets task information
     * @param taskId The task ID to query
     * @return publisher The address that published the task
     * @return dataHash The data hash associated with the task
     */
    function getTaskInfo(uint256 taskId) 
        public 
        view 
        returns (address publisher, string memory dataHash) 
    {
        require(taskExists(taskId), "TaskManager: Task does not exist");
        return (taskPublisher[taskId], taskDataHash[taskId]);
    }
}

