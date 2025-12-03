import requests
import json
import time
from typing import Dict, Any


class IPFSHandler:
    """Simple IPFS helper using the local Kubo HTTP API.

    - Uploads JSON via the HTTP API add endpoint (default 127.0.0.1:5001).
    - Retrieves JSON via the gateway (default 127.0.0.1:8080).
    """

    def __init__(self, api_url: str = "http://127.0.0.1:5001", gateway_url: str = "http://127.0.0.1:8080"):
        self.api_url = api_url.rstrip('/')
        self.gateway_url = gateway_url.rstrip('/')

    def upload_json(self, data: Dict[str, Any]) -> str:
        """Uploads a JSON object to IPFS and returns the CID string.

        :param data: A JSON-serializable dictionary
        :return: CID string (e.g., Qm...)
        """
        url = f"{self.api_url}/api/v0/add"
        # ipfs expects a file-like upload; convert JSON to bytes and send as 'file'
        payload = json.dumps({**data, 'timestamp': int(time.time())}).encode('utf-8')
        files = {'file': ('data.json', payload, 'application/json')}
        try:
            resp = requests.post(url, files=files, timeout=10)
            resp.raise_for_status()
            # Response is a newline-delimited list of JSON objects; parse last line
            text = resp.text.strip()
            if '\n' in text:
                last = text.split('\n')[-1]
            else:
                last = text
            parsed = json.loads(last)
            cid = parsed.get('Hash') or parsed.get('Name')
            return cid
        except Exception as e:
            raise RuntimeError(f"IPFS upload failed: {e}")

    def get_json(self, cid: str) -> Dict[str, Any]:
        """Fetches JSON from the IPFS gateway and returns a dict.

        :param cid: CID string
        :return: Parsed JSON
        """
        url = f"{self.gateway_url}/ipfs/{cid}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"IPFS fetch failed for {cid}: {e}")
