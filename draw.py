import numpy as np 
from high_frequency_trading.hft.equations import price_grid
import settings

def draw_arrival_times(size, period_length, distribution=np.random.uniform, 
        seed=None, **kwargs):
    np.random.seed(seed=seed)
    arr = distribution(size=size, **kwargs)
    arr.sort()
    arr.cumsum()
    sub_arr = arr[arr < period_length].round(decimals=3)
    return sub_arr


def draw_noise(size, period_length, distribution=np.random.normal, 
        cumsum=False, seed=None, **kwargs):
    np.random.seed(seed=seed)
    arr = distribution(size=size, **kwargs)
    if cumsum:
        arr.cumsum()
    return arr


def elo_asset_value_arr(initial_price, period_length, loc_delta, scale_delta, 
        lambdaJ, seed=None):
    """
    the fundamental price
    """
    f_size = int(lambdaJ * period_length)
    f_price_change_times = draw_arrival_times(f_size, period_length, seed=seed, 
        low=0.0, high=period_length)
    num_f_price_changes = f_price_change_times.size
    f_prices = np.random.normal(size=num_f_price_changes, loc=loc_delta, 
                    scale=scale_delta).cumsum() + initial_price
    return np.vstack((f_price_change_times, f_prices)).round(3)
    

def elo_random_order_sequence(asset_value_arr, period_length, loc_noise, 
        scale_noise, lambdaI, time_in_force_lam, random_tif=False, buy_prob=0.5, seed=None):
    orders_size = np.random.poisson(lam=lambdaI * period_length, size=1)
    order_times = draw_arrival_times(orders_size, period_length, seed=seed, 
        low=0.0, high=period_length)
    asset_value_jump_times = asset_value_arr[0]
    asset_values = asset_value_arr[1]
    asset_value_indexes = np.searchsorted(asset_value_jump_times, order_times) - 1
    asset_value_asof = np.array([asset_values.item(ix) for ix in asset_value_indexes])
    order_directions = np.random.binomial(1, buy_prob, orders_size)
    noise_around_asset_value = np.random.normal(loc_noise, scale_noise, orders_size)
    order_prices = (
        asset_value_asof + noise_around_asset_value * (2 *
        order_directions - 1)
    ).astype(int)
    grid = np.vectorize(price_grid)
    order_prices = grid(order_prices)
    if random_tif:
        orders_tif = np.random.exponential(time_in_force_lam, size=orders_size)
    else:
        orders_tif = np.full(orders_size, time_in_force_lam)
    convert_string = np.vectorize(lambda x: 'B' if x is 0 else 'S')
    order_directions = convert_string(order_directions)
    orders_tif = orders_tif.astype(int)
    return np.vstack((
        order_times, asset_value_asof.round(3), order_prices.round(3), order_directions, 
            orders_tif))

def elo_draw(period_length, conf: dict):
    fundamental_values = elo_asset_value_arr(
        conf['initial_price'], period_length, conf['noise_mean'], 
        conf['noise_variance'], conf['lambdaJ'])
    random_orders = elo_random_order_sequence(fundamental_values, 
        period_length, conf['noise_mean'], conf['noise_variance'], 
        conf['lambdaI'], conf['time_in_force'])
    random_orders = np.swapaxes(random_orders, 0, 1)
    return random_orders


if __name__ == '__main__':
    print(elo_draw(10, settings.random_orders_defaults))


     