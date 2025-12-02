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

SIM_RESULTS_FILE = Path(__file__).resolve().parent.parent / 'simulation_results.json'



def _run_simulation_thread(task_id=None, tx_hash=None, publish_params=None):
    from integration.simulation_runner import setup_environment, run_healchain_simulation
    try:
        STATE['status'] = 'running'
        STATE['error'] = None
        STATE['last_task_id'] = task_id
        STATE['last_tx'] = tx_hash

        # Setup environment
        publisher, aggregator, miners, pk_A, ndd_fe, web3_client = setup_environment()

        # Run the simulation (this will write `simulation_results.json` on success)
        run_healchain_simulation(publisher, aggregator, miners, pk_A, ndd_fe, web3_client, publish_params=publish_params)

        # After run, check results file
        if SIM_RESULTS_FILE.exists():
            STATE['result_path'] = str(SIM_RESULTS_FILE)
            STATE['status'] = 'completed'
        else:
            STATE['error'] = 'Simulation finished but results file not found.'
            STATE['status'] = 'failed'

    except Exception as e:
        STATE['error'] = f"Simulation error: {e}\n" + traceback.format_exc()
        STATE['status'] = 'failed'


@app.route('/run-simulation', methods=['POST'])
def run_simulation():
    payload = request.get_json(silent=True) or {}
    task_id = payload.get('taskId')
    tx_hash = payload.get('txHash')

    if STATE['status'] == 'running':
        return jsonify({'status': 'running', 'message': 'A simulation is already in progress.'}), 409

    # Start background thread with provided payload as publish params
    t = threading.Thread(target=_run_simulation_thread, args=(task_id, tx_hash, payload), daemon=True)
    t.start()

    return jsonify({'status': 'started', 'taskId': task_id, 'txHash': tx_hash}), 202


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


if __name__ == '__main__':
    # Default flask host/port for local development
    app.run(host='127.0.0.1', port=5000, debug=False)
