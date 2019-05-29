from high_frequency_trading.hft.incoming_message import IncomingWSMessage
from random import randint, choice

def transform_incoming_message(source, message):
    if source == 'external' and message['type'] == 'bbo':
        message['type'] = 'external_feed_change'
        message['e_best_bid'] = message['best_bid']   
        message['e_best_offer'] = message['best_offer']
    if source == 'external' and message['type'] == 'signed_volume':
        message['type'] = 'external_feed_change'
        message['e_signed_volume'] = message['signed_volume']
    return message


def generate_random_test_orders(num_orders, session_duration):
    return iter(
            {'arrival_time': randint(10, 60) / 10,
            'price': randint(100, 110),
            'buy_sell_indicator': choice(['B', 'S']),
            'time_in_force': choice([10, 15, 20])
            } for o in range(50))


class MockWSMessage(IncomingWSMessage):

    sanitizer_cls = None

    def translate(self, message):
        return message


incoming_message_defaults = {
    'subsession_id': 0,  'market_id': 0, 'player_id': 0}