#!/bin/bash

pushd ..

mkdir TournamentStreamHelper
cp -R assets \
	layout \
	user_data \
	LICENSE \
	TSH.exe \
	TournamentStreamHelper/

zip -rv \
    release.zip \
    TournamentStreamHelper/assets -x \
    	"TournamentStreamHelper/assets/versions.json" \
    	"TournamentStreamHelper/assets/contributors.txt" \
    TournamentStreamHelper/layout \
    TournamentStreamHelper/user_data \
    TournamentStreamHelper/LICENSE \
    TournamentStreamHelper/TSH.exe

rm -rf TournamentStreamHelper
popd
