from db.db import ELOMarket, ELOAgent
from db.conf import psql_db
import settings
import csv
import datetime
import logging

log = logging.getLogger(__name__)
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


def export_csv(session_id, record_class, dest=None):
    timestamp = datetime.datetime.now()
    fieldnames = record_class.csv_meta
    if not dest:
        # then write to file in the system
        dest = settings.results_export_path.format(
                session_id=session_id, record_class=record_class.tag, 
                timestamp=timestamp)
    query = get_session_data(session_id, record_class)
    with open(dest, 'w') as filelike:
        log.debug('writing as csv: headers %s: %s' % (fieldnames, dest))
        writer = csv.DictWriter(filelike, fieldnames=fieldnames, 
                                extrasaction='ignore')
        writer.writeheader()
        for row in query.dicts():
            writer.writerow(row)
    return filelike


def export_session(session_id):
    for model_cls in models:
        export_csv(session_id, model_cls)
