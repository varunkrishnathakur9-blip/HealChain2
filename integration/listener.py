"""
Event Listener for TaskManager Smart Contract

This script listens for TaskPublished events from the TaskManager contract
and extracts taskId, publisher, and dataHash from the event logs.

Usage:
    python listener.py

Requirements:
    - Local Ganache node running at http://127.0.0.1:7545
    - TaskManager contract deployed and address configured
    - Contract ABI available in artifacts directory
"""

import json
import os
import sys
import time
from pathlib import Path
from web3 import Web3, HTTPProvider
import requests
import http.client as http_client
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout as RequestsTimeout

# Try to import POA middleware (for compatibility with different web3.py versions)
# This is optional and only needed for Proof of Authority networks
# Note: Ganache doesn't require this middleware, so it's safe to skip if unavailable
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    try:
        # Newer web3.py versions (v6+) may have it in a different location
        from web3.middleware.geth_poa import geth_poa_middleware
    except ImportError:
        # If not available, we'll skip it (not needed for Ganache)
        geth_poa_middleware = None


class TaskManagerEventListener:
    """
    Event listener for TaskManager contract events.
    Continuously monitors the blockchain for TaskPublished events.
    """
    
    def __init__(self, rpc_url="http://127.0.0.1:7545", contract_address=None, abi_path=None):
        """
        Initialize the event listener.
        
        Args:
            rpc_url: RPC endpoint URL (default: Ganache local node)
            contract_address: Deployed TaskManager contract address
            abi_path: Path to the contract ABI JSON file
        """
        # Initialize Web3 connection
        self.w3 = Web3(HTTPProvider(rpc_url))
        
        # Add POA middleware if available and needed (for some test networks like Goerli)
        # Note: Ganache doesn't require this middleware
        if geth_poa_middleware is not None:
            try:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            except Exception:
                pass  # Not needed for all networks (e.g., Ganache)
        
        # Verify connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC: {rpc_url}")
        
        print(f"✓ Connected to blockchain at {rpc_url}")
        print(f"  Chain ID: {self.w3.eth.chain_id}")
        print(f"  Latest Block: {self.w3.eth.block_number}")
        
        # Load contract address and ABI
        config_path = Path(__file__).parent.parent / "blockchain" / "deployment" / "contract_config.json"
        
        if contract_address is None or abi_path is None:
            # Try to load from config file
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if contract_address is None:
                        task_manager_config = config.get('TaskManager', {})
                        contract_address = task_manager_config.get('address')
                        if not contract_address:
                            # Show helpful error message
                            print(f"\n⚠️  TaskManager not found in config file: {config_path}")
                            print("   Available contracts in config:")
                            for key in config.keys():
                                if isinstance(config[key], dict) and 'address' in config[key]:
                                    print(f"     - {key}: {config[key]['address']}")
                            print("\n   To fix this:")
                            print("   1. Deploy TaskManager contract:")
                            print("      npx hardhat run blockchain/contracts/migrations/deploy_taskmanager.js --network ganache")
                            print("   2. Or manually add TaskManager to contract_config.json")
                            raise ValueError(
                                f"TaskManager contract address not found in config file.\n"
                                f"Please deploy the contract first or add it to: {config_path}"
                            )
                    if abi_path is None:
                        abi_path = config.get('TaskManager', {}).get('abiFile')
                        if abi_path:
                            # Resolve relative path from config file's directory
                            # The abiFile path is relative to the config file location
                            config_dir = config_path.parent
                            # Handle both relative and absolute paths
                            if not Path(abi_path).is_absolute():
                                abi_path = config_dir / abi_path
                            else:
                                abi_path = Path(abi_path)
                            # Convert to absolute path and normalize
                            abi_path = abi_path.resolve()
            else:
                print(f"⚠️  Config file not found: {config_path}")
        
        if not contract_address:
            raise ValueError(
                "Contract address not provided and not found in config.\n"
                "Please provide contract_address parameter or deploy the contract first."
            )
        
        if not abi_path:
            # Try default path
            abi_path = Path(__file__).parent.parent / "artifacts" / "blockchain" / "contracts" / "TaskManager.sol" / "TaskManager.json"
            abi_path = abi_path.resolve()
        
        if not Path(abi_path).exists():
            raise FileNotFoundError(
                f"ABI file not found: {abi_path}\n"
                f"Please compile the contract first: npx hardhat compile"
            )
        
        # Load ABI
        with open(abi_path, 'r') as f:
            abi_data = json.load(f)
            abi = abi_data.get('abi', [])
        
        # Create contract instance
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)
        
        print(f"✓ Contract loaded at {self.contract_address}")
        
        # Note: avoid using private web3.py internals (like _get_event_signature)
        # which are not stable across web3.py versions. We'll rely on the
        # public event API (create_filter and event['args']) when polling.
        print("✓ Event listener ready for 'TaskPublished' events")

    def _safe_get_logs(self, from_block, to_block, max_retries=5, base_delay=1):
        """
        Safe wrapper around `w3.eth.get_logs` with retries and exponential backoff.
        Returns list of logs or an empty list on non-fatal failures.
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                # web3 accepts integers for blocks
                params = {
                    'fromBlock': int(from_block),
                    'toBlock': int(to_block),
                    'address': self.contract_address
                }
                logs = self.w3.eth.get_logs(params)
                return logs
            except (RequestsConnectionError, RequestsTimeout, http_client.RemoteDisconnected, OSError) as e:
                attempt += 1
                delay = min(60, base_delay * (2 ** attempt))
                print(f"get_logs network error (attempt {attempt}/{max_retries}): {e}; retrying in {delay}s")
                time.sleep(delay)
                continue
            except Exception as e:
                # Non-network error parsing logs — log and return empty
                print(f"get_logs failed with error: {e}")
                return []

        print("Exceeded max get_logs retries, returning empty list")
        return []

    def _parse_log_to_event(self, log):
        """
        Parse a raw log dict into a ContractEvent-style event object using the
        contract's TaskPublished event parser. Tries common method names across
        web3.py versions.
        Returns the parsed event object or raises if parsing fails.
        """
        # Try known method names (processLog in v5, process_log in some variants)
        try:
            # Typical web3.py API
            event = self.contract.events.TaskPublished().processLog(log)
            return event
        except AttributeError:
            try:
                event = self.contract.events.TaskPublished().process_log(log)
                return event
            except Exception:
                # re-raise original error to be handled by caller
                raise
    
    def listen_for_events(self, from_block='latest', poll_interval=2):
        """
        Start listening for TaskPublished events in an infinite loop.
        
        Args:
            from_block: Block number to start listening from ('latest' or block number)
            poll_interval: Seconds to wait between polling for new blocks
        """
        print("\n" + "="*60)
        print("Starting event listener for TaskPublished events...")
        print("="*60 + "\n")
        
        # Track the last processed block to avoid duplicates
        last_processed_block = None
        
        if from_block == 'latest':
            last_processed_block = self.w3.eth.block_number
        else:
            last_processed_block = from_block
        
        print(f"Starting from block: {last_processed_block}\n")
        
        try:
            # Use a simple exponential backoff for transient network errors
            retry_count = 0
            max_retries = 6
            fallback_to_get_logs = False

            while True:
                try:
                    # Get current block number
                    current_block = self.w3.eth.block_number

                    # Only process if there are new blocks
                    if current_block >= last_processed_block:
                        # Query for events from last processed block to current
                        # We query from last_processed_block + 1 to avoid duplicates
                        query_from = last_processed_block + 1 if last_processed_block else None

                        # Try the convenient ContractEvent filter API first
                        if not fallback_to_get_logs:
                            try:
                                kwargs = {}
                                if query_from is not None:
                                    kwargs['from_block'] = query_from
                                kwargs['to_block'] = current_block
                                event_filter = self.contract.events.TaskPublished.create_filter(**kwargs)
                                events = event_filter.get_all_entries()
                                for event in events:
                                    self._process_event(event)
                                # success — reset retry_count
                                retry_count = 0
                                fallback_to_get_logs = False
                            except (TypeError, ValueError, AttributeError) as sig_exc:
                                # Some web3.py versions differ in parameter names or API
                                print(f"Event filter API not usable ({sig_exc}), switching to get_logs fallback.")
                                fallback_to_get_logs = True
                            except (RequestsConnectionError, RequestsTimeout, http_client.RemoteDisconnected, OSError) as conn_exc:
                                # Network hiccup — back off and retry
                                print(f"Network error while using event filter: {conn_exc}")
                                retry_count += 1
                                if retry_count > max_retries:
                                    print("Max retries exceeded, switching to get_logs fallback")
                                    fallback_to_get_logs = True
                                    retry_count = 0
                                else:
                                    backoff = min(60, 2 ** retry_count)
                                    print(f"Retrying in {backoff} seconds...")
                                    time.sleep(backoff)
                                    continue

                        # If filter API is not usable or was disabled, use get_logs fallback
                        if fallback_to_get_logs:
                            # Compute from_block for get_logs
                            from_block = query_from if query_from is not None else current_block
                            to_block = current_block
                            logs = self._safe_get_logs(from_block, to_block)
                            if logs:
                                for log in logs:
                                    try:
                                        event = self._parse_log_to_event(log)
                                        if event:
                                            self._process_event(event)
                                    except Exception as parse_exc:
                                        print(f"Failed to parse log into event: {parse_exc}")

                            # success — reset retry_count and unset fallback only if everything worked
                            retry_count = 0

                        # Update last processed block
                        if current_block > last_processed_block:
                            last_processed_block = current_block

                    # Wait before next poll
                    time.sleep(poll_interval)

                except (RequestsConnectionError, RequestsTimeout, http_client.RemoteDisconnected, OSError) as e:
                    # Handle connection-level problems with exponential backoff
                    retry_count += 1
                    backoff = min(60, 2 ** retry_count)
                    print(f"Connection error while polling: {e}; retrying in {backoff}s (attempt {retry_count})")
                    time.sleep(backoff)
                    if retry_count > max_retries:
                        print("Persistent connection errors — waiting longer before retrying")
                        time.sleep(30)
                        retry_count = 0
                    continue
                except Exception as e:
                    # Generic catch-all; log and continue rather than crash
                    print(f"Unexpected error during event polling: {e}")
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

        except KeyboardInterrupt:
            print("\n\nEvent listener stopped by user.")
    
    def _process_event(self, event):
        """
        Process a single TaskPublished event.
        
        Args:
            event: The event object from web3.py
        """
        # Extract event data
        event_args = event['args']
        
        task_id = event_args.get('taskId')
        publisher = event_args.get('publisher')
        data_hash = event_args.get('dataHash')
        
        # Get transaction details
        tx_hash = event['transactionHash'].hex()
        block_number = event['blockNumber']
        
        # Display event information
        print("-" * 60)
        print(f"📢 TaskPublished Event Detected!")
        print(f"  Transaction Hash: {tx_hash}")
        print(f"  Block Number: {block_number}")
        print(f"  Task ID: {task_id}")
        print(f"  Publisher: {publisher}")
        print(f"  Data Hash: {data_hash}")
        print("-" * 60)
        
        # ============================================================
        # INTEGRATION POINT: Trigger External HealChain Algorithms
        # ============================================================
        # 
        # This is where you should integrate with your existing
        # HealChain Python backend to trigger processing algorithms.
        # 
        # Example integration:
        # 
        # from federated_layer.task_publisher.publisher import process_task
        # from federated_layer.aggregator.aggregator import start_aggregation
        # 
        # try:
        #     # Trigger task processing
        #     process_task(
        #         task_id=task_id,
        #         publisher_address=publisher,
        #         data_hash=data_hash,
        #         block_number=block_number
        #     )
        #     
        #     # Or trigger aggregation if needed
        #     # start_aggregation(task_id=task_id)
        #     
        # except Exception as e:
        #     print(f"Error triggering HealChain algorithms: {e}")
        # 
        # ============================================================
        
        # For now, just log that this is the integration point
        print(f"\n💡 Integration Point: Trigger HealChain algorithms here")
        print(f"   Task ID {task_id} is ready for processing\n")
        # Attempt to notify local simulation server to start the end-to-end flow
        try:
            sim_url = os.getenv('SIM_SERVER_URL', 'http://127.0.0.1:5000/run-simulation')
            payload = {
                'taskId': task_id.hex() if isinstance(task_id, (bytes, bytearray)) else str(task_id),
                'publisher': publisher,
                'dataHash': str(data_hash),
                'txHash': tx_hash
            }
            print(f"Posting event to simulation server: {sim_url} payload={payload}")
            resp = requests.post(sim_url, json=payload, timeout=5)
            print(f"Simulation server response: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Failed to notify simulation server: {e}")


def main():
    """
    Main entry point for the event listener script.
    
    Usage:
        python listener.py [contract_address] [rpc_url]
        
    Or set environment variables:
        TASKMANAGER_ADDRESS=0x... python listener.py
        RPC_URL=http://127.0.0.1:7545 python listener.py
    """
    # Configuration - can be overridden by command-line args or env vars
    RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:7545")
    CONTRACT_ADDRESS = os.getenv("TASKMANAGER_ADDRESS", None)
    ABI_PATH = os.getenv("TASKMANAGER_ABI_PATH", None)
    
    # Allow command-line arguments
    if len(sys.argv) > 1:
        CONTRACT_ADDRESS = sys.argv[1]
    if len(sys.argv) > 2:
        RPC_URL = sys.argv[2]
    
    try:
        # Initialize listener
        listener = TaskManagerEventListener(
            rpc_url=RPC_URL,
            contract_address=CONTRACT_ADDRESS,
            abi_path=ABI_PATH
        )
        
        # Start listening (infinite loop)
        listener.listen_for_events(
            from_block='latest',  # Start from latest block
            poll_interval=2  # Poll every 2 seconds
        )
        
    except KeyboardInterrupt:
        print("\n\nShutting down event listener...")
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\n💡 Quick fix options:")
        print("   1. Deploy the contract first:")
        print("      npx hardhat run blockchain/contracts/migrations/deploy_taskmanager.js --network ganache")
        print("   2. Or provide contract address directly:")
        print("      python listener.py 0xYourContractAddress")
        print("   3. Or set environment variable:")
        print("      set TASKMANAGER_ADDRESS=0xYourContractAddress")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()

