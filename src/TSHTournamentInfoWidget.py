from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from Helpers.TSHCountryHelper import TSHCountryHelper
from StateManager import StateManager
from TSHGameAssetManager import TSHGameAssetManager
from TSHPlayerDB import TSHPlayerDB
from TSHTournamentDataProvider import TSHTournamentDataProvider


class TSHTournamentInfoWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)

        uic.loadUi("src/layout/TSHTournamentInfo.ui", self)

        TSHTournamentDataProvider.signals.tournament_data_updated.connect(
            self.UpdateData)
        print("signalconnected")

    def UpdateData(self, data):
        print("tournamentdata", data)

        for key in data.keys():
            print(key)
            widget: QWidget = self.findChild(QWidget, key)

            if widget:
                if type(widget) == QLineEdit:
                    widget.setText(data[key])

                if type(widget) == QSpinBox:
                    widget.setValue(data[key])
