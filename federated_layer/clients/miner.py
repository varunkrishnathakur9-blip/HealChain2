import os
import sys
import numpy as np
import random
import time
from typing import Tuple, Dict, List
from eth_utils import keccak
from web3 import Web3

# Ensure the project root is on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crypto.dgc import DGC, calculate_contribution_score_from_sparse
from crypto.ndd_fe import key_gen, encrypt_integer_vector
from integration.web3_client import Web3Client
from integration.ipfs_handler import IPFSHandler

class Miner:
    def __init__(self, data_set, address: str, private_key: str = None):
        """
        :param private_key: Required for signing on-chain transactions.
        """
        # Generate miner keys using module-level function
        self.pk_i, self.sk_i = key_gen()
        self.address = address
        self.private_key = private_key 
        self.data_set = data_set
        
        self.dgc_tool = DGC(tau=0.9, max_int=1023)
        self.web3_client = Web3Client()
        # IPFS handler for publishing miner capability proofs
        try:
            self.ipfs = IPFSHandler()
        except Exception:
            self.ipfs = None
        self.residual = None
        
        # Store reveal data for M7
        self.reveal_data = {} 

    # M3: Local Model Training, Compression, Encryption, and Commit
    def run_training_round(self, 
                           W_t: np.ndarray, 
                           pk_TP, 
                           pk_A, 
                           task_ID: bytes, 
                           round_ctr: int) -> Tuple[object, bytes, object, int, int]:

        # 1. Local Training (Simulated)
        raw_gradient = np.random.randn(*W_t.shape) * 0.01

        # 2. DGC Compression - returns (indices, values_int, scale)
        indices, values_int, scale = self.dgc_tool.compress_and_quantize(raw_gradient)
        
        # Store compression metadata for encryption
        self._last_indices = indices
        self._last_values_int = values_int
        self._last_scale = scale
        self._last_shape = raw_gradient.shape

        # 3. Calculate Contribution Score using sparse representation
        score = calculate_contribution_score_from_sparse(indices, values_int, scale)
        score_int = int(score * 100)
        
        # 4. Score Commit
        nonce_i = random.randint(1000000, 9999999)
        
        # Store securely for M7
        self.reveal_data[task_ID.hex()] = {
            'score_int': score_int,
            'nonce_i': nonce_i
        }
        
        # Packed: uint256(score) + uint256(nonce) + bytes32(taskID) + address(miner)
        miner_addr_bytes = bytes.fromhex(self.address[2:]) if self.address.startswith("0x") else bytes.fromhex(self.address)
        
        packed_data = (
            score_int.to_bytes(32, 'big') +
            nonce_i.to_bytes(32, 'big') +
            task_ID +
            miner_addr_bytes
        )
        score_commit = keccak(packed_data)

        # Record commit hex and timestamp for later export/verification
        try:
            self.reveal_data[task_ID.hex()]['score_commit'] = score_commit.hex()
            self.reveal_data[task_ID.hex()]['commit_timestamp'] = time.time()
        except Exception:
            # ensure reveal_data present
            self.reveal_data[task_ID.hex()] = {
                'score_int': score_int,
                'nonce_i': nonce_i,
                'score_commit': score_commit.hex(),
                'commit_timestamp': time.time()
            }

        # Store commit locally; the Aggregator will include these commits
        # in the on-chain `publishBlock` call. The contract does not define
        # a per-miner `commitScore` function, so committing locally preserves
        # the anti-free-riding commitment for the simulation.
        print(f"[Miner {self.address[:8]}..] Storing score commit locally (will be included by Aggregator)...")

        # 5. Encrypt with NDD-FE using module-level function
        # Convert sparse values to dense integer vector for encryption
        dense_int_delta = np.zeros(np.prod(self._last_shape), dtype=np.int64)
        if len(indices) > 0:
            dense_int_delta[indices] = values_int
        
        U_i = encrypt_integer_vector(
            sk_miner=self.sk_i,
            pk_TP=pk_TP,
            pk_A=pk_A,
            int_delta=dense_int_delta,
            ctr=round_ctr,
            task_id=task_ID,
        )

        # Return the plaintext dense integer delta as last element to allow
        # simulation-only fallbacks (aggregator can use this if FE decryption
        # fails due to BSGS bounds). This does not affect on-chain flow.
        return U_i, score_commit, self.pk_i, score_int, nonce_i

    # M5: Miner Verification Feedback
    def verify_candidate_block(self, block_data: Dict, task_ID: bytes) -> bool:
        print(f"[Miner {self.address[:8]}..] Verifying Block for Task {task_ID.hex()[:8]}...")
        
        my_data = self.reveal_data.get(task_ID.hex())
        if not my_data:
            return False
            
        # Reconstruct my commit
        score_int = my_data['score_int']
        nonce_i = my_data['nonce_i']
        miner_addr_bytes = bytes.fromhex(self.address[2:])
        
        packed_data = (
            score_int.to_bytes(32, 'big') +
            nonce_i.to_bytes(32, 'big') +
            task_ID +
            miner_addr_bytes
        )
        expected_commit = keccak(packed_data)
        
        # Check against block's list
        block_commits = block_data.get('scoreCommits', [])
        
        is_included = False
        for c in block_commits:
            # Handle both bytes and hex string formats
            if c == expected_commit or c == expected_commit.hex() or (hasattr(c, 'hex') and c.hex() == expected_commit.hex()):
                is_included = True
                break
        
        if not is_included:
            print(f"[Miner] INVALID: My score commit was excluded!")
            return False 
            
        print(f"[Miner] Block Verified. Voting VALID.")
        return True

    # M7: Miner Reveal Score
    def reveal_score_on_chain(self, task_ID: bytes):
        data = self.reveal_data.get(task_ID.hex())
        if not data:
            print(f"[Miner] Cannot reveal: No data for task {task_ID.hex()}")
            return

        print(f"[Miner {self.address[:8]}..] Revealing score: {data['score_int']}")
        
        tx_info = None
        try:
            self.web3_client.send_transaction(
                self.web3_client.task_contract,
                'minerRevealScore',
                task_ID,
                data['score_int'],
                data['nonce_i'],
                from_addr=self.address 
            )
            # record reveal timestamp
            self.reveal_data[task_ID.hex()]['reveal_timestamp'] = time.time()
            tx_info = {'status': 'submitted'}
            print(f"[Miner] Score revealed.")
        except Exception as e:
            # record attempt timestamp
            self.reveal_data[task_ID.hex()]['reveal_timestamp'] = time.time()
            print(f"[Miner] Reveal failed: {e}")
            tx_info = {'status': 'failed', 'error': str(e)}

        return tx_info

    # New: generate_task_response uploads capability proof to IPFS
    def generate_task_response(self, task_ID: bytes) -> dict:
        """Generates miner capability proof, uploads to IPFS and returns response packet.

        Returns: { 'address': address, 'pk': pk_i, 'proof_cid': cid }
        """
        metadata = {
            'miner_address': self.address,
            'compute_power': float(random.uniform(1.0, 10.0)),
            'dataset_size': int(random.randint(100, 10000)),
        }
        try:
            if self.ipfs is None:
                # attempt to instantiate if previously failed
                self.ipfs = IPFSHandler()
            cid = self.ipfs.upload_json(metadata)
            print(f"[Miner {self.address[:8]}..] Uploaded proof to IPFS: {cid}")
        except Exception as e:
            print(f"[Miner {self.address[:8]}..] IPFS upload failed: {e}")
            cid = None

        return {
            'address': self.address,
            'pk': self.pk_i,
            'proof_cid': cid,
            'metadata': metadata
        }