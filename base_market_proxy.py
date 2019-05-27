from twisted.internet import reactor
from hft.incoming_message import IncomingOuchMessage
from hft.market import BaseMarket
from hft.event import Event
from hft.exchange import OUCHConnectionFactory
from .protocols.ouch_proxy_protocol import ProxyOuchServerFactory, ProxyOuchClientFactory
from .protocols.json_line_protocol import JSONLineServerFactory
from itertools import count
import json
import logging

log = logging.getLogger(__name__)


class BaseMarketProxy:

    market_events = ()
    market_cls = BaseMarket
    event_cls = Event
    _ids = count(1, 1)


    def __init__(self, exchange_host, exchange_port, ouch_server_port, 
            json_line_server_port, **kwargs):
        self.market_id = next(self._ids)
        self.ouch_server_port = ouch_server_port
        self.json_line_server_port = json_line_server_port
        self.exchange_host = exchange_host
        self.exchange_port = exchange_port
        self.market = self.market_cls(0, 0, 0, exchange_host, exchange_port, **kwargs)
        self.exchange_connection = None
        self.JSON_server_conn_factory = JSONLineServerFactory(self)
        self.OUCH_server_conn_factory = ProxyOuchServerFactory(self)
        self.OUCH_client_conn_factory = ProxyOuchClientFactory(self)
    
    def handle_OUCH(self, message: IncomingOuchMessage, original_msg: bytes, direction: int):
        if direction is 1:
            account_id = message.firm
            try:
                account_conn = self.OUCH_conn_factory.users[account_id]
            except:
                # hmm what should be the behavior in this case
                log.error('connection for account id %s not found.' % account_id)
            else:
                account_conn.sendMessage(original_msg)
        elif direction is 2:
            self.exchange_connection.sendMessage(original_msg)
        if message.type in self.market_events:
            event = self.event_cls('OUCH', message)
            self.market.handle_event(event)
            while event.broadcast_msgs:
                broadcast_msg = event.broadcast_msgs.pop()
                self.JSON_server_conn_factory.broadcast(broadcast_msg.to_json())
    
    def handle_JSON(self):
        # this is not a requirement at this point
        pass
    
    def setup(self):
        reactor.connectTCP(
            self.exchange_host, self.exchange_port, self.OUCH_client_conn_factory)
        reactor.listenTCP(self.ouch_server_port, self.OUCH_server_conn_factory)
        reactor.listenTCP(self.json_line_server_port, self.JSON_server_conn_factory)
        



    

    
