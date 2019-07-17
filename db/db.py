from peewee import *
import datetime
from high_frequency_trading.hft.utility import serialize_in_memo_model
from .conf import psql_db
from collections import deque
import time
import logging

log = logging.getLogger(__name__)


def get_db_model(entity_tag):
    try:
        return in_memo_to_db_model_table[entity_tag]
    except KeyError:
        raise Exception('invalid model tag %s' % entity_tag)


def write_to_db(model_class, records=[], flush_on=('market_start', 'market_end'), 
            ts_field_name='timestamp', **kwargs):
    """
    each record is a result of an event
    batch inputs and bulk create objects
    """
    # keys should be identical in all dict for
    # bulk inserts
    clean_kwargs = {k: kwargs[k] if k in kwargs else None for k, v in model_class._meta.fields.items()} 
    del clean_kwargs['id']
    clean_kwargs[ts_field_name] = datetime.datetime.now()
    records.append(clean_kwargs)
    total_items = len(records)
    if total_items >= 300 or kwargs.get('trigger_msg_type') in flush_on:
        log.debug('insert %s records to db' % total_items)
        model_class.insert_many(records).execute()
        records.clear()
            
            
def freeze_state():
    attr_name = 'model'

    def decorator(func):
        def db_recorded(market_entity, *args, **kwargs):
            event = func(market_entity, *args, **kwargs)
            if event:
                model_to_record = getattr(market_entity, attr_name)
                ftf = get_freezed_fields_by_class(market_entity.tag)
                props = ftf['properties_to_serialize']
                subprops = ftf['subproperties_to_serialize']
                frozen_model = serialize_in_memo_model(
                    model_to_record, props, subprops)
                db_model_class = get_db_model(market_entity.tag)
                write_to_db(
                    db_model_class, trigger_msg_type=event.event_type, 
                    **frozen_model)
        return db_recorded
    return decorator


class BaseModel(Model):

    timestamp = DateTimeField(default=datetime.datetime.now)
    trigger_msg_type = CharField()

    class Meta:
        database = psql_db


class ELOMarket(BaseModel):
    tag = 'market'

    csv_meta = (
        'timestamp', 'subsession_id',
        'market_id', 'trigger_msg_type',
        'reference_price', 'best_bid', 'best_offer', 
        'next_bid', 'next_offer', 'volume_at_best_bid', 'volume_at_best_offer', 
        'e_best_bid', 'e_best_offer', 'signed_volume', 'e_signed_volume')

    subsession_id = CharField()
    market_id = IntegerField()
    reference_price = IntegerField()
    best_bid = IntegerField()
    best_offer = IntegerField()
    next_bid = IntegerField()
    next_offer = IntegerField()
    volume_at_best_bid = IntegerField()
    volume_at_best_offer = IntegerField()
    e_best_bid = IntegerField()
    e_best_offer = IntegerField()
    signed_volume = FloatField()
    e_signed_volume = FloatField()


class ELOAgent(BaseModel):
    tag = 'agent'

    csv_meta = (
        'timestamp', 'subsession_id', 'account_id', 'trigger_msg_type',
        'market_id', 'trader_model_name', 'inventory', 'best_bid', 'best_offer',
        'next_bid', 'next_offer', 'e_best_bid', 'e_best_offer',
        'bid', 'offer', 
        'best_bid_except_me', 'best_offer_except_me',
        'delay', 'staged_bid', 'staged_offer', 'implied_bid', 
        'implied_offer', 'slider_a_x','slider_a_y', 'slider_a_z',
        'net_worth', 'cash', 'tax_paid', 'speed_cost')

    subsession_id = CharField()
    market_id = CharField(default=0)
    account_id = CharField()
    trader_model_name =  CharField()
    delay = FloatField()
    net_worth = IntegerField()
    cash = IntegerField()
    cost = IntegerField()
    speed_cost = IntegerField()
    tax_paid = IntegerField()
    reference_price = IntegerField()
    best_bid = IntegerField()
    best_offer = IntegerField()
    next_bid = IntegerField()
    next_offer = IntegerField()
    e_best_bid = IntegerField()
    e_best_offer = IntegerField()
    inventory = IntegerField()
    bid = IntegerField(null=True)
    offer = IntegerField(null=True)
    staged_bid = IntegerField(null=True)
    staged_offer = IntegerField(null=True)
    implied_bid = IntegerField(null=True)
    implied_offer = IntegerField(null=True)
    best_bid = IntegerField()
    best_offer = IntegerField()
    best_bid_except_me = IntegerField()
    best_offer_except_me = IntegerField()
    next_bid = IntegerField()
    next_offer = IntegerField()
    volume_at_best_bid = IntegerField()
    volume_at_best_offer = IntegerField()
    e_best_bid = IntegerField()
    e_best_offer = IntegerField()
    slider_a_x = FloatField()
    slider_a_y = FloatField()
    slider_a_z = FloatField()
    signed_volume = FloatField()
    e_signed_volume = FloatField()    

def session_results_ready(session_id, timeout=10):
    t = 0
    sleep_dur = 0.5
    while t < timeout:
        starters_count = ELOAgent.select().where(
            (ELOAgent.subsession_id == session_id) &  
            (ELOAgent.trigger_msg_type == 'market_start')
        ).count()
        closers_count = ELOAgent.select().where(
            (ELOAgent.subsession_id == session_id) &  
            (ELOAgent.trigger_msg_type == 'market_end')
        ).count()
        if starters_count == closers_count != 0:
            log.warning('session %s results ready, number of agents %s.' % (
                    session_id, closers_count))
            return True
        else:
            time.sleep(sleep_dur)
            t += sleep_dur
            log.warning('waiting for session %s results. starters: %s, closers %s' % (
                session_id, starters_count, closers_count))
    log.warning('error: timeout waiting session %s' % session_id)

        
in_memo_to_db_model_table = {
    'agent': ELOAgent, 'market': ELOMarket
}



fields_to_freeze =  {
    'agent': {
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


def get_freezed_fields_by_class(entity_tag):
    try: return fields_to_freeze[entity_tag]
    except KeyError: raise Exception('%s is invalid entity tag' % entity_tag)



