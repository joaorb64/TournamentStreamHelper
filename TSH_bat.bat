@echo off
python.exe -m pip install pipenv
python.exe -m pipenv install -r "dependencies/requirements.txt"
python.exe -m pipenv run python "./main.py"
