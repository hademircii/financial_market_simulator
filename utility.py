from high_frequency_trading.hft.incoming_message import IncomingWSMessage, IncomingMessage
from twisted.internet import reactor, error
from random import randint, choice
import subprocess
import shlex
import settings
import string
import csv
import logging
import datetime
import yaml

log = logging.getLogger(__name__)

SESSION_CODE_CHARSET = string.ascii_lowercase + string.digits  # otree <3


def get_simulation_parameters():
    custom_parameters = read_yaml(settings.custom_config_path)
    merged_parameters = settings.default_simulation_parameters.copy()
    if custom_parameters:
        for k, v in custom_parameters.items():
            if k in merged_parameters:
                merged_parameters[k] = v
    return merged_parameters


def get_elo_agent_parameters(
        parameter_names=('a_x_multiplier', 'a_y_multiplier', 'speed_unit_cost')
    ):
    all_parameters = get_simulation_parameters()
    return {k: all_parameters[k] for k in parameter_names}


def export_session_report(session_id: str, session_note: str):
    params = get_simulation_parameters()
    timestamp = datetime.datetime.now()
    path = settings.params_export_path.format(session_id=session_id, 
        timestamp=timestamp)
    str_params = '\n\t'.join('{0}:{1}'.format(k, v) for k, v in params.items())
    report = 'session note:\n    %s\nparameters:\n\t%s' % (session_note, str_params)
    with open(path, 'w') as f:
        f.write(report)


def get_agent_state_config(config_number=None):
    events = read_agent_events_from_csv(settings.agent_event_config_path)
    if config_number is not None:
        try:
            result = events[config_number]
        except IndexError:
            log.error('invalid config number %s.' % config_number)
        else:
            return result
    else:
        return events


def get_interactive_agent_count():
    result = len(get_agent_state_config())
    log.info('%s agents found in event configurations.' % result)
    return result


def get_traders_initial_market_view():
    result = settings.initial_trader_market_view
    for k, v in get_simulation_parameters().items():
        if k in result:
            result[k] = v
    log.info('initial market view of trader: %s' % ' '.join(
                '{0}:{1}'.format(k, v) for k, v in result.items()))
    return result


def dict_stringify(dict_to_str):
    return '%s' % ' '.join('{0}:{1}'.format(k, v) for k, v in dict_to_str.items())


def generate_account_id(size=4):
    return ''.join(choice(string.ascii_uppercase) for i in range(size))


def random_chars(num_chars):
    return ''.join(choice(SESSION_CODE_CHARSET) for _ in range(num_chars))


def transform_incoming_message(source, message, external_market_state=None):
    """ this handles key mismatches in messages
        between the otree app and simulator"""
    def transform_external_proxy_msg(message):
        """
        traders in elo environment treat one of the
        markets as external, format the message so
        correct handlers are activated on trader model
        """
        if message['type'] == 'reference_price_change':
            message['type'] = 'external_reference_price'
            return message
        if not external_market_state:
            raise Exception('external_market_state is not set.')
        if message['type'] == 'bbo':
            message['e_best_bid'] = message['best_bid']
            message['e_best_offer'] = message['best_offer']
            external_market_state['e_best_bid'] = message['best_bid']
            external_market_state['e_best_offer'] = message['best_offer']
            message['e_signed_volume'] = external_market_state['e_signed_volume']
            # if message['e_signed_volume'] is None:
            #     message['e_signed_volume'] = 0
        if message['type'] == 'signed_volume':
            message['e_signed_volume'] = message['signed_volume']
            message['e_best_bid'] = external_market_state['e_best_bid']
            message['e_best_offer'] = external_market_state['e_best_offer']
            external_market_state['e_signed_volume'] = message['signed_volume']
        message['type'] = 'external_feed_change'
        return message
    message['subsession_id'] = 0
    message['market_id'] = 0
    if message['type'] == 'reference_price':
        message['type'] = 'reference_price_change'
    if source == 'external':
        message = transform_external_proxy_msg(message)
    if message['type'] == 'bbo':
        message['type'] = 'bbo_change'
    if message['type'] == 'signed_volume':
        message['type'] = 'signed_volume_change'
    if 'technology_on' in message:
        message['value'] = message['technology_on']
    return message


def extract_firm_from_message(message):
    if hasattr(message, 'order_token'):
        return message.order_token[:4]


def read_fundamental_values_from_csv(path):
    """ well this code sucks but it is very specific to elo"""
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # first row is column names
        rows = list(reader)
    # assume values are valid
    rows = [(float(row[0]), int(row[1])) for row in rows]
    return rows

def read_agent_events_from_csv(path):
    """ some obvious duplication here, but it is good to keep them separate
        both are very custom to context
    """
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # first row is column names
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


def get_mock_market_msg(market_facts: dict, msg_type: str):
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


incoming_message_defaults = {'subsession_id': 0,  'market_id': 0, 'player_id': 0}


def read_yaml(path: str):
    with open(path, 'r') as f:
        try:
            config = yaml.load(f)
        except yaml.YAMLError as e:
            raise e
    return config
