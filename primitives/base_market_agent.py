from itertools import count
from random import choice
import string
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from high_frequency_trading.hft.event import Event

def generate_account_id(size=4):
    return ''.join(choice(string.ascii_uppercase) for i in range(size))


class BaseMarketAgent:

    _ids = count(1, 1)
    event_cls = Event

    def __init__(self, *trader_model_args, account_id=None, **trader_model_kwargs):
        self.id = next(self._ids)
        self.account_id = account_id or generate_account_id()
        self._exchange_connection = None

    @property
    def exchange_connection(self):
        return self._exchange_connection

    @exchange_connection.setter
    def exchange_connection(self, conn):
        self._exchange_connection = conn

    def handle_JSON(self, message: dict):
        pass

    def handle_OUCH(self, msg: IncomingOuchMessage):
        raise NotImplementedError()



