from flask import Flask, jsonify
from simulate import run_elo_simulation
from utility import random_chars, dict_stringify, get_simulation_parameters
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

success_message = """scheduled simulation: code --> %s, parameters --> %s"""


@app.route('/v1/simulate', methods=['GET', 'POST'])
def simulate():
    """ simulator end point, normally this should be receiving
    configurations in request payload, but not a requirement for now
    """
    global simulator_process
    if simulator_process and simulator_process.poll() is None:
        return respond_with_message('simulator already running', 503)
    else:
        session_code = random_chars(8)
        simulator_process = subprocess.Popen(
            [settings.python_path, 'simulate.py', '--debug', '--session_code', session_code])
        params_str = dict_stringify(get_simulation_parameters())
        return respond_with_message(success_message % (session_code, params_str), 200)


def respond_with_message(message: str, response_code):
    """ response with an error code in json format with an error message """
    return jsonify({'message': message}), response_code
