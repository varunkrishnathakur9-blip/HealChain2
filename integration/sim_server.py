from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import time
import os
import json
import traceback
from pathlib import Path
import sys

# Ensure project root is on sys.path so threaded imports work when this file
# is executed directly as a script (not as a package module).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__)
CORS(app)

# Shared state for a single simulation runner instance
STATE = {
    'status': 'idle',        # idle | running | completed | failed
    'last_task_id': None,
    'last_tx': None,
    'result_path': None,
    'error': None
}

# In-memory simulation context used to pause after miner discovery so the
# publisher (frontend) can fetch applicants and select participants before
# the PoS selection and training loop continue. This keeps objects in memory
# between HTTP calls (single-run, single-user assumption).
SIM_CONTEXT = {
    'publisher': None,
    'aggregator': None,
    'miners': None,
    'pk_A': None,
    'ndd_fe': None,
    'web3_client': None,
    'task_id': None,
    'publish_params': None,
    'miner_responses': None
}

SIM_RESULTS_FILE = Path(__file__).resolve().parent.parent / 'simulation_results.json'

# File to persist published tasks so dashboards can reload state across restarts
PERSISTED_TASKS_FILE = Path(__file__).resolve().parent / 'published_tasks.json'

# In-memory persisted tasks cache (loaded from disk on startup)
PERSISTED_TASKS = []


def _load_persisted_tasks():
    global PERSISTED_TASKS
    try:
        if PERSISTED_TASKS_FILE.exists():
            with open(PERSISTED_TASKS_FILE, 'r', encoding='utf-8') as f:
                PERSISTED_TASKS = json.load(f) or []
        else:
            PERSISTED_TASKS = []
    except Exception:
        PERSISTED_TASKS = []


def _save_persisted_tasks():
    try:
        with open(PERSISTED_TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(PERSISTED_TASKS, f, indent=2)
    except Exception:
        # best-effort, don't crash the server on failure to persist
        app.logger.exception('Failed to save persisted tasks')


def _persist_task_record(payload: dict):
    """Create a minimal persisted record from incoming payload and save it.

    Returns the record that was saved.
    """
    try:
        record = {
            'taskId': payload.get('taskId'),
            'txHash': payload.get('txHash') or payload.get('tx_hash') or None,
            'dataHash': payload.get('dataHash') or payload.get('data_hash') or payload.get('dataHashHex') or None,
            'publisher': payload.get('publisher') or payload.get('publisherAddress') or None,
            'time': int(time.time()),
            'meta': {k: v for k, v in payload.items() if k not in ('taskId', 'txHash', 'tx_hash', 'dataHash', 'data_hash', 'publisher', 'publisherAddress')}
        }
        # Avoid duplicates: if taskId exists, update existing entry
        existing = None
        if record.get('taskId') is not None:
            for e in PERSISTED_TASKS:
                if str(e.get('taskId')) == str(record.get('taskId')):
                    existing = e
                    break
        if existing:
            existing.update(record)
            rec = existing
        else:
            PERSISTED_TASKS.append(record)
            rec = record
        _save_persisted_tasks()
        return rec
    except Exception:
        app.logger.exception('Failed to persist task record')
        return None


def _assign_taskid_to_persisted(tx_hash: str = None, data_hash: str = None, task_id=None):
    """Try to find an existing persisted record by tx_hash or data_hash and assign its taskId.
    Returns True if updated, False otherwise.
    """
    try:
        for rec in PERSISTED_TASKS:
            if tx_hash and rec.get('txHash') and str(rec.get('txHash')).lower() == str(tx_hash).lower():
                rec['taskId'] = task_id
                _save_persisted_tasks()
                return True
            if data_hash and rec.get('dataHash') and str(rec.get('dataHash')) == str(data_hash):
                rec['taskId'] = task_id
                _save_persisted_tasks()
                return True
        return False
    except Exception:
        app.logger.exception('Failed to assign task id to persisted record')
        return False


# Load persisted tasks on startup
_load_persisted_tasks()



def _run_simulation_thread(task_id=None, tx_hash=None, publish_params=None):
    from integration.simulation_runner import setup_environment, run_healchain_simulation
    try:
        STATE['status'] = 'running'
        STATE['error'] = None
        STATE['last_task_id'] = task_id
        STATE['last_tx'] = tx_hash

        # Setup environment
        publisher, aggregator, miners, pk_A, ndd_fe, web3_client = setup_environment()

        # Store environment objects for later continuation; do NOT auto-run
        # miner discovery here. The new decentralized flow expects miners to
        # submit applications independently via /miner-submit.
        SIM_CONTEXT['publisher'] = publisher
        SIM_CONTEXT['aggregator'] = aggregator
        SIM_CONTEXT['miners'] = miners
        SIM_CONTEXT['pk_A'] = pk_A
        SIM_CONTEXT['ndd_fe'] = ndd_fe
        SIM_CONTEXT['web3_client'] = web3_client
        # Normalize task_id into 32-byte representation for downstream contract calls
        try:
            if task_id is None:
                # Generate a fresh sim task id when none provided (avoid encoding 'None')
                try:
                    if web3_client and not getattr(web3_client, '_mock_mode', False):
                        sim_task_id = web3_client.w3.keccak(text=f"task_{time.time()}")
                    else:
                        # mock mode: use deterministic zero bytes
                        sim_task_id = (0).to_bytes(32, 'big')
                except Exception:
                    sim_task_id = (0).to_bytes(32, 'big')
            else:
                if isinstance(task_id, int):
                    sim_task_id = int(task_id).to_bytes(32, 'big')
                elif isinstance(task_id, str):
                    s = task_id
                    if s.startswith('0x') or s.startswith('0X'):
                        sim_task_id = int(s, 16).to_bytes(32, 'big')
                    else:
                        try:
                            sim_task_id = int(s).to_bytes(32, 'big')
                        except Exception:
                            sim_task_id = s.encode('utf-8').rjust(32, b'\x00')[:32]
                elif isinstance(task_id, bytes):
                    sim_task_id = task_id.rjust(32, b'\x00')[:32]
                else:
                    sim_task_id = str(task_id).encode('utf-8').rjust(32, b'\x00')[:32]
        except Exception:
            sim_task_id = (0).to_bytes(32, 'big')

        SIM_CONTEXT['task_id'] = sim_task_id
        SIM_CONTEXT['publish_params'] = publish_params
        SIM_CONTEXT['applicants'] = []

        # Perform only the publish step (tpCommit, deposit, startProcessing).
        try:
            publish_params = publish_params or {}
            acc_req = float(publish_params.get('acc_req', 85.0))
        except Exception:
            acc_req = 85.0

        try:
            reward_R = float(publish_params.get('reward', 10.0))
        except Exception:
            reward_R = 10.0

        try:
            nonce_TP = int(publish_params.get('nonceTP', 0))
        except Exception:
            nonce_TP = 0

        D = publish_params.get('D', publish_params.get('datasetReq', 'simulated_dataset'))
        L = publish_params.get('L', publish_params.get('initialModelLink', 'classification'))

        # Execute TP publish (this will call tpCommit, deposit, startProcessing)
        commit_hash, W_current = publisher.publish_task(
            SIM_CONTEXT['task_id'],
            reward_R=reward_R,
            acc_req=acc_req,
            nonce_TP=nonce_TP,
            D=D,
            L=L,
            Texp=int(publish_params.get('texp', 86400))
        )

        # Save current model state so continuation can reuse it
        SIM_CONTEXT['W_current'] = W_current

        # Open the task for miner submissions. The frontend will poll
        # /get-applicants and miner scripts will POST to /miner-submit.
        # Represent the task id as a hex string for readability in persisted records
        try:
            task_hex = '0x' + sim_task_id.hex()
        except Exception:
            task_hex = None

        STATE['status'] = 'open'
        STATE['last_task_id'] = task_hex or task_id

        # If we persisted an earlier record (from /run-simulation), update it with generated task id
        try:
            tx = tx_hash or (publish_params or {}).get('txHash') or (publish_params or {}).get('tx_hash')
            data_h = (publish_params or {}).get('dataHash') or (publish_params or {}).get('data_hash')
            if task_hex:
                updated = _assign_taskid_to_persisted(tx_hash=tx, data_hash=data_h, task_id=task_hex)
                if updated:
                    app.logger.info('[sim_server] Updated persisted record with generated task id: %s', task_hex)
        except Exception:
            app.logger.exception('Failed updating persisted task with generated id')

        app.logger.info('[sim_server] Task published and OPEN for applicants: %s', STATE['last_task_id'])
        return

        # After run, check results file
        if SIM_RESULTS_FILE.exists():
            STATE['result_path'] = str(SIM_RESULTS_FILE)
            STATE['status'] = 'completed'
        else:
            STATE['error'] = 'Simulation finished but results file not found.'
            STATE['status'] = 'failed'

    except Exception as e:
        tb = traceback.format_exc()
        STATE['error'] = f"Simulation error: {e}\n"
        # Store traceback in SIM_CONTEXT for later retrieval and write to disk
        SIM_CONTEXT['last_traceback'] = tb
        try:
            err_path = Path(__file__).resolve().parent / 'sim_server_error.log'
            with open(err_path, 'a', encoding='utf-8') as ef:
                ef.write('\n--- Exception at ' + time.strftime('%Y-%m-%d %H:%M:%S') + ' ---\n')
                ef.write(tb)
        except Exception:
            pass
        STATE['status'] = 'failed'


@app.route('/run-simulation', methods=['POST'])
def run_simulation():
    payload = request.get_json(silent=True) or {}
    task_id = payload.get('taskId')
    tx_hash = payload.get('txHash')

    app.logger.info('[sim_server] /run-simulation called with payload keys: %s', list(payload.keys()))

    if STATE.get('status') == 'running':
        app.logger.debug('[sim_server] run_simulation refused: already running')
        return jsonify({'status': 'running', 'message': 'A simulation is already in progress.'}), 409
    # Persist incoming publish info if present so dashboards can show it later
    try:
        if payload:
            rec = _persist_task_record(payload)
            if rec and rec.get('taskId') is not None:
                # keep last_task_id in state in sync with persisted record
                STATE['last_task_id'] = rec.get('taskId')
                app.logger.info('[sim_server] Persisted task during /run-simulation: %s', rec.get('taskId'))
    except Exception:
        app.logger.exception('Error while persisting task from /run-simulation')

    # Start background thread with provided payload as publish params
    t = threading.Thread(target=_run_simulation_thread, args=(task_id, tx_hash, payload), daemon=True)
    t.start()
    app.logger.info('[sim_server] Started simulation thread (daemon=%s) for task_id=%s', t.daemon, task_id)

    return jsonify({'status': 'started', 'taskId': task_id, 'txHash': tx_hash}), 202


@app.route('/publish-task', methods=['POST'])
def publish_task_endpoint():
    """Persist a published task record for dashboard consumption.

    Expected JSON keys (any): `taskId`, `txHash`, `dataHash`, `publisher`, etc.
    This endpoint only stores the record and does not start the simulation thread.
    """
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({'stored': False, 'error': 'empty payload'}), 400

    rec = _persist_task_record(payload)
    if rec is None:
        return jsonify({'stored': False, 'error': 'failed to persist'}), 500

    # Update STATE to reflect the last published task
    try:
        if rec.get('taskId') is not None:
            STATE['last_task_id'] = rec.get('taskId')
    except Exception:
        pass

    return jsonify({'stored': True, 'task': rec}), 201


@app.route('/published-tasks', methods=['GET'])
def get_published_tasks():
    """Return the list of persisted published tasks."""
    try:
        return jsonify({'tasks': PERSISTED_TASKS, 'count': len(PERSISTED_TASKS)})
    except Exception as e:
        return jsonify({'tasks': [], 'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': STATE['status'],
        'last_task_id': STATE['last_task_id'],
        'last_tx': STATE['last_tx'],
        'result_path': STATE['result_path'],
        'error': STATE['error']
    })


@app.route('/results', methods=['GET'])
def results():
    if SIM_RESULTS_FILE.exists():
        try:
            with open(SIM_RESULTS_FILE, 'r') as f:
                data = json.load(f)
            return jsonify({'found': True, 'results': data})
        except Exception as e:
            return jsonify({'found': False, 'error': str(e)}), 500
    return jsonify({'found': False, 'message': 'No results found.'}), 404


@app.route('/debug', methods=['GET'])
def debug_info():
    """Return a sanitized summary of SIM_CONTEXT for quick debugging from the frontend."""
    try:
        miner_responses = SIM_CONTEXT.get('miner_responses') or []
        miners = SIM_CONTEXT.get('miners') or []
        tb = SIM_CONTEXT.get('last_traceback') or None
        tb_short = None
        if tb:
            tb_short = tb[-4000:] if len(tb) > 4000 else tb
        # Helper: coerce values into JSON-serializable primitives
        def _safe(v):
            if v is None:
                return None
            if isinstance(v, (str, int, float, bool)):
                return v
            if isinstance(v, (bytes, bytearray)):
                try:
                    return v.hex()
                except Exception:
                    return str(v)
            if isinstance(v, dict):
                return {str(k): _safe(val) for k, val in v.items()}
            if isinstance(v, (list, tuple, set)):
                return [_safe(x) for x in v]
            # Fallback to string representation
            try:
                return str(v)
            except Exception:
                return None

        out = {
            'state': _safe(STATE.get('status')),
            'task_id': _safe(SIM_CONTEXT.get('task_id')),
            'miner_response_count': _safe(len(miner_responses)),
            'miner_addresses': _safe([r.get('address') for r in miner_responses]),
            'applicant_count': _safe(len(SIM_CONTEXT.get('applicants') or [])),
            'applicant_addresses': _safe([a.get('address') for a in (SIM_CONTEXT.get('applicants') or [])]),
            'miner_count': _safe(len(miners)),
            'error': _safe(STATE.get('error')),
            'last_traceback_tail': _safe(tb_short)
        }
        return jsonify(out)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get-applicants', methods=['GET'])
def get_applicants():
    """Return miner applicant packets collected during the last publish run.
    Frontend calls this endpoint after seeing the sim server status at
    'awaiting_selection' to fetch the list of miner responses (address, cid, metadata).
    """
    # Only return applicants when the task is open/receiving/awaiting_selection.
    if STATE.get('status') not in ('open', 'receiving_applicants', 'awaiting_selection'):
        app.logger.debug('[sim_server] /get-applicants called but status not open/receiving/awaiting; returning empty list')
        return jsonify({'applicants': []}), 200

    # Read submitted applicants (miners POSTed to /miner-submit)
    applicants = SIM_CONTEXT.get('applicants') or []
    out = []
    for r in applicants:
        out.append({
            'address': r.get('address'),
            'pk': r.get('pk'),
            'proof_cid': r.get('proof_cid'),
            'metadata': r.get('metadata')
        })
    try:
        print(f"[sim_server] Returning {len(out)} applicants (status={STATE['status']})")
    except Exception:
        pass
    # extra debug: list addresses
    app.logger.debug('[sim_server] applicant addresses: %s', [p.get('address') for p in out])
    return jsonify({'status': 'awaiting_selection', 'applicants': out})


@app.route('/miner-submit', methods=['POST'])
def miner_submit():
    """Endpoint for miners to submit their capability proofs.
    Expected JSON: { address, pk, proof_cid, metadata }
    """
    payload = request.get_json(silent=True) or {}
    addr = payload.get('address')
    pk = payload.get('pk')
    proof_cid = payload.get('proof_cid')
    proof_inline = payload.get('proof') or payload.get('proof_inline')
    metadata = payload.get('metadata')
    if not addr or (not proof_cid and not proof_inline):
        return jsonify({'error': 'address and proof_cid or inline proof required'}), 400

    applicant = {
        'address': addr,
        'pk': pk,
        'proof_cid': proof_cid,
        'metadata': metadata
    }

    # If an inline proof is provided, attempt server-side IPFS upload when available.
    if proof_inline:
        try:
            from integration.ipfs_handler import IPFSHandler
            ipfs = IPFSHandler()
            cid = ipfs.upload_json(proof_inline)
            applicant['proof_cid'] = cid
        except Exception:
            # If IPFS upload fails or handler not available, store the inline proof
            applicant['proof_inline'] = proof_inline

    SIM_CONTEXT.setdefault('applicants', []).append(applicant)
    # Set state to receiving_applicants to indicate live submissions
    if STATE.get('status') == 'open':
        STATE['status'] = 'receiving_applicants'
    app.logger.info('[sim_server] Miner submitted application: %s', addr)
    return jsonify({'status': 'accepted'}), 202


@app.route('/select-participants', methods=['POST'])
def select_participants():
    """Frontend posts the list of selected miner addresses to resume the simulation.
    Expected body: { 'selected': ['0xabc...', '0xdef...'] }
    """
    payload = request.get_json(silent=True) or {}
    selected = payload.get('selected')
    if not selected or not isinstance(selected, list):
        return jsonify({'error': 'selected must be a non-empty list of addresses'}), 400
    # Allow selection when task is open and receiving applicants as well
    if STATE['status'] not in ('open', 'receiving_applicants', 'awaiting_selection'):
        return jsonify({'status': STATE['status'], 'message': 'Simulation not accepting selections at this time.'}), 409

    # Convert any collected applicants into the format expected by the continuation
    # code (miner_responses). This copies submitted applicant packets into
    # SIM_CONTEXT['miner_responses'] so the PoS/process can use them.
    SIM_CONTEXT['miner_responses'] = list(SIM_CONTEXT.get('applicants', []))

    # Start background thread to continue simulation with selected participants
    t = threading.Thread(target=_continue_simulation_thread, args=(selected,), daemon=True)
    t.start()
    app.logger.info('[sim_server] Resuming simulation with %d selected participants', len(selected))
    return jsonify({'status': 'resumed', 'selected_count': len(selected)}), 202


@app.route('/start-pos', methods=['POST'])
def start_pos():
    """Alias for starting PoS/resuming the simulation from the frontend.
    Accepts the same body as `/select-participants`.
    """
    return select_participants()


def _continue_simulation_thread(selected_miners):
    import numpy as np
    try:
        STATE['status'] = 'running'
        publisher = SIM_CONTEXT.get('publisher')
        aggregator = SIM_CONTEXT.get('aggregator')
        miners = SIM_CONTEXT.get('miners')
        pk_A = SIM_CONTEXT.get('pk_A')
        ndd_fe = SIM_CONTEXT.get('ndd_fe')
        web3_client = SIM_CONTEXT.get('web3_client')
        publish_params = SIM_CONTEXT.get('publish_params') or {}
        task_ID = SIM_CONTEXT.get('task_id')
        W_current = SIM_CONTEXT.get('W_current')

        if not publisher or not aggregator or not miners:
            STATE['error'] = 'Simulation context lost or not initialized.'
            STATE['status'] = 'failed'
            return

        # Filter miner_responses and miner objects to selected participants
        miner_responses = SIM_CONTEXT.get('miner_responses', [])
        selected_responses = [r for r in miner_responses if r.get('address') in selected_miners]
        selected_miners_objs = [m for m in miners if m.address in selected_miners]

        # Run PoS selection among selected participants only
        agg_addr_selected, sk_FE, weights_y = publisher.setup_round(
            task_ID, selected_responses, round_ctr=0
        )
        aggregator.set_functional_key(sk_FE)
        try:
            aggregator.address = agg_addr_selected
        except Exception:
            pass

        # Training loop using only selected_miners_objs
        W_t = W_current if W_current is not None else np.random.rand(10,10)
        status = 'RETRAIN'
        start_time = time.time()
        deadline = start_time + int(publish_params.get('texp', 86400))
        candidate_block_payload = None

        while status == 'RETRAIN' and time.time() < deadline:
            submissions = []
            for miner in selected_miners_objs:
                U_i, score_commit, pk_i, score_int, nonce_i = miner.run_training_round(
                    W_t, publisher.pk_TP, pk_A, task_ID, aggregator.round_ctr
                )
                submissions.append((U_i, score_commit, pk_i, score_int, nonce_i))

            acc_req_fraction = float(publish_params.get('acc_req', 85.0)) / 100.0
            status, result = aggregator.secure_aggregate_and_evaluate(
                task_ID, submissions, publisher.pk_TP, weights_y, acc_req_fraction
            )
            W_t = aggregator.W_current

            if status == 'AWAITING_VERIFICATION':
                W_new, acc_calc, score_commits = result
                participant_addrs = [m.address for m in selected_miners_objs]
                candidate_block_payload = aggregator.form_candidate_block(
                    task_ID, W_new, acc_calc, score_commits, participant_addrs
                )
                break

        if not candidate_block_payload:
            STATE['error'] = 'Did not reach candidate block status.'
            STATE['status'] = 'failed'
            return

        # M5: verification by selected miners
        votes = []
        for miner in selected_miners_objs:
            is_valid = miner.verify_candidate_block(candidate_block_payload, task_ID)
            votes.append(is_valid)

        if all(votes):
            aggregator.publish_final_block(candidate_block_payload)
            publisher.reveal_task(task_ID, publish_params.get('acc_req', 85.0), publish_params.get('nonceTP', 0))
            for miner in selected_miners_objs:
                miner.reveal_score_on_chain(task_ID)
            web3_client.send_transaction(web3_client.escrow_contract, 'distributeRewards', task_ID)

            # Save a minimal results file
            out_path = Path(__file__).resolve().parent.parent / 'simulation_results.json'
            try:
                results = {
                    'task_id': task_ID.hex(),
                    'participants': [m.address for m in selected_miners_objs],
                    'aggregator': agg_addr_selected
                }
                with open(out_path, 'w') as f:
                    json.dump(results, f, indent=2)
                STATE['result_path'] = str(out_path)
                STATE['status'] = 'completed'
            except Exception as e:
                STATE['error'] = f'Failed to write results: {e}'
                STATE['status'] = 'failed'
        else:
            STATE['error'] = 'Consensus failed during resumed simulation.'
            STATE['status'] = 'failed'
    except Exception as e:
        tb = traceback.format_exc()
        STATE['error'] = f"Continue simulation error: {e}\n"
        SIM_CONTEXT['last_traceback'] = tb
        try:
            err_path = Path(__file__).resolve().parent / 'sim_server_error.log'
            with open(err_path, 'a', encoding='utf-8') as ef:
                ef.write('\n--- Continue Exception at ' + time.strftime('%Y-%m-%d %H:%M:%S') + ' ---\n')
                ef.write(tb)
        except Exception:
            pass
        STATE['status'] = 'failed'


if __name__ == '__main__':
    # Default flask host/port for local development
    # Disable the reloader and enable threaded mode to avoid Windows-specific
    # libuv/async handle shutdown races that can manifest as assertions in
    # `src\win\async.c` when the process forks/restarts. Explicitly set
    # `use_reloader=False` to prevent Werkzeug from spawning a child process
    # which can cause handle double-close on Windows.
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
    except AssertionError as ae:
        # Catch low-level assertion from underlying libraries and print
        # a helpful message rather than crashing with an obscure C-level trace.
        print(f"AssertionError while running sim_server: {ae}")
        raise
