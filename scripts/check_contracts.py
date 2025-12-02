import json
from pathlib import Path
import traceback

config_path = Path(__file__).resolve().parent.parent / 'blockchain' / 'deployment' / 'contract_config.json'
print('config_path=', config_path)
config = json.loads(open(config_path).read())
print('TaskContract entry=', config.get('TaskContract'))
config_dir = config_path.parent
abi_rel = config['TaskContract']['abiFile']
abi_full = (config_dir / abi_rel).resolve()
print('abi_full=', abi_full)
print('exists=', abi_full.exists())
print('First 200 chars of ABI file:')
print(open(abi_full).read()[:200].replace('\n',' '))

from web3 import Web3, HTTPProvider
w = Web3(HTTPProvider(config['network']['rpcUrl']))
print('w3 connected=', w.is_connected())

abi = json.loads(open(abi_full).read()).get('abi')
addr = config['TaskContract']['address']
print('addr=', addr)
try:
    contract = w.eth.contract(address=w.to_checksum_address(addr), abi=abi)
    print('Contract created. ABI length=', len(abi) if abi else 0)
except Exception as e:
    print('Exception while creating contract:')
    traceback.print_exc()
