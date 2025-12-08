import numpy as np
import random
import time
import sys
import traceback
import os
import json
from pathlib import Path

# Add project root to path to find local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integration.web3_client import Web3Client
from federated_layer.task_publisher.publisher import TaskPublisher
from federated_layer.clients.miner import Miner
from federated_layer.aggregator.aggregator import Aggregator
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# --- 0. Setup and Initialization ---
def setup_environment():
    """Initializes crypto tools and assigns accounts/roles."""
    
    # Initialize Web3Client
    web3_client = Web3Client() 

    # Explicitly ensure contracts are loaded on the shared client (guard against
    # cases where per-instance initialization left contract attributes None).
    try:
        config_path = Path(__file__).resolve().parent.parent / "blockchain" / "deployment" / "contract_config.json"
        if config_path.exists():
            config = json.loads(open(config_path, 'r').read())
            try:
                web3_client._load_contract('TaskContract', config, config_path.parent, required=True)
                web3_client._load_contract('EscrowContract', config, config_path.parent, required=True)
            except Exception as e:
                print(f"Warning: explicit contract load failed: {e}")
    except Exception as e:
        print(f"Warning: could not read contract config for explicit load: {e}")
    
    # Get test accounts
    accounts = web3_client.w3.eth.accounts
    
    if len(accounts) < 6:
        raise Exception(f"Only {len(accounts)} accounts found. Need at least 6.")

    TP_ADDR = accounts[1]
    AGG_ADDR = accounts[2]
    MINER_ADDRS = accounts[3:6]
    
    # Initialize Placeholder Data
    MODEL_SHAPE = (10, 10)
    initial_model_W0 = np.random.rand(*MODEL_SHAPE)
    validation_set = "simulated_validation_data"

    # Initialize roles (no longer need ndd_fe instance - using module-level functions)
    publisher = TaskPublisher(initial_model_W0, TP_ADDR)
    
    aggregator = Aggregator(initial_model_W0, AGG_ADDR, validation_set, max_rounds=5)
    
    miners = [
        Miner(f"dataset_{i}", addr) for i, addr in enumerate(MINER_ADDRS)
    ]

    # Ensure all components share the same Web3 client (single initialized instance)
    # This prevents multiple clients from attempting to load contracts independently
    # and avoids cases where some instances end up with `None` contracts.
    publisher.web3_client = web3_client
    aggregator.web3_client = web3_client
    for m in miners:
        m.web3_client = web3_client
    # Shared web3_client initialized and attached to components
    
    pk_A = aggregator.pk_A
    print("--- Environment Setup Complete ---")
    return publisher, aggregator, miners, pk_A, web3_client

# --- 1. Orchestration and Simulation ---

def run_healchain_simulation(publisher, aggregator, miners, pk_A, web3_client, publish_params=None):
    
    # --- M1: Task Publishing ---
    if web3_client._mock_mode:
        task_ID = b'\x00' * 32
    else:
        task_ID = web3_client.w3.keccak(text=f"task_{time.time()}")
        
    
    print(f"\n=== HEALCHAIN END-TO-END SIMULATION ===")
    # Print a short hex preview for debugging, but canonical ID will be integer
    try:
        hex_preview = task_ID.hex()[:16]
    except Exception:
        hex_preview = str(task_ID)[:16]
    print(f"Task ID (preview hex): {hex_preview}...")
    run_start_time = time.time()

    # M1: TP interactively provides inputs and executes task commit + reward deposit
    # If `publish_params` provided, use them as defaults to avoid interactive prompts
    publish_params = publish_params or {}
    try:
        acc_req_default = float(publish_params.get('acc_req', 85.0))
    except Exception:
        acc_req_default = 85.0
    try:
        reward_default = float(publish_params.get('reward', 10.0))
    except Exception:
        reward_default = 10.0
    try:
        texp_default = int(publish_params.get('texp', 86400))
    except Exception:
        texp_default = 86400

    # If publish_params provided, run non-interactive publish using those values
    if publish_params:
        try:
            acc_req = float(publish_params.get('acc_req', acc_req_default))
        except Exception:
            acc_req = acc_req_default
        try:
            REWARD_R = float(publish_params.get('reward', reward_default))
        except Exception:
            REWARD_R = reward_default
        try:
            Texp = int(publish_params.get('texp', texp_default))
        except Exception:
            Texp = texp_default
        try:
            nonce_TP = int(publish_params.get('nonceTP', random.randint(1000, 9999)))
        except Exception:
            nonce_TP = random.randint(1000, 9999)

        D = publish_params.get('D', publish_params.get('datasetReq', 'simulated_dataset'))
        L = publish_params.get('L', publish_params.get('initialModelLink', 'classification'))

        # Execute non-interactive publish
        commit_hash, W_current = publisher.publish_task(
            task_ID,
            reward_R=REWARD_R,
            acc_req=acc_req,
            nonce_TP=nonce_TP,
            D=D,
            L=L,
            Texp=Texp
        )
    else:
        acc_req, REWARD_R, Texp, nonce_TP, commit_hash, W_current, D, L = publisher.interactive_publish(
            task_ID,
            default_acc_req=acc_req_default,
            default_reward=reward_default,
            default_texp=texp_default
        )
    
    # --- Miner Discovery Phase: miners upload capability proofs to IPFS ---
    miner_responses = []
    for m in miners:
        resp = m.generate_task_response(task_ID)
        miner_responses.append(resp)

    # --- M2: Miner Selection & Key Derivation ---
    # Let TP verify miner proofs and run PoS selection (no forced aggregator override)
    # Store the round_ctr used to derive sk_FE - miners MUST use the same ctr value
    sk_FE_ctr = 0
    agg_addr_selected, sk_FE, weights_y, valid_miner_addrs = publisher.setup_round(
        task_ID, miner_responses, round_ctr=sk_FE_ctr
    )
    aggregator.set_functional_key(sk_FE)
    pk_TP = publisher.pk_TP
    
    # Filter miners to only those who passed proof verification
    # Preserve the ordering returned by publisher.setup_round (valid_miner_addrs)
    addr_to_miner = {m.address: m for m in miners}
    valid_miners = []
    for addr in valid_miner_addrs:
        m = addr_to_miner.get(addr)
        if m is not None:
            valid_miners.append(m)
    print(f"[SIM] {len(valid_miners)} miners passed verification out of {len(miners)}")
    
    # Ensure the off-chain Aggregator instance uses the PoS-selected address so
    # on-chain `onlyAggregator` checks pass when publishing the final block.
    # The selected address is expected to be one of the node's unlocked accounts
    # (created in `setup_environment`) so node-managed signing will succeed.
    try:
        print(f"[SIM] Setting off-chain Aggregator.address = {agg_addr_selected}")
        aggregator.address = agg_addr_selected
    except Exception as e:
        print(f"[SIM] Warning: failed to set aggregator address: {e}")
    
    print(f"\n--- M2: Aggregator {agg_addr_selected} Selected ---")

    # --- Training Loop (driven by Texp deadline) ---
    W_t = W_current
    status = "RETRAIN"
    start_time = time.time()
    deadline = start_time + int(Texp)

    # Loop until success or Texp exceeded
    while status == "RETRAIN" and time.time() < deadline:
        print(f"\nRound {aggregator.round_ctr + 1} Starting...")
        
        # M3: Only valid miners train (and commit score inside this call)
        # IMPORTANT: Use sk_FE_ctr (the ctr value used to derive sk_FE), NOT aggregator.round_ctr
        # The encryption mask depends on ctr via derive_ri_from_shared, so it must match
        submissions = []
        miner_int_updates = []
        for miner in valid_miners:
            U_i, score_commit, pk_i, score_int, nonce_i = miner.run_training_round(
                W_t, pk_TP, pk_A, task_ID, sk_FE_ctr
            )
            submissions.append((U_i, score_commit, pk_i, score_int, nonce_i))
            # Reconstruct dense integer update from miner's stored sparse metadata
            try:
                shape = getattr(miner, '_last_shape', None)
                idxs = getattr(miner, '_last_indices', None)
                vals = getattr(miner, '_last_values_int', None)
                if shape is None or idxs is None or vals is None:
                    dense = np.zeros(np.prod(W_t.shape), dtype=np.int64)
                else:
                    dense = np.zeros(int(np.prod(shape)), dtype=np.int64)
                    if len(idxs) > 0:
                        dense[idxs] = vals
            except Exception:
                dense = np.zeros(int(np.prod(W_t.shape)), dtype=np.int64)
            miner_int_updates.append(dense)

        # M4: Aggregation
        # `acc_req` returned from the TP prompt is a percentage (e.g. 82.76).
        # Aggregator.evaluate_model returns a fractional accuracy (0.82..), so convert here.
        acc_req_fraction = float(acc_req) / 100.0
        status, result = aggregator.secure_aggregate_and_evaluate(
            task_ID, submissions, pk_TP, weights_y, acc_req_fraction, miner_int_updates=miner_int_updates
        )
        W_t = aggregator.W_current
        
        if status == "AWAITING_VERIFICATION":
            # result contains (W_new, acc_calc, score_commits)
            W_new, acc_calc, score_commits = result
            
            # Form Candidate Block Payload
            participant_addrs = [m.address for m in valid_miners]
            candidate_block_payload = aggregator.form_candidate_block(
                task_ID, W_new, acc_calc, score_commits, participant_addrs
            )
            break
        elif status == "FAILED_MAX_ROUNDS":
            print(f"\n❌ Task Failed: Max rounds reached.")
            return

    # If loop exited due to deadline expiration and not success
    if status == "RETRAIN" and time.time() >= deadline:
        print(f"\n❌ Task Failed: Texp ({Texp} seconds) expired before reaching target accuracy.")
        return

    # --- M5 & M6: Consensus and Block Publishing ---
    if status == "AWAITING_VERIFICATION":
        print(f"\n--- M5: Verifying Candidate Block ---")
        
        # Simulate valid miners verifying the block
        votes = []
        for miner in valid_miners:
            is_valid = miner.verify_candidate_block(candidate_block_payload, task_ID)
            votes.append(is_valid)
            
        if all(votes):
            print("✅ Consensus Reached: Block Verified.")
            
            # M6: Publish the final block on-chain
            aggregator.publish_final_block(candidate_block_payload)
            
            # --- M7: Reveals & Rewards ---
            print("\n--- M7: Reveals & Rewards ---")
            
            # 1. TP Reveal
            publisher.reveal_task(task_ID, acc_req, nonce_TP) # use the same nonceTP provided at M1
            
            # 2. Miner Score Reveals
            print(f"--- Executing Miner Score Reveals ---")
            for miner in valid_miners:
                # Use the Miner class method we created
                miner.reveal_score_on_chain(task_ID)
                
            print("✅ All valid miners revealed scores.")

            # 3. Final Reward Distribution
            print("--- Distributing Rewards ---")
            web3_client.send_transaction(
                web3_client.escrow_contract,
                'distributeRewards',
                task_ID
            )
            print("\n✅ Task Complete: Rewards distributed.")

            # Save a detailed JSON summary for later visualization/analysis
            try:
                run_end_time = time.time()
                duration = run_end_time - run_start_time

                cb = candidate_block_payload
                candidate = {
                    'modelHash': cb.get('modelHash').hex() if isinstance(cb.get('modelHash'), (bytes, bytearray)) else cb.get('modelHash'),
                    'modelLink': cb.get('modelLink'),
                    'accCalc_basis_points': cb.get('accCalc'),
                    'accCalc': cb.get('accCalc') / 10000.0 if cb.get('accCalc') is not None else None,
                    'participants': cb.get('participants', []),
                    'scoreCommits': [c.hex() if isinstance(c, (bytes, bytearray)) else c for c in cb.get('scoreCommits', [])],
                    'aggregator': cb.get('aggregatorAddress'),
                    'signature': cb.get('signature')
                }

                miners_info = []
                for m in valid_miners:
                    # miners may have a reveal_data attribute mapping task_id hex to details
                    reveal_map = getattr(m, 'reveal_data', {})
                    # try both hex key and integer key for compatibility
                    d = {}
                    if isinstance(reveal_map, dict):
                        d = reveal_map.get(task_ID.hex(), {}) or reveal_map.get(str(int.from_bytes(task_ID, 'big')), {})
                    miners_info.append({
                        'address': getattr(m, 'address', None),
                        'score_commit': d.get('score_commit'),
                        'commit_timestamp': d.get('commit_timestamp'),
                        'revealed_score': d.get('score_int'),
                        'reveal_nonce': d.get('nonce_i'),
                        'reveal_timestamp': d.get('reveal_timestamp')
                    })

                results = {
                    # canonical task id as integer for downstream UI/DB
                    'task_id': int.from_bytes(task_ID, 'big'),
                    'final_accuracy': candidate.get('accCalc'),
                    'candidate_block': candidate,
                    'miners': miners_info,
                    'run_start': run_start_time,
                    'run_end': run_end_time,
                    'duration_seconds': duration
                }

                out_path = Path(__file__).resolve().parent.parent / "simulation_results.json"
                with open(out_path, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Results saved to {out_path}")
            except Exception as _:
                print(f"Warning: failed to save simulation results: {_}")
        else:
            print("❌ Consensus Failed: Block rejected by miners.")

# --- Execution ---
if __name__ == "__main__":
    try:
        publisher, aggregator, miners, pk_A, web3_client = setup_environment()
        run_healchain_simulation(publisher, aggregator, miners, pk_A, web3_client)
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        traceback.print_exc(file=sys.stdout)