import math
import numpy as np
import sys
import os

# ensure project root on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integration.simulation_runner import setup_environment


def reconstruct_dense_from_miner(miner):
    # miner sets _last_shape, _last_indices, _last_values_int after run_training_round
    shape = miner._last_shape
    size = int(np.prod(shape))
    dense = np.zeros(size, dtype=np.int64)
    idxs = getattr(miner, '_last_indices', None)
    vals = getattr(miner, '_last_values_int', None)
    if idxs is None or vals is None:
        raise RuntimeError('Miner has no last indices/values')
    if len(idxs) > 0:
        dense[idxs] = vals
    return dense


def suggest_chunk_sizes(miners_deltas, weights_y, original_L, start_chunk=256, cap=1<<28, scale_weights=1000):
    # returns largest chunk size (power-of-two multiple of start_chunk) that fits cap
    weight_scaled = [int(round(w * scale_weights)) for w in weights_y]
    # max_int from DGC in simulation is 1023 by default
    # But we compute exact aggregated per-param values from miners_deltas

    def chunk_ok(chunk_size):
        num_chunks = math.ceil(original_L / chunk_size)
        for c in range(num_chunks):
            s = c * chunk_size
            e = min(original_L, (c + 1) * chunk_size)
            # compute aggregated S for this chunk
            agg = np.zeros(e - s, dtype=np.int64)
            for i, arr in enumerate(miners_deltas):
                agg += (weight_scaled[i] * arr[s:e]).astype(np.int64)
            max_abs = int(np.max(np.abs(agg))) if agg.size > 0 else 0
            if max_abs + 16 > cap:
                return False, max_abs
        return True, None

    # Try doubling chunk size starting from start_chunk up to original_L
    chunk = start_chunk
    feasible = start_chunk
    last_max = None
    while chunk <= original_L:
        ok, max_abs = chunk_ok(chunk)
        print(f"Testing chunk_size={chunk}: ok={ok}, max_abs={max_abs}")
        if ok:
            feasible = chunk
            last_max = max_abs
            chunk *= 2
        else:
            break
    return feasible, last_max


if __name__ == '__main__':
    publisher, aggregator, miners, pk_A, web3_client = setup_environment()

    # Create a dummy task id
    task_ID = b'\x00' * 32

    # miners upload proofs (simulate)
    miner_responses = [m.generate_task_response(task_ID) for m in miners]

    # Simulate TP selection locally (avoid on-chain state transitions)
    # Accept miners whose inline metadata passes the simple proof check
    valid_miners = []
    for resp, m in zip(miner_responses, miners):
        meta = resp.get('metadata') or {}
        ds = int(meta.get('dataset_size', 0))
        if ds >= 500:
            valid_miners.append(m)
        else:
            print(f"[TP] Rejected miner {m.address[:8]}... due to small dataset ({ds})")

    if len(valid_miners) == 0:
        # fallback: accept all miners
        valid_miners = miners

    h = len(valid_miners)
    weights_y = [1.0 / h] * h

    # Run one training round for each valid miner to collect deltas
    W_t = publisher.W0
    for m in valid_miners:
        m.run_training_round(W_t, publisher.pk_TP, pk_A, task_ID, 0)

    # Reconstruct dense deltas
    miners_deltas = [reconstruct_dense_from_miner(m) for m in valid_miners]
    original_L = miners_deltas[0].size

    print('\nCollected miner deltas shape:', original_L)
    print('Weights:', weights_y)

    feasible_chunk, example_max_abs = suggest_chunk_sizes(miners_deltas, weights_y, original_L, start_chunk=256, cap=1<<28, scale_weights=1000)

    print(f"\nLargest feasible chunk (power-of-two multiples of 256): {feasible_chunk}")
    if example_max_abs is not None:
        print(f"Example max_abs in last feasible chunk: {example_max_abs}")
    else:
        print("No chunk tested or no data")
