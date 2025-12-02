import json
import os
import time
from pathlib import Path
from web3 import Web3, HTTPProvider
try:
    from web3.middleware import construct_sign_and_send_raw_middleware
except Exception:
    try:
        # web3 v6 moved signing middleware under middleware.signing
        from web3.middleware.signing import construct_sign_and_send_raw_middleware
    except Exception:
        construct_sign_and_send_raw_middleware = None
from eth_account import Account

# --- Web3 Client Class ---

class Web3Client:
    """
    A robust Web3 client wrapper for interacting with EVM networks.
    Includes contract loading, transaction helpers, and a mock mode fallback.
    """
    
    # Simple default EIP-1559 settings for reliable transaction inclusion
    DEFAULT_MAX_PRIORITY_FEE_GWEI = 2  # The tip for the validator/miner
    DEFAULT_MAX_FEE_BUFFER_MULTIPLIER = 2.0  # (Base Fee * 2) + Priority Fee

    def __init__(self, config_path=None, rpc_url=None, private_key=None):
        
        self.task_contract = None
        self.escrow_contract = None
        self._signer_account = None
        self._manual_signing = False

        # --- 1. Path Resolution ---
        # Resolve the script's path absolutely for reliable config file loading
        current_file_path = Path(__file__).resolve()
        
        if config_path is None:
            # Assumes project root is two levels up from this file (Healchain/integration/web3_client.py)
            config_path = current_file_path.parent.parent / "blockchain" / "deployment" / "contract_config.json"
        
        config_path = Path(config_path)
        
        # --- 2. Config Loading ---
        config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Failed to load/parse config file {config_path}. Error: {e}")
        
        if rpc_url is None:
            rpc_url = config.get('network', {}).get('rpcUrl', 'http://127.0.0.1:7545')
        
        # --- 3. Web3 Initialization and Mock Fallback ---
        self._mock_mode = False
        try:
            self.w3 = Web3(HTTPProvider(rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to RPC: {rpc_url}")
        except Exception as e:
            print(f"Warning: RPC unavailable ({rpc_url}), entering mock mode: {e}")
            self._mock_mode = True
            self._setup_mock_classes()
        
        # --- 4. Account Setup & Signing Middleware ---
        if not self._mock_mode:
            try:
                accounts = self.w3.eth.accounts
                if not accounts:
                    raise ValueError("No accounts available. Hardhat/Ganache likely not running.")
                
                # Use the first account as the default sender
                self.w3.eth.default_account = self.w3.to_checksum_address(accounts[0])
                
                # Setup local signing if private_key is provided
                if private_key:
                    self._setup_signer(private_key)
            except Exception as e:
                raise ValueError(f"Error initializing accounts/signing: {e}")

        # --- 5. Contract Loading ---
        if not self._mock_mode:
            self._load_contract('TaskContract', config, config_path.parent, required=True)
            self._load_contract('EscrowContract', config, config_path.parent, required=True)
            # Attempt to load optional TokenContract to support PoS stake reads (non-fatal)
            # If the token contract isn't deployed or referenced in the config, this will
            # silently set `self.token_contract = None` and PoS will fall back to random stakes.
            try:
                self._load_contract('TokenContract', config, config_path.parent, required=False)
            except Exception:
                # Be defensive: ensure attribute exists even if loading raises unexpectedly
                try:
                    self.token_contract
                except Exception:
                    self.token_contract = None
        # Note: If in mock mode, mock contracts are already assigned in _setup_mock_classes

    # --- Utility Methods ---
    
    def _setup_mock_classes(self):
        """Internal method to assign mock objects when RPC connection fails."""
        # Defining mock classes locally to avoid cluttering the main class scope
        
        class _MockEth:
            def __init__(self):
                # Provide 6 deterministic mock addresses
                self.accounts = [f'0x{i:040x}' for i in range(1, 7)]
                self.default_account = self.accounts[0]
            
            # Mock the wait function to instantly return success
            def wait_for_transaction_receipt(self, tx_hash, timeout=120):
                class _Receipt: status = 1
                return _Receipt()
            # Provide a minimal account helper for `.account.create()` used in aggregator
            def account_create(self):
                # Return a simple object with .key and .address similar to eth_account.Account.create()
                return type('_Acct', (), {'key': b"\x01" * 32, 'address': self.accounts[0]})()

            def account_sign_message(self, signable_message, private_key=None):
                # Try to use eth_account if available to produce a realistic signature
                try:
                    return Account.sign_message(signable_message, private_key=private_key)
                except Exception:
                    # Fallback: return a simple object with a fake signature
                    return type('_Sig', (), {'signature': b'\x00' * 65})()

            # Expose `.account.create()` and `.account.sign_message()`
            @property
            def account(self):
                return type('A', (), {'create': self.account_create, 'sign_message': self.account_sign_message})()
            
        class _MockW3:
            def __init__(self):
                self.eth = _MockEth()
            def is_connected(self): return False
            def keccak(self, text=None, hexstr=None): return b'\x00' * 32
            def to_wei(self, number, unit: str):
                units = {'wei': 1, 'gwei': 10**9, 'ether': 10**18}
                return int(float(number) * units.get(unit.lower(), 0))
            def to_checksum_address(self, value): return value # Simplistic mock
            
        class _MockContract:
            def __init__(self):
                class _MockFunctions:
                    def __getattr__(self, name):
                        def _fn(*args, **kwargs):
                            class _MockFunction:
                                def estimate_gas(self, tx_params): return 21000
                                def transact(self, tx_params): return type('_Tx', (object,), {'hex': lambda: '0x' + '0' * 64})()
                                def call(self, *args): return None
                            return _MockFunction()
                        return _fn
                self.functions = _MockFunctions()
        
        self.w3 = _MockW3()
        self.task_contract = _MockContract()
        self.escrow_contract = _MockContract()

    def _setup_signer(self, private_key: str):
        """Injects signing middleware using a local private key."""
        try:
            # 1. Create a local account object
            signer_account = Account.from_key(private_key)
            
            # 2. Verify account matches the default one (optional, but good practice)
            if self.w3.eth.default_account != signer_account.address:
                 self.w3.eth.default_account = signer_account.address
                 print(f"Signer account set to: {signer_account.address}")

            # 3. Inject the middleware to automatically sign all transactions if available
            if construct_sign_and_send_raw_middleware is not None:
                self.w3.middleware_onion.add(
                    construct_sign_and_send_raw_middleware(signer_account)
                )
                self._signer_account = signer_account
                print("Local signing middleware successfully injected.")
            else:
                # Fallback: manual signing will be used in send_transaction
                self._signer_account = signer_account
                self._manual_signing = True
                print("Signing middleware not available; using manual signing fallback.")
        except Exception as e:
            raise ValueError(f"Failed to setup local signer with provided key: {e}")

    def _load_contract(self, name, config, config_dir, required=True):
        """Helper function to load contracts from config JSON and ABI."""
        contract_config = config.get(name, {})
        contract_addr = contract_config.get('address')
        contract_abi_path = contract_config.get('abiFile')
        
        # Check if deployment info is missing
        if not contract_addr or contract_addr == "0x0000000000000000000000000000000000000000":
            if required:
                raise ValueError(f"{name} address not set. Please deploy contracts first.")
            # Determine attribute name consistently (e.g., 'TaskContract' -> 'task_contract')
            if name.lower().endswith('contract'):
                attr_name = name[:-8].lower() + '_contract'
            else:
                attr_name = name.lower() + '_contract'
            setattr(self, attr_name, None)
            return

        # Check for ABI file
        abi_full_path = config_dir / contract_abi_path
        if not abi_full_path.exists():
            if required:
                raise FileNotFoundError(f"{name} ABI file not found: {abi_full_path}")
            print(f"Warning: {name} ABI file not found: {abi_full_path}")
            setattr(self, name.lower() + '_contract', None)
            return
        
        # Load ABI and instantiate contract
        try:
            with open(abi_full_path, 'r') as f:
                abi_data = json.load(f)
                abi = abi_data.get('abi', [])
            
            contract_instance = self.w3.eth.contract(
                address=self.w3.to_checksum_address(contract_addr),
                abi=abi
            )
            # Use a consistent attribute name for contract instances
            if name.lower().endswith('contract'):
                attr_name = name[:-8].lower() + '_contract'
            else:
                attr_name = name.lower() + '_contract'
            setattr(self, attr_name, contract_instance)
        except Exception as e:
            if required:
                raise ValueError(f"Error loading {name}: {e}")
            print(f"Warning: Could not load {name}: {e}")
            setattr(self, name.lower() + '_contract', None)

    def _get_eip1559_fees(self):
        """Calculates EIP-1559 fees (maxPriorityFee and maxFee) using web3.py's suggestions."""
        try:
            # 1. Get the priority fee suggestion (the 'tip')
            max_priority_fee = self.w3.eth.max_priority_fee
            
            # 2. Get the base fee from the latest block
            latest_block = self.w3.eth.get_block('latest')
            base_fee_per_gas = latest_block['baseFeePerGas']
            
            # 3. Calculate max fee per gas: MaxFee = (BaseFee * 2) + MaxPriorityFee
            # Multiplying BaseFee by 2 ensures the transaction stays valid for max congestion (12.5% increase per block for 6 blocks)
            max_fee_per_gas = (base_fee_per_gas * self.DEFAULT_MAX_FEE_BUFFER_MULTIPLIER) + max_priority_fee
            
            # Ensure MaxPriorityFee is at least the set default GWEI to ensure inclusion
            min_priority_fee_wei = self.w3.to_wei(self.DEFAULT_MAX_PRIORITY_FEE_GWEI, 'gwei')
            
            return {
                'maxPriorityFeePerGas': max(max_priority_fee, min_priority_fee_wei),
                'maxFeePerGas': max(int(max_fee_per_gas), int(max(max_priority_fee, min_priority_fee_wei)))
            }
        except Exception:
            # Fallback to a safe, fixed EIP-1559 value if RPC calls fail (e.g., Hardhat is not fully EIP-1559 compatible by default)
            return {
                'maxPriorityFeePerGas': self.w3.to_wei(self.DEFAULT_MAX_PRIORITY_FEE_GWEI, 'gwei'),
                'maxFeePerGas': self.w3.to_wei(300, 'gwei') # A reasonable high maximum
            }


    # --- Public Transaction Methods ---

    def send_transaction(self, contract, function_name, *args, value=0, gas_limit=None, from_addr=None):
        """
        Helper to send a transaction, handle EIP-1559 fees, and wait for confirmation.
        """
        if contract is None:
            raise ValueError("Contract not initialized. Check config file or RPC connection.")
        
        try:
            # 1. Get the function object
            func = getattr(contract.functions, function_name)
            
            # 2. Build the initial transaction parameters
            tx_params = {
                'from': self.w3.to_checksum_address(from_addr) if from_addr else self.w3.eth.default_account,
                'value': value, # in Wei
                # nonce is handled automatically by web3.py or signing middleware
            }
            
            # 3. Handle Gas Parameters (EIP-1559 or Legacy)
            if not self._mock_mode:
                try:
                    # Attempt to fetch dynamic fees (EIP-1559)
                    eip1559_fees = self._get_eip1559_fees()
                    tx_params.update(eip1559_fees)
                except Exception:
                    # Fallback to legacy gasPrice estimation if EIP-1559 fails
                    tx_params['gasPrice'] = self.w3.eth.gas_price
            
            # 4. Handle Gas Limit (required for both EIP-1559 and Legacy)
            if gas_limit is None:
                estimated_gas = func(*args).estimate_gas(tx_params)
                tx_params['gas'] = int(estimated_gas * 1.2) # 20% buffer
            else:
                tx_params['gas'] = gas_limit
            
            # 5. Send transaction
            # If manual signing fallback is enabled (no middleware), build, sign and send raw transaction.
            # However, if the caller requests a `from_addr` different from the configured local signer,
            # prefer to let the node (e.g., Ganache) sign the transaction using its unlocked account.
            if getattr(self, '_manual_signing', False) and self._signer_account is not None:
                # If a from_addr is provided and it's not the local signer, prefer node-managed signing
                try:
                    requested_from = tx_params.get('from')
                    signer_addr = getattr(self._signer_account, 'address', None)
                    if requested_from and signer_addr and self.w3.to_checksum_address(requested_from) != self.w3.to_checksum_address(signer_addr):
                        # Let the node sign/send using transact
                        tx_hash = func(*args).transact(tx_params)
                        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                        if receipt.status != 1:
                            raise Exception(f"Transaction reverted for {function_name}: {tx_hash.hex()}. Check node logs/trace.")
                        return receipt
                except Exception:
                    # Fall through to manual signing if node signing path fails
                    pass
                # Ensure nonce and chainId are present
                try:
                    tx_params['nonce'] = self.w3.eth.get_transaction_count(self._signer_account.address)
                except Exception:
                    tx_params.setdefault('nonce', 0)

                try:
                    tx = func(*args).build_transaction(tx_params)
                except Exception:
                    # If build_transaction isn't available, fall back to using transact (may fail)
                    tx = None

                if tx is not None:
                    if 'chainId' not in tx:
                        try:
                            tx['chainId'] = self.w3.eth.chain_id
                        except Exception:
                            pass
                    signed = Account.sign_transaction(tx, self._signer_account.key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
                else:
                    # Last resort: try transact (node-managed signing)
                    tx_hash = func(*args).transact(tx_params)
            else:
                # Normal path: middleware or node will sign/send
                tx_hash = func(*args).transact(tx_params)
            
            # 6. Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status != 1:
                raise Exception(f"Transaction reverted for {function_name}: {tx_hash.hex()}. Check node logs/trace.")
            
            return receipt
        except Exception as e:
            raise Exception(f"Transaction error for {function_name}: {e}")

    def call_view_function(self, contract, function_name, *args):
        """Helper to call a read-only contract function."""
        if contract is None:
            raise ValueError("Contract not initialized. Check config file.")
        
        try:
            func = getattr(contract.functions, function_name)
            return func(*args).call()
        except Exception as e:
            raise Exception(f"View function call error for {function_name}: {e}")

# Example of how the client should be instantiated in simulation_runner.py:
# web3_client = Web3Client(private_key=os.environ.get('PRIVATE_KEY'))