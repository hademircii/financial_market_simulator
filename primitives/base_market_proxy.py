from twisted.internet import reactor
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from high_frequency_trading.hft.market import BaseMarket
from high_frequency_trading.hft.event import Event
from db import db
from collections import deque
import utility
import json
import logging

log = logging.getLogger(__name__)


class BaseMarketProxy:
    tag = 'market'
    market_event_headers = ()
    private_exchange_message_headers = ()
    market_cls = BaseMarket
    event_cls = Event

    def __init__(self, tag, session_id, exchange_host, exchange_port, 
                    **kwargs):
        self.market_id = 0 if tag == 'focal' else 1
        self.session_id = session_id
        self.model = self.market_cls(self.market_id, 0, session_id, 
                exchange_host, exchange_port, **kwargs)
        self.exchange_connection = None
        self.json_server_factory = None
        self.ouch_server_factory = None
        # queue to store messages 
        # when ouch channel to exchange is down.
        self.outgoing_queue = deque(maxlen=100)
    
    @db.freeze_state()     
    def handle_OUCH(self, message: IncomingOuchMessage, original_msg: bytes, direction: int):
        # outbound message
        if direction is 1:
            # assume public messages will be broadcasted over
            # a separate channel, and filtered by a market model.
            # so only handle private messages here, ignore the rest
            if message.type in self.private_exchange_message_headers:
                try:
                    account_id = message.firm
                except AttributeError:
                    firm = utility.extract_firm_from_message(message)
                    if firm:
                        account_id = firm
                    else:
                        raise Exception('unable to determine recipient for: %s' % message)
                try:
                    account_conn = self.ouch_server_factory.users[account_id]
                except KeyError:
                    log.error('connection for account id %s not found.' % account_id)
                else:
                    account_conn.sendMessage(original_msg, 0)
        # inbound message
        elif direction is 2:
            if self.exchange_connection is None:
                self.outgoing_queue.append(message)
                log.debug('message %s in queue..' % message)
            else:
                while self.outgoing_queue:
                    earlier_msg = self.outgoing_queue.popleft()
                    self.exchange_connection.sendMessage(earlier_msg, 0)
                self.exchange_connection.sendMessage(original_msg, 0)
        else:
            log.error('invalid message direction %s' % direction)
        if hasattr(message, 'type') and message.type in self.market_event_headers:
            # the message should be handled by the market model
            event = self.event_cls('OUCH', message)
            self.model.handle_event(event)
            while event.broadcast_msgs:
                broadcast_msg = event.broadcast_msgs.pop()
                self.json_server_factory.broadcast(broadcast_msg)
                log.info('broadcast after handling %s event: %s' % (
                    event.event_type, broadcast_msg))
            return event
    
    @db.freeze_state()
    def handle_JSON(self):
        # this is not a requirement at this point
        pass
 
    @db.freeze_state()       
    def close_session(self):
        msg = utility.get_mock_market_msg({}, 'market_end')
        event = self.event_cls('market close', msg)
        self.model.handle_event(event)
        return event


    

    
