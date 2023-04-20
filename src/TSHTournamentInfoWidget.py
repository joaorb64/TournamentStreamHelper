from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
import time
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .SettingsManager import SettingsManager
from .Helpers.TSHLocaleHelper import TSHLocaleHelper
import traceback
import os
import shutil
import urllib

class TSHTournamentInfoWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)

        uic.loadUi("src/layout/TSHTournamentInfo.ui", self)

        TSHTournamentDataProvider.instance.signals.tournament_data_updated.connect(
            self.UpdateData)

        for widget in self.findChildren(QDateEdit):
            widget.dateChanged.connect(lambda value, element=widget: [
                StateManager.Set(
                    f"tournamentInfo.{element.objectName()}", value.toString(QLocale(TSHLocaleHelper.exportLocale).dateFormat(QLocale.FormatType.ShortFormat)))
            ])
            # widget.setDate(d)
            # widget.setValue(StateManager.Get(
            #    f"tournamentInfo.{widget.objectName()}", 0))

        for widget in self.findChildren(QLineEdit):
            if widget.objectName() != "qt_spinbox_lineedit":
                widget.editingFinished.connect(
                    lambda element=widget: [
                        StateManager.Set(
                            f"tournamentInfo.{element.objectName()}", element.text())
                    ])
                widget.editingFinished.emit()

        for widget in self.findChildren(QSpinBox):
            widget.valueChanged.connect(lambda value, element=widget: [
                StateManager.Set(
                    f"tournamentInfo.{element.objectName()}", value)
            ])

        self.btLoadInfoFromTournament: QPushButton = self.findChild(QPushButton, "btLoadInfoFromTournament")
        self.btLoadInfoFromTournament.clicked.connect(lambda: [
            TSHTournamentDataProvider.instance.GetTournamentData()
        ])

        self.btClearInfo: QPushButton = self.findChild(QPushButton, "btClearInfo")
        self.btClearInfo.clicked.connect(lambda: [
            self.UpdateData({})
        ])

        self.btLoadIconFile: QPushButton = self.findChild(QPushButton, "btLoadIconFile")
        self.btLoadIconFile.clicked.connect(lambda: [
            self.LoadIcon()
        ])

        self.btDownloadIcon: QPushButton = self.findChild(QPushButton, "btDownloadIcon")
        self.btDownloadIcon.clicked.connect(lambda: [
            self.DownloadIcon()
        ])

        self.btClearIcon: QPushButton = self.findChild(QPushButton, "btClearIcon")
        self.btClearIcon.clicked.connect(lambda: [
            self.SetDefaultIcon()
        ])

        self.iconView: QLabel = self.findChild(QLabel, "iconView")

        self.UpdateIcon()
    
    def UpdateIcon(self):
        try:
            # Load icon
            icon = QPixmap("./layout/logo.png").scaledToWidth(64)
        except:
            # Something's wrong with the icon
            icon = QPixmap("./assets/icons/cancel.svg").scaledToWidth(32)

        self.iconView.setPixmap(icon)
    
    def LoadIcon(self):
        try:
            fileName = QFileDialog.getOpenFileName(
                self,
                QApplication.translate("app", "Open Image"),
                ".",
                QApplication.translate("app", "Image Files")+" (*.png *.jpg *.bmp)"
            )[0]
        
            if fileName != None:
                pix = QPixmap(fileName)
                pix.save("./layout/logo.png")
        except Exception as e:
            print(traceback.format_exc())
            
        self.UpdateIcon()

    def DownloadIcon(self):
        try:
            url = TSHTournamentDataProvider.instance.provider.GetIconURL()

            response = urllib.request.urlopen(url)
            data = response.read()
            
            pix = QPixmap()
            pix.loadFromData(data)

            pix.save("./layout/logo.png")
        except Exception as e:
            print(traceback.format_exc())
        
        self.UpdateIcon()

    def SetDefaultIcon(self):
        try:
            shutil.copy("./assets/icons/icon.png", "./layout/logo.png")
        except:
            print(traceback.format_exc())
        
        self.UpdateIcon()

    def DisplayErrorMessage(self, message):
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon('assets/icons/icon.png'))
        msgBox.setWindowTitle(QApplication.translate("app", "Error"))
        msgBox.setText(QApplication.translate("app", "Error"))
        msgBox.setInformativeText(message)
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.exec()

    def UpdateData(self, data):
        print("tournamentdata", data)

        if not data.get("initial_load"):
            for widget in self.findChildren(QLineEdit):
                widget.setText("")
                widget.editingFinished.emit()
            for widget in self.findChildren(QSpinBox):
                widget.setValue(0)

        for key in data.keys():
            try:
                widget: QWidget = self.findChild(QWidget, key)

                if widget:
                    if type(widget) == QLineEdit:
                        widget.setText(data[key])
                        widget.editingFinished.emit()

                    if type(widget) == QSpinBox:
                        widget.setValue(data[key])

                    if type(widget) == QDateEdit:
                        # This is how to put a date into QDateEdit Element using a timestamp
                        #        aTime = '2018-07-24 19:24:11.272000'
                        unix_timestamp = float(data[key])
                        #        tmToDate = datetime.datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        #        utc_time = time.gmtime(unix_timestamp)
                        local_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
                            unix_timestamp))  # converts timestampt to local time and apply the format
                        local_date = local_datetime.split(
                            " ")[0]  # get only the date
                        # Convert date into QDate object
                        d = QDate.fromString(local_date, "yyyy-MM-dd")
                        widget.setDate(d)
            except:
                print(traceback.format_exc())
                SettingsManager.Set("TOURNAMENT_URL", '')
                error_message = QApplication.translate("app", "The tournament URL could not be loaded.") + "\n" + QApplication.translate(
                    "app", "Make sure that your tournament URL is correctly formatted and points to an existing event, and try again.")
                self.DisplayErrorMessage(error_message)
                break
