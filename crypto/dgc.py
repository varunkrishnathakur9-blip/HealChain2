import numpy as np
from typing import Tuple, List

class DGC:
    """
    Implements the Decentralized Gradient Compression (DGC) algorithm.
    Includes compression (M3) and decompression (M4) logic.
    """

    def __init__(self, compression_threshold_tau: float = 0.9, quantization_scale: int = 1000000):
        """
        Initializes the DGC module.
        :param compression_threshold_tau: The sparsity threshold (e.g., 0.9 means keep 10% largest gradients)[cite: 171].
        :param quantization_scale: Scaling factor to convert floats to integers for NDD-FE compatibility.
        """
        self.tau = compression_threshold_tau
        self.scale = quantization_scale
        # Local state: Accumulated gradients that were too small to send in previous rounds
        self.residual = None  

    def compress(self, raw_gradient: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compresses the raw gradient (Delta_i) into a sparse update (Delta_i').
        Executed by Miner in Module 3 (Algorithm 3).

        :param raw_gradient: The raw local gradient update (Delta_i).
        :return: (compressed_update_float, full_gradient_with_residual)
        """
        # Ensure residual is initialized with zeros if it's the first round
        if self.residual is None:
            self.residual = np.zeros_like(raw_gradient)

        # Step 1: Add current gradient to residual from previous rounds (Momentum Correction)
        # "Apply accumulated residuals from DGC"[cite: 567].
        full_gradient = raw_gradient + self.residual

        # Step 2: Sparsification (Thresholding)
        # Calculate threshold T for the top (1 - tau) elements[cite: 501].
        flat_magnitudes = np.abs(full_gradient.flatten())
        
        # Determine number of elements to keep
        num_to_keep = int(len(flat_magnitudes) * (1.0 - self.tau))
        
        # Safety check for extreme compression
        if num_to_keep == 0:
             if len(flat_magnitudes) > 0:
                 num_to_keep = 1
             else:
                 return np.zeros_like(full_gradient), full_gradient

        # Find magnitude threshold
        # (partition is faster than sort for finding kth element)
        partitioned = np.partition(flat_magnitudes, -num_to_keep)
        threshold_value = partitioned[-num_to_keep]

        # Create mask: True for elements >= T[cite: 171].
        mask = np.abs(full_gradient) >= threshold_value
        
        # Step 3: Create Sparse Update
        # "minimizes communication costs... by compressing... into a sparse update"[cite: 171].
        compressed_update = full_gradient * mask

        # Step 4: Update Residual
        # Store the gradients that were NOT sent (masked out) for the next round.
        self.residual = full_gradient * (~mask)

        # Return the sparse float update. 
        # Note: Explicit quantization to int happens during NDD-FE Encryption or here depending on pipeline.
        # NDD-FE Encrypt (Module 3) expects this sparse vector.
        return compressed_update, full_gradient

    def decompress(self, recovered_vector_int: np.ndarray) -> np.ndarray:
        """
        Decompresses the aggregated integer vector back to float weights.
        Executed by Aggregator in Module 4 (Algorithm 4, Step 5).
        
        :param recovered_vector_int: The aggregated integer vector recovered via BSGS[cite: 566].
        :return: The floating point model update.
        """
        # Step 5: DGC Decompress and Update Model[cite: 543].
        # "Restore sparse gradients to full dimensionality"[cite: 567].
        # Convert integers back to float representation using the shared scaling factor.
        decompressed_update = recovered_vector_int.astype(float) / self.scale
        
        return decompressed_update

# --- Auxiliary Function for Scoring (Module 3) ---

def calculate_contribution_score(compressed_update: np.ndarray) -> float:
    """
    Calculates the Gradient-Norm Based Contribution Score (L2 norm) (M3).
    score = ||Delta_i'||_2 [cite: 47, 113, 502]
    
    This score is computed on the compressed gradient *before* encryption to 
    serve as a proxy for the miner's contribution quality[cite: 114].
    """
    if compressed_update.size == 0:
        return 0.0
    
    # Calculate the L2 norm (Euclidean norm)
    score = np.linalg.norm(compressed_update)
    
    return float(score)