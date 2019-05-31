from twisted.internet import reactor
from high_frequency_trading.hft.market import ELOMarket
from high_frequency_trading.hft.event import ELOEvent
from primitives.base_market_proxy import BaseMarketProxy
from protocols.ouch_proxy_protocol import ProxyOuchServerFactory, ProxyOuchClientFactory
from protocols.json_line_protocol import JSONLineServerFactory
import logging

logging.basicConfig(level=logging.DEBUG)

class ELOMarketProxy(BaseMarketProxy):
    market_events = ('E', 'Q')
    public_msg_types = ('Q', )
    market_cls =  ELOMarket
    event_cls = ELOEvent

if __name__ == '__main__':
    exchange_host, exchange_port = '127.0.0.1', 9001
    proxy_server_port = 9100
    json_line_server_port = 9200
    proxy_server = ELOMarketProxy(exchange_host, exchange_port, session_duration=240)
    reactor.connectTCP(exchange_host, exchange_port, 
        ProxyOuchClientFactory(proxy_server))
    reactor.listenTCP(proxy_server_port, ProxyOuchServerFactory(proxy_server))
    reactor.listenTCP(json_line_server_port, JSONLineServerFactory(
        proxy_server))
    reactor.run()
