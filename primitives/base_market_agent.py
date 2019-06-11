from itertools import count
from random import choice
import string
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from high_frequency_trading.hft.event import ELOEvent
from db import db
from collections import deque

def generate_account_id(size=4):
    return ''.join(choice(string.ascii_uppercase) for i in range(size))


class BaseMarketAgent:

    _ids = count(1, 1)
    event_cls = ELOEvent

    def __init__(self, session_id, *trader_model_args, account_id=None, **trader_model_kwargs):
        self.id = next(self._ids)
        self.session_id = session_id
        self.account_id = account_id or generate_account_id()
        self._exchange_connection = None
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

    @db.freeze_state('trader_model')     
    def handle_JSON(self, message: dict):
        pass

    @db.freeze_state('trader_model')     
    def handle_OUCH(self, msg: IncomingOuchMessage):
        raise NotImplementedError()

    def run(self):
        pass


