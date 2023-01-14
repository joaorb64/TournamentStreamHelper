import json
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import traceback
from copy import deepcopy

from src.SettingsManager import SettingsManager


class TSHLocaleHelperSignals(QObject):
    localeChanged = pyqtSignal()


class TSHLocaleHelper(QObject):
    exportLocale = "en-US"
    programLocale = "en-US"
    fgTermLocale = "en-US"
    matchNames = {}
    phaseNames = {}
    translator = None
    languages = []
    remapping = {}

    def LoadLocale():
        settingsProgramLocale = SettingsManager.Get("program_language", None)
        settingsExportLocale = SettingsManager.Get("export_language", None)
        settingsFgTerm = SettingsManager.Get("fg_term_language", None)

        if settingsProgramLocale and settingsProgramLocale != "default":
            current_locale = [settingsProgramLocale]
        else:
            current_locale = QtCore.QLocale().uiLanguages()

        print("OS locale", current_locale)

        oldTranslator = TSHLocaleHelper.translator

        if oldTranslator:
            QGuiApplication.instance().removeTranslator(oldTranslator)

        TSHLocaleHelper.translator = QTranslator()
        for locale in current_locale:
            for f in os.listdir("./src/i18n/"):
                if f.endswith(".qm"):
                    lang = f.split("_", 1)[1].split(".")[0]
                    if lang == locale:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), "./src/i18n/"+f)
                        TSHLocaleHelper.programLocale = locale
                        break
                    elif lang == locale.split("-")[0]:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), "./src/i18n/"+f)
                        TSHLocaleHelper.programLocale = locale
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
            languages_json = json.load(open("./src/i18n/mapping.json", 'rt', encoding='utf-8'))
            TSHLocaleHelper.languages = languages_json.get("languages")
            TSHLocaleHelper.remapping = languages_json.get("remapping")
        except Exception as e:
            raise Exception(f"Error loading languages") from e
    
    def LoadRoundNames():
        # Load default round names and translation
        try:
            original_round_names: dict = json.load(open("./src/i18n/round_names/en.json", 'rt', encoding='utf-8'))
            round_names = deepcopy(original_round_names)

            for f in os.listdir("./src/i18n/round_names/"):
                if f.endswith(".json"):
                    lang = f.split(".")[0]

                    if lang == TSHLocaleHelper.fgTermLocale:
                        # We found the exact language file
                        translatedRoundNames = json.load(open(f"./src/i18n/round_names/{f}", 'rt', encoding='utf-8'))
                        round_names = original_round_names.copy()
                        round_names.update(translatedRoundNames)
                        break
                    elif lang == TSHLocaleHelper.fgTermLocale.split("-")[0]:
                        # We found a more generic language file
                        # Good enough if we don't find a specific one
                        translatedRoundNames = json.load(open(f"./src/i18n/round_names/{f}", 'rt', encoding='utf-8'))
                        round_names = original_round_names.copy()
                        round_names.update(translatedRoundNames)
            
            TSHLocaleHelper.matchNames = round_names.get("match")
            TSHLocaleHelper.phaseNames = round_names.get("phase")
        except:
            print(traceback.format_exc())
        
        # Load user round names in a separate try/catch
        try:
            round_names: dict = json.load(open("./user_data/round_names.json", 'rt', encoding='utf-8'))
            
            round_names["phase"] = {k: v for k, v in round_names.get("phase", {}).items() if v}
            round_names["match"] = {k: v for k, v in round_names.get("match", {}).items() if v}

            TSHLocaleHelper.phaseNames.update(round_names["phase"])
            TSHLocaleHelper.matchNames.update(round_names["match"])
        except:
            print(traceback.format_exc())


    def GetRemaps(language: str):
        for remap, langs in TSHLocaleHelper.remapping.items():
            if language.replace('-', '_') in langs:
                print("Loaded remap: ", remap)
                return remap
        return None


TSHLocaleHelper.LoadLanguages()