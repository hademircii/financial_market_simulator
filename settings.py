from utility import read_agent_events_from_csv 

random_orders_defaults = {
    'initial_price': 1000000,
    'noise_mean': 0,
    'noise_variance': 10000,
    'lambdaJ': 0.5,
    'lambdaI': 1,
    'time_in_force': 5
}

agent_event_config_path = 'event_conf.csv'

agent_event_confs = read_agent_events_from_csv(agent_event_config_path)