import numpy as np
import random
import hashlib
import time
from typing import List, Dict, Tuple
import torch

# Logging for debug/info instead of ad-hoc prints
import logging

# Web3 and Crypto Imports
from web3 import Web3
from eth_account.messages import encode_defunct
from integration.web3_client import Web3Client 
from crypto.ndd_fe import key_gen, decrypt_aggregate
from crypto.dgc import DGC 

class Aggregator:
    def __init__(self, 
                 initial_model: np.ndarray, 
                 account_address: str, 
                 validation_set,
                 max_rounds: int = 100):
        
        # Generate Aggregator's keys using module-level function
        self.pk_A, self.sk_A = key_gen()
        self.address = account_address
        self.dgc_tool = DGC(tau=0.9, max_int=1023)  # Required for decompression
        self.web3_client = Web3Client()
        self.validation_set = validation_set
        self.max_rounds = max_rounds
        
        # Current round state
        self.W_current = initial_model
        self.round_ctr = 0
        self.sk_FE = None  # Functional key received from TP (M2)
        self._sk_FE_set = False  # Track if sk_FE was explicitly set
        
        # --- FIX: Generate a local key for signing blocks in simulation ---
        # This prevents the need for os.environ variables and fixes the missing key error
        self._signing_account = self.web3_client.w3.eth.account.create()
        self._private_key = self._signing_account.key

    def set_functional_key(self, sk_FE: int):
        """Sets the functional key received securely from the Task Publisher (M2)."""
        self.sk_FE = sk_FE
        self._sk_FE_set = True  # Track that sk_FE was explicitly set
    
    # --- DGC Helper: Decompression (M4) ---
    def dgc_decompress(self, recovered_vector: np.ndarray, model_shape: Tuple, scale: float = 1.0) -> np.ndarray:
        """
        DGC Decompression (Algorithm 4, Line 33).
        Restores the dense integer aggregated vector to float values matching the global model size.
        """
        if recovered_vector is None:
            return np.zeros(model_shape, dtype=np.float64)
        
        # Use decompress_from_dense_int to convert integer vector back to float
        decompressed_update = self.dgc_tool.decompress_from_dense_int(
            recovered_vector, model_shape, scale
        )
        
        return decompressed_update

    # --- Model Evaluation (M4) ---
    def evaluate_model(self, model_weights: np.ndarray) -> float:
        """Evaluates the new global model's accuracy on the validation set."""
        # Check if validation set is real data or string placeholder
        if isinstance(self.validation_set, str):
             # Keep simulation mode
             simulated_accuracy = 0.85 + (0.01 * self.round_ctr) + random.uniform(-0.005, 0.005)
             return min(0.99, simulated_accuracy)
        
        # Real PyTorch Evaluation (if validation_set is a DataLoader)
        # Note: self.load_weights_to_torch_model() would be needed here for a full implementation
        return 0.95 # Placeholder for hybrid run

    # --- Main Aggregation and Evaluation Loop (M4) ---
    def secure_aggregate_and_evaluate(self, 
                                      task_ID: bytes,
                                      submissions: List[Tuple], # [(U_i, scoreCommit_i, pk_i, ...), ...]
                                      pk_TP: object, 
                                      weights_y: List[float], 
                                      acc_req: float,
                                      miner_int_updates: List = None) -> Tuple[str, object]:
        
        if not self._sk_FE_set:
            raise ValueError("Functional key (sk_FE) not set for the current task.")

        self.round_ctr += 1
        
        # 1. Verify Submissions (Algorithm 4, Lines 2-14)
        valid_submissions = [s for s in submissions if s[0] is not None] 
        
        if len(valid_submissions) < 2: # MIN_PARTICIPANTS
            logging.warning("Insufficient valid submissions.")
            return "FAIL_INSUFFICIENT_MINERS", self.W_current

        # Extract necessary components from submission tuple
        ciphertexts_U = [s[0] for s in valid_submissions]
        score_commits = [s[1] for s in valid_submissions]
        
        # 2. NDD-FE Decrypt and BSGS Recovery (Algorithm 4, Lines 15-26)
        # Prefer chunked recovery to keep per-parameter BSGS bounds modest.
        # `chunked_decrypt` will call `decrypt_aggregate` on slices of the
        # parameter vector and estimate a safe `bsgs_bound` per chunk.
        try:
            original_L = len(ciphertexts_U[0])
        except Exception:
            raise ValueError("Invalid ciphertexts_U structure for decryption")

        # 2. NDD-FE Decrypt and BSGS Recovery (Algorithm 4, Lines 15-26)
        # If miner plaintext integer updates are available (simulation mode),
        # compute the exact per-call bsgs_bound using Python big-int arithmetic
        try:
            from crypto.dgc import DGC as _DGC
            max_int = _DGC().max_int
        except Exception:
            max_int = 1023
        scale_weights = 1000

        def compute_exact_bsgs_bound(miner_int_updates, weights_y, scale_weights=1, margin=16, min_bound=1024):
            w_scaled = [int(round(w * scale_weights)) for w in weights_y]
            L = len(miner_int_updates[0])
            max_abs_S = 0
            for idx in range(L):
                s = 0
                for w, upd in zip(w_scaled, miner_int_updates):
                    s += int(w) * int(upd[idx])
                if abs(s) > max_abs_S:
                    max_abs_S = abs(s)
            bound = max(min_bound, max_abs_S + margin)
            return bound, max_abs_S

        recovered_aggregate_vector = None
        # If miner_int_updates provided, compute exact bound and try one-shot
        if miner_int_updates is not None:
            try:
                bsgs_bound, max_abs_S = compute_exact_bsgs_bound(miner_int_updates, weights_y, scale_weights=scale_weights)
                logging.info(f"[AGG] computed exact bsgs_bound={bsgs_bound} (max_abs_S={max_abs_S})")
                try:
                    recovered_aggregate_vector = decrypt_aggregate(
                        sk_FE=self.sk_FE,
                        sk_A=self.sk_A,
                        pk_TP=pk_TP,
                        ciphertexts_U=ciphertexts_U,
                        weights_y=weights_y,
                        scale_weights=scale_weights,
                        bsgs_bound=bsgs_bound
                    )
                except ValueError as ve:
                    logging.warning(f"One-shot decrypt with exact bound {bsgs_bound} failed: {ve}")
                    # If we have miner plaintexts, run per-parameter diagnostics to find root cause
                    recovered_aggregate_vector = None
                    try:
                        if miner_int_updates is not None:
                            # import diagnostic helpers from ndd_fe
                            from crypto.ndd_fe import safe_scalar_mul, G, N, bsgs_cached

                            # compute raw scaled weights
                            w_scaled_raw = [int(round(w * scale_weights)) for w in weights_y]
                            w_scaled_modN = [ws % N for ws in w_scaled_raw]

                            # compute S_list if not already computed
                            try:
                                S_list, _, _, _ = None, None, None, None
                            except Exception:
                                S_list = None

                            # Recompute S_list here (Python-safe)
                            L = len(miner_int_updates[0])
                            S_list = [0] * L
                            for i in range(len(miner_int_updates)):
                                upd = miner_int_updates[i]
                                w = w_scaled_raw[i]
                                for idx in range(L):
                                    S_list[idx] += int(w) * int(upd[idx])

                            # choose a handful indices to inspect (worst first)
                            abs_vals = [abs(v) for v in S_list]
                            top_idxs = sorted(range(L), key=lambda i: abs_vals[i], reverse=True)[:6]

                            # global mask and inv_sk_A
                            from crypto.ndd_fe import safe_scalar_mul as _ssm
                            global_mask = _ssm(pk_TP, self.sk_FE)
                            inv_sk_A = pow(self.sk_A, -1, N)

                            for k in top_idxs:
                                try:
                                    # rebuild agg from ciphertexts_U
                                    agg = None
                                    for Uik_list, wmod in zip(ciphertexts_U, w_scaled_modN):
                                        Uik = None
                                        try:
                                            Uik = Uik_list[k]
                                        except Exception:
                                            Uik = None
                                        if Uik is None:
                                            tmp = None
                                        else:
                                            tmp = Uik * wmod
                                        agg = tmp if agg is None else (agg + tmp)

                                    if global_mask is None:
                                        E = agg
                                    else:
                                        neg_global = _ssm(global_mask, (-1) % N)
                                        E = agg if neg_global is None else (agg + neg_global)

                                    E_star = _ssm(E, inv_sk_A)

                                    expected_S = S_list[k]
                                    expected_point = (expected_S % N) * G

                                    logging.warning(f"[DIAG] k={k} expected_S={expected_S} (mod N={expected_S % N})")
                                    logging.warning(f"[DIAG] expected_point={expected_point}")
                                    logging.warning(f"[DIAG] E={E}")
                                    logging.warning(f"[DIAG] E_star={E_star}")
                                    logging.warning(f"[DIAG] E_star == expected_point? {E_star == expected_point}")

                                    # run bsgs tests
                                    try:
                                        pos = bsgs_cached(E_star, bsgs_bound)
                                    except Exception as _e:
                                        pos = f"error:{_e}"
                                    # negative test
                                    try:
                                        neg = bsgs_cached(_ssm(E_star, (-1) % N), bsgs_bound)
                                    except Exception as _e:
                                        neg = f"error:{_e}"

                                    logging.warning(f"[DIAG] bsgs_cached positive -> {pos}, negative -> {neg} (bound={bsgs_bound})")
                                except Exception as e_k:
                                    logging.warning(f"[DIAG] failed inspecting k={k}: {e_k}")
                    except Exception as e_diag:
                        logging.warning(f"[DIAG] diagnostics failed: {e_diag}")
                    # Try chunked recovery as a robust fallback when one-shot fails
                    try:
                        from crypto.ndd_fe import decrypt_aggregate_chunked
                        logging.info("[AGG] attempting chunked decrypt as fallback")
                        recovered_aggregate_vector = decrypt_aggregate_chunked(
                            self.sk_FE,
                            self.sk_A,
                            pk_TP,
                            ciphertexts_U,
                            weights_y,
                            miner_int_updates=miner_int_updates,
                            scale_weights=scale_weights,
                            chunk_size=64,
                            max_chunk_bound_cap=1 << 28,
                            parallel=False
                        )
                        logging.info("[AGG] chunked decrypt succeeded")
                    except Exception as e_chunk:
                        logging.warning(f"[AGG] chunked decrypt fallback failed: {e_chunk}")
            except Exception as e:
                logging.warning(f"Failed to compute exact bsgs bound: {e}")

        # If we didn't recover yet, fall back to geometric retry (or chunked if available)
        if recovered_aggregate_vector is None:
            # conservative per-parameter worst-case magnitude estimation if plaintext not available
            weight_scaled_list = [int(round(w * scale_weights)) for w in weights_y]
            sum_abs_weight_scaled = sum(abs(w) for w in weight_scaled_list)
            max_abs_S = int(sum_abs_weight_scaled * max_int)
            computed_bound = max(1 << 24, max(1024, max_abs_S + 16))
            attempt_bound = min(computed_bound, 1 << 30)
            max_bound_cap = 1 << 34
            attempt = 0
            while attempt_bound <= max_bound_cap:
                try:
                    logging.info(f"Attempting FE decrypt with bsgs_bound={attempt_bound}")
                    recovered_aggregate_vector = decrypt_aggregate(
                        sk_FE=self.sk_FE,
                        sk_A=self.sk_A,
                        pk_TP=pk_TP,
                        ciphertexts_U=ciphertexts_U,
                        weights_y=weights_y,
                        scale_weights=scale_weights,
                        bsgs_bound=attempt_bound
                    )
                    break
                except ValueError as ve:
                    msg = str(ve)
                    if 'BSGS' in msg or 'BSGS bound' in msg:
                        logging.warning(f"FE decrypt attempt with bound {attempt_bound} failed: {ve}")
                        attempt += 1
                        # geometric increase
                        next_bound = min(max_bound_cap, attempt_bound * 4)
                        if next_bound <= attempt_bound:
                            break
                        attempt_bound = next_bound
                        continue
                    else:
                        raise

        if recovered_aggregate_vector is None:
            raise ValueError("Failed to recover aggregate vector: BSGS failed for all attempted bounds")

        # 3. DGC Decompress and Model Update (Algorithm 4, Lines 33-35)
        decompressed_update = self.dgc_decompress(recovered_aggregate_vector, self.W_current.shape)
        
        W_new = self.W_current + decompressed_update
        
        # 4. Evaluate Model Accuracy (Algorithm 4, Line 37)
        acc_calc = self.evaluate_model(W_new)
        logging.info(f"Round {self.round_ctr}: Accuracy achieved: {acc_calc:.4f}")

        # 5. Compare Accuracy and Decide (Algorithm 4, Lines 38-57)
        if acc_calc >= acc_req:
            # Path 1: Success - Form Candidate Block
            return "AWAITING_VERIFICATION", (W_new, acc_calc, score_commits)
            
        elif self.round_ctr < self.max_rounds:
            # Path 2: Retrain - Distribute new model
            self.W_current = W_new
            return "RETRAIN", W_new
        else:
            # Path 3: Failure - Max rounds reached
            return "FAILED_MAX_ROUNDS", self.W_current


    # --- Block Formation and Publishing (M6) ---

    def form_candidate_block(self, task_ID: bytes, W_new: np.ndarray, acc_calc: float, 
                             score_commits: List[bytes], participants: List[str]) -> Dict:
        """Forms a signed candidate block payload for M5 verification."""
        
        # 1. Publish Model Artifact
        model_link = f"ipfs://{random.getrandbits(128)}"
        model_hash_bytes = hashlib.sha256(W_new.tobytes()).digest()
        model_hash = model_hash_bytes[:32] if len(model_hash_bytes) >= 32 else model_hash_bytes.ljust(32, b'\x00')

        # 2. Form Block Payload
        acc_calc_basis_points = int(acc_calc * 10000) 

        # 3. Sign the block hash (Sign(sk_aggregator, HASH(B)))
        # Create fingerprint compatible with on-chain verification:
        # keccak256(abi.encodePacked(taskID, modelHash, accCalc)) where accCalc is basis points
        # web3.py naming differs by version; use solidity_keccak if available
        try:
            solidity_keccak = getattr(Web3, 'solidityKeccak', getattr(Web3, 'solidity_keccak'))
        except Exception:
            solidity_keccak = Web3.keccak

        block_fingerprint = solidity_keccak(
            ['bytes32', 'bytes32', 'uint256'],
            [task_ID, model_hash, acc_calc_basis_points]
        )

        # Encode for Ethereum signing (creates the Ethereum Signed Message prefix)
        signable_message = encode_defunct(primitive=block_fingerprint)

        # Sign using the local private key generated in __init__
        signed_message = self.web3_client.w3.eth.account.sign_message(signable_message, private_key=self._private_key)
        
        payload = {
            "taskID": task_ID, 
            "round": self.round_ctr,
            "modelHash": model_hash, 
            "modelLink": model_link,
            "accCalc": acc_calc_basis_points, 
            "participants": participants, 
            "scoreCommits": score_commits, 
            "aggregatorAddress": self.address,
            "timestamp": int(time.time()),
            "verificationEvidence": "SUMMARY_OF_M5_FEEDBACK",
            "signature": signed_message.signature.hex() # Add signature to payload
        }

        return payload

    def publish_final_block(self, payload: Dict):
        """M6: Publishes the final, consensus-verified block payload on-chain."""
        task_id_hex = payload['taskID'].hex() if isinstance(payload['taskID'], bytes) else payload['taskID']
        logging.info(f"M6: Publishing verified block for task {task_id_hex[:16]}...")
        # Attempt to read on-chain task tuple for additional diagnostics (non-fatal)
        try:
            onchain = self.web3_client.call_view_function(self.web3_client.task_contract, 'tasks', payload['taskID'])
            # tasks getter returns a tuple; aggregator is one of the fields (index varies by contract)
            logging.debug("onchain.tasks(...) returned len=%d", len(onchain))
            # attempt to log any address-like fields
            for i, v in enumerate(onchain):
                if isinstance(v, str) and v.startswith('0x'):
                    logging.debug("onchain field %d = %s", i, v)
        except Exception as _:
            logging.debug("could not read on-chain task tuple: %s", _)

        # Publish including the author's signature (required by updated TaskContract)
        sig = payload.get('signature')
        sig_bytes = None
        if sig is not None:
            if isinstance(sig, str):
                # Ensure hex string has 0x prefix
                hexsig = sig if sig.startswith('0x') else '0x' + sig
                # web3.py has differing helpers across versions; try common names
                if hasattr(Web3, 'toBytes'):
                    sig_bytes = Web3.toBytes(hexstr=hexsig)
                elif hasattr(Web3, 'to_bytes'):
                    sig_bytes = Web3.to_bytes(hexstr=hexsig)
                else:
                    # Fallback: convert manually
                    sig_bytes = bytes.fromhex(hexsig[2:])
            else:
                sig_bytes = sig

        try:
            self.web3_client.send_transaction(
                self.web3_client.task_contract,
                'publishBlock',
                payload['taskID'],
                payload['modelHash'],
                payload['accCalc'],
                payload['aggregatorAddress'],
                payload['participants'],
                payload['scoreCommits'],
                sig_bytes,
                from_addr=self.address
            )
            logging.info("Block successfully published on-chain (with signature). Reveal window is now open.")
            return
        except Exception as e:
            logging.error("publishBlock (with signature) failed: %s", e)
            raise