import json
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os


class TSHLocaleHelperSignals(QObject):
    localeChanged = pyqtSignal()


class TSHLocaleHelper(QObject):
    exportLocale = "ja"
    programLocale = "en-US"
    translator = None
    languages = []

    def LoadLocale(programLocale: str = None):
        if not programLocale:
            current_locale = QtCore.QLocale().uiLanguages()
        else:
            current_locale = [programLocale]

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

        print(TSHLocaleHelper.programLocale)

        QGuiApplication.instance().installTranslator(TSHLocaleHelper.translator)

    def LoadLanguages():
        try:
            languages_json = json.load(open("./src/i18n/mapping.json"))
            TSHLocaleHelper.languages = languages_json.get("languages")
        except:
            print("Error loading languages")


TSHLocaleHelper.LoadLanguages()
