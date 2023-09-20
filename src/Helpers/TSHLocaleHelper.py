import json
from qtpy import QtGui, QtWidgets, QtCore
from qtpy.QtCore import *
from qtpy.QtGui import *
import os
import traceback
from copy import deepcopy
from loguru import logger

from src.SettingsManager import SettingsManager
from src.StateManager import StateManager


class TSHLocaleHelperSignals(QObject):
    localeChanged = Signal()


class TSHLocaleHelper(QObject):
    exportLocale = "en-US"
    programLocale = "en-US"
    fgTermLocale = "en-US"
    matchNames = {}
    phaseNames = {}
    translator = None
    languages = []
    remapping = {}
    countryToLanguage = {}
    countryToContinent = {}

    def LoadLocale():
        settingsProgramLocale = SettingsManager.Get("program_language", None)
        settingsExportLocale = SettingsManager.Get("game_asset_language", None)
        settingsFgTerm = SettingsManager.Get("fg_term_language", None)

        if settingsProgramLocale and settingsProgramLocale != "default":
            current_locale = [settingsProgramLocale]
        else:
            current_locale = QtCore.QLocale().uiLanguages()

        logger.info("OS locale: " + str(current_locale))

        oldTranslator = TSHLocaleHelper.translator

        if oldTranslator:
            QGuiApplication.instance().removeTranslator(oldTranslator)

        TSHLocaleHelper.translator = QTranslator()
        localeFound = False
        for locale in current_locale:
            if localeFound:
                break
            for f in os.listdir("./src/i18n/"):
                if f.endswith(".qm"):
                    lang = f.split("_", 1)[1].split(".")[0]
                    if lang == locale:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), "./src/i18n/"+f)
                        TSHLocaleHelper.programLocale = locale
                        localeFound = True
                        break
                    elif lang == locale.split("-")[0]:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), "./src/i18n/"+f)
                        TSHLocaleHelper.programLocale = locale
                        localeFound = True
                        break

        QGuiApplication.instance().installTranslator(TSHLocaleHelper.translator)

        if settingsExportLocale and settingsExportLocale != "default":
            TSHLocaleHelper.exportLocale = settingsExportLocale
        else:
            TSHLocaleHelper.exportLocale = current_locale[0]

        if settingsFgTerm and settingsFgTerm != "default":
            TSHLocaleHelper.fgTermLocale = settingsFgTerm
        else:
            TSHLocaleHelper.fgTermLocale = current_locale[0]

    def LoadLanguages():
        try:
            languages_json = json.load(
                open("./src/i18n/mapping.json", 'rt', encoding='utf-8'))
            TSHLocaleHelper.languages = languages_json.get("languages")
            TSHLocaleHelper.remapping = languages_json.get("remapping")
        except Exception as e:
            raise Exception(f"Error loading languages") from e

    def LoadCountryToLanguage():
        try:
            languages_json = json.load(
                open("./assets/data_countries.json", 'rt', encoding='utf-8'))
            TSHLocaleHelper.countryToLanguage = {ccode: cdata.get(
                "languages") for ccode, cdata in languages_json.items()}
            TSHLocaleHelper.countryToContinent = {ccode: cdata.get(
                "continent") for ccode, cdata in languages_json.items()}
        except Exception as e:
            raise Exception(f"Error loading languages") from e

    def GetCountrySpokenLanguages(countryCode2: str):
        return TSHLocaleHelper.countryToLanguage.get(countryCode2.upper(), [])

    def GetCountryContinent(countryCode2: str):
        return TSHLocaleHelper.countryToContinent.get(countryCode2.upper(), "")

    def LoadRoundNames():
        # Load default round names and translation
        try:
            original_term_names: dict = json.load(
                open("./src/i18n/tournament_term/en.json", 'rt', encoding='utf-8'))
            term_names = deepcopy(original_term_names)

            for f in os.listdir("./src/i18n/tournament_term/"):
                if f.endswith(".json"):
                    lang = f.split(".")[0]

                    if lang == TSHLocaleHelper.fgTermLocale:
                        # We found the exact language file
                        translatedRoundNames = json.load(
                            open(f"./src/i18n/tournament_term/{f}", 'rt', encoding='utf-8'))
                        term_names = original_term_names.copy()
                        term_names.update(translatedRoundNames)
                        break
                    elif lang == TSHLocaleHelper.fgTermLocale.split("-")[0]:
                        # We found a more generic language file
                        # Good enough if we don't find a specific one
                        translatedRoundNames = json.load(
                            open(f"./src/i18n/tournament_term/{f}", 'rt', encoding='utf-8'))
                        term_names = original_term_names.copy()
                        term_names.update(translatedRoundNames)

            TSHLocaleHelper.matchNames = term_names.get("match")
            TSHLocaleHelper.phaseNames = term_names.get("phase")
        except:
            logger.error(traceback.format_exc())

        # Load user round names in a separate try/catch
        try:
            term_names: dict = json.load(
                open("./user_data/tournament_terms.json", 'rt', encoding='utf-8'))

            term_names["phase"] = {
                k: v for k, v in term_names.get("phase", {}).items() if v}
            term_names["match"] = {
                k: v for k, v in term_names.get("match", {}).items() if v}

            TSHLocaleHelper.phaseNames.update(term_names["phase"])
            TSHLocaleHelper.matchNames.update(term_names["match"])
        except:
            logger.error("Custom Tournament Terms were not found and/or loaded.")

    def GetRemaps(language: str):
        for remap, langs in TSHLocaleHelper.remapping.items():
            if language.replace('-', '_') in langs:
                logger.info("Loaded remap: " + str(remap))
                return remap
        return None


TSHLocaleHelper.LoadLanguages()
TSHLocaleHelper.LoadCountryToLanguage()
