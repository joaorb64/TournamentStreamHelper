#!/bin/bash

python3 -m pip install pipenv
python3 -m pipenv install -r dependencies/requirements.txt
python3 -m pipenv run python main.py