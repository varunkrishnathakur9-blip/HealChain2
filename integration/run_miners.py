#!/usr/bin/env python3
"""
Simple miner simulator that polls the sim server and submits miner capability
proofs collected from a local JSON file `integration/miner_submissions.json`.

Behavior:
- Polls `GET {server}/status` until a run is `open` or `receiving_applicants`.
- Reads `integration/miner_submissions.json` (list of entries).
- For each entry not yet submitted, obtains/produces a proof CID:
  - If `proof_cid` is present, uses it.
  - If `proof` is an object or `proof_path` is provided, uploads JSON to IPFS via
    the repo's `integration.ipfs_handler.IPFSHandler.upload_json` helper.
- POSTs applicant packet to `POST {server}/miner-submit` as JSON:
    { address, pk, proof_cid, metadata }
- Keeps a small local state file `integration/miner_submissions_sent.json`
  to avoid re-submitting the same miner addresses.

This approach allows a frontend or any external process to write miner inputs
to `integration/miner_submissions.json` (for example, a simple UI where a miner
enters their public key and proof JSON). The script will then pick them up
and forward them to the sim server as if independent miner processes did so.

Usage:
  python integration\run_miners.py --server http://127.0.0.1:5000 --interval 2

"""

import argparse
import json
import time
import os
from pathlib import Path
from typing import Any, Dict, List

import requests

# Import the repo's IPFS helper if available
try:
    from integration.ipfs_handler import IPFSHandler
except Exception:
    IPFSHandler = None

DEFAULT_SERVER = "http://127.0.0.1:5000"
SCRIPT_DIR = Path(__file__).resolve().parent
SUBMISSIONS_FILE = SCRIPT_DIR / 'miner_submissions.json'
SENT_FILE = SCRIPT_DIR / 'miner_submissions_sent.json'


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Any):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def ensure_sent_file():
    if not SENT_FILE.exists():
        save_json(SENT_FILE, [])


def mark_sent(address: str):
    sent = load_json(SENT_FILE) or []
    if address not in sent:
        sent.append(address)
        save_json(SENT_FILE, sent)


def already_sent(address: str) -> bool:
    sent = load_json(SENT_FILE) or []
    return address in sent


def upload_proof_to_ipfs(ipfs: Any, entry: Dict) -> str:
    # entry may have 'proof_cid', 'proof' (object), or 'proof_path'
    if entry.get('proof_cid'):
        return entry.get('proof_cid')

    if ipfs is None:
        # Try a direct HTTP API fallback to local Kubo (127.0.0.1:5001)
        # This makes the script robust when package-style import fails.
        api_url = "http://127.0.0.1:5001/api/v0/add"
        def _add_via_api(payload_obj: Dict) -> str:
            try:
                import requests as _requests
                import json as _json
                data_bytes = _json.dumps({**payload_obj, 'timestamp': int(time.time())}).encode('utf-8')
                files = {'file': ('data.json', data_bytes, 'application/json')}
                r = _requests.post(api_url, files=files, timeout=10)
                r.raise_for_status()
                text = r.text.strip()
                if '\n' in text:
                    last = text.split('\n')[-1]
                else:
                    last = text
                parsed = _json.loads(last)
                cid = parsed.get('Hash') or parsed.get('Name')
                return cid
            except Exception as e:
                raise RuntimeError(f'IPFS HTTP API upload failed: {e}')

        # prefer upload via ipfs object if available, otherwise fallback to HTTP API
        # but continue below to branch into proof/proof_path handling

    if entry.get('proof'):
        payload = entry.get('proof')
        if ipfs is not None:
            return ipfs.upload_json(payload)
        return _add_via_api(payload)

    proof_path = entry.get('proof_path')
    if proof_path:
        p = Path(proof_path)
        if not p.exists():
            raise FileNotFoundError(f'proof_path not found: {proof_path}')
        # Read file content as JSON
        with open(p, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        if ipfs is not None:
            return ipfs.upload_json(payload)
        return _add_via_api(payload)

    raise RuntimeError('No proof data present to upload')


def submit_applicant(server: str, payload: Dict) -> bool:
    url = f"{server.rstrip('/')}/miner-submit"
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code in (200, 202):
            print(f"[run_miners] Submitted applicant {payload.get('address')} -> {r.status_code}")
            return True
        else:
            print(f"[run_miners] Submission failed: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"[run_miners] Submission error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default=DEFAULT_SERVER, help='Sim server base URL')
    parser.add_argument('--interval', type=float, default=2.0, help='Poll interval seconds')
    parser.add_argument('--once', action='store_true', help='Run one pass and exit after submitting')
    parser.add_argument('--auto-select', type=int, default=0, help='Automatically select N applicants by POSTing to /select-participants when available (0 = disabled)')
    args = parser.parse_args()

    server = args.server
    interval = args.interval

    print(f"run_miners: polling {server} every {interval}s; submissions file: {SUBMISSIONS_FILE}")

    # Prepare IPFS handler if available
    ipfs = None
    if IPFSHandler is not None:
        try:
            ipfs = IPFSHandler()
        except Exception as e:
            print(f"[run_miners] Warning: could not initialize IPFSHandler: {e}")
            ipfs = None

    ensure_sent_file()

    try:
        while True:
            # Check sim server status
            try:
                status_r = requests.get(f"{server.rstrip('/')}/status", timeout=5)
                status_r.raise_for_status()
                status_json = status_r.json()
                state = status_json.get('status')
            except Exception as e:
                print(f"[run_miners] Could not fetch status: {e}")
                state = None

            if state in ('open', 'receiving_applicants', 'awaiting_selection'):
                submissions = load_json(SUBMISSIONS_FILE) or []
                for entry in submissions:
                    addr = entry.get('address')
                    if not addr:
                        print('[run_miners] Skipping entry without address')
                        continue
                    if already_sent(addr):
                        print(f"[run_miners] Already submitted {addr}; skipping")
                        continue

                    try:
                        # Determine CID
                        proof_cid = None
                        try:
                            proof_cid = upload_proof_to_ipfs(ipfs, entry)
                        except Exception as up_e:
                            print(f"[run_miners] IPFS upload skipped/failed: {up_e}")
                            # If entry provided a proof_cid fallback, use it
                            proof_cid = entry.get('proof_cid')

                        payload = {
                            'address': addr,
                            'pk': entry.get('pk'),
                            'proof_cid': proof_cid,
                            'metadata': entry.get('metadata') or entry.get('proof') or None
                        }

                        ok = submit_applicant(server, payload)
                        if ok:
                            mark_sent(addr)
                        else:
                            print(f"[run_miners] Submission for {addr} failed; will retry later")

                    except Exception as e:
                        print(f"[run_miners] Error processing entry for {addr}: {e}")

                # If requested, attempt auto-selection when enough applicants are present
                if args.auto_select and args.auto_select > 0:
                    try:
                        apps_r = requests.get(f"{server.rstrip('/')}/get-applicants", timeout=5)
                        if apps_r.ok:
                            apps_json = apps_r.json()
                            apps = apps_json.get('applicants') or []
                            if len(apps) >= args.auto_select:
                                # pick first N addresses
                                selected_addrs = [a.get('address') for a in apps[:args.auto_select]]
                                sel_payload = {'selected': selected_addrs}
                                sel_r = requests.post(f"{server.rstrip('/')}/select-participants", json=sel_payload, timeout=10)
                                if sel_r.ok:
                                    print(f"[run_miners] Auto-selected participants: {selected_addrs}")
                                    # After auto-select, if --once requested, exit
                                    if args.once:
                                        print('[run_miners] --once used: exiting after selection')
                                        return
                                else:
                                    print(f"[run_miners] Auto-selection failed: {sel_r.status_code} {sel_r.text}")
                    except Exception as se:
                        print(f"[run_miners] Auto-selection error: {se}")

                if args.once:
                    print('[run_miners] --once used: exiting after one pass')
                    return

            else:
                # Nothing to do yet
                print(f"[run_miners] Server state: {state}; waiting for task to open...")

            time.sleep(interval)

    except KeyboardInterrupt:
        print('\n[run_miners] Interrupted by user; exiting')


if __name__ == '__main__':
    main()
