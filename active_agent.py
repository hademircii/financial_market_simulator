from twisted.internet import reactor
from primitives.base_market_agent import BaseMarketAgent
from high_frequency_trading.hft.trader import ELOTrader
from high_frequency_trading.hft.incoming_message import IncomingMessage
from . import utility
from itertools import count
import string
from random import choice


# this is an active agent
# listens on 2 different channels
# treats one as focal market and sends orders to it
# treats other as external market and receives signals
# reacts to market events and readjusts position

def generate_account_id(size=4):
    return ''.join(choice(string.ascii_uppercase) for i in range(size))


class ActiveAgent(BaseMarketAgent):
    trader_model_cls = ELOTrader

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trader_model = self.trader_model_cls(0, 0, self.id, self.id, '', 0, 
                'automated', firm=self.account_id)
    
    def handle_JSON(self, message: dict, type_code:str):
        clean_message = message
        if type_code == 'external':
            clean_message = utility.transform_incoming_message('external', message)
        msg = IncomingMessage(clean_message)
        event = self.event_cls(type_code, msg)
        self.trader_model.handle_event(event)
        while event.exchange_msgs:
            e_msg = event.exchange_msgs.pop()
            self.exchange_connection.sendMessage(e_msg.translate(), e_msg.delay)
        
    def handle_OUCH(self, msg):
        event = self.event_cls('OUCH', msg)
        self.trader_model.handle_event(event)
        while event.exchange_msgs:
            e_msg = event.exchange_msgs.pop()
            self.exchange_connection.sendMessage(e_msg.translate(), e_msg.delay)

    # def connect(self):
    #     reactor.connectTCP(self.focal_exchange_host, self.focal_exchange_json_line_port,
    #         JSONLineClientFactory('focal', self))
    #     reactor.connectTCP(self.focal_exchange_host, self.focal_exchange_ouch_port,
    #         OUCHClientFactory(self))
    #     if self.external_exchange_host is not None:
    #         reactor.connectTCP(self.external_exchange_host, self.external_exchange_json_line_port,
    #             JSONLineClientFactory('external', self))