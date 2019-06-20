from primitives.base_market_agent import BaseMarketAgent
from db import db
from high_frequency_trading.hft.trader import ELOTrader
from high_frequency_trading.hft.incoming_message import IncomingMessage
import utility
from itertools import count
import string
from random import choice
import logging

log = logging.getLogger(__name__)
# this is an active agent
# listens on 2 different channels
# treats one as focal market and sends orders to it
# treats other as external market and receives signals
# reacts to market events and readjusts position

def generate_account_id(size=4):
    return ''.join(choice(string.ascii_uppercase) for i in range(size))


class DynamicAgent(BaseMarketAgent):
    trader_model_cls = ELOTrader

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trader_model = self.trader_model_cls(self.session_id, 0, self.id, self.id, 'automated', 
                '', 0, firm=self.account_id)

    @db.freeze_state('trader_model')   
    def handle_JSON(self, message: dict, type_code:str):
        clean_message = utility.transform_incoming_message(type_code, message)
        msg = IncomingMessage(clean_message)
        log.debug('received json message %s' % msg)
        event = self.event_cls(type_code, msg)
        self.trader_model.handle_event(event)
        event = self.process_event(event)
        return event

    @db.freeze_state('trader_model')           
    def handle_OUCH(self, msg):
        event = self.event_cls('OUCH', msg)
        log.debug('received ouch message %s' % msg)
        self.trader_model.handle_event(event)
        event = self.process_event(event)
        return event

    @db.freeze_state('trader_model')
    def handle_discrete_event(self, event_data):
        clean_message = utility.transform_incoming_message(event_data)
        log.debug('received discrete event message %s' % clean_message)
        event = self.event_cls('scheduled event', clean_message)
        event = self.process_event(event)
        return event







