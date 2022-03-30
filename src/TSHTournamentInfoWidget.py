from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider


class TSHTournamentInfoWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)

        uic.loadUi("src/layout/TSHTournamentInfo.ui", self)

        TSHTournamentDataProvider.instance.signals.tournament_data_updated.connect(
            self.UpdateData)

        for widget in self.findChildren(QLineEdit):
            if widget.objectName() != "qt_spinbox_lineedit":
                widget.editingFinished.connect(
                    lambda element=widget: [
                        StateManager.Set(
                            f"tournamentInfo.{element.objectName()}", element.text())
                    ])
                widget.editingFinished.emit()
                widget.setText(StateManager.Get(
                    f"tournamentInfo.{widget.objectName()}", ""))

        for widget in self.findChildren(QSpinBox):
            widget.valueChanged.connect(lambda value, element=widget: [
                StateManager.Set(
                    f"tournamentInfo.{element.objectName()}", value)
            ])
            widget.setValue(StateManager.Get(
                f"tournamentInfo.{widget.objectName()}", 0))

    def UpdateData(self, data):
        print("tournamentdata", data)

        if not data.get("initial_load"):
            for widget in self.findChildren(QLineEdit):
                widget.setText("")
                widget.editingFinished.emit()
            for widget in self.findChildren(QSpinBox):
                widget.setValue(0)

        for key in data.keys():
            widget: QWidget = self.findChild(QWidget, key)

            if widget:
                if type(widget) == QLineEdit:
                    widget.setText(data[key])
                    widget.editingFinished.emit()

                if type(widget) == QSpinBox:
                    widget.setValue(data[key])
