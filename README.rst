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

  CREATE DATABASE simulations;
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
  
cd into the directory you just downlaoded.
  
::
  
    cd financial_market_simulator
   
download and update submodules
  
::
    
    git submodule init
    git submodule update
 
install dependencies
 
::
 
    pip install -r requirements.txt
 
start two more shells
and cd into the exchange_server directory in the repo
you just downloaded.
in the first shell, run:
 
::
 
    python3 run_exchange_server.py --host 0.0.0.0 --port 9001 --debug --mechanism cda
   
in the second shell, run:
 
::
 
    python3 run_exchange_server.py --host 0.0.0.0 --port 9002 --debug --mechanism cda
    
you just started two matching engine processes listening on port 9001 and 9002


Session-wide static parameters are defined in file parameters.yaml  edit it accordingly.
Dynamic parameters (agent's sensitivities, techonolgy subscription) is configured by editing agent_state_configs.csv.

usage:
=======
after editing the files to reflect desired configuration.
 
::
 
    python run_web_api.py
  
this will wake up the simulator engine.

now, go to a browser of your choice and visit http://localhost:5000/v1/simulate . you will get a response message which includes
a session id and parameters, note down this session code since output files will be tagged with this identifier.
this will trigger a simulation session, which after completion will dump two files in the exports directory.
next you need to upload these files to analytics service to do visual inspection.
it is at: http://167.99.111.185:8888 ; next steps are located in README file in the home directory of the notebook server there.


   
.. _link: https://www.postgresql.org/download/
  
