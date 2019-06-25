from high_frequency_trading.hft.incoming_message import IncomingWSMessage, IncomingMessage
from random import randint, choice
import string
import csv

SESSION_CODE_CHARSET = string.ascii_lowercase + string.digits  # otree <3

def random_chars(num_chars):
    return ''.join(choice(SESSION_CODE_CHARSET) for _ in range(num_chars))    

def transform_incoming_message(source, message, external_market_state=None):
    
    if source == 'external':
        if message['type'] == 'reference_price':
             message['type'] = 'external_reference_price'
        if not external_market_state:
            raise Exception('external_market_state is none.')
        if message['type'] == 'bbo':
            message['e_best_bid'] = message['best_bid']   
            message['e_best_offer'] = message['best_offer']
            external_market_state['e_best_bid'] = message['best_bid']   
            external_market_state['e_best_offer'] = message['best_offer']
            message['e_signed_volume'] = external_market_state['e_signed_volume']
            if message['e_signed_volume'] is None:
                message['e_signed_volume'] = 0
            message['type'] = 'external_feed_change'
        if message['type'] == 'signed_volume':
            message['e_signed_volume'] = message['signed_volume']
            message['e_best_bid'] = external_market_state['e_best_bid']   
            message['e_best_offer'] = external_market_state['e_best_offer']
            external_market_state['e_signed_volume'] = message['signed_volume']
            message['type'] = 'external_feed_change'
    if message['type'] == 'bbo':
        message['type'] = 'bbo_change'
    if message['type'] == 'signed_volume':
        message['type'] = 'signed_volume_change'
    if 'technology_on' in message:
        message['value'] = message['technology_on']
    message['subsession_id'] = 0
    message['market_id'] = 0
    return message

def generate_random_test_orders(num_orders, session_duration):
    return iter(
            {'arrival_time': randint(10, 60) / 10,
            'price': randint(100, 110),
            'buy_sell_indicator': choice(['B', 'S']),
            'time_in_force': choice([10, 15, 20])
            } for o in range(50))

def extract_firm_from_message(message):
    if hasattr(message, 'order_token'):
        return message.order_token[:4]


def read_agent_events_from_csv(path):
    """ well this code sucks but it is very specific to elo"""
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader) # first row is column names
        rows = list(reader)
        num_agents = max([int(row[1]) for row in rows])
        input_lists = [{'speed': [], 'slider': []} for _ in range(num_agents)]
        for row in rows:
            arrival_time, agent_num, tech_subsc, a_x, a_y, a_z = row
            agent_num = int(agent_num)
            speed_row = (arrival_time, tech_subsc)
            slider_row = (arrival_time, a_x, a_y, a_z)
            input_lists[agent_num - 1]['speed'].append(speed_row)
            input_lists[agent_num - 1]['slider'].append(slider_row)
    return input_lists


def get_mock_market_msg(market_facts:dict, msg_type:str):
    mock_msg = market_facts
    mock_msg['type'] = msg_type
    mock_msg['subsession_id'] = 0
    mock_msg['market_id'] = 0
    msg = IncomingMessage(mock_msg)
    return msg


class MockWSMessage(IncomingWSMessage):

    sanitizer_cls = None

    def translate(self, message):
        return message


incoming_message_defaults = {
    'subsession_id': 0,  'market_id': 0, 'player_id': 0}


fields_to_freeze =  {
    'trader_model': {
        'events_to_capture': ('speed_change', 'role_change', 'slider', 
                'market_start', 'market_end', 'A', 'U', 'C', 'E'),
        'properties_to_serialize': (
            'subsession_id', 'market_id', 'id_in_market', 'player_id', 'delay', 
            'staged_bid', 'staged_offer', 'net_worth', 'cash', 'cost', 'tax_paid',
            'speed_cost', 'implied_bid', 'implied_offer', 'best_bid_except_me',
            'best_offer_except_me', 'account_id'),
        'subproperties_to_serialize': {
            'trader_role': ('trader_model_name', ),
            'sliders': ('slider_a_x', 'slider_a_y', 'slider_a_z'),
            'orderstore': ('inventory', 'bid', 'offer', 'firm'),
            'inventory': ('position', ),
            'market_facts': (
                'reference_price', 'best_bid', 'best_offer', 
                'signed_volume', 'e_best_bid', 'e_best_offer', 'e_signed_volume',
                'next_bid', 'next_offer', 'volume_at_best_bid', 'volume_at_best_offer')
        }
    },
    'market': {
        'events_to_capture': ('Q', 'E', 'market_start', 'market_end',
            'external_feed'), 
        'properties_to_serialize': ('subsession_id', 'market_id'),
        'subproperties_to_serialize': {
            'bbo': ('best_bid', 'best_offer', 'next_bid', 'next_offer', 
                    'volume_at_best_bid', 'volume_at_best_offer'),
            'external_feed': ('e_best_bid', 'e_best_offer', 'e_signed_volume'),
            'signed_volume': ('signed_volume', ),
            'reference_price': ('reference_price', ),
        }
    }
}


