from twisted.internet import reactor
from high_frequency_trading.hft.trader import ELOTrader
from high_frequency_trading.protocols.ouch_trade_client_protocol import OUCHClientFactory
from high_frequency_trading.protocols.json_line_protocol import JSONLineClientFactory
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from high_frequency_trading.hft.event import Event
from high_frequency_trading.hft.incoming_message import IncomingMessage
from . import utility
from itertools import count
import string
from random import choice


def generate_account_id(size=4):
    return ''.join(choice(string.ascii_uppercase) for i in range(size))


class MarketClient:

    _ids = count(1, 1)
    event_cls = Event


    def __init__(self, focal_exchange_host, focal_exchange_ouch_port, 
            focal_exchange_json_line_port, external_exchange_host, 
            external_exchange_json_line_port):
        self.account_id = generate_account_id()
        self.trader_id = next(self._ids)
        self.trader = ELOTrader(0, 0, self.trader_id, self.trader_id,
            focal_exchange_host, focal_exchange_ouch_port, 'automated', 
            firm=self.account_id)
        self.focal_exchange_host = focal_exchange_host
        self.focal_exchange_ouch_port = focal_exchange_ouch_port
        self.focal_exchange_json_line_port = focal_exchange_json_line_port
        self.external_exchange_host = external_exchange_host
        self.external_exchange_json_line_port = external_exchange_json_line_port
        self.focal_exchange_conn = None
    
    def handle_JSON(self, message: dict, type_code:str):
        clean_message = message
        if type_code == 'external':
            clean_message = utility.transform_incoming_message('external', message)
        msg = IncomingMessage(clean_message)
        event = self.event_cls(type_code, msg)
        self.trader.handle_event(event)
        while event.exchange_msgs:
            e_msg = event.exchange_msgs.pop()
            self.focal_exchange_conn.sendMessage(e_msg.translate(), e_msg.delay)
        
    def handle_OUCH(self, msg: IncomingOuchMessage):
        event = self.event_cls('OUCH', msg)
        self.trader.handle_event(event)
        while event.exchange_msgs:
            e_msg = event.exchange_msgs.pop()
            self.focal_exchange_conn.sendMessage(e_msg.translate(), e_msg.delay)

    def connect(self):
        reactor.connectTCP(self.focal_exchange_host, self.focal_exchange_json_line_port,
            JSONLineClientFactory('focal', self))
        reactor.connectTCP(self.focal_exchange_host, self.focal_exchange_ouch_port,
            OUCHClientFactory(self))
        reactor.connectTCP(self.external_exchange_host, self.external_exchange_json_line_port,
            JSONLineClientFactory('external', self))