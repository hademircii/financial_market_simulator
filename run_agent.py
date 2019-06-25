import configargparse
from twisted.internet import reactor
import draw
from discrete_event_emitter import *
from agents.pacemaker_agent import PaceMakerAgent
from agents.dynamic_agent import DynamicAgent 
from protocols.ouch_trade_client_protocol import OUCHClientFactory
from protocols.json_line_protocol import JSONLineClientFactory
from utility import random_chars
import settings
import logging as log

p = configargparse.getArgParser()
p.add('--session_duration', required=True, type=int, 
    help='required: session duration in seconds')
p.add('--debug', action='store_true')
p.add('--session_id', default=random_chars(8))
p.add('--exchange_host', default='127.0.0.1', help='Address of matching engine')
p.add('--exchange_ouch_port', required=True, type=int)
p.add('--exchange_json_port', type=int)
p.add('--external_exchange_host')
p.add('--external_exchange_json_port', type=int)
p.add('--agent_type', choices=['rabbit', 'elo'], required=True)
options, args = p.parse_known_args()

        
        
def main():
    log.basicConfig(level= log.DEBUG if options.debug else log.INFO,
        format = "[%(asctime)s.%(msecs)03d] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt = '%H:%M:%S')
    
    agent_type = options.agent_type
    session_duration = options.session_duration
    if agent_type == 'rabbit':
        random_orders = draw.elo_draw(session_duration, settings.random_orders_defaults)
        event_emitters = [RandomOrderEmitter(source_data=random_orders), ]
        agent_cls = PaceMakerAgent

    elif agent_type == 'elo':
        events = settings.agent_event_confs[0]   # well, index 0 definitely not none.
        event_emitters = [ELOSliderChangeEmitter(source_data=events['slider']), 
            ELOSpeedChangeEmitter(source_data=events['speed'])]
        agent_cls = DynamicAgent
 
    agent = agent_cls(options.session_id, options.exchange_host, 
        options.exchange_ouch_port, event_emitters=event_emitters)

    reactor.connectTCP(options.exchange_host, options.exchange_ouch_port,
        OUCHClientFactory(agent))
   
    if options.exchange_json_port:
        reactor.connectTCP(options.exchange_host, options.exchange_json_port,
            JSONLineClientFactory('focal', agent))
    
    if options.external_exchange_host:
        reactor.connectTCP(options.external_exchange_host, 
            options.external_exchange_json_port,  
            JSONLineClientFactory('external', agent))

    agent.ready()
    reactor.callLater(session_duration, agent.close_session)
    reactor.callLater(session_duration, reactor.stop)
    reactor.run()

if __name__ == '__main__':
    main()
    