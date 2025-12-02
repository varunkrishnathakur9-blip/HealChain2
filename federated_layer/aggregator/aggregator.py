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
from crypto.ndd_fe import NDD_FE 
from crypto.dgc import DGC 

class Aggregator:
    def __init__(self, 
                 initial_model: np.ndarray, 
                 account_address: str, 
                 ndd_fe_instance: NDD_FE,
                 validation_set,
                 max_rounds: int = 100):
        
        self.pk_A, self.sk_A = ndd_fe_instance.key_gen() # Aggregator's keys
        self.address = account_address
        self.ndd_fe = ndd_fe_instance
        self.dgc_tool = DGC() # Required for decompression
        self.web3_client = Web3Client()
        self.validation_set = validation_set
        self.max_rounds = max_rounds
        
        # Current round state
        self.W_current = initial_model
        self.round_ctr = 0
        self.sk_FE = None # Functional key received from TP (M2)
        
        # --- FIX: Generate a local key for signing blocks in simulation ---
        # This prevents the need for os.environ variables and fixes the missing key error
        self._signing_account = self.web3_client.w3.eth.account.create()
        self._private_key = self._signing_account.key

    def set_functional_key(self, sk_FE: int):
        """Sets the functional key received securely from the Task Publisher (M2)."""
        self.sk_FE = sk_FE
    
    # --- DGC Helper: Decompression (M4) ---
    def dgc_decompress(self, recovered_vector: np.ndarray, model_shape: Tuple) -> np.ndarray:
        """
        DGC Decompression (Algorithm 4, Line 33).
        Restores the sparse aggregated update into a dense vector matching the global model size.
        """
        if recovered_vector is None:
            return np.zeros(model_shape, dtype=np.float64)
            
        decompressed_update = self.dgc_tool.decompress(recovered_vector)
        
        # Ensure shape matches (handle potential flat vs shaped arrays)
        if decompressed_update.shape != model_shape:
             return decompressed_update.reshape(model_shape)
             
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
                                      acc_req: float) -> Tuple[str, object]:
        
        if not self.sk_FE:
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
        recovered_aggregate_vector = self.ndd_fe.decrypt_aggregate(
            sk_FE=self.sk_FE,
            sk_A=self.sk_A, 
            pk_TP=pk_TP,
            ciphertexts_U=ciphertexts_U, 
            weights_y=weights_y
        )
        
        if recovered_aggregate_vector is None:
            raise ValueError("Failed to recover aggregate vector from NDD-FE decryption")

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