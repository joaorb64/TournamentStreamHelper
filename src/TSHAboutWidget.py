from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy import uic
import json
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider


class TSHAboutWidget(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        uic.loadUi("src/layout/TSHAbout.ui", self)

        try:
            version = json.load(
                open('./assets/versions.json', encoding='utf-8')).get("program", "?")
        except Exception as e:
            version = "?"

        self.findChild(QLabel, "tsh").setText(
            f"TournamentStreamHelper v{version}")

        try:
            icon = QPixmap("./assets/icons/icon.png").scaledToWidth(128)
        except:
            icon = QPixmap()

        self.findChild(QLabel, "icon").setPixmap(icon)

        try:
            contributors = open('./assets/contributors.txt',
                                encoding='utf-8').readlines()
        except Exception as e:
            contributors = ["?"]

        self.findChild(QTextEdit, "contributors").setMarkdown(
            "\n".join(contributors))
