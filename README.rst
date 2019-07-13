a tool to create systems / networks with financial market contexts

installation:
=============

this is tested with python 3.5 - 3.6 - 3.7.

postgres database must be installed.
follow this `link`_ for instructions.

next,
create a virtual environment

::

  python3 -m venv simulations_venv

and activate it

::
  
  source ~/simulations_venv/bin/activate
  
given postgres is succesfully installed, 
start a shell
switch to postgres user

::

  sudo su - postgres

start postgres shell

::

  psql

create an user, database and grant permissions to user

::

  CREATE DATABASE fimsim;
  CREATE USER simulation_user WITH PASSWORD 'somepassword';
  GRANT ALL PRIVILEGES ON DATABASE simulations TO simulation_user;

and exit

::
  
  \q
  exit

define and set some environmental variables
for application to use while talking to the database.

::

  export DBUSER=simulation_user
  export DBPASSWORD=somepassword
 
download and clone this repo
 
::

    git clone https://github.com/hademircii/financial_market_simulator.git
  
cd into the directory you just downloaded.
  
::
  
    cd financial_market_simulator
   
download and update submodules
  
::
    
    git submodule init
    git submodule update
 
install dependencies
 
::
 
    pip install -r requirements.txt
    
    
from the root directory
start an interactive python session

::

  python 
  
and create the relevant tables in the db.

::

  from db import db_commands
  db_commands.create_tables()

**matching engines**

start two more shells
and cd into the exchange_server directory in the repo
you just downloaded.
follow the `instructions`_ here to run an matching engine instance, run two matching engines in separate shells on ports 9001 and 9002 with the CDA format (if you need different ports, make sure to edit settings.py in the root directory accordingly).

usage:
=======
 
::
 
    python run_web_api.py
  
this will wake up the simulator engine.

session-wide static parameters are defined in file parameters.yaml  edit it accordingly.

dynamic parameters (agent's sensitivities, techonolgy subscription) is configured by editing agent_state_configs.csv.

now, go to a browser of your choice and visit http://localhost:5000/v1/simulate . you will get a response message which includes
a session id and parameters, note down this session code since output files will be tagged with this identifier.
this will trigger a simulation session, which after completion will dump two files in the exports directory.

next you need to upload these files to analytics service to do visual inspection.
it is at: http://167.99.111.185:8888 ; next steps are located in README file in the home directory of the notebook server there.


   
.. _link: https://www.postgresql.org/download/
.. _instructions: https://github.com/Leeps-Lab/exchange_server/blob/master/README.rst
