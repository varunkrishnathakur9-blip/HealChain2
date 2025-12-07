"""
HealChain NDD-FE + Chunked BSGS (High-performance version)

FEATURES ADDED:
---------------
1) Baby-step caching (massive speedup)
2) Cached BSGS positive + negative fallback
3) Chunked recovery wrapper (decrypt_aggregate_chunked)
4) Optional parallel processing of chunks
5) Backward compatibility with existing decrypt_aggregate()

Dependencies:
    pip install tinyec numpy
"""

import math
import hashlib
import os
from typing import List, Tuple
import numpy as np
from tinyec import registry
from concurrent.futures import ProcessPoolExecutor

# =======================
# Curve setup
# =======================
curve = registry.get_curve('secp256r1')
G = curve.g
N = curve.field.n

# =======================
# Utilities
# =======================
def int_to_bytes(x: int, length: int = 32) -> bytes:
    return x.to_bytes(length, "big")


def point_to_bytes(pt):
    # treat tinyec's point-at-infinity (x/y == None) as zero bytes
    if pt is None or getattr(pt, "x", None) is None or getattr(pt, "y", None) is None:
        return b"\x00" * 64
    return int_to_bytes(pt.x, 32) + int_to_bytes(pt.y, 32)


def derive_ri_from_shared(shared_point, ctr: int, task_id: bytes) -> int:
    payload = (
        point_to_bytes(shared_point)
        + int_to_bytes(ctr, 8)
        + int_to_bytes(len(task_id), 2)
        + task_id
    )
    return int.from_bytes(hashlib.sha256(payload).digest(), "big") % N


def safe_scalar_mul(point, scalar):
    """
    Safely compute scalar * point (or point * scalar), handling:
      - point being the identity/infinity (x/y == None) -> return None
      - tinyec's multiplication quirks where Inf * int may raise TypeError
    Returns: a point object or None to indicate identity (point-at-infinity).
    """
    if point is None or getattr(point, "x", None) is None or getattr(point, "y", None) is None:
        return None
    try:
        return point * scalar
    except TypeError:
        # try scalar on left (some tinyec types support this)
        try:
            return scalar * point
        except Exception:
            # defensive fallback: return None (identity)
            return None


# =======================
# KeyGen + KeyDerive
# =======================
def key_gen() -> Tuple[object, int]:
    sk = int.from_bytes(os.urandom(32), "big") % (N - 1) + 1
    return sk * G, sk


def key_derive(sk_TP: int, pk_miners: List[object], weights_y: List[float],
               ctr: int, task_id: bytes, scale_weights: int = 1) -> int:

    sk_FE = 0
    for pk_i, w in zip(pk_miners, weights_y):
        shared = pk_i * sk_TP
        r_i = derive_ri_from_shared(shared, ctr, task_id)
        w_scaled = int(round(w * scale_weights)) % N
        sk_FE = (sk_FE + r_i * w_scaled) % N

    return sk_FE


# =======================
# Encryption (miner-side)
# =======================
def encrypt_integer_vector(sk_miner: int, pk_TP: object, pk_A: object,
                           int_delta: np.ndarray, ctr: int, task_id: bytes):

    shared = pk_TP * sk_miner
    r_i = derive_ri_from_shared(shared, ctr, task_id)
    mask = pk_TP * r_i

    ciphertexts = []
    for x in np.asarray(int_delta).flatten():
        clipped = int(x) % N
        ciphertexts.append(mask + clipped * pk_A)

    return ciphertexts


# =====================================================================================
#                               FAST BSGS — WITH CACHE (PATCHED)
# =====================================================================================

_BABY_CACHE = {}


def _point_key(pt):
    """
    Safe point→key conversion.
    Handles tinyec's representation of point-at-infinity (x=None,y=None).
    """
    if pt is None:
        return (None, None)
    x = getattr(pt, "x", None)
    y = getattr(pt, "y", None)
    if x is None or y is None:
        return (None, None)
    return (int(x), int(y) & 1)


def _precompute_babysteps(bound: int):
    m = int(math.ceil(math.sqrt(bound)))
    if m in _BABY_CACHE:
        return _BABY_CACHE[m], m

    baby = {}
    # identity
    baby[(None, None)] = 0

    # generate j*G safely
    for j in range(1, m):
        Pj = j * G
        baby[_point_key(Pj)] = j

    _BABY_CACHE[m] = baby
    return baby, m


def bsgs_cached(pt, bound: int):
    """
    BSGS with safe infinity handling.
    Returns integer x in [0,bound) or -1.
    """
    # if pt is infinity → return 0
    if pt is None or getattr(pt, "x", None) is None or getattr(pt, "y", None) is None:
        return 0

    baby, m = _precompute_babysteps(bound)
    neg_mG = ((-m) % N) * G

    current = pt
    for i in range(m):
        key = _point_key(current)
        if key in baby:
            j = baby[key]
            candidate = i * m + j
            if candidate < bound and candidate * G == pt:
                return candidate

        current = current + neg_mG

    return -1


# =====================================================================================
#                     decrypt_aggregate — WITH NEGATIVE FALLBACK
# =====================================================================================
def decrypt_aggregate(
    sk_FE: int,
    sk_A: int,
    pk_TP: object,
    ciphertexts_U: List[List[object]],
    weights_y: List[float],
    scale_weights: int = 1,
    bsgs_bound: int = 1 << 20
) -> np.ndarray:

    num_params = len(ciphertexts_U[0])
    weight_scaled = [int(round(w * scale_weights)) % N for w in weights_y]

    # global FE mask (can be identity / None if sk_FE == 0)
    global_mask = safe_scalar_mul(pk_TP, sk_FE)
    inv_sk_A = pow(sk_A, -1, N)

    recovered = np.zeros(num_params, dtype=np.int64)

    for k in range(num_params):

        # weighted ciphertext sum
        agg = None
        for Uik, w in zip([m[k] for m in ciphertexts_U], weight_scaled):
            tmp = Uik * w
            agg = tmp if agg is None else agg + tmp

        # If there were no ciphertexts (agg is None) treat as identity
        if agg is None:
            E = None
        else:
            # remove FE mask: agg - global_mask
            if global_mask is None:
                E = agg
            else:
                # both agg and global_mask are points: compute agg + (-1)*global_mask
                neg_global = safe_scalar_mul(global_mask, (-1) % N)
                # neg_global may be None if global_mask is identity; handle it
                if neg_global is None:
                    E = agg
                else:
                    E = agg + neg_global

        # Remove pk_A factor safely (compute E * inv_sk_A)
        E_star = safe_scalar_mul(E, inv_sk_A)

        # Try positive BSGS (bsgs_cached treats None/infinity as 0)
        val = bsgs_cached(E_star, bsgs_bound)

        if val < 0:
            # Try negative fallback: compute -E_star and BSGS it
            if E_star is None:
                neg_val = bsgs_cached(None, bsgs_bound)
            else:
                neg_E_star = safe_scalar_mul(E_star, (-1) % N)
                neg_val = bsgs_cached(neg_E_star, bsgs_bound)

            if neg_val >= 0:
                val = -neg_val
            else:
                raise ValueError(f"BSGS bound insufficient for param {k}")

        # Map signed representation (avoid huge mod-N wrapping)
        if val > N // 2:
            val -= N

        recovered[k] = val

    return recovered


# =====================================================================================
#                         CHUNKED RECOVERY WRAPPER
# =====================================================================================
def decrypt_aggregate_chunked(
    sk_FE: int,
    sk_A: int,
    pk_TP: object,
    ciphertexts_U: List[List[object]],
    weights_y: List[float],
    miner_int_updates: List[np.ndarray],
    scale_weights: int = 1,
    chunk_size: int = 256,
    max_chunk_bound_cap: int = 1 << 28,
    parallel: bool = False,
) -> np.ndarray:

    L = len(ciphertexts_U[0])
    weight_scaled = [int(round(w * scale_weights)) for w in weights_y]

    def solve_chunk(start, end):
        chunk_cts = [miner[start:end] for miner in ciphertexts_U]

        # compute exact S range for bound
        S = np.zeros(end - start, dtype=np.int64)
        for w, upd in zip(weight_scaled, miner_int_updates):
            S += w * upd[start:end]

        max_abs_S = int(np.max(np.abs(S))) if np.any(S) else 0
        bound = min(max_chunk_bound_cap, max(max_abs_S + 16, 1024))

        return (start, end, decrypt_aggregate(
            sk_FE, sk_A, pk_TP,
            chunk_cts, weights_y,
            scale_weights=scale_weights,
            bsgs_bound=bound
        ))

    chunks = [(i, min(L, i + chunk_size)) for i in range(0, L, chunk_size)]
    recovered = np.zeros(L, dtype=np.int64)

    if parallel:
        with ProcessPoolExecutor() as ex:
            for start, end, vec in ex.map(lambda c: solve_chunk(*c), chunks):
                recovered[start:end] = vec
    else:
        for start, end in chunks:
            _, _, vec = solve_chunk(start, end)
            recovered[start:end] = vec

    return recovered


# =====================================================================================
# Demo (local test)
# =====================================================================================
if __name__ == "__main__":
    print("Running NDD-FE CHUNKED demo...")

    pkA, skA = key_gen()
    pkTP, skTP = key_gen()

    # miners
    pk_miners = []
    sk_miners = []
    for _ in range(3):
        p, s = key_gen()
        pk_miners.append(p)
        sk_miners.append(s)

    # test vector
    L = 500
    rnd = np.random.default_rng(99)
    miners_updates = [rnd.integers(-40, 40, size=L) for _ in range(3)]

    weights = [1, 1, 1]
    ctr = 1
    task_id = b"test"

    # FE key
    sk_FE = key_derive(skTP, pk_miners, weights, ctr, task_id)

    # encrypt
    cts = []
    for sk_m, upd in zip(sk_miners, miners_updates):
        cts.append(encrypt_integer_vector(sk_m, pkTP, pkA, upd, ctr, task_id))

    rec = decrypt_aggregate_chunked(
        sk_FE, skA, pkTP,
        cts, weights,
        miner_int_updates=miners_updates,
        chunk_size=128,
        parallel=False
    )

    print("Recovered first 10:", rec[:10])
    print("Expected first 10:", (miners_updates[0] + miners_updates[1] + miners_updates[2])[:10])
    print("OK:", np.all(rec == sum(miners_updates)))
