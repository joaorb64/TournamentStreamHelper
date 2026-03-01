#!/bin/bash

# Python 3.14 install instructions for Ubuntu 22.04 LTS
#sudo add-apt-repository ppa:deadsnakes/ppa
#sudo apt update
#sudo apt install python3.14-dev

python3.14 -m venv ./venv
./venv/bin/pip3 install --upgrade pip
MSGPACK_PUREPYTHON=1 ./venv/bin/pip3 install -r dependencies/requirements.txt
./venv/bin/python3.14 main.py