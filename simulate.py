import configargparse
import honcho.manager
import logging as log

p = configargparse.getArgParser()
p.add('--host', default='127.0.0.1')
p.add('--focal_exchange_host', default='127.0.0.1')
p.add('--focal_exchange_port', default=9001, help='OUCH port to listen on')
p.add('--external_exchange_host', default=None)
p.add('--external_exchange_port', default=None)
p.add('--focal_proxy_ouch_port', default=9201)
p.add('--focal_proxy_json_port', default=9202)
p.add('--external_proxy_ouch_port', default=None)
p.add('--external_proxy_json_port', default=None)
p.add('--num_dynamic_agents', default=1)
p.add('--logfile', default=None, type=str)
options, args = p.parse_known_args()

dynamic_agent_ports = range(9301,9399)

# this will not run matching engines, 
# assumes they are already there and listening
# on specified addresses and ports

def main():
    log.basicConfig(level= log.DEBUG if options.debug else log.INFO,
        format = "[%(asctime)s.%(msecs)03d] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt = '%H:%M:%S',
        filename = options.logfile)
