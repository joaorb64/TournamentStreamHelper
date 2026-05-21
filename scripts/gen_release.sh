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



if ! pushd "${DIR}/.." >/dev/null 2>&1; then
  echo "Couldn't enter directory ${DIR}/.. Quitting."
  popd >/dev/null 2>&1
  exit 255
fi


# Create TSH dir and its stage_strike_app folders
mkdir -p TournamentStreamHelper/stage_strike_app/build

cp -R assets \
	layout \
	user_data \
	LICENSE \
	TSH.exe \
	TournamentStreamHelper/

cp -R stage_strike_app/build \
	TournamentStreamHelper/stage_strike_app/

rm -rf \
	TournamentStreamHelper/assets/versions.json \
	TournamentStreamHelper/assets/contributors.txt \
	TournamentStreamHelper/layout/game_images \
	TournamentStreamHelper/layout/game_screenshots

zip -rv release-windows.zip TournamentStreamHelper

rm -rf TournamentStreamHelper

popd >/dev/null 2>&1