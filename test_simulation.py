# elo simulation
import sys
from honcho.manager import Manager
import settings
import utility
import numpy as np
from db.db import session_results_ready
from db.db_commands import export_session

# assume matching engines are running and listening


session_id = utility.random_chars(8)
random_seed = np.random.randint(0, 99)
conf = settings.elo_simulation_configs
# commands to run each process
# one proxy per exchange
# one pacemaker agent per proxy
# dynamic agent count is derived from config file
focal_proxy = 'python run_proxy.py --debug --ouch_port {0} --json_port {1} \
        --session_id {2} --tag focal'.format(conf['focal_proxy_ouch_port'], 
        conf['focal_proxy_json_port'], session_id), 'focal_proxy'
external_proxy = 'python run_proxy.py --debug --ouch_port {0} --json_port {1} \
    --session_id {2} --exchange_port {3} --tag external'.format(conf['external_proxy_ouch_port'], 
        conf['external_proxy_json_port'], session_id, 9002), 'external_proxy'
rabbit_agent_focal = 'python run_agent.py --session_duration {0} --exchange_ouch_port {1} \
    --session_id {2} --agent_type rabbit --config_num {3} --random_seed {4}'.format(conf['session_duration'], 
        conf['focal_proxy_ouch_port'], session_id, 0, random_seed), 'rabbit_agent_focal'
rabbit_agent_external = 'python run_agent.py --session_duration {0} --exchange_ouch_port {1} \
    --session_id {2} --agent_type rabbit --config_num {3} --random_seed {4}'.format(conf['session_duration'], 
        conf['external_proxy_ouch_port'], session_id, 0, random_seed), 'rabbit_agent_external'
interactive_agents = []
for i in range(settings.num_interactive_agents):
    agent_i = """python run_agent.py --session_duration {0} --exchange_ouch_port {1} \
    --exchange_json_port {2}  --external_exchange_host 127.0.0.1 \
        --external_exchange_json_port {3} --session_id {4} \
         --agent_type elo --config_num {5} --debug""".format(
            conf['session_duration'], conf['focal_proxy_ouch_port'], 
            conf['focal_proxy_json_port'], 
            conf['external_proxy_json_port'],
            session_id, i), 'dynamic_agent_{0}'.format(i)
    interactive_agents.append(agent_i)

m = Manager()
for cmd_process_name_pair in [focal_proxy, external_proxy, 
            rabbit_agent_focal, rabbit_agent_external] + interactive_agents:
    m.add_process(cmd_process_name_pair[1], cmd_process_name_pair[0])
m.loop()
if session_results_ready(session_id):
    export_session(session_id)
sys.stdout.write('session %s complete!' % session_id)

