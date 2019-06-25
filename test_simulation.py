# elo simulation
import shlex
from honcho.manager import Manager
import settings
import utility
# assume matching engines are running and listening


conf = settings.elo_simulation_configs
session_id = utility.random_chars(8)
focal_proxy = 'python run_proxy.py --debug --ouch_port {0} --json_port {1} \
        --session_id {2}'.format(conf['focal_proxy_ouch_port'], 
        conf['focal_proxy_json_port'], session_id), 'focal_proxy'
external_proxy = 'python run_proxy.py --debug --ouch_port {0} --json_port {1} \
    --session_id {2} --exchange_port {3}'.format(conf['external_proxy_ouch_port'], 
        conf['external_proxy_json_port'], session_id, 9002), 'external_proxy'
rabbit_agent_focal = 'python run_agent.py --session_duration {0} --exchange_ouch_port {1} \
    --session_id {2} --agent_type rabbit'.format(conf['session_duration'], 
        conf['focal_proxy_ouch_port'], session_id), 'rabbit_agent_focal'
rabbit_agent_external = 'python run_agent.py --session_duration {0} --exchange_ouch_port {1} \
    --session_id {2} --agent_type rabbit'.format(conf['session_duration'], 
        conf['external_proxy_ouch_port'], session_id), 'rabbit_agent_external'
dynamic_agent = 'python run_agent.py --session_duration {0} --exchange_ouch_port {1} \
    --exchange_json_port {2}  --external_exchange_host 127.0.0.1 \
        --external_exchange_json_port {3} --session_id {4} --agent_type elo --debug'.format(
            conf['session_duration'], conf['focal_proxy_ouch_port'], 
            conf['focal_proxy_json_port'], 
            conf['external_proxy_json_port'],
            session_id), 'dynamic_agent'

m = Manager()
for pair in (focal_proxy, external_proxy, rabbit_agent_focal, rabbit_agent_external,
            dynamic_agent):
    m.add_process(pair[1], pair[0])
m.loop()

