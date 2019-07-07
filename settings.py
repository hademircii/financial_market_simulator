from utility import read_agent_events_from_csv 

MIN_BID = 0
MAX_ASK = 2147483647

# edit below

simulation_parameters = {
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

# edit above 
custom_config_path = './parameters.yaml'
agent_event_config_path = './event_conf.csv'

agent_event_confs = read_agent_events_from_csv(agent_event_config_path)
num_interactive_agents = len(agent_event_confs)


ports = {
    'focal_exchange_port': 9001,
    'external_exchange_port': 9002,
    'focal_proxy_ouch_port': 9201,
    'focal_proxy_json_port': 9202,
    'external_proxy_ouch_port': 9301,
    'external_proxy_json_port': 9302,
}


initial_trader_state = {
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
    'tax_rate': simulation_parameters['tax_rate'],
    'reference_price': simulation_parameters['initial_price']
}