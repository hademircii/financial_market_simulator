from high_frequency_trading.hft.market import ELOMarket
from high_frequency_trading.hft.event import ELOEvent
from primitives.base_market_proxy import BaseMarketProxy

class ELOMarketProxy(BaseMarketProxy):
    market_event_headers = ('E', 'Q')
    private_exchange_message_headers = ('A', 'U', 'C', 'E')
    market_cls =  ELOMarket
    event_cls = ELOEvent