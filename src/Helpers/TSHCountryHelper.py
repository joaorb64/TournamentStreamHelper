from typing import final
import unicodedata
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import requests
import os
import traceback
from .TSHDictHelper import deep_get
from ..TournamentDataProvider import TournamentDataProvider
import json


class TSHCountryHelper(QObject):
    instance: "TSHCountryHelper" = None

    countries_json = {}
    countries = {}
    cities = {}

    def __init__(self) -> None:
        super().__init__()
        self.UpdateCountriesFile()

    def UpdateCountriesFile(self):
        class DownloaderThread(QThread):
            def run(self):
                try:
                    url = 'https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/countries%2Bstates%2Bcities.json'
                    r = requests.get(url, allow_redirects=True)
                    open('./assets/countries+states+cities.json',
                         'wb').write(r.content)
                    print("Countries file updated")
                except Exception as e:
                    print(
                        "Could not update /assets/countries+states+cities.json: "+str(e))
        downloaderThread = DownloaderThread(self)
        downloaderThread.start()

    def remove_accents_lower(input_str):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

    def LoadCountries():
        f = open("./assets/countries+states+cities.json",
                 'r', encoding='utf-8')
        countries_json = json.loads(f.read())
        TSHCountryHelper.countries_json = countries_json

        for c in countries_json:
            TSHCountryHelper.countries[c["iso2"]] = {
                "name": c["name"],
                "code": c["iso2"],
                "states": {}
            }

            for s in c["states"]:
                TSHCountryHelper.countries[c["iso2"]]["states"][s["state_code"]] = {
                    "state_code": s["state_code"],
                    "state_name": s["name"]
                }

        for country in countries_json:
            for state in country["states"]:
                for c in state["cities"]:
                    if country["iso2"] not in TSHCountryHelper.cities:
                        TSHCountryHelper.cities[country["iso2"]] = {}
                    city_name = TSHCountryHelper.remove_accents_lower(
                        c["name"])
                    if city_name not in TSHCountryHelper.cities[country["iso2"]]:
                        TSHCountryHelper.cities[country["iso2"]
                                                ][city_name] = state["state_code"]

    def FindState(countryCode, city):
        # State explicit?
        split = city.split(" ")

        for part in split:
            state = next(
                (st for st in TSHCountryHelper.countries.get(countryCode, {}).get("states", {}).values(
                ) if TSHCountryHelper.remove_accents_lower(st["state_code"]) == TSHCountryHelper.remove_accents_lower(part)),
                None
            )
            if state is not None:
                return state["state_code"]

        # No, so get by City
        state = TSHCountryHelper.cities.get(countryCode, {}).get(
            TSHCountryHelper.remove_accents_lower(city), None)

        if state is not None:
            return state

        return None


TSHCountryHelper.instance = TSHCountryHelper()
TSHCountryHelper.LoadCountries()
