from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os


class TSHLocaleHelperSignals(QObject):
    localeChanged = pyqtSignal()


class TSHLocaleHelper(QObject):
    currentLocale = []
    translator = None

    def LoadLocale():
        current_locale = QtCore.QLocale().uiLanguages()
        print("Current locale", current_locale)

        TSHLocaleHelper.currentLocale = current_locale

        TSHLocaleHelper.translator = QTranslator()
        for locale in current_locale:
            for f in os.listdir("./src/i18n/"):
                if f.endswith(".qm"):
                    lang = f.split("_", 1)[1].split(".")[0]
                    if lang == locale:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), "./src/i18n/"+f)
                        break
                    elif lang == locale.split("-")[0]:
                        TSHLocaleHelper.translator.load(
                            QLocale(lang), "./src/i18n/"+f)
                        break

        QGuiApplication.instance().installTranslator(TSHLocaleHelper.translator)
