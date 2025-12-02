import numpy as np
import random
from typing import List, Tuple
from web3 import Web3
from eth_utils import keccak

# Import your modules (adjust paths if necessary)
from integration.web3_client import Web3Client 
from crypto.ndd_fe import NDD_FE 

class TaskPublisher:
    def __init__(self, initial_model: np.ndarray, account_address: str, ndd_fe_instance: NDD_FE):
        self.ndd_fe = ndd_fe_instance
        # Generate TP keys locally (for NDD-FE)
        self.pk_TP, self.sk_TP = self.ndd_fe.key_gen()
        
        self.address = account_address
        self.W0 = initial_model
        self.web3_client = Web3Client() # Initialize connection

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
        
        # 1. Prepare Accuracy Requirement
        # Convert to basis points (e.g., 92.5% -> 9250) for integer compatibility on-chain
        acc_req_basis_points = int(acc_req * 100) 

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
        self.web3_client.send_transaction(
            self.web3_client.task_contract,
            'tpCommit', 
            task_ID, 
            reward_wei, 
            commit_hash
        )

        # 4. Call EscrowContract.deposit (Algorithm 1, Step 4)
        print(f"[TP] Depositing {reward_R} ETH to Escrow...")
        self.web3_client.send_transaction(
            self.web3_client.escrow_contract,
            'deposit', 
            task_ID,
            value=reward_wei # Payable function
        )

        # 5. Start Processing (State Transition)
        # Algorithm 2 usually sets this, but TP needs to signal "Task Ready" after deposit.
        self.web3_client.send_transaction(
            self.web3_client.task_contract,
            'startProcessing',
            task_ID
        )

        print(f"[TP] Task {task_ID.hex()} published and active.")
        return commit_hash, self.W0

    # M2: Miner Selection and Key Derivation (Algorithm 2)
    def setup_round(self, 
                    task_ID: bytes,
                    participants_info: List[Tuple[str, object]], # (address, pk_miner_point)
                    round_ctr: int,
                    aggregator_address: str = None):
        """
        Executes Algorithm 2:
        1. Select Aggregator (Proof-of-Stake logic simulated)
        2. Derive NDD-FE functional key (sk_FE)
        3. Register Aggregator on-chain
        """
        
        # 1. PoS Selection (Simplified for Simulation)
        # In a real PoS, we'd check stake balances. Here we deterministically pick index 0.
        # If an `aggregator_address` override is provided, use it so the on-chain
        # aggregator matches the off-chain Aggregator instance used in simulation.
        if aggregator_address:
            aggregator_addr = aggregator_address
            # Try to find the corresponding pk in participants_info if present
            aggregator_pk = None
            for addr, pk in participants_info:
                if addr.lower() == aggregator_addr.lower():
                    aggregator_pk = pk
                    break
            print(f"[TP] Manually Selected Aggregator: {aggregator_addr}")
        else:
            # --- ACTUAL POS LOGIC START ---
            print("\n[TP] --- Executing Algorithm 2: PoS Selection ---")
            
            stakes = []
            addresses = []
            public_keys = []
            
            print(f"[TP] Calculating selection probabilities based on stake:")
            for addr, pk in participants_info:
                # Attempt to read stake from token contract; fallback to random if unavailable
                stake = self._get_stake_for_address(addr)
                
                stakes.append(stake)
                addresses.append(addr)
                public_keys.append(pk)
            
            total_stake = sum(stakes)
            if total_stake == 0:
                # Fallback to uniform probabilities if all stakes are zero
                probabilities = [1.0 / len(stakes)] * len(stakes)
            else:
                probabilities = [s / total_stake for s in stakes]
            
            # Log probabilities for verification
            for i, addr in enumerate(addresses):
                print(f"  Miner {addr[:8]}... | Stake: {stakes[i]} | Prob: {probabilities[i]:.4f}")

            # Select ONE Aggregator based on the calculated probabilities
            # "Aggregator = Random.Choice(Miners, Weights=Stakes)"
            selected_index = np.random.choice(len(participants_info), p=probabilities)
            
            aggregator_addr = addresses[selected_index]
            aggregator_pk = public_keys[selected_index]
            
            print(f"✅ [TP] PoS Winner (Aggregator): {aggregator_addr[:10]}...")
            # --- ACTUAL POS LOGIC END ---
        
        miner_pks = [pk for addr, pk in participants_info]


        # 2. Update TaskContract with Aggregator (Algorithm 2, Line 16)
        # "taskPool[taskID].aggregator = A_pk"
        # We use markAwaitingVerification to set the aggregator and move state.
        # Note: In strict flow, this might happen later, but setting it now authorizes the Aggregator.
        self.web3_client.send_transaction(
            self.web3_client.task_contract,
            'markAwaitingVerification',
            task_ID,
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
            task_ID=task_ID
        )
        
        print(f"[TP] sk_FE derived. (Value hidden for security)")

        # 5. Secure Delivery (Algorithm 2, Line 21)
        # In this simulation, we return it. In production, this is encrypted with Aggregator's PK.
        return aggregator_addr, sk_FE, weights_y

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
            task_ID,
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