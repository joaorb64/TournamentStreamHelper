import unicodedata
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import requests
import os
import traceback
from .TSHDictHelper import deep_get
from ..TournamentDataProvider import TournamentDataProvider
from .TSHLocaleHelper import TSHLocaleHelper
import json


class TSHCountryHelper(QObject):
    instance: "TSHCountryHelper" = None

    countries_json = {}
    countries = {}
    cities = {}
    countryModel = None

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

        # Setup countries - states
        for c in countries_json:
            country_name = c["name"]

            # Load translated name
            for locale in TSHLocaleHelper.currentLocale:
                if locale in c["translations"]:
                    country_name = c["translations"][locale]
                    break

            TSHCountryHelper.countries[c["iso2"]] = {
                "name": country_name,
                "code": c["iso2"],
                "latitude": c.get("latitude"),
                "longitude": c.get("longitude"),
                "states": {}
            }

            for s in c["states"]:
                TSHCountryHelper.countries[c["iso2"]]["states"][s["state_code"]] = {
                    "name": s["name"],
                    "code": s["state_code"],
                    "latitude": s.get("latitude"),
                    "longitude": s.get("longitude"),
                }

        # Setup model
        TSHCountryHelper.countryModel = QStandardItemModel()

        noCountry = QStandardItem()
        noCountry.setData({}, Qt.ItemDataRole.UserRole)
        TSHCountryHelper.countryModel.appendRow(noCountry)

        for i, country_code in enumerate(TSHCountryHelper.countries.keys()):
            item = QStandardItem()
            item.setIcon(
                QIcon(f'./assets/country_flag/{country_code.lower()}.png'))
            countryData = {
                "name": TSHCountryHelper.countries[country_code]["name"],
                "code": TSHCountryHelper.countries[country_code]["code"],
                "latitude": TSHCountryHelper.countries[country_code]["latitude"],
                "longitude": TSHCountryHelper.countries[country_code]["longitude"],
                "asset": f'./assets/country_flag/{country_code.lower()}.png'
            }
            item.setData(countryData, Qt.ItemDataRole.UserRole)
            item.setData(
                f'{TSHCountryHelper.countries[country_code]["name"]} ({country_code})', Qt.ItemDataRole.EditRole)
            TSHCountryHelper.countryModel.appendRow(item)

        # Setup cities - states for reverse search
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
