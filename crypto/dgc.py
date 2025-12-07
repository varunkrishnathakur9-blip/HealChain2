# dgc.py
"""
Improved DGC (Decentralized Gradient Compression) utilities.

- Deterministic top-k sparsification with residual accumulation.
- Quantization to integer range with clipping and scale metadata.
- Sparse (COO) output format: (indices: np.ndarray[int], values_int: np.ndarray[int], scale: float)
- Decompression helpers to reconstruct dense float vector from recovered integer vector.
- Serialization helpers for creating merkle/leaf payloads.

Intended usage in Miner:
    dgc = DGC(tau=0.9, max_int=1023)
    indices, vals_int, scale = dgc.compress_and_quantize(local_gradient)
    leaf_bytes = dgc.pack_leaf(miner_address, indices, vals_int, nonce)   # for merkle leaf
    send encrypted Ui and leaf meta to aggregator

Intended usage in Aggregator after BSGS recovers integer vector:
    recovered_int_vector = ... (full dense np.int64 vector or per-chunk)
    float_update = dgc.decompress_from_dense_int(recovered_int_vector, scale)
    # or if aggregator receives sparse (indices + vals_int) from FE recovery:
    float_update = dgc.decompress_from_sparse(indices, vals_int, original_shape, scale)
"""

from typing import Tuple, List, Optional
import numpy as np
import math
import struct

# default dtype for integer quantization
INT_DTYPE = np.int64

class DGC:
    def __init__(self, tau: float = 0.9, max_int: int = 1023, min_nonzeros: int = 1):
        """
        :param tau: sparsity threshold in [0,1]. tau=0.9 => keep top 10% elements.
        :param max_int: maximum |value| after quantization (Q). quantized values will be in [-max_int, max_int].
        :param min_nonzeros: ensure at least this many elements are kept (avoid empty updates).
        """
        assert 0.0 <= tau < 1.0
        assert max_int >= 1
        self.tau = float(tau)
        self.max_int = int(max_int)
        self.min_nonzeros = int(min_nonzeros)
        self.residual_sparse = None  # store residual as tuple (indices: np.ndarray, floats: np.ndarray, shape)
        # residual_sparse represents values not sent previously (float values)

    # ----------------------
    # Compression / Quantize
    # ----------------------
    def compress_and_quantize(self, raw_gradient: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Compress raw gradient to sparse integer representation.

        Returns:
            indices (np.ndarray[int]): 1D indices of non-zero elements (flattened index order),
            values_int (np.ndarray[int]): quantized integer values (same length as indices),
            scale (float): float scaling factor used (so receiver can decompress).
        """
        if not isinstance(raw_gradient, np.ndarray):
            raw_gradient = np.array(raw_gradient, dtype=float)

        # Flatten to 1D for deterministic indexing
        shape = raw_gradient.shape
        flat = raw_gradient.flatten().astype(float)

        # Add residual if exists (convert residual sparse -> dense then add)
        if self.residual_sparse is not None:
            r_idx, r_vals, r_shape = self.residual_sparse
            # build dense residual vector lazily
            res_dense = np.zeros(flat.shape, dtype=float)
            res_dense[r_idx] = r_vals
            flat = flat + res_dense

        # Determine number to keep (top (1-tau) fraction)
        n = flat.size
        k = int(math.floor(n * (1.0 - self.tau)))
        k = max(k, self.min_nonzeros)
        k = min(k, n)

        # If all zeros short-circuit
        if np.all(flat == 0):
            self.residual_sparse = (np.array([], dtype=np.int64), np.array([], dtype=float), flat.shape)
            return np.array([], dtype=np.int64), np.array([], dtype=INT_DTYPE), 1.0

        # Select top-k by magnitude deterministically, then sort indices ascending for stable ordering
        abs_flat = np.abs(flat)
        # partition indices
        kth = np.partition(abs_flat, -k)[-k]
        mask = abs_flat >= kth
        idxs = np.nonzero(mask)[0]
        # If too many due to ties, take the top-k by value then index
        if idxs.size > k:
            # sort by (-abs, index) and take first k
            order = np.lexsort((idxs, -abs_flat[idxs]))
            idxs = idxs[order][:k]
        # sort indices for deterministic leaf order
        idxs = np.sort(idxs)

        selected_vals = flat[idxs]

        # Compute scale: we will map floats -> integers in [-max_int, max_int]
        max_abs = float(np.max(np.abs(selected_vals))) if selected_vals.size > 0 else 1.0
        # To avoid divide-by-zero map to scale 1 if max_abs == 0
        if max_abs == 0:
            scale = 1.0
        else:
            scale = max_abs / self.max_int  # so value_int = round(val/scale) in [-max_int, max_int]

        # Quantize and clip to ensure bounds
        vals_int = np.rint(selected_vals / scale).astype(INT_DTYPE)
        vals_int = np.clip(vals_int, -self.max_int, self.max_int)

        # Residual: store everything not sent
        mask_sent = np.zeros(n, dtype=bool)
        mask_sent[idxs] = True
        residual_vals = flat[~mask_sent]
        residual_idxs = np.nonzero(~mask_sent)[0]
        # convert residual into sparse representation for next round
        self.residual_sparse = (residual_idxs.astype(np.int64), residual_vals.astype(float), flat.shape)

        return idxs.astype(np.int64), vals_int.astype(INT_DTYPE), float(scale)

    # ----------------------
    # Decompression helpers
    # ----------------------
    def decompress_from_sparse(self, indices: np.ndarray, values_int: np.ndarray, original_shape: Tuple[int, ...], scale: float) -> np.ndarray:
        """
        Reconstruct dense float update from sparse (indices + quantized ints + scale).

        :param indices: 1D array of flattened indices
        :param values_int: corresponding integer values
        :param original_shape: shape tuple of the original gradient
        :param scale: scale used during quantization (float)
        :return: dense numpy float array of original_shape
        """
        size = int(np.prod(original_shape))
        dense = np.zeros(size, dtype=float)
        if indices.size > 0:
            dense[indices] = (values_int.astype(float)) * scale
        return dense.reshape(original_shape)

    def decompress_from_dense_int(self, dense_int_vector: np.ndarray, original_shape: Tuple[int, ...], scale: float) -> np.ndarray:
        """
        If aggregator obtains a dense recovered integer vector (via BSGS covering full dimension),
        convert it back to float using scale.

        :param dense_int_vector: 1D integer array length = prod(original_shape)
        """
        assert dense_int_vector.size == np.prod(original_shape)
        return (dense_int_vector.astype(float) * scale).reshape(original_shape)

    # ----------------------
    # Serialization helpers
    # ----------------------
    @staticmethod
    def pack_leaf(miner_address: str, indices: np.ndarray, values_int: np.ndarray, nonce: str) -> bytes:
        """
        Create a deterministic byte representation for a Merkle leaf:
        leaf = keccak256(abi.encodePacked(minerAddress, indices[], values_int[], nonce))
        For portability we create a canonical bytes layout:
            - miner_address (20 bytes, hex string with or without 0x)
            - count (4 bytes unsigned)
            - for each entry: index (8 bytes unsigned big-endian), value (8 bytes signed big-endian)
            - nonce length (2 bytes) + nonce utf-8 bytes
        Return the raw bytes; leaf hash is keccak256 over these bytes (do hashing off-chain).
        """
        addr = miner_address[2:] if miner_address.startswith("0x") else miner_address
        addr_bytes = bytes.fromhex(addr.rjust(40, "0"))
        count = len(indices)
        buf = bytearray()
        buf += addr_bytes
        buf += struct.pack(">I", int(count))
        for i, v in zip(indices, values_int):
            buf += struct.pack(">Q", int(i))  # 8 byte index
            # pack value as signed 8-byte
            buf += struct.pack(">q", int(v))
        nonce_b = nonce.encode("utf-8")
        nb = len(nonce_b)
        buf += struct.pack(">H", nb)
        buf += nonce_b
        return bytes(buf)

    @staticmethod
    def unpack_leaf(raw: bytes):
        """
        Reverse of pack_leaf for verification/debugging.
        Returns (miner_address_hex, indices, values_int, nonce)
        """
        offset = 0
        addr_bytes = raw[offset:offset+20]; offset += 20
        miner_address = "0x" + addr_bytes.hex()
        (count,) = struct.unpack_from(">I", raw, offset); offset += 4
        indices = []
        values = []
        for _ in range(count):
            (idx,) = struct.unpack_from(">Q", raw, offset); offset += 8
            (val,) = struct.unpack_from(">q", raw, offset); offset += 8
            indices.append(idx)
            values.append(val)
        (nb,) = struct.unpack_from(">H", raw, offset); offset += 2
        nonce_b = raw[offset:offset+nb]; offset += nb
        try:
            nonce = nonce_b.decode("utf-8")
        except Exception:
            nonce = nonce_b.hex()
        return miner_address, np.array(indices, dtype=np.int64), np.array(values, dtype=INT_DTYPE), nonce

# ----------------------
# Simple score function
# ----------------------
def calculate_contribution_score_from_sparse(indices: np.ndarray, values_int: np.ndarray, scale: float) -> float:
    """
    Score computed as L2 norm of the float compressed update:
        score = || Delta_i' ||_2

    Because values are quantized, we reconstruct floats using scale and compute norm.
    """
    if indices is None or indices.size == 0:
        return 0.0
    floats = values_int.astype(float) * scale
    return float(np.linalg.norm(floats))

# ----------------------
# Tiny self-test / usage example (run when module executed)
# ----------------------
if __name__ == "__main__":
    # small test
    rng = np.random.default_rng(1234)
    grad = rng.standard_normal(1000) * 0.01  # small gradient
    d = DGC(tau=0.9, max_int=1023)
    idxs, vals_int, scale = d.compress_and_quantize(grad)
    print("kept", idxs.size, "entries; scale", scale)
    dense = d.decompress_from_sparse(idxs, vals_int, grad.shape, scale)
    # Check reconstruction error
    err = np.linalg.norm(grad - dense) / max(1e-12, np.linalg.norm(grad))
    print("rel error:", err)
    # pack leaf
    leaf = DGC.pack_leaf("0x" + "11" * 20, idxs, vals_int, "nonce1")
    print("leaf bytes len", len(leaf))
    miner, i_u, v_u, nonce = DGC.unpack_leaf(leaf)
    assert miner.lower() == "0x" + "11" * 20
    assert np.array_equal(i_u, idxs)
    assert np.array_equal(v_u, vals_int)
    assert nonce == "nonce1"
    print("self-test ok")
