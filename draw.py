import numpy as np 
from high_frequency_trading.hft.equations import price_grid
import utility
import logging
import settings

log = logging.getLogger(__name__)


class ContextSeed:
    """
    context manager to ensure sample draws are
    shared among different agents
    """
    def __init__(self, seed):
        self.seed = seed
    
    def __enter__(self):
        np.random.seed(self.seed)
    
    def __exit__(self, *_):
        np.random.seed(np.random.randint(0, high=100))


def asof(a, b):
    """
    assumes a and b are sorted array of times
    return indexes of a 
    so values of b at such indexes
    are 'as of' a, commonly used
    when dealing with timeseries data
    (so the closest numpy gets to this is via searchsorted,
     which is still not the tool, wtf numpy folks ?)
    """
    current_index = 0
    last_a_index = len(a) - 1
    result = np.zeros(b.size, dtype=int)
    for ix, t in enumerate(b):
        try:
            while t >= a[current_index]:
                current_index += 1
        except IndexError:
            current_index = last_a_index + 1
        result[ix] = current_index - 1
    return result 
         

def draw_arrival_times(size, period_length, distribution=np.random.uniform, **kwargs):
    """
    given a distributon, draw a sample of time points
    sort and cum sum them so you have arrival times 
    spread over the period length
    """  
    arr = distribution(size=size, **kwargs)
    arr.sort()
    arr.cumsum()
    sub_arr = arr[arr < period_length].round(decimals=3)
    return sub_arr


def draw_noise(size, period_length, distribution=np.random.normal, 
               cumsum=False, **kwargs):
    arr = distribution(size=size, **kwargs)
    if cumsum:
        arr.cumsum()
    return arr


def _elo_asset_value_arr(initial_price, period_length, loc_delta, scale_delta, 
                         lambdaJ):
    """
    generate a sequence of asset values and asset value jump times
    """
    f_size = int(lambdaJ * period_length)
    f_price_change_times = draw_arrival_times(
        f_size, period_length, low=0.0, high=period_length)
    num_f_price_changes = f_price_change_times.size
    f_prices = np.random.normal(
        size=num_f_price_changes, loc=loc_delta, 
        scale=scale_delta).cumsum() + initial_price
    return np.vstack((f_price_change_times, f_prices)).round(3)
    

def elo_random_order_sequence(
        asset_value_arr, period_length, loc_noise, scale_noise, bid_ask_offset, 
        lambdaI, time_in_force, buy_prob=0.5):
    """
    draws bid/ask prices around fundamental value,
    generate input sequnce for random orders with arrival times as array
    """
    orders_size = np.random.poisson(lam=(1 / lambdaI) * period_length, size=1)
    order_times = draw_arrival_times(
        orders_size, period_length, low=0.0, high=period_length)
    unstacked_asset_values = np.swapaxes(asset_value_arr, 0, 1)
    asset_value_jump_times, asset_values = unstacked_asset_values[0], unstacked_asset_values[1]
    asset_value_indexes = asof(asset_value_jump_times, order_times)
    asset_value_asof = asset_values[asset_value_indexes]
    order_directions = np.random.binomial(1, buy_prob, orders_size)
    noise_by_order_side = np.vectorize(
        lambda x: np.random.normal(loc_noise - bid_ask_offset, scale_noise
            ) if x == 0 else np.random.normal(loc_noise + bid_ask_offset, scale_noise))
    noise_around_asset_value = noise_by_order_side(order_directions)
    order_prices = (asset_value_asof + noise_around_asset_value).astype(int)
    grid = np.vectorize(price_grid)
    gridded_order_prices = grid(order_prices)
    orders_tif = np.full(orders_size, time_in_force).astype(int)
    convert_to_string = np.vectorize(lambda x: 'B' if x is 0 else 'S')
    order_directions = convert_to_string(order_directions)
    stacked = np.vstack((
        order_times, asset_value_asof, gridded_order_prices, order_directions, 
            orders_tif))
    return stacked

def elo_draw(period_length, conf: dict, seed=np.random.randint(0, high=2 ** 8),
        config_num=0):
    """
    generates random order sequence as specified in ELO market research plan
    first draws fundamental value series or read from a csv file
    then pipes this sequence to random order producer function
    """
    if conf['read_fundamental_values_from_file']:
        path = settings.fundamental_values_config_path
        fundamental_values = utility.read_fundamental_values_from_csv(path)
        fundamental_values.insert(0, (0, conf['initial_price']))
        fundamental_values = np.array(fundamental_values)
        log.info('read fundamental value sequence from %s.' % path)
    else:
        with ContextSeed(seed):
            fundamental_values = _elo_asset_value_arr(
                conf['initial_price'], 
                period_length, 
                conf['fundamental_value_noise_mean'], 
                conf['fundamental_value_noise_std'], 
                conf['lambdaJ'])
            log.info('drew fundamental value sequence, initial price %s'
                     '%s jumps per second.' % (
                        conf['initial_price'],
                        round(len(fundamental_values) / period_length, 2)))
    log.info('fundamental values: %s' % (', '.join('{0}:{1}'.format(t, v) 
                                            for t, v in fundamental_values)))
    random_orders = elo_random_order_sequence(
        fundamental_values, 
        period_length, 
        conf['exogenous_order_price_noise_mean'], 
        conf['exogenous_order_price_noise_std'], 
        conf['bid_ask_offset'],
        conf['lambdaI'][config_num],    # so rabbits differ in arrival rate..
        conf['time_in_force'])
    random_orders = np.swapaxes(random_orders, 0, 1)
    log.info(
        '%s random orders generated. period length: %s, per second: %s.' % (
            random_orders.shape[0], 
            period_length, 
            round(random_orders.shape[0] / period_length, 2)))
    log.info('random orders (format: [fundamental price]:[order price]:[order direction]:[time in force]): %s' % (
                ', '.join('{0}:{1}:{2}:{3}'.format(row[1], row[2], row[3], row[4]) for 
                            row in random_orders)))
    return random_orders


if __name__ == '__main__':
    d = elo_draw(20, utility.get_simulation_parameters())
    for r in d:
        print(r)


     