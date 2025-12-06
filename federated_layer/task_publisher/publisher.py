import numpy as np
import random
from typing import List, Tuple
from web3 import Web3
from eth_utils import keccak

# Import your modules (adjust paths if necessary)
from integration.web3_client import Web3Client 
from crypto.ndd_fe import NDD_FE, curve
from integration.ipfs_handler import IPFSHandler

class TaskPublisher:
    def __init__(self, initial_model: np.ndarray, account_address: str, ndd_fe_instance: NDD_FE):
        self.ndd_fe = ndd_fe_instance
        # Generate TP keys locally (for NDD-FE)
        self.pk_TP, self.sk_TP = self.ndd_fe.key_gen()
        
        self.address = account_address
        self.W0 = initial_model
        self.web3_client = Web3Client() # Initialize connection
        # IPFS helper for task metadata storage
        try:
            self.ipfs = IPFSHandler()
        except Exception:
            self.ipfs = None

    def _normalize_task_id(self, task_ID):
        """Return a 32-byte representation for task_ID accepting int/str/bytes."""
        try:
            if isinstance(task_ID, int):
                return int(task_ID).to_bytes(32, 'big')
            elif isinstance(task_ID, str):
                s = task_ID
                if s.startswith('0x') or s.startswith('0X'):
                    task_id_int = int(s, 16)
                else:
                    try:
                        task_id_int = int(s)
                    except ValueError:
                        b = s.encode('utf-8')
                        return b.rjust(32, b'\x00')[:32]
                return int(task_id_int).to_bytes(32, 'big')
            elif isinstance(task_ID, bytes):
                if len(task_ID) == 32:
                    return task_ID
                return task_ID.rjust(32, b'\x00')[:32]
            else:
                s = str(task_ID)
                b = s.encode('utf-8')
                return b.rjust(32, b'\x00')[:32]
        except Exception:
            return (0).to_bytes(32, 'big')

    def _get_stake_for_address(self, addr: str) -> int:
        """
        Safely attempt to read stake from a token contract via balanceOf(addr).
        Falls back to a random stake if the contract call fails.
        
        :param addr: Miner address
        :return: Stake amount (from contract or random fallback)
        """
        try:
            # Try to read from token contract if available
            if hasattr(self.web3_client, 'token_contract') and self.web3_client.token_contract is not None:
                stake = self.web3_client.token_contract.functions.balanceOf(addr).call()
                if stake > 0:
                    print(f"[TP] Stake for {addr[:10]}...: {stake} (from contract)")
                    return stake
                else:
                    print(f"[TP] Stake for {addr[:10]}...: 0 (from contract, using random fallback)")
                    return random.randint(100, 1000)
        except Exception as e:
            # Fallback: contract not available, call failed, etc.
            print(f"[TP] Could not read stake from contract for {addr[:10]}...: {e}")
            print(f"[TP] Using random stake for {addr[:10]}...")
        
        # Default fallback: random stake
        return random.randint(100, 1000)

    # M1: Task Publishing with EscrowCommit (Algorithm 1)
    def publish_task(self, 
                     task_ID: bytes, 
                     reward_R: int,  # In ETH (or wei, depending on input expectation)
                     acc_req: float, # Percentage e.g. 92.5
                     nonce_TP: int,
                     D: str = "Dataset_Desc",
                     L: str = "Model_Link_IPFS",
                     Texp: int = 0) -> Tuple[bytes, np.ndarray]:
        """
        Executes Algorithm 1:
        1. Compute commitHash = HASH(acc_req || nonce_TP)
        2. tpCommit (on-chain)
        3. Deposit Reward (on-chain escrow)
        """
        
        # Upload task metadata to IPFS (so miners can reference it)
        try:
            if self.ipfs is None:
                self.ipfs = IPFSHandler()
            meta = {'D': D, 'L': L, 'publisher': self.address}
            task_meta_cid = self.ipfs.upload_json(meta)
            print(f"[TP] Uploaded task metadata to IPFS: {task_meta_cid}")
        except Exception as e:
            print(f"[TP] IPFS upload failed for task metadata: {e}")
            task_meta_cid = None

        # 1. Prepare Accuracy Requirement
        # Convert to basis points (e.g., 92.5% -> 9250) for integer compatibility on-chain
        acc_req_basis_points = int(acc_req * 100) 

        # NORMALIZE task_ID -> bytes32
        # Accept ints, decimal/hex strings, or bytes and coerce to 32-byte big-endian
        try:
            if isinstance(task_ID, int):
                task_id_bytes = int(task_ID).to_bytes(32, 'big')
            elif isinstance(task_ID, str):
                # handle hex string like '0x1e' or decimal string like '30'
                s = task_ID
                if s.startswith('0x') or s.startswith('0X'):
                    task_id_int = int(s, 16)
                else:
                    try:
                        task_id_int = int(s)
                    except ValueError:
                        # treat as utf-8 bytes and pad/truncate
                        b = s.encode('utf-8')
                        task_id_bytes = b.rjust(32, b'\x00')[:32]
                        task_id_int = None
                if 'task_id_int' in locals() and task_id_int is not None:
                    task_id_bytes = int(task_id_int).to_bytes(32, 'big')
            elif isinstance(task_ID, bytes):
                if len(task_ID) == 32:
                    task_id_bytes = task_ID
                else:
                    # pad or truncate to 32
                    task_id_bytes = task_ID.rjust(32, b'\x00')[:32]
            else:
                # Fallback: convert to string then to bytes
                s = str(task_ID)
                b = s.encode('utf-8')
                task_id_bytes = b.rjust(32, b'\x00')[:32]
        except Exception:
            # On any error, fallback to zero bytes32
            task_id_bytes = (0).to_bytes(32, 'big')

        # 2. Compute Commit Hash (Strictly Algorithm 1, Step 1)
        # HASH(acc_req || nonce_TP)
        # We pack them tightly: uint256, uint256
        packed_data = (
            int(acc_req_basis_points).to_bytes(32, 'big') + 
            int(nonce_TP).to_bytes(32, 'big')
        )
        commit_hash = keccak(packed_data)

        print(f"[TP] Generated CommitHash: {commit_hash.hex()}")
        print(f"[TP] Inputs: acc_req={acc_req_basis_points}, nonce={nonce_TP}")

        # 3. Call TaskContract.tpCommit (Algorithm 1, Step 3)
        # Note: reward_R passed here is just for recording metadata; actual funds go to Escrow.
        # We convert reward to Wei for the record if needed, or keep as integer unit.
        reward_wei = self.web3_client.w3.to_wei(reward_R, 'ether')
        
        print("[TP] Submitting tpCommit transaction...")
        # If contract supports a metadata CID, include it when present.
        try:
            if task_meta_cid:
                self.web3_client.send_transaction(
                    self.web3_client.task_contract,
                    'tpCommit',
                    task_id_bytes,
                    reward_wei,
                    commit_hash,
                    task_meta_cid
                )
            else:
                self.web3_client.send_transaction(
                    self.web3_client.task_contract,
                    'tpCommit', 
                    task_id_bytes, 
                    reward_wei, 
                    commit_hash
                )
        except Exception:
            # Fallback to original call if contract ABI doesn't accept metadata
            self.web3_client.send_transaction(
                self.web3_client.task_contract,
                'tpCommit', 
                task_id_bytes, 
                reward_wei, 
                commit_hash
            )

        # 4. Call EscrowContract.deposit (Algorithm 1, Step 4)
        print(f"[TP] Depositing {reward_R} ETH to Escrow...")
        self.web3_client.send_transaction(
            self.web3_client.escrow_contract,
            'deposit', 
            task_id_bytes,
            value=reward_wei # Payable function
        )

        # 5. Start Processing (State Transition)
        # Algorithm 2 usually sets this, but TP needs to signal "Task Ready" after deposit.
        self.web3_client.send_transaction(
            self.web3_client.task_contract,
            'startProcessing',
            task_id_bytes
        )

        print(f"[TP] Task {task_ID.hex()} published and active.")
        return commit_hash, self.W0

    # M2: Miner Selection and Key Derivation (Algorithm 2)
    def setup_round(self, 
                    task_ID: bytes,
                    miner_responses: list,  # list of dicts: {address, pk, proof_cid, metadata}
                    round_ctr: int,
                    aggregator_address: str = None):
        """
        Executes Algorithm 2:
        1. Select Aggregator (Proof-of-Stake logic simulated)
        2. Derive NDD-FE functional key (sk_FE)
        3. Register Aggregator on-chain
        """
        
        # 1. PoS Selection: accept miner responses, verify proofs, then weight by stake
        print("\n[TP] --- Executing Algorithm 2: PoS Selection (with IPFS proofs) ---")

        # Filter and verify miner responses
        valid_miners = []  # tuples (address, pk, stake)
        for resp in miner_responses:
            addr = resp.get('address')
            pk = resp.get('pk')
            cid = resp.get('proof_cid')
            # Verify proof cid (if present)
            is_valid = True
            try:
                if cid and self.ipfs is not None:
                    proof = self.ipfs.get_json(cid)
                    is_valid = self.verify_miner_proof(proof)
                else:
                    # Allow inline proofs submitted in the simulation (no IPFS available)
                    inline = resp.get('proof_inline') or resp.get('proof') or resp.get('metadata')
                    if inline:
                        is_valid = self.verify_miner_proof(inline)
                    else:
                        is_valid = False
            except Exception as e:
                print(f"[TP] Warning: failed to verify proof for {addr}: {e}")
                is_valid = False

            if not is_valid:
                print(f"  [TP] Rejected miner {addr[:8]}... due to failed proof")
                continue

            # Read stake and collect
            stake = self._get_stake_for_address(addr)
            valid_miners.append((addr, pk, stake))

        if len(valid_miners) == 0:
            raise Exception("No valid miners available after proof verification")

        addresses = [m[0] for m in valid_miners]
        public_keys = [m[1] for m in valid_miners]
        stakes = [m[2] for m in valid_miners]

        total_stake = sum(stakes)
        if total_stake == 0:
            probabilities = [1.0 / len(stakes)] * len(stakes)
        else:
            probabilities = [s / total_stake for s in stakes]

        for i, addr in enumerate(addresses):
            print(f"  Miner {addr[:8]}... | Stake: {stakes[i]} | Prob: {probabilities[i]:.4f}")

        selected_index = np.random.choice(len(addresses), p=probabilities)
        aggregator_addr = addresses[selected_index]
        aggregator_pk = public_keys[selected_index]
        print(f"✅ [TP] PoS Winner (Aggregator): {aggregator_addr[:10]}...")
        
        # Normalize public keys: if miners submitted simple strings (simulator),
        # derive an EC point deterministically from the PK string so key_derive
        # can perform EC operations. Real deployments should pass proper EC points.
        normalized_pks = []
        for pk in public_keys:
            try:
                # If already a point-like object with coordinate 'x', accept it
                if hasattr(pk, 'x'):
                    normalized_pks.append(pk)
                else:
                    # Derive a scalar from the pk (string/int) and multiply base point
                    import hashlib
                    pk_bytes = str(pk).encode('utf-8')
                    scalar = int(hashlib.sha256(pk_bytes).hexdigest(), 16) % curve.field.n
                    normalized_pks.append(scalar * curve.g)
            except Exception:
                # Fallback: use generator
                normalized_pks.append(1 * curve.g)

        miner_pks = normalized_pks


        # 2. Update TaskContract with Aggregator (Algorithm 2, Line 16)
        # "taskPool[taskID].aggregator = A_pk"
        # We use markAwaitingVerification to set the aggregator and move state.
        # Note: In strict flow, this might happen later, but setting it now authorizes the Aggregator.
        self.web3_client.send_transaction(
            self.web3_client.task_contract,
            'markAwaitingVerification',
            self._normalize_task_id(task_ID),
            aggregator_addr
        )

        # 3. Prepare Weights (y_i = 1/h) (Algorithm 2, Line 18)
        h = len(miner_pks)
        weights_y = [1.0 / h] * h

        # 4. Generate Functional Key sk_FE (Algorithm 2, Line 20)
        # "NDD_FE.KeyDerive(...)"
        print("[TP] Deriving sk_FE for Aggregator...")
        sk_FE = self.ndd_fe.key_derive(
            sk_TP=self.sk_TP, 
            pk_miners=miner_pks, 
            weights_y=weights_y, 
            ctr=round_ctr, 
            task_ID=self._normalize_task_id(task_ID)
        )
        
        print(f"[TP] sk_FE derived. (Value hidden for security)")

        # 5. Secure Delivery (Algorithm 2, Line 21)
        # In this simulation, we return it. In production, this is encrypted with Aggregator's PK.
        return aggregator_addr, sk_FE, weights_y

    def verify_miner_proof(self, proof: dict, min_dataset_size: int = 500) -> bool:
        """Verify a miner's capability proof fetched from IPFS.

        Basic checks: dataset_size above a threshold and compute_power present.
        """
        try:
            if not proof:
                return False
            ds = int(proof.get('dataset_size', 0))
            cp = float(proof.get('compute_power', 0.0))
            if ds >= min_dataset_size and cp > 0:
                return True
            return False
        except Exception:
            return False

    # M7: TP Reveal (Algorithm 7, Function 1)
    def reveal_task(self, task_ID: bytes, acc_req: float, nonce_TP: int):
        """
        Executes the final TP Reveal step to unlock payments.
        """
        acc_req_basis_points = int(acc_req * 100)
        
        print(f"[TP] Revealing Task: acc={acc_req_basis_points}, nonce={nonce_TP}")
        
        self.web3_client.send_transaction(
            self.web3_client.task_contract,
            'tpReveal',
            self._normalize_task_id(task_ID),
            acc_req_basis_points,
            nonce_TP
        )
        print("[TP] Task revealed successfully.")

    def interactive_publish(self, task_ID: bytes,
                            default_acc_req: float = 92.0,
                            default_reward: float = 10.0,
                            default_texp: int = 86400):
        """Interactive helper: prompts user for TP inputs, calls `publish_task`, and
        returns a tuple (acc_req, reward_R, nonce_TP, commit_hash, W0).
        """
        print("\nProvide Task Publishing inputs (press Enter to accept defaults):")
        try:
            acc_input = input(f"Target accuracy percent (default {default_acc_req}): ").strip()
        except EOFError:
            acc_input = ""
        try:
            acc_req = float(acc_input) if acc_input != "" else default_acc_req
        except ValueError:
            print(f"Invalid accuracy '{acc_input}', using default {default_acc_req}.")
            acc_req = default_acc_req

        try:
            reward_input = input(f"Reward in ETH (default {default_reward}): ").strip()
        except EOFError:
            reward_input = ""
        try:
            reward_R = float(reward_input) if reward_input != "" else default_reward
        except ValueError:
            print(f"Invalid reward '{reward_input}', using default {default_reward} ETH.")
            reward_R = default_reward

        try:
            texp_input = input(f"Texp (expiration seconds, default {default_texp}): ").strip()
        except EOFError:
            texp_input = ""
        try:
            Texp = int(texp_input) if texp_input != "" else default_texp
        except ValueError:
            print(f"Invalid Texp '{texp_input}', using default {default_texp}.")
            Texp = default_texp

        try:
            nonce_input = input("nonceTP (integer, default random): ").strip()
        except EOFError:
            nonce_input = ""
        if nonce_input == "":
            nonce_TP = random.randint(1000, 9999)
        else:
            try:
                nonce_TP = int(nonce_input)
            except ValueError:
                print(f"Invalid nonce '{nonce_input}', using random value.")
                nonce_TP = random.randint(1000, 9999)

        # Optional pk/sk overrides (kept for compatibility but not typically used)
        try:
            D = input("D (dataset description or identifier, default 'simulated_dataset'): ").strip()
        except EOFError:
            D = ""
        if D == "":
            D = 'simulated_dataset'

        try:
            L = input("L (task label/model link, default 'classification'): ").strip()
        except EOFError:
            L = ""
        if L == "":
            L = 'classification'

        # Optional pk/sk overrides (kept for compatibility but not typically used)
        try:
            pk_override = input("pkTP (press Enter to use publisher key): ").strip()
        except EOFError:
            pk_override = ""
        pk_override_val = None if pk_override == "" else pk_override

        try:
            sk_override = input("skTP (press Enter to use publisher key): ").strip()
        except EOFError:
            sk_override = ""
        sk_override_val = None if sk_override == "" else sk_override

        commit_hash, W0 = self.publish_task(
            task_ID,
            reward_R=reward_R,
            acc_req=acc_req,
            nonce_TP=nonce_TP,
            D=D,
            L=L,
            Texp=Texp
        )

        return acc_req, reward_R, Texp, nonce_TP, commit_hash, W0, D, L