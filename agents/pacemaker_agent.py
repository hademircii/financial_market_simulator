from primitives.base_market_agent import BaseMarketAgent
from high_frequency_trading.hft.trader import ELOInvestor
from utility import MockWSMessage
from discrete_event_emitter import RandomOrderEmitter
import draw
from db import db
import logging

log = logging.getLogger(__name__)

# this is a passive agent
# given a random order generator
# 'next's it and derives orders from data 
# to send the matching engine/proxy
# does not react (except handling exchange responses)
# or adjusts market position via price producer model,
# does not handle public messages as well.


class PaceMakerAgent(BaseMarketAgent):

    message_class = MockWSMessage

    trader_model_cls = ELOInvestor

    def __init__(self, session_id, *args, **kwargs):
        super().__init__(session_id, *args,  **kwargs)
        self.model = self.trader_model_cls(self.session_id, 0, 1, 0, 'investor', 
            0, 0, firm=self.account_id, **kwargs)
        self.exchange_connection = None

    @db.freeze_state() 
    def handle_OUCH(self, msg):
        event = self.event_cls('exchange', msg)
        log.info('agent %s:%s --> handling ouch message %s' % (
                  self.account_id ,self.typecode, event.event_type))
        self.model.handle_event(event)
        return event

    def handle_discrete_event(self, event_data):
        if event_data['type'] is 'investor_arrivals':
            self.enter_order(event_data)

    def enter_order(self, order_data):
        message = MockWSMessage(order_data, type='investor_arrivals', 
                                subsession_id=0, market_id=0, player_id=0)
        event = self.event_cls('random_order', message)
        self.model.handle_event(event)
        while event.exchange_msgs:
            message = event.exchange_msgs.pop()
            if self.exchange_connection is not None:
                self.exchange_connection.sendMessage(message.translate(), message.delay)
            else:
                self.outgoing_msg.append((message.translate(), message.delay))
