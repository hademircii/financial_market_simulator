from peewee import PostgresqlDatabase
import os

db_name = 'fimsim'
host = 'localhost'
db_user = os.getenv('DBUSER')
db_password = os.getenv('DBPASSWORD')

psql_db = PostgresqlDatabase(db_name, user=db_user, 
    password=db_password, host=host)

