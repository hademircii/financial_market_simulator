from primitives.base_market_agent import BaseMarketAgent
from db import db
from high_frequency_trading.hft.trader import ELOTrader
from high_frequency_trading.hft.incoming_message import IncomingMessage
import utility
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
    typecode = 'elo_interactive_agent'
    handled_ouch_events = ('C', 'U', 'E', 'A')
    handled_external_market_events = ('external_feed_change', )
    handled_focal_market_events = ('bbo_change', 'signed_volume_change', 'reference_price_change')

    def __init__(self, session_id, *args, **kwargs):
        super().__init__(session_id, *args, **kwargs)
        self.model = self.trader_model_cls(
            self.session_id, 0, self.id, self.id, 'automated', '', 0, 
            firm=self.account_id, **kwargs)
        # the agent expects an external feed message
        # with fields e_best_bid e_best_offer e_signed_volume
        # so I need a hack as market proxies always send those 
        # separately, this is very specific to elo environment
        self.external_market_state = {'e_best_bid': None, 'e_best_offer': None, 
            'e_signed_volume': 0}

    @db.freeze_state()   
    def handle_JSON(self, message: dict, type_code:str):
        clean_message = utility.transform_incoming_message(type_code, message,
            self.external_market_state)
        msg_type = clean_message['type']
        log.info('received json message with type --> %s' % msg_type)
        if (type_code == 'focal' and msg_type in self.handled_focal_market_events) or (
            type_code == 'external' and msg_type in self.handled_external_market_events):
            msg = IncomingMessage(clean_message)
            log.info('agent %s:%s --> handling json message %s:%s' % (
                self.account_id, self.typecode, type_code, msg))
            event = self.event_cls(type_code, msg)
            self.model.handle_event(event)
            self.process_event(event)
            return event

    @db.freeze_state()           
    def handle_OUCH(self, msg):
        event = self.event_cls('OUCH', msg)
        log.info('received ouch message with type --> %s' % event.event_type)
        if event.event_type in self.handled_ouch_events:
            log.info('agent %s:%s --> handling ouch message %s' % (
                self.account_id ,self.typecode, msg))
            self.model.handle_event(event)
            self.process_event(event)
        return event

    @db.freeze_state()
    def handle_discrete_event(self, event_data):
        clean_message = utility.transform_incoming_message('scheduled event', 
                            event_data)
        clean_message = IncomingMessage(clean_message)
        log.info('agent %s:%s: received discrete event message %s' % (
                    self.account_id, self.typecode, clean_message))
        event = self.event_cls('scheduled event', clean_message)
        self.model.handle_event(event)
        self.process_event(event)
        return event







