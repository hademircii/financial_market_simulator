from high_frequency_trading.hft.market import ELOMarket
from high_frequency_trading.hft.event import ELOEvent
from primitives.base_market_proxy import BaseMarketProxy

class ELOMarketProxy(BaseMarketProxy):
    market_events = ('E', 'Q')
    public_msg_types = ('Q', )
    market_cls =  ELOMarket
    event_cls = ELOEvent