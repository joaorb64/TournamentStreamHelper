import json
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os

from src.SettingsManager import SettingsManager


class TSHLocaleHelperSignals(QObject):
    localeChanged = pyqtSignal()


class TSHLocaleHelper(QObject):
    exportLocale = "en-US"
    programLocale = "en-US"
    roundLocale = "en-US"
    translator = None
    languages = []
    remapping = {}

    def LoadLocale():

        settingsProgramLocale = SettingsManager.Get("program_language", None)
        settingsExportLocale = SettingsManager.Get("export_language", None)
        settingsRoundLocale = SettingsManager.Get("round_language", None)

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

        if settingsRoundLocale and settingsRoundLocale != "default":
            TSHLocaleHelper.roundLocale = settingsRoundLocale
        else:
            TSHLocaleHelper.roundLocale = current_locale[0]

    def LoadLanguages():
        try:
            languages_json = json.load(open("./src/i18n/mapping.json", 'rt', encoding='utf-8'))
            TSHLocaleHelper.languages = languages_json.get("languages")
            TSHLocaleHelper.remapping = languages_json.get("remapping")
        except Exception as e:
            raise Exception(f"Error loading languages") from e

    def GetRemaps(language: str):
        for remap, langs in TSHLocaleHelper.remapping.items():
            if language.replace('-', '_') in langs:
                print("Loaded remap: ", remap)
                return remap
        return None


TSHLocaleHelper.LoadLanguages()
