from primitives.base_market_agent import BaseMarketAgent
from high_frequency_trading.hft.trader import ELOInvestor
from utility import MockWSMessage, generate_random_test_orders
from db import db
import logging

log = logging.getLogger(__name__)

# this is a passive agent
# given a random order generator
# 'next's it and sends orders to the exchange
# does not react (except handling exchange responses)
# or adjusts market position
# does not listen on public message channel as well.

ws_message_defaults = {
    'subsession_id': 0,  'market_id': 0, 'player_id': 0,
    'type': 'investor_arrivals'}

NUM_ORDERS = 60

class PassiveAgent(BaseMarketAgent):

    default_trader_model_args = (0, 0, 0, 1, 'investor', 0, 0)
    message_class = MockWSMessage
    required_message_fields = {
        'arrival_time': float, 'price': int, 'buy_sell_indicator': str, 
        'time_in_force': int}
    trader_model_cls = ELOInvestor

    def __init__(self, session_duration=60, random_order_file=None):
        super().__init__()
        self.trader_model = self.trader_model_cls(
            *self.default_trader_model_args, firm=self.account_id)
        self.random_order_generator = generate_random_test_orders(NUM_ORDERS, session_duration)
        self.exchange_connection = None

    def run(self):
        try:
            while True:
                new_order = self.generate_order()
                self.enter_order(new_order, new_order['arrival_time'])
        except StopIteration:
            log.debug('all orders are scheduled.')

    @db.freeze_state('trader_model') 
    def handle_OUCH(self, msg):
        event = self.event_cls('exchange', msg)
        self.trader_model.handle_event(event)
        return event

    def generate_order(self, *args, **kwargs):
        new_order = next(self.random_order_generator)
        req_flds = self.required_message_fields
        for field, _ in req_flds.items():
            if field not in new_order:
                raise Exception('key %s is missing in %s' % (field, new_order))
            else:
                required_type = req_flds[field]
                if not isinstance(new_order[field], required_type):
                    new_order[field] = required_type(new_order[field])
        return new_order

    def enter_order(self, order, delay):
        message = MockWSMessage(order, **ws_message_defaults)
        event = self.event_cls('random_order', message)
        self.trader_model.handle_event(event)
        while event.exchange_msgs:
            message = event.exchange_msgs.pop()
            if self.exchange_connection is not None:
                self.exchange_connection.sendMessage(message.translate(), delay)
            else:
                self.outgoing_msg.append((message.translate(), delay))
