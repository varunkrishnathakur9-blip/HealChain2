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
        return point * int(scalar)
    except TypeError:
        try:
            return int(scalar) * point
        except Exception:
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
    baby[(None, None)] = 0

    # compute j * G deterministically
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
    """
    Return x in [0,bound) such that x*G == pt, or -1 if not found.
    Handles identity (None) and avoids unsafe tinyec states.
    """
    if pt is None or getattr(pt, "x", None) is None or getattr(pt, "y", None) is None:
        return 0

    baby, m = _precompute_babysteps(bound)
    # compute -m*G safely
    neg_mG = safe_scalar_mul(G, (-m) % N)
    if neg_mG is None:
        neg_mG = ((-m) % N) * G

    current = pt
    for i in range(m):
        # if current became invalid, stop early
        if current is None or getattr(current, "x", None) is None or getattr(current, "y", None) is None:
            key = (None, None)
        else:
            key = _point_key(current)

        if key in baby:
            j = baby[key]
            candidate = i * m + j
            if candidate < bound:
                # final verification
                try:
                    if candidate * G == pt:
                        return candidate
                except Exception:
                    return -1

        try:
            current = current + neg_mG
        except Exception:
            return -1

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
    bsgs_bound: int = 1 << 20,
    miner_int_updates: List[np.ndarray] = None
) -> np.ndarray:

    num_params = len(ciphertexts_U[0])
    # signed scaled weights (Python ints)
    weight_scaled_raw = [int(round(w * scale_weights)) for w in weights_y]
    # also keep mod-N scalars for EC multiplication
    weight_scaled_mod = [ws % N for ws in weight_scaled_raw]

    global_mask = safe_scalar_mul(pk_TP, sk_FE)
    inv_sk_A = pow(sk_A, -1, N)

    recovered = np.zeros(num_params, dtype=np.int64)

    for k in range(num_params):

        # Reconstruct aggregate deterministically from ciphertexts and weights_mod
        agg = None
        for miner_cts, w_mod in zip(ciphertexts_U, weight_scaled_mod):
            Uik = miner_cts[k]
            tmp = safe_scalar_mul(Uik, w_mod)
            agg = tmp if agg is None else (agg + tmp if tmp is not None else agg)

        # Remove FE mask
        if agg is None:
            E = None
        else:
            if global_mask is None:
                E = agg
            else:
                neg_global = safe_scalar_mul(global_mask, (-1) % N)
                E = agg if neg_global is None else (agg + neg_global)

        # Remove pk_A factor
        E_star = safe_scalar_mul(E, inv_sk_A)

        # ---------- CONSISTENCY CHECK (robust, uses clipped modular encoding) ----------
        # Miners encrypt clipped = int(x) % N, so we must use the same modular arithmetic
        if miner_int_updates is not None:
            try:
                # Compute S_mod using clipped modular values (same as miner encryption)
                S_mod = 0
                for w_mod, upd in zip(weight_scaled_mod, miner_int_updates):
                    clipped = int(upd[k]) % N  # Same encoding miners use
                    S_mod = (S_mod + (w_mod * clipped)) % N

                expected_point = safe_scalar_mul(G, S_mod)
                if E_star != expected_point:
                    print(f"[ERROR] Modular consistency failed at param {k}")
                    print(f"  S_mod (sum w_mod*clipped mod N) = {S_mod}")
                    print(f"  expected_point = {expected_point}")
                    print(f"  E_star         = {E_star}")
                    raise ValueError(f"Encrypted point mismatch for param {k}: check miner ciphertexts / pk_A / pk_TP / sk_FE / scale_weights.")
            except ValueError:
                raise  # Re-raise ValueError (the mismatch error)
            except Exception as _ex:
                # Only warn on non-critical errors (e.g., index errors if updates shape differs)
                pass

        # Compute dynamic bsgs_bound from signed S if miner_int_updates available
        dynamic_bound = bsgs_bound
        if miner_int_updates is not None:
            try:
                S_signed = 0
                for w_raw, upd in zip(weight_scaled_raw, miner_int_updates):
                    S_signed += int(w_raw) * int(upd[k])
                dynamic_bound = max(1024, abs(S_signed) + 16)
            except Exception:
                pass  # Fall back to provided bsgs_bound

        # Try positive BSGS with dynamic bound
        val = bsgs_cached(E_star, dynamic_bound)

        if val < 0:
            neg_E_star = None if E_star is None else safe_scalar_mul(E_star, (-1) % N)
            val2 = bsgs_cached(neg_E_star, dynamic_bound)
            if val2 >= 0:
                val = -val2
            else:
                raise ValueError(f"BSGS bound insufficient for param {k} (dynamic_bound={dynamic_bound})")

        # Map signed representation
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
    # keep Python ints for weight scaling (no modulo here; used for S calc)
    weight_scaled = [int(round(w * scale_weights)) for w in weights_y]

    def compute_chunk_bound_py(start, end):
        # Compute S per-index using Python ints (no overflow)
        max_abs_S = 0
        for idx in range(start, end):
            s_val = 0
            # sum using Python ints
            for w, upd in zip(weight_scaled, miner_int_updates):
                s_val += int(w) * int(upd[idx])
            abs_s = abs(s_val)
            if abs_s > max_abs_S:
                max_abs_S = abs_s

        bound = max(max_abs_S + 16, 1024)
        # cap to avoid runaway
        capped = min(bound, max_chunk_bound_cap)
        hit_cap = (bound > max_chunk_bound_cap)
        return capped, max_abs_S, hit_cap

    def solve_chunk(start, end):
        chunk_cts = [miner[start:end] for miner in ciphertexts_U]

        # Use Python-safe bound computation
        bound, max_abs_S, hit_cap = compute_chunk_bound_py(start, end)

        # diagnostic logging (remove or reduce in production)
        print(f"[CHUNK] start={start} end={end} max_abs_S={max_abs_S} requested_bound={max(max_abs_S+16,1024)} used_bound={bound} hit_cap={hit_cap}")

        if hit_cap:
            # Helpful error: shows why BSGS might fail and suggests actions
            raise ValueError(
                f"Required BSGS bound {max_abs_S + 16} exceeds max_chunk_bound_cap "
                f"{max_chunk_bound_cap} for chunk [{start}:{end}]. "
                "Either increase max_chunk_bound_cap, reduce chunk_size, or quantize/clip updates."
            )

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
        chunk_size=256,
        parallel=False
    )

    print("Recovered first 10:", rec[:10])
    print("Expected first 10:", (miners_updates[0] + miners_updates[1] + miners_updates[2])[:10])
    print("OK:", np.all(rec == sum(miners_updates)))
