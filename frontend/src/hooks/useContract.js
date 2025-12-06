import { useAccount, useReadContract, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { useMemo } from 'react';

/**
 * Hook for interacting with smart contracts
 * 
 * @param {string} contractAddress - Contract address
 * @param {Array} contractABI - Contract ABI
 * @returns {Object} Contract interaction methods
 */
export const useContract = (contractAddress, contractABI) => {
  const { address, isConnected } = useAccount();
  const { writeContract, data: hash, isPending, error } = useWriteContract();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash,
  });

  // Read contract function
  const read = (functionName, args = []) => {
    const { data, isLoading, error: readError } = useReadContract({
      address: contractAddress,
      abi: contractABI,
      functionName,
      args,
    });

    return { data, isLoading, error: readError };
  };

  // Write contract function
  const write = async (functionName, args = [], value = null) => {
    if (!isConnected) {
      throw new Error('Wallet not connected');
    }

    try {
      await writeContract({
        address: contractAddress,
        abi: contractABI,
        functionName,
        args,
        ...(value && { value: BigInt(value) }),
      });
    } catch (err) {
      throw err;
    }
  };

  return {
    address,
    isConnected,
    read,
    write,
    hash,
    isPending,
    isConfirming,
    isConfirmed,
    error,
  };
};

/**
 * Hook for EscrowContract interactions (M1 - Publish Task)
 */
export const useEscrowContract = (contractAddress, contractABI) => {
  const contract = useContract(contractAddress, contractABI);

  const publishTask = async (taskID, commitHash, revealDeadline, reward) => {
    // Convert reward to wei
    const value = BigInt(Math.floor(parseFloat(reward) * 1e18));
    
    return contract.write('publishTask', [taskID, commitHash, revealDeadline], value);
  };

  return {
    ...contract,
    publishTask,
  };
};

/**
 * Hook for RewardContract interactions (M7 - Distribute Rewards)
 */
export const useRewardContract = (contractAddress, contractABI) => {
  const contract = useContract(contractAddress, contractABI);

  const tpReveal = async (taskID, revealedAccuracy, nonce, commitHash) => {
    return contract.write('tpReveal', [taskID, revealedAccuracy, nonce, commitHash]);
  };

  const minerRevealScore = async (taskID, score, scoreNonce, scoreCommit) => {
    return contract.write('minerRevealScore', [taskID, score, scoreNonce, scoreCommit]);
  };

  const distributeRewards = async (taskID, minerAddresses, scores) => {
    return contract.write('distributeRewards', [taskID, minerAddresses, scores]);
  };

  return {
    ...contract,
    tpReveal,
    minerRevealScore,
    distributeRewards,
  };
};

