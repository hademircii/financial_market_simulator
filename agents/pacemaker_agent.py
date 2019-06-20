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
# 'next's it and sends orders to the exchange
# does not react (except handling exchange responses)
# or adjust market position
# does not listen to public message channel as well.

ws_message_defaults = {
    'subsession_id': 0,  'market_id': 0, 'player_id': 0,
    'type': 'investor_arrivals'}

class PaceMakerAgent(BaseMarketAgent):

    message_class = MockWSMessage

    trader_model_cls = ELOInvestor

    def __init__(self, session_duration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trader_model = self.trader_model_cls(self.session_id, 0, 1, 0, 'investor', 
            0, 0, firm=self.account_id)
        self.exchange_connection = None

    @db.freeze_state('trader_model') 
    def handle_OUCH(self, msg):
        event = self.event_cls('exchange', msg)
        self.trader_model.handle_event(event)
        return event

    def handle_discrete_event(self, event_data):
        if event_data['type'] is 'investor_arrivals':
            self.enter_order(event_data)

    def enter_order(self, order_data):
        message = MockWSMessage(order_data, **ws_message_defaults)
        event = self.event_cls('random_order', message)
        self.trader_model.handle_event(event)
        while event.exchange_msgs:
            message = event.exchange_msgs.pop()
            if self.exchange_connection is not None:
                self.exchange_connection.sendMessage(message.translate(), message.delay)
            else:
                self.outgoing_msg.append((message.translate(), message.delay))
