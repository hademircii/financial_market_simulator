#! ./bin/bash
PYTHON=/usr/local/bin/python3

all: clean dependencies submodules directories

dependencies: venv
	source ./env/bin/activate && \
	pip install -r ./requirements.txt

submodules:
	git submodule init && git submodule update
	$(cd high_frequency_trading ; git submodule init && git submodule update)

venv: 
	if [ ! -d ./env ] ; then $(PYTHON) -m venv ./env; fi

directories: 
	mkdir -p ./app/logs ./app/data ./app/results


clean: clean_venv clean_session_data

clean_venv:
	if [ -d ./env ] ; then rm -rf ./env; fi

clean_session_data: clean_session_logs clean_session_output clean_post_processed

clean_session_logs:
	rm -f ./app/logs/*

clean_post_processed:
	rm -rf ./app/results/*

clean_session_output:
	rm -rf ./app/data/*

	