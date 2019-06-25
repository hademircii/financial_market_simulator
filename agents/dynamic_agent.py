from primitives.base_market_agent import BaseMarketAgent
from db import db
from high_frequency_trading.hft.trader import ELOTrader
from high_frequency_trading.hft.incoming_message import IncomingMessage
import utility
from itertools import count
import string
from random import choice
import settings
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

    def __init__(self, session_id, *args, **kwargs):
        super().__init__(session_id, *args, **kwargs)
        self.trader_model = self.trader_model_cls(self.session_id, 0, self.id, self.id, 'automated', 
                '', 0, firm=self.account_id)
        # the agent expects an external feed message
        # with fields e_best_bid e_best_offer e_signed_volume
        # so I need a hack as market proxies always send those 
        # separately, this is very specific to elo environment
        self.external_market_state = {'e_best_bid': None, 'e_best_offer': None, 
            'e_signed_volume': 0}

    @db.freeze_state('trader_model')   
    def ready(self):
        super().ready()
        msg = utility.get_mock_market_msg(settings.initial_trader_state,
            'market_start')
        event = self.event_cls('initial state', msg)
        self.trader_model.handle_event(event)
        return event

    @db.freeze_state('trader_model')       
    def close_session(self):
        msg = utility.get_mock_market_msg({}, 'market_end')
        event = self.event_cls('market close', msg)
        event.attach(tax_rate=settings.market_settings['tax_rate'])
        self.trader_model.handle_event(event)
        log.info('agent %s:%s --> closing session %s..' % (
            self.account_id, self.typecode, self.session_id))
        return event

    @db.freeze_state('trader_model')   
    def handle_JSON(self, message: dict, type_code:str):
        clean_message = utility.transform_incoming_message(type_code, message,
            self.external_market_state)
        msg = IncomingMessage(clean_message)
        log.debug('agent %s:%s --> received json message %s:%s' % (
            self.account_id, self.typecode, type_code, msg))
        event = self.event_cls(type_code, msg)
        self.trader_model.handle_event(event)
        log.warning('exchange_messages %s' % event.exchange_msgs)
        self.process_event(event)
        return event

    @db.freeze_state('trader_model')           
    def handle_OUCH(self, msg):
        event = self.event_cls('OUCH', msg)
        log.debug('agent %s:%s --> received ouch message %s' % (
            self.account_id ,self.typecode, msg))
        self.trader_model.handle_event(event)
        self.process_event(event)
        return event

    @db.freeze_state('trader_model')
    def handle_discrete_event(self, event_data):
        clean_message = utility.transform_incoming_message('scheduled event', 
                            event_data)
        clean_message = IncomingMessage(clean_message)
        log.debug('agent %s:%s: received discrete event message %s' % (
                    self.account_id, self.typecode, clean_message))
        event = self.event_cls('scheduled event', clean_message)
        self.trader_model.handle_event(event)
        self.process_event(event)
        return event







