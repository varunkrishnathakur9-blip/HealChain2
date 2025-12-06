import math
import hashlib
import numpy as np
import random
from typing import List, Tuple

from tinyec import registry

# Use a standard curve (NIST P-256 / secp256r1)
curve = registry.get_curve('secp256r1')

class NDD_FE:
    """
    NDD-FE Implementation aligning with Chapter 3 Preliminaries of the HealChain Report.
    
    Implements:
    - KeyDerive (Eq 3.1): sk_FE = sum(r_i * y_i)
    - Encrypt (Eq 3.3): U_i = (r_i * pk_TP) + (Delta_i * pk_A)
    - Decrypt (Eq 3.5 - 3.7): Aggregation, Mask Removal, and Recovery
    
    Note: 'weights_y' are treated as scaled integers (x 10^6) to simulate 
    fixed-point arithmetic on the Elliptic Curve.
    """

    def __init__(self):
        self.curve = curve
        self.n = curve.field.n  # Order of the curve

    def key_gen(self) -> Tuple[object, int]:
        """Generate (pk, sk) where pk is a Point and sk is an integer."""
        sk = random.randint(1, self.n - 1)
        pk = sk * self.curve.g
        return pk, sk

    def key_derive(self, sk_TP: int, pk_miners: List[object], weights_y: List[float], ctr: int, task_ID: bytes) -> int:
        """
        Derive the functional secret key sk_FE for the Aggregator.
        
        Corresponds to PDF Eq 3.1: sk_FE = sum(r_i^crt * y_i)
        where r_i is derived from the shared secret (CDH assumption).
        """
        sk_FE = 0
        for i, pk_i in enumerate(pk_miners):
            # 1. Compute Shared Secret (CDH): g^(s_TP * s_i) = pk_i * sk_TP
            # Ensure we perform Point * scalar (point.__mul__(scalar))
            shared_point = pk_i * sk_TP
            
            # 2. Derive r_i via Hashing (Eq 3.2 / 3.4)
            hash_input = f"{shared_point.x}|{ctr}|{task_ID.hex()}".encode()
            r_i = int(hashlib.sha256(hash_input).hexdigest(), 16) % self.n
            
            # 3. Scale weight to integer for EC scalar multiplication
            # We scale by 10^6 to handle float weights in discrete log field
            weight_scaled = int(weights_y[i] * 10**6)
            
            # 4. Accumulate sk_FE
            term = (r_i * weight_scaled) % self.n
            sk_FE = (sk_FE + term) % self.n
            
        return sk_FE

    def encrypt(self, sk_miner: int, pk_TP: object, pk_A: object, update_delta_prime: np.ndarray, ctr: int, task_ID: bytes) -> List[object]:
        """
        Encrypt the local gradient vector.
        
        Corresponds to PDF Eq 3.3: U_i = pk_1^r_i * pk_A^Delta_i
        In Additive ECC notation:  U_i = (r_i * pk_TP) + (Delta_i * pk_A)
        """
        # 1. Derive random mask r_i (must match Aggregator's derivation)
        # Shared secret: sk_miner * pk_TP (Same as sk_TP * pk_miner)
        # Shared secret: pk_TP * sk_miner (Point * scalar)
        shared_point = pk_TP * sk_miner
        hash_input = f"{shared_point.x}|{ctr}|{task_ID.hex()}".encode()
        r_i = int(hashlib.sha256(hash_input).hexdigest(), 16) % self.n

        # Mask Point (pk_TP * r_i)
        mask_point = pk_TP * r_i

        ciphertext_list = []
        
        # 2. Encrypt each element of the gradient vector
        for x_val in np.nditer(update_delta_prime):
            # Quantize gradient value to integer
            x_int = int(float(x_val))
            
            # Data Point (Delta_i * pk_A)
            data_point = x_int * pk_A
            
            # U = Mask + Data
            U = mask_point + data_point
            ciphertext_list.append(U)
            
        return ciphertext_list

    def decrypt_aggregate(self, sk_FE: int, sk_A: int, pk_TP: object, ciphertexts_U: List[List[object]], weights_y: List[float]) -> np.ndarray:
        """
        Decrypt and recover the aggregated update.
        
        Corresponds to PDF Eq 3.5 & 3.6 (Aggregation & Mask Removal)
        and Eq 3.7 (Weight Recovery via BSGS).
        """
        num_miners = len(ciphertexts_U)
        num_params = len(ciphertexts_U[0])
        
        # 1. Calculate the Global Noise Mask
        # Mask = sk_FE * pk_TP (Derived from Eq 3.5 denominator)
        # Global mask: pk_TP * sk_FE (Point * scalar)
        global_mask_point = pk_TP * sk_FE
        
        # Compute negative mask for subtraction: -Mask = (n-1) * Mask
        neg_mask_point = (self.n - 1) * global_mask_point
        
        # 2. Calculate modular inverse of Aggregator's Secret Key (sk_A^-1)
        # Needed for Eq 3.7: E* = E^(1/sk_A) -> E* = inv_sk_A * E
        inv_sk_A = pow(sk_A, -1, self.n)
        
        recovered_values = []

        # 3. Process each gradient parameter
        for k in range(num_params):
            agg_ciphertext = None
            
            # A. Weighted Aggregation of Ciphertexts (numerator of Eq 3.5)
            # Sum( y_i * U_{i,k} )
            for i in range(num_miners):
                U_ik = ciphertexts_U[i][k]
                weight_scaled = int(weights_y[i] * 10**6)
                
                weighted_U = weight_scaled * U_ik
                
                if agg_ciphertext is None:
                    agg_ciphertext = weighted_U
                else:
                    agg_ciphertext = agg_ciphertext + weighted_U
            
            # B. Remove Noise Mask (Eq 3.5 result E)
            # E = AggCipher - Mask
            E_point = agg_ciphertext + neg_mask_point
            
            # C. Remove pk_A factor (Eq 3.7 result E*)
            # Result_Point = sk_A^-1 * E
            # Handle point-at-infinity cases safely: if E_point is at infinity, treat value as 0
            if getattr(E_point, 'x', None) is None:
                val = 0
            else:
                result_point = inv_sk_A * E_point
                # D. Solve Discrete Log (BSGS) to get the integer value
                val = self.bsgs_recovery(result_point)
            
            # Handle standard overflow for negative numbers in finite fields
            if val > self.n // 2:
                val -= self.n
                
            recovered_values.append(val)
            
        return np.array(recovered_values)

    def bsgs_recovery(self, target_point: object) -> int:
        """
        Baby-step Giant-step to recover small discrete log x.
        Finds x such that x * G = target_point.
        """
        # Range of recovery (adjust based on expected gradient sum size)
        # For testing/demo, 2^20 is reasonable (~1 million)
        limit = 1 << 20
        m = int(math.ceil(math.sqrt(limit)))
        
        # Baby steps
        baby_steps = {}
        curr = self.curve.g * 0 # Point at infinity
        
        # Note: tinyec might not handle 0 scalar mult resulting in a specific object
        # We manually handle the loop
        for j in range(m):
            Pj = j * self.curve.g
            baby_steps[Pj.x] = j

        # Giant step pre-computation: -m * G
        neg_mG = ((self.n - m) % self.n) * self.curve.g
        
        current_giant = target_point
        
        for i in range(m):
            # Check for collision
            if current_giant.x in baby_steps:
                j = baby_steps[current_giant.x]
                # Check Y coordinate to ensure it's the correct point, not just same X
                # (Simple x-check is usually sufficient for random curves, 
                # but rigorous implementation checks full point equality)
                candidate_point = (i * m + j) * self.curve.g
                if candidate_point == target_point:
                    return i * m + j
                
                # Check negative y case (symmetric point)
                if candidate_point.x == target_point.x and candidate_point.y != target_point.y:
                     # This usually implies the negative value in the field
                     pass

            current_giant = current_giant + neg_mG
            
        return 0

if __name__ == '__main__':
    print('NDD-FE module loaded (Aligned with HealChain PDF Chapter 3)')