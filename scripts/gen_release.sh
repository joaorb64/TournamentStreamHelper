#!/bin/bash

pushd $PWD/..
zip -r release.zip assets layout user_data LICENSE TSH.exe
popd
