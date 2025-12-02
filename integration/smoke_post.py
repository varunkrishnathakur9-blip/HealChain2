import requests
import json

payload = {
    "publisher": "0x0000000000000000000000000000000000000000",
    "dataHash": "QmTestHash",
    "initialModelLink": "ipfs://init-model",
    "datasetReq": "chest_xray",
    "accReq": 0.8,
    "reward": 1,
    "texp": 60,
    "nonceTP": 1,
    "L": 1
}

try:
    r = requests.post('http://127.0.0.1:5000/run-simulation', json=payload)
    print('status_code:', r.status_code)
    print('response:', r.text)
except Exception as e:
    print('error:', e)
