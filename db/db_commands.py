from db.db import ELOMarket, ELOAgent
from db.conf import psql_db
import csv
import datetime

models = [ELOMarket, ELOAgent]


def drop_tables(tables=models):
    psql_db.drop_tables(tables)

def create_tables(tables=models):
    psql_db.create_tables(models)

def resetdb(tables=models):
    drop_tables()
    create_tables()

def get_session_data(session_id, model_cls):
    return model_cls.select().where(model_cls.subsession_id == session_id).order_by(
        model_cls.timestamp)

export_path = 'exports/{record_class}_accessed_{timestamp}.csv'

def export_csv(session_id, record_class):
    def write_csv(path, raw_data, fieldnames):
        with open(path, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for row in raw_data:
                writer.writerow(row)
    timestamp = datetime.datetime.now()
    fieldnames = record_class.csv_meta
    file_path = export_path.format(record_class=record_class.__name__, 
        timestamp=timestamp)
    query = get_session_data(session_id, record_class)
    write_csv(file_path, query.dicts(), fieldnames)

def export_session(session_id):
    for model_cls in models:
        export_csv(session_id, model_cls)