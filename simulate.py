# elo simulation
import sys
import subprocess
import shlex
import settings
import configargparse
from utility import (
    random_chars, get_interactive_agent_count, 
    get_simulation_parameters, export_session_report)
import numpy as np
from db.db import session_results_ready
from db.db_commands import export_session
import logging

log = logging.getLogger(__name__)


# assume matching engines are listening
p = configargparse.getArgParser()
p.add('--debug', action='store_true')
p.add('--session_code', default=random_chars(8), type=str)
p.add('--note', type=str)
options, args = p.parse_known_args()


def run_elo_simulation(
        session_code, random_seed=np.random.randint(0, 99)):
    """
    given a session code
    runs a a simulation of ELO type
    blocks until the all agents write a market_end event
    to db otherwise timeouts
    returns session data as two csv formatted files
    one for markets, one for agents
    """
    logging.basicConfig(
        level=logging.DEBUG if options.debug else logging.INFO,
        filename=settings.logs_dir + 'session_%s_manager.log' % (session_code),
        format="[%(asctime)s.%(msecs)03d] %(levelname)s \
        [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt='%H:%M:%S')
    # commands to run each process
    # one proxy per exchange
    # one pacemaker agent per proxy
    p = settings.ports
    session_dur = get_simulation_parameters()['session_duration']
    # (cmd, process_name)
    focal_proxy = """ run_proxy.py --ouch_port {0} --json_port {1}
                      --session_code {2} --exchange_host {3} --exchange_port {4} 
                      --session_duration {5} --tag focal""".format(
                p['focal_proxy_ouch_port'], 
                p['focal_proxy_json_port'],
                session_code, 
                settings.focal_exchange_host,
                p['focal_exchange_port'], 
                session_dur), 'focal_proxy'
    external_proxy = """run_proxy.py --ouch_port {0} --json_port {1}
                        --session_code {2} --exchange_host {3} --exchange_port {4} 
                        --session_duration {5} --tag external""".format(
                p['external_proxy_ouch_port'], 
                p['external_proxy_json_port'], 
                session_code, 
                settings.external_exchange_host,
                p['external_exchange_port'], 
                session_dur), 'external_proxy'

    rabbit_agent_focal = """run_agent.py --session_duration {0} --exchange_ouch_port {1}
                            --session_code {2} --agent_type rabbit --config_num {3} 
                            --random_seed {4}""".format(
                    session_dur, 
                    p['focal_proxy_ouch_port'],
                    session_code, 
                    0, 
                    random_seed), 'rabbit_agent_focal'
    rabbit_agent_external = """run_agent.py --session_duration {0} --exchange_ouch_port {1}
                               --session_code {2} --agent_type rabbit --config_num {3} 
                               --random_seed {4}""".format(
                    session_dur, 
                    p['external_proxy_ouch_port'],
                    session_code, 
                    1, 
                    random_seed), 'rabbit_agent_external'

    interactive_agents = []
    for i in range(get_interactive_agent_count()):
        agent_i = """run_agent.py --session_duration {0} --exchange_ouch_port {1} \
            --exchange_json_port {2}  --external_exchange_host 127.0.0.1 \
            --external_exchange_json_port {3} --session_code {4} \
            --agent_type elo --config_num {5} --debug""".format(
                session_dur, 
                p['focal_proxy_ouch_port'],
                p['focal_proxy_json_port'], 
                p['external_proxy_json_port'],
                session_code, 
                i), 'dynamic_agent_{0}'.format(i)
        interactive_agents.append(agent_i)

    processes = {}
    for pair in [focal_proxy, external_proxy, rabbit_agent_focal,
                 rabbit_agent_external] + interactive_agents:
        cmd, process_tag = pair[0], pair[1]
        if options.debug:
            cmd += ' --debug'
        cmd = sys.executable + ' ' + cmd
        processes[process_tag] = subprocess.Popen(shlex.split(cmd))
    exit_codes = [p.wait() for p in processes.values()]
    if sum(exit_codes) == 0 and session_results_ready(session_code):
        export_session(session_code)
        export_session_report(session_code, options.note)
        log.info('session %s complete!' % session_code)


if __name__ == '__main__':
    run_elo_simulation(options.session_code)
