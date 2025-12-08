import sys
import os
import numpy as np

# ensure project root on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integration.simulation_runner import setup_environment


def reconstruct_dense_from_miner(miner):
    shape = getattr(miner, '_last_shape', None)
    idxs = getattr(miner, '_last_indices', None)
    vals = getattr(miner, '_last_values_int', None)
    if shape is None or idxs is None or vals is None:
        raise RuntimeError('Miner has no last indices/values')
    size = int(np.prod(shape))
    dense = np.zeros(size, dtype=np.int64)
    if len(idxs) > 0:
        dense[idxs] = vals
    return dense


def compute_S_exact(miner_int_updates, weights, scale_weights=1, top_n=20):
    w_scaled = [int(round(w * scale_weights)) for w in weights]
    L = miner_int_updates[0].size
    S = [0] * L
    for i in range(len(miner_int_updates)):
        upd = miner_int_updates[i]
        w = w_scaled[i]
        for idx in range(L):
            S[idx] += int(w) * int(upd[idx])
    abs_vals = [abs(v) for v in S]
    max_abs = max(abs_vals) if abs_vals else 0
    max_idx = abs_vals.index(max_abs) if abs_vals else None
    sorted_idx = sorted(range(L), key=lambda i: abs_vals[i], reverse=True)
    return S, max_abs, max_idx, sorted_idx[:top_n]


def per_miner_contribs(miner_int_updates, weights, scale_weights=1, idx_list=None):
    w_scaled = [int(round(w * scale_weights)) for w in weights]
    if idx_list is None:
        idx_list = [0]
    rows = []
    for idx in idx_list:
        row = []
        for i in range(len(miner_int_updates)):
            contrib = int(w_scaled[i]) * int(miner_int_updates[i][idx])
            row.append((i, int(miner_int_updates[i][idx]), w_scaled[i], contrib))
        rows.append((idx, row))
    return rows


if __name__ == '__main__':
    print('Setting up environment (no on-chain transactions will be performed)')
    publisher, aggregator, miners, pk_A, web3_client = setup_environment()

    # Prepare a fake task id
    task_ID = b'\x00' * 32
    W_t = publisher.W0

    # Run one training round per miner and collect dense deltas and ciphertexts
    valid_miners = miners
    ciphertexts_U = []
    for m in valid_miners:
        try:
            ret = m.run_training_round(W_t, publisher.pk_TP, pk_A, task_ID, 0)
            if ret is None:
                print(f'Warning: miner.run_training_round returned None for {m.address}')
            else:
                U_i = ret[0]
                ciphertexts_U.append(U_i)
        except Exception as e:
            print(f'Warning: miner.run_training_round failed for {m.address}: {e}')

    miners_deltas = []
    for i, m in enumerate(valid_miners):
        try:
            dense = reconstruct_dense_from_miner(m)
            miners_deltas.append(dense)
        except Exception as e:
            print(f'Error reconstructing miner {i} delta: {e}')
            raise

    L = miners_deltas[0].size
    print(f'Collected {len(miners_deltas)} miner deltas; vector length L={L}')

    # Print per-miner ranges and dtypes
    import numpy as _np
    for i, d in enumerate(miners_deltas):
        print(f'[DIAG] miner {i}: dtype={getattr(d, "dtype", None)} len={len(d)} min={int(_np.min(d))} max={int(_np.max(d))}')

    # Use weights uniform for valid miners
    h = len(miners_deltas)
    weights_y = [1.0 / h] * h

    for scale_weights in [1, 1000]:
        print('\n=== Diagnostics for scale_weights=', scale_weights, '===')
        S, max_abs, max_idx, top_idxs = compute_S_exact(miners_deltas, weights_y, scale_weights=scale_weights, top_n=20)
        print(f'[DIAG] scale_weights={scale_weights} -> max_abs_S={max_abs} at index {max_idx}')
        print('[DIAG] Top indices by abs(S):', top_idxs)
        # print top offenders
        for idx in top_idxs:
            print(f'  idx {idx}: S={S[idx]}')
        # Show per-miner contributions for top indices
        rows = per_miner_contribs(miners_deltas, weights_y, scale_weights=scale_weights, idx_list=top_idxs[:5])
        for idx, row in rows:
            print(f'Contributions for idx {idx}:')
            for (mi, upd, wscaled, contrib) in row:
                print(f'  miner{mi}: upd={upd}, w_scaled={wscaled}, contrib={contrib}')

    # --- EC point reconstruction check (C2) using scale_weights=1000 ---
    try:
        from crypto.ndd_fe import safe_scalar_mul, G, N, key_derive
        scale_weights_used = 1000
        print('\n=== EC Reconstruction Check (C2) ===')
        weight_scaled_modN = [int(round(w * scale_weights_used)) % N for w in weights_y]
        weight_scaled_raw = [int(round(w * scale_weights_used)) for w in weights_y]
        print('[CHECK] scale_weights_used =', scale_weights_used)
        print('[CHECK] weight_scaled (mod N) =', weight_scaled_modN)
        print('[CHECK] weight_scaled_raw =', weight_scaled_raw)

        # compute S_list with exact Python ints
        S_list, _, max_idx_exact, top_idxs_exact = compute_S_exact(miners_deltas, weights_y, scale_weights=scale_weights_used, top_n=20)
        print(f'[CHECK] computed max_abs_S at index {max_idx_exact}; top_idxs={top_idxs_exact}')

        # Rebuild sk_FE (as TP would) to compute global mask
        miner_pks = [m.pk_i for m in valid_miners]
        sk_FE = key_derive(publisher.sk_TP, miner_pks, weights_y, 0, publisher._normalize_task_id(task_ID), scale_weights=scale_weights_used)

        # pick worst index k
        k = max_idx_exact if max_idx_exact is not None else 0
        print(f'[CHECK] Comparing E_star vs expected_point for worst index k={k}')

        # Rebuild agg from ciphertexts_U
        agg = None
        for Uik_list, wmod in zip(ciphertexts_U, weight_scaled_modN):
            try:
                Uik = Uik_list[k]
            except Exception:
                Uik = None
            if Uik is None:
                tmp = None
            else:
                tmp = Uik * wmod
            agg = tmp if agg is None else (agg + tmp)

        # compute global mask and remove it
        global_mask = safe_scalar_mul(publisher.pk_TP, sk_FE)
        if global_mask is None:
            E = agg
        else:
            neg_global = safe_scalar_mul(global_mask, (-1) % N)
            E = agg if neg_global is None else (agg + neg_global)

        # inv_sk_A from aggregator
        inv_sk_A = pow(aggregator.sk_A, -1, N)
        E_star_rebuilt = safe_scalar_mul(E, inv_sk_A)

        expected_S = S_list[k]
        expected_point = (expected_S % N) * G

        print('[CHECK_REBUILD] E_star_rebuilt:', E_star_rebuilt)
        print('[CHECK_REBUILD] expected_point:', expected_point)
        print('[CHECK_REBUILD] equality:', E_star_rebuilt == expected_point)
    except Exception as e:
        print('[CHECK] EC reconstruction check failed:', e)

    print('\nDiagnostics complete.')
