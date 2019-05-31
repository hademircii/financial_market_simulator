from twisted.internet import reactor
from .active_agent import ActiveAgent
from .protocols.json_line_protocol import JSONLineClientFactory
from .protocols.ouch_trade_client_protocol import OUCHClientFactory

focal_exchange_host = '127.0.0.1'
focal_exchange_ouch_port = 9100
focal_exchange_json_port = 9200

external_exchange_host = None
external_exchange_json_line_port = None

if __name__ == '__main__':
    agent = ActiveAgent()
    reactor.connectTCP(focal_exchange_host, focal_exchange_json_port,
        JSONLineClientFactory('focal', agent))
    reactor.connectTCP(focal_exchange_host, focal_exchange_ouch_port,
        OUCHClientFactory(agent))
    if external_exchange_host is not None:
        reactor.connectTCP(external_exchange_host, external_exchange_json_line_port,
            JSONLineClientFactory('external', agent))