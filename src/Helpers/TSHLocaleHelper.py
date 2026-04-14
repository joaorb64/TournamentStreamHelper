import json
from qtpy import QtGui, QtWidgets, QtCore
from qtpy.QtCore import *
from qtpy.QtGui import *
import os
import traceback
from loguru import logger

from src.SettingsManager import SettingsManager
from src.StateManager import StateManager
from .TSHDictHelper import deep_clone
from .TSHDirHelper import TSHResolve


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
        i18n_dir = TSHResolve('src/i18n')

        if oldTranslator:
            QGuiApplication.instance().removeTranslator(oldTranslator)

        TSHLocaleHelper.translator = QTranslator()
        localeFound = False
        for locale in current_locale:
            if localeFound:
                break
            for f in os.listdir(f"{i18n_dir}/"):
                if f.endswith(".qm"):
                    lang = f.split("_", 1)[1].split(".")[0]
                    if lang == locale:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), f"{i18n_dir}/{f}")
                        TSHLocaleHelper.programLocale = locale
                        localeFound = True
                        break
                    elif lang == locale.split("-")[0]:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), f"{i18n_dir}/{f}")
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
            i18n_dir = TSHResolve('src/i18n')
            languages_json = json.load(
                open(f"{i18n_dir}/mapping.json", 'rt', encoding='utf-8'))
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
            tterm_dir = TSHResolve('./src/i18n/tournament_term')
            original_term_names: dict = json.load(
                open(f"{tterm_dir}/en.json", 'rt', encoding='utf-8'))
            term_names = deep_clone(original_term_names)

            for f in os.listdir(f"{tterm_dir}/"):
                if f.endswith(".json"):
                    lang = f.split(".")[0]

                    if lang == TSHLocaleHelper.fgTermLocale:
                        # We found the exact language file
                        translatedRoundNames = json.load(
                            open(f"{tterm_dir}/{f}", 'rt', encoding='utf-8'))
                        term_names = original_term_names.copy()
                        term_names.update(translatedRoundNames)
                        break
                    elif lang == TSHLocaleHelper.fgTermLocale.split("-")[0]:
                        # We found a more generic language file
                        # Good enough if we don't find a specific one
                        translatedRoundNames = json.load(
                            open(f"{tterm_dir}/{f}", 'rt', encoding='utf-8'))
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
            logger.warning("Custom Tournament Terms were not found and/or loaded.")

    def GetRemaps(language: str):
        for remap, langs in TSHLocaleHelper.remapping.items():
            if language.replace('-', '_') in langs:
                logger.info("Loaded remap: " + str(remap))
                return remap
        return None
    
    def LoadPhaseNamesToWidget(widget):
        for key in dict(sorted(TSHLocaleHelper.phaseNames.items(), key=lambda item: item[1])).keys():
            phaseString = TSHLocaleHelper.phaseNames[key]

            if "{0}" in phaseString:
                if "top" not in key:
                    for letter in ["A", "B", "C", "D"]:
                        if widget.findText(phaseString.format(letter)) < 0:
                            widget.addItem(phaseString.format(letter))
            else:
                if widget.findText(phaseString) < 0:
                    widget.addItem(phaseString)
    
    def LoadMatchNamesToWidget(widget):
        for key in dict(sorted(TSHLocaleHelper.matchNames.items(), key=lambda item: item[1])).keys():
            matchString = TSHLocaleHelper.matchNames[key]
            try:
                if "{0}" in matchString and ("qualifier" in key):
                    # Generate preset qualifier names
                    couples = [
                        (TSHLocaleHelper.phaseNames.get("top_n").format(8), TSHLocaleHelper.matchNames.get("qualifier_winners_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(16), TSHLocaleHelper.matchNames.get("qualifier_winners_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(32), TSHLocaleHelper.matchNames.get("qualifier_winners_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(6), TSHLocaleHelper.matchNames.get("qualifier_losers_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(8), TSHLocaleHelper.matchNames.get("qualifier_losers_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(12), TSHLocaleHelper.matchNames.get("qualifier_losers_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(16), TSHLocaleHelper.matchNames.get("qualifier_losers_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(24), TSHLocaleHelper.matchNames.get("qualifier_losers_indicator")),
                        (TSHLocaleHelper.phaseNames.get("top_n").format(32), TSHLocaleHelper.matchNames.get("qualifier_losers_indicator"))
                    ]

                    for couple in couples:
                        # logger.info(couple)
                        widget.addItem(matchString.format(*couple))
                elif "{0}" in matchString and ("qualifier" not in key):
                    for number in range(5):
                        if key == "best_of":
                            if widget.findText(matchString.format(str(2*number+1))) < 0:
                                widget.addItem(matchString.format(str(2*number+1)))
                        else:
                            if widget.findText(matchString.format(str(number+1))) < 0:
                                widget.addItem(matchString.format(str(number+1)))
                elif "indicator" in key:
                    pass
                else:
                    if widget.findText(matchString) < 0:
                        widget.addItem(matchString)
            except:
                logger.error(
                    f"Unable to generate match strings for {matchString}")


TSHLocaleHelper.LoadLanguages()
TSHLocaleHelper.LoadCountryToLanguage()
