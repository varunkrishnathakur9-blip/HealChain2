# ndd_fe.py
"""
Updated NDD-FE module with x-coordinate+parity BSGS (bsgs_discrete_log_x)
Drop-in for HealChain aggregator/miner prototyping.

Requirements:
  pip install tinyec numpy
"""

# ndd_fe.py
"""
Updated NDD-FE module with consistent scale handling and auto BSGS bound computation.

Usage:
  python ndd_fe.py

Notes:
 - Ensure 'tinyec' and 'numpy' are installed:
     pip install tinyec numpy
 - This is a prototyping/demo implementation. For production:
     * choose scale conventions carefully
     * chunk large vectors
     * persist E/E_star for dispute handling
"""


# ndd_fe.py
"""
Updated NDD-FE module with negative-value fallback for BSGS.
Drop-in for HealChain aggregator/miner prototyping.

Requirements:
  pip install tinyec numpy
"""

import math
import hashlib
import os
from typing import List, Tuple, Optional

import numpy as np
from tinyec import registry

# Curve setup: NIST P-256 / secp256r1
curve = registry.get_curve('secp256r1')
G = curve.g
N = curve.field.n  # order
Pp = curve.field.p

# -----------------------
# Utility helpers
# -----------------------
def int_to_bytes(x: int, length: int = 32) -> bytes:
    return x.to_bytes(length, byteorder='big', signed=False)

def point_to_bytes(pt) -> bytes:
    if pt is None:
        return b'\x00' * 64
    return int_to_bytes(pt.x, 32) + int_to_bytes(pt.y, 32)

def canonical_hash_bytes(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()

def derive_ri_from_shared(shared_point, ctr: int, task_id: bytes) -> int:
    """
    Deterministic r_i derivation from shared point, ctr and task_id.
    Uses canonical serialization: x||y||ctr(8 bytes)||len(task_id)(2 bytes)||task_id
    """
    if shared_point is None:
        shared_bytes = b'\x00' * 64
    else:
        shared_bytes = point_to_bytes(shared_point)
    b = shared_bytes + int_to_bytes(ctr, 8) + int_to_bytes(len(task_id), 2) + task_id
    val = int.from_bytes(hashlib.sha256(b).digest(), 'big') % N
    return val

# -----------------------
# Key generation & derive
# -----------------------
def key_gen() -> Tuple[object, int]:
    sk = int.from_bytes(os.urandom(32), 'big') % (N - 1) + 1
    pk = sk * G
    return pk, sk

def key_derive(sk_TP: int, pk_miners: List[object], weights_y: List[float], ctr: int, task_id: bytes, scale_weights: int = 10**6) -> int:
    """
    sk_FE = sum_i ( r_i * weight_scaled_i ) mod N
    """
    sk_FE = 0
    for i, pk_i in enumerate(pk_miners):
        shared = pk_i * (sk_TP % N)
        r_i = derive_ri_from_shared(shared, ctr, task_id)
        weight_scaled = int(round(weights_y[i] * scale_weights)) % N
        sk_FE = (sk_FE + (r_i * weight_scaled) % N) % N
    return sk_FE

# -----------------------
# Encryption (miner-side)
# -----------------------
def encrypt_integer_vector(sk_miner: int, pk_TP: object, pk_A: object, int_delta: np.ndarray, ctr: int, task_id: bytes) -> List[object]:
    """
    Encrypt integer delta vector:
      U_j = mask_point + (int_delta_j mod N) * pk_A
    mask_point = r_i * pk_TP where r_i derived from shared secret
    """
    shared = pk_TP * (sk_miner % N)
    r_i = derive_ri_from_shared(shared, ctr, task_id)
    r_i = r_i % N
    mask_point = pk_TP * r_i

    flat = np.asarray(int_delta).flatten()
    ciphertexts = []
    for xi in flat:
        scalar = int(xi) % N
        data_point = pk_A * scalar
        U = mask_point + data_point
        ciphertexts.append(U)
    return ciphertexts

# -----------------------
# BSGS optimized: x + parity keys
# -----------------------
def _point_parity(pt):
    if pt is None:
        return None
    return int(pt.y & 1)

def _point_key(pt):
    if pt is None:
        return (None, None)
    return (int(pt.x), _point_parity(pt))

def bsgs_discrete_log_x(target_point, max_range: int = 1 << 20) -> int:
    """
    Baby-step Giant-step using (x, parity) keys.
    Searches x in [0, max_range-1] such that x*G == target_point.
    Returns x if found; otherwise -1.
    """
    if target_point is None:
        return 0

    m = int(math.ceil(math.sqrt(max_range)))
    baby = {}
    # j = 0 -> point at infinity
    baby[(None, None)] = 0

    # build baby steps Pj = j*G iteratively
    prev = None
    for j in range(1, m):
        if prev is None:
            Pj = G
        else:
            Pj = prev + G
        key = _point_key(Pj)
        if key not in baby:
            baby[key] = j
        prev = Pj

    # precompute -mG
    neg_mG = ((-m) % N) * G

    current = target_point
    for i in range(0, m):
        k = _point_key(current)
        if k in baby:
            j = baby[k]
            candidate = i * m + j
            if candidate < max_range:
                candidate_point = (candidate % N) * G
                if candidate_point == target_point:
                    return candidate
        current = current + neg_mG

    return -1

# -----------------------
# Aggregator decryption & recovery (with negative fallback)
# -----------------------
def decrypt_aggregate(sk_FE: int, sk_A: int, pk_TP: object, ciphertexts_U: List[List[object]], weights_y: List[float], scale_weights: int = 10**6, bsgs_bound: int = 1<<20) -> np.ndarray:
    """
    Inputs:
      - sk_FE (int): functional secret derived by key_derive
      - sk_A (int): aggregator private scalar
      - pk_TP: TP public point
      - ciphertexts_U: [num_miners][num_params] list of Points
      - weights_y: list of floats (same length as miners)
    Returns:
      - numpy int64 array of recovered integer aggregated values per parameter
    Behavior:
      - Tries BSGS on E_star
      - If not found, tries on -E_star and restores negative sign if successful
    """
    num_miners = len(ciphertexts_U)
    assert num_miners == len(weights_y), "miners vs weights mismatch"
    num_params = len(ciphertexts_U[0])

    global_mask = pk_TP * (sk_FE % N)
    weight_scaled_list = [int(round(w * scale_weights)) % N for w in weights_y]
    inv_sk_A = pow(sk_A, -1, N)

    recovered = np.zeros(num_params, dtype=np.int64)
    for k in range(num_params):
        agg_point = None
        for i in range(num_miners):
            Uik = ciphertexts_U[i][k]
            scalar = weight_scaled_list[i]
            tmp = Uik * scalar
            agg_point = tmp if agg_point is None else (agg_point + tmp)

        # remove mask: E = agg_point - global_mask  (add negative)
        neg_global_mask = global_mask * ((-1) % N)
        E = agg_point + neg_global_mask

        # E_star = inv_sk_A * E
        E_star = E * (inv_sk_A % N)

        # Attempt BSGS on E_star
        val = bsgs_discrete_log_x(E_star, max_range=bsgs_bound)
        if val < 0:
            # Fallback: try BSGS on -E_star (point negation) to detect negative values
            try:
                # negate E_star: -E_star is (N-1)*E_star
                neg_E_star = E_star * ((-1) % N)
                val_pos = bsgs_discrete_log_x(neg_E_star, max_range=bsgs_bound)
                if val_pos >= 0:
                    # recovered a positive candidate for |S| -> original was negative
                    val = -int(val_pos)
                    # store and continue
                else:
                    raise ValueError(f"BSGS out of bound for parameter index {k}; increase bsgs_bound or reduce chunk max")
            except Exception:
                raise ValueError(f"BSGS out of bound for parameter index {k}; increase bsgs_bound or reduce chunk max")
        else:
            # val found is non-negative; proceed
            pass

        # if val is modulo > N//2 mapping, but we handled negative via negation above, ensure signed mapping:
        if isinstance(val, int) and val > N // 2:
            val = val - N

        recovered[k] = int(val)
    return recovered

# -----------------------
# Demo / test harness (consistent scale + auto-bound)
# -----------------------
if __name__ == "__main__":
    print("Running ndd_fe small-vector simulation...")

    # Generate keys
    pkA, skA = key_gen()
    pkTP, skTP = key_gen()

    # miners
    NUM_MINERS = 3
    miners = [key_gen() for _ in range(NUM_MINERS)]
    pk_miners = [m[0] for m in miners]
    sk_miners = [m[1] for m in miners]

    # small integer deltas per miner (length L)
    L = 8
    rng = np.random.default_rng(12345)
    # produce small ints in range [-10,10]
    deltas = [rng.integers(-10, 11, size=L).astype(np.int64) for _ in range(NUM_MINERS)]

    # weights
    weights = [1.0 for _ in range(NUM_MINERS)]

    ctr = 1
    task_id = b"task-demo-1"

    # Choose consistent scale_weights used everywhere in this demo
    scale_weights_demo = 1

    # derive sk_FE using the SAME scale_weights
    sk_FE = key_derive(skTP, pk_miners, weights, ctr, task_id, scale_weights=scale_weights_demo)
    print("sk_FE derived with scale_weights =", scale_weights_demo)

    # Each miner encrypts its integer vector using their private key
    ciphertexts = []
    for i in range(NUM_MINERS):
        U = encrypt_integer_vector(sk_miners[i], pkTP, pkA, deltas[i], ctr, task_id)
        ciphertexts.append(U)

    # Compute exact aggregated integer S per parameter (using the SAME scale)
    weight_scaled_list_demo = [int(round(w * scale_weights_demo)) % N for w in weights]
    expected_exact = np.zeros(L, dtype=np.int64)
    for i in range(NUM_MINERS):
        expected_exact += (weight_scaled_list_demo[i] * deltas[i]).astype(np.int64)

    max_abs_S = int(np.max(np.abs(expected_exact)))
    # margin to be safe:
    bsgs_bound_auto = max(1024, max_abs_S + 16)

    print("Expected aggregated int per param (example):", expected_exact.tolist())
    print("Setting bsgs_bound to:", bsgs_bound_auto)

    try:
        recovered = decrypt_aggregate(sk_FE, skA, pkTP, ciphertexts, weights, scale_weights=scale_weights_demo, bsgs_bound=bsgs_bound_auto)
        print("recovered:", recovered.tolist())
        if np.array_equal(expected_exact, recovered):
            print("SUCCESS: recovered == expected_exact")
        else:
            print("WARNING: mismatch recovered vs expected_exact")
    except Exception as ex:
        print("Error during decryption/recovery:", ex)
        # Helpful debug: compute E_star for first parameter and show x,y
        try:
            k = 0
            global_mask = pkTP * (sk_FE % N)
            agg_point = None
            for i in range(NUM_MINERS):
                Uik = ciphertexts[i][k]
                scalar = int(round(weights[i] * scale_weights_demo)) % N
                tmp = Uik * scalar
                agg_point = tmp if agg_point is None else (agg_point + tmp)
            neg_global_mask = global_mask * ((-1) % N)
            E = agg_point + neg_global_mask
            inv_sk_A = pow(skA, -1, N)
            E_star = E * (inv_sk_A % N)
            print("Debug E_star point (x,y):", getattr(E_star, 'x', None), getattr(E_star, 'y', None))
            print("Approx expected S for k=0:", expected_exact[0])
        except Exception as ex2:
            print("Error while preparing debug info:", ex2)
