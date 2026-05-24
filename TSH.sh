#!/bin/bash

# The following stub makes it so that this script always runs in the directory it is located within.
# It works on macos, and will follow symbolic links and generally will make it difficult to have

SOURCE=${BASH_SOURCE[0]}
while [ -L "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )



if ! pushd "${DIR}" >/dev/null 2>&1; then
  echo "Couldn't enter directory ${DIR}. Quitting."
  exit 255
fi

# If pip isn't in the host python, it won't be in the venv. This shows up
# for example in ubuntu system-packaged python where `python3` is installed but not
# `python3-dev`
echo "Checking pip version for host python... "
if ! python3.14 -m pip --version; then
  echo "Failed to find pip. Quitting."
  exit 255
fi

# Python 3.14 install instructions for Ubuntu 22.04 LTS
#sudo add-apt-repository ppa:deadsnakes/ppa
#sudo apt update
#sudo apt install python3.14-dev

python3.14 -m venv --upgrade-deps ./venv
MSGPACK_PUREPYTHON=1 ./venv/bin/pip3 install -r dependencies/requirements.txt

./venv/bin/python3.14 main.py
popd "${DIR}" >/dev/null 2>&1