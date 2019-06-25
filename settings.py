from utility import read_agent_events_from_csv 

MIN_BID = 0
MAX_ASK = 2147483647
INITIAL_PRICE =1000000


random_orders_defaults = {
    'initial_price': INITIAL_PRICE,
    'noise_mean': 0,
    'noise_variance': 10000,
    'lambdaJ': 0.5,
    'lambdaI': 10,
    'time_in_force': 5
}

agent_event_config_path = 'event_conf.csv'

agent_event_confs = read_agent_events_from_csv(agent_event_config_path)

market_settings = {
    'tax_rate': 0.1
}

elo_simulation_configs = {
    'session_duration': 30,
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
    'tax_rate': 0.1,
    'reference_price': 1000000
}