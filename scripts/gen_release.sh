#!/bin/bash

pushd .. > /dev/null

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

popd > /dev/null