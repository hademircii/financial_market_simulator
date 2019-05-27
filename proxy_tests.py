from twisted.internet import reactor
from high_frequency_trading.hft.market import ELOMarket
from high_frequency_trading.hft.event import ELOEvent
from .base_market_broker import BaseMarketProxy

class ELOMarketProxy(BaseMarketProxy):
    market_events = ('E', 'Q')
    market_cls =  ELOMarket
    event_cls = ELOEvent

if __name__ == '__main__':
    host, port = '127.0.0.1', 9001
    proxy_server = ELOMarketProxy(host, port, session_duration=240)
    reactor.run()
