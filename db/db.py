from peewee import *
import datetime
from high_frequency_trading.hft.utility import serialize_in_memo_model
import os
import utility
from .conf import psql_db


def get_db_model(model_key):
    try:
        return in_memo_to_db_model_table[model_key]
    except KeyError:
        raise Exception('invalid model key %s' % model_key)


def write_to_db(model_class, **kwargs):
# TODO: bulk inserts and queueing
    model_class.create(**kwargs)

def freeze_state(field_name):
    def decorator(func):
        def db_recorded(market_entity, *args, **kwargs):
            event = func(market_entity, *args, **kwargs)
            if event:
                model_to_record = getattr(market_entity, field_name)
                try:
                    ftf = utility.fields_to_freeze[field_name]
                except KeyError:
                    raise Exception('invalid field name %s' % field_name)
                props = ftf['properties_to_serialize']
                subprops = ftf['subproperties_to_serialize']
                frozen_model = serialize_in_memo_model(model_to_record, props, subprops)
                db_model_class = get_db_model(field_name)
                write_to_db(db_model_class, trigger_msg_type=event.event_type, 
                    **frozen_model)
        return db_recorded
    return decorator


class BaseModel(Model):

    timestamp = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = psql_db

class ELOMarket(BaseModel):

    csv_meta = (
    'timestamp', 'subsession_id', 'market_id', 'trigger_event_type',
    'reference_price', 'best_bid', 'best_offer', 
    'next_bid', 'next_offer', 'volume_at_best_bid', 'volume_at_best_offer', 
    'e_best_bid', 'e_best_offer', 'signed_volume', 'e_signed_volume')

    subsession_id = CharField()
    trigger_msg_type = CharField()
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

    csv_meta = (
    'timestamp', 'subsession_id', 'account_id', 'trigger_msg_type',
    'trader_model_name', 'inventory', 'bid', 'offer', 
    'best_bid_except_me', 'best_offer_except_me',
    'delay', 'staged_bid', 'staged_offer', 'implied_bid', 
    'implied_offer', 'slider_a_x','slider_a_y', 'slider_a_z',
    'net_worth', 'cash', 'tax_paid', 'speed_cost')

    subsession_id = CharField()
    trigger_msg_type = CharField()
    firm = CharField()
    trader_model_name =  CharField()
    delay = FloatField()
    net_worth = IntegerField()
    cash = IntegerField()
    cost = IntegerField()
    speed_cost = IntegerField()
    tax_paid = IntegerField()
    reference_price = IntegerField()
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

in_memo_to_db_model_table = {
    'trader_model': ELOAgent, 'market': ELOMarket
}
