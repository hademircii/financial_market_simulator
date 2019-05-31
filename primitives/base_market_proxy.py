from twisted.internet import reactor
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from high_frequency_trading.hft.market import BaseMarket
from high_frequency_trading.hft.event import Event
from itertools import count
from collections import deque
import utility
import json
import logging

log = logging.getLogger(__name__)


class BaseMarketProxy:

    market_events = ()
    public_msg_types = ()
    market_cls = BaseMarket
    event_cls = Event
    _ids = count(1, 1)


    def __init__(self, exchange_host, exchange_port, **kwargs):
        self.market_id = next(self._ids)
        self.market = self.market_cls(0, 0, 0, exchange_host, exchange_port, **kwargs)
        self.exchange_connection = None
        self.json_server_factory = None
        self.ouch_server_factory = None
        self.outgoing_queue = deque(maxlen=100)
    
    def handle_OUCH(self, message: IncomingOuchMessage, original_msg: bytes, direction: int):
        if direction is 1:
            if message.type in self.public_msg_types:
                self.ouch_server_factory.broadcast(original_msg)
            else:
                try:
                    account_id = message.firm
                except AttributeError:
                    firm = utility.extract_firm_from_message(message)
                    if firm:
                        account_id = firm
                    else:
                        raise Exception('unable to find recipient for: %s' % message)
                try:
                    account_conn = self.ouch_server_factory.users[account_id]
                except KeyError:
                    # hmm what should be the behavior in this case
                    log.error('connection for account id %s not found.' % account_id)
                else:
                    account_conn.sendMessage(original_msg, 0)
        elif direction is 2:
            if self.exchange_connection is None:
                self.outgoing_queue.append(message)
                log.debug('message %s in queue..' % message)
            else:
                while self.outgoing_queue:
                    earlier_msg = self.outgoing_queue.popleft()
                    self.exchange_connection.sendMessage(earlier_msg, 0)
                self.exchange_connection.sendMessage(original_msg, 0)
        if hasattr(message, 'type') and message.type in self.market_events:
            event = self.event_cls('OUCH', message)
            self.market.handle_event(event)
            while event.broadcast_msgs:
                broadcast_msg = event.broadcast_msgs.pop()
                self.json_server_factory.broadcast(broadcast_msg.to_json())
    
    def handle_JSON(self):
        # this is not a requirement at this point
        pass

        



    

    
