from itertools import count
from random import choice
import string
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from high_frequency_trading.hft.event import ELOEvent
from db import db
from collections import deque
import utility
import logging

log = logging.getLogger(__name__)


class BaseMarketAgent:
    tag = 'agent'
    _ids = count(1, 1)
    event_cls = ELOEvent
    typecode = ''

    def __init__(self, session_id, *trader_model_args, account_id=None, 
                    event_emitters=None, **kwargs):
        self.id = next(self._ids)
        self.session_id = session_id
        self.model = None   # trader model plugs here..
        self.account_id = account_id or utility.generate_account_id()
        self.trader_model = None
        self._exchange_connection = None
        self.event_emitters = event_emitters
        self.outgoing_msg = deque()

    @property
    def exchange_connection(self):
        return self._exchange_connection

    @exchange_connection.setter
    def exchange_connection(self, conn):
        self._exchange_connection = conn
        while self.outgoing_msg:
            msg, delay = self.outgoing_msg.popleft()
            self._exchange_connection.sendMessage(msg, delay)

    @db.freeze_state()     
    def handle_JSON(self, message: dict):
        pass

    @db.freeze_state()     
    def handle_OUCH(self, msg: IncomingOuchMessage):
        raise NotImplementedError()

    @db.freeze_state()        
    def handle_discrete_event(self, event_data: dict):
        raise NotImplementedError()
    
    def process_event(self, event):
        while event.exchange_msgs:
            e_msg = event.exchange_msgs.pop()
            log.info('responding %s event with message ---> %s' % (event.event_type,
                e_msg))
            self.exchange_connection.sendMessage(e_msg.translate(), e_msg.delay)

    @db.freeze_state()
    def ready(self):
        if self.event_emitters:
            for em in self.event_emitters:
                em.owner = self
                em.register_events() 
        msg = utility.get_mock_market_msg(
                    utility.get_traders_initial_market_view(), 'market_start')
        event = self.event_cls('initial state', msg)
        self.model.handle_event(event)
        return event

    @db.freeze_state()       
    def close_session(self):
        msg = utility.get_mock_market_msg({}, 'market_end')
        event = self.event_cls('market close', msg)
        self.model.handle_event(event)
        log.info('agent %s:%s --> closing session %s..' % (
            self.account_id, self.typecode, self.session_id))
        return event

