from flask import Flask, jsonify
from simulate import run_elo_simulation
from utility import random_chars, dict_stringify
import subprocess
import settings

app = Flask(__name__)

simulator_process = None

"""
endpoint to trigger a simulation
ensures only one simulation is running at time
does not block, and responds to client right away.
runs simulation asyncly
"""


@app.route('/v1/simulate', methods=['POST'])
def simulate():
    """ simulator end point, normally this should be receiving
    configurations in request payload, but not a requirement for now
    """
    global simulator_process
    if simulator_process and simulator_process.poll() is None:
        return respond_with_message('simulator already running', 503)
    else:
        session_code = random_chars(8)
        settings.refresh_agent_state_configs()
        settings.refresh_simulation_parameters()
        simulator_process = subprocess.Popen(['python', 'simulate.py', '--debug'])
        params_str = dict_stringify(settings.SIMULATION_PARAMETERS)
        return respond_with_message(
            'simulation is scheduled with id: %s and parameters --> %s' % (
                session_code, params_str), 200)


def respond_with_message(message: str, response_code):
    """ response with an error code in json format with an error message """
    return jsonify({'message': message}), response_code
