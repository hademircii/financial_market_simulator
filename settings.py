from utility import read_agent_events_from_csv, read_yaml, dict_stringify
import sys
import logging

log = logging.getLogger(__name__)

MIN_BID = 0
MAX_ASK = 2147483647

default_simulation_parameters = {
    # configs for elo simulation
    'session_duration': 10,
    'initial_price': 1000000,
    'noise_mean': 0,
    'noise_std': 20000,
    'bid_ask_offset': 50,
    'lambdaJ': 0.5,
    'lambdaI': 0.1,
    'time_in_force': 5,
    'tax_rate': 0.1,
    'k_reference_price': 0.01,
    'k_signed_volume': 0.5
}

logs_dir = './logs/'
results_export_path = './exports/{session_id}_{record_class}_accessed_{timestamp}.csv'

custom_config_path = './parameters.yaml'
agent_event_config_path = './agent_state_configs.csv'

AGENT_STATE_CONFS = read_agent_events_from_csv(agent_event_config_path)
SIMULATION_PARAMETERS = default_simulation_parameters


def refresh_agent_state_configs():
    global AGENT_STATE_CONFS
    AGENT_STATE_CONFS = read_agent_events_from_csv(agent_event_config_path)


def get_interactive_agent_count():
    result = len(AGENT_STATE_CONFS)
    log.info('%s agents found in event configurations.' % result)
    return result


def get_traders_initial_market_view():
    result = initial_trader_market_view
    for k, v in SIMULATION_PARAMETERS.items():
        if k in result:
            result[k] = v
    log.info('initial market view of trader: %s' % ' '.join(
                '{0}:{1}'.format(k, v) for k, v in result.items()))
    return result


def refresh_simulation_parameters():
    custom_parameters = read_yaml(custom_config_path)
    augment_simulation_parameters(custom_parameters)


def augment_simulation_parameters(custom_parameters):
    merged_parameters = default_simulation_parameters.copy()
    if custom_parameters:
        for k, v in custom_parameters.items():
            if k in merged_parameters:
                merged_parameters[k] = v
    global SIMULATION_PARAMETERS
    SIMULATION_PARAMETERS = merged_parameters
    string_parameters = dict_stringify(SIMULATION_PARAMETERS)
    log.info('session parameters %s' % string_parameters)


ports = {
    'focal_exchange_port': 9001,
    'external_exchange_port': 9002,
    'focal_proxy_ouch_port': 9201,
    'focal_proxy_json_port': 9202,
    'external_proxy_ouch_port': 9301,
    'external_proxy_json_port': 9302,
}


initial_trader_market_view = {
    'best_bid': MIN_BID,
    'volume_at_best_bid': 0,
    'next_bid': MIN_BID,
    'best_offer': MAX_ASK,
    'volume_at_best_offer': 0,
    'next_offer': MAX_ASK,
    'signed_volume': 0,
    'e_best_bid': MIN_BID,
    'e_best_offer': MAX_ASK,
    'e_signed_volume': 0,
    'tax_rate': default_simulation_parameters['tax_rate'],
    'reference_price': default_simulation_parameters['initial_price']
}
