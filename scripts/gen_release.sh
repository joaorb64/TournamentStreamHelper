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
    	TournamentStreamHelper \
    -x \
    	"TournamentStreamHelper/assets/versions.json" \
    	"TournamentStreamHelper/assets/contributors.txt" \

rm -rf TournamentStreamHelper
popd
