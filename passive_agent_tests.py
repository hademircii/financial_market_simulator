from twisted.internet import reactor
from passive_agent import PassiveAgent
from protocols.json_line_protocol import JSONLineClientFactory
from protocols.ouch_trade_client_protocol import OUCHClientFactory
import time
import logging

logging.basicConfig(level=logging.DEBUG)

focal_exchange_host = '127.0.0.1'
focal_exchange_ouch_port = 9100

if __name__ == '__main__':
    agent = PassiveAgent()
    reactor.connectTCP(focal_exchange_host, focal_exchange_ouch_port,
        OUCHClientFactory(agent))
    agent.run()
    reactor.run()
    