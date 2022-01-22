from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import requests
import threading
from SettingsManager import SettingsManager
from TSHGameAssetManager import TSHGameAssetManagerSignals
from TournamentDataProvider.TournamentDataProvider import TournamentDataProvider
from TournamentDataProvider.ChallongeDataProvider import ChallongeDataProvider
from TournamentDataProvider.SmashGGDataProvider import SmashGGDataProvider
import json


class TSHTournamentDataProviderSignals(QObject):
    tournament_changed = pyqtSignal()
    entrants_updated = pyqtSignal()


class TSHTournamentDataProvider:
    provider: TournamentDataProvider = None
    signals: TSHTournamentDataProviderSignals = TSHTournamentDataProviderSignals()
    entrantsModel: QStandardItemModel = None

    def SetTournament(url):
        if "smash.gg" in url:
            TSHTournamentDataProvider.provider = SmashGGDataProvider(url)
        elif "challonge.com" in url:
            TSHTournamentDataProvider.provider = ChallongeDataProvider(url)
        else:
            print("Unsupported provider...")

        TSHTournamentDataProvider.provider.GetTournamentData()
        TSHTournamentDataProvider.provider.GetEntrants()
        TSHTournamentDataProvider.signals.tournament_changed.emit()

    def SetSmashggEventSlug(mainWindow):
        inp = QDialog(mainWindow)

        layout = QVBoxLayout()
        inp.setLayout(layout)

        inp.layout().addWidget(QLabel(
            "Paste the tournament URL. \nFor SmashGG, the link must contain the /event/ part"
        ))

        lineEdit = QLineEdit()
        okButton = QPushButton("OK")
        validators = [
            QRegularExpression("smash.gg/tournament/[^/]+/event/[^/]+"),
            QRegularExpression("challonge.com.*/.+")
        ]

        def validateText():
            okButton.setDisabled(True)

            for validator in validators:
                match = validator.match(lineEdit.text()).capturedTexts()
                if len(match) > 0:
                    okButton.setDisabled(False)

        lineEdit.textEdited.connect(validateText)

        inp.layout().addWidget(lineEdit)

        okButton.clicked.connect(inp.accept)
        okButton.setDisabled(True)
        inp.layout().addWidget(okButton)

        inp.setWindowTitle('Set tournament URL')
        inp.resize(600, 10)

        if inp.exec_() == QDialog.Accepted:
            mainWindow.settings["TOURNAMENT_URL"] = lineEdit.text()
            mainWindow.SaveSettings()
            mainWindow.smashggTournamentSlug.setText(
                "Set tournament slug (" + str(mainWindow.settings.get(
                    "TOURNAMENT_URL", None)) + ")"
            )
            mainWindow.LoadPlayersFromSmashGGTournamentStart(
                mainWindow.settings.get("TOURNAMENT_URL", None))

        inp.deleteLater()

    def LoadSetsFromTournament(mainWindow):
        sets = TSHTournamentDataProvider.provider.GetMatches()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            ["Stream", "Wave", "Title", "Player 1", "Player 2"])

        if sets is not None:
            for s in sets:
                dataItem = QStandardItem(str(s.get("id")))
                dataItem.setData(s, Qt.ItemDataRole.UserRole)

                model.appendRow([
                    QStandardItem(s.get("stream", {}).get(
                        "streamName", "") if s.get("stream") != None else ""),
                    QStandardItem(s.get("tournament_phase", "")),
                    QStandardItem(s["round_name"]),
                    QStandardItem(s["p1_name"]),
                    QStandardItem(s["p2_name"]),
                    dataItem
                ])

        mainWindow.smashGGSetSelecDialog = QDialog(mainWindow)
        mainWindow.smashGGSetSelecDialog.setWindowTitle("Select a set")
        mainWindow.smashGGSetSelecDialog.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        mainWindow.smashGGSetSelecDialog.setLayout(layout)

        proxyModel = QSortFilterProxyModel()
        proxyModel.setSourceModel(model)
        proxyModel.setFilterKeyColumn(-1)
        proxyModel.setFilterCaseSensitivity(False)

        def filterList(text):
            proxyModel.setFilterFixedString(text)

        searchBar = QLineEdit()
        searchBar.setPlaceholderText("Filter...")
        layout.addWidget(searchBar)
        searchBar.textEdited.connect(filterList)

        mainWindow.smashggSetSelectionItemList = QTableView()
        layout.addWidget(mainWindow.smashggSetSelectionItemList)
        mainWindow.smashggSetSelectionItemList.setSortingEnabled(True)
        mainWindow.smashggSetSelectionItemList.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        mainWindow.smashggSetSelectionItemList.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        mainWindow.smashggSetSelectionItemList.setModel(proxyModel)
        mainWindow.smashggSetSelectionItemList.setColumnHidden(5, True)
        mainWindow.smashggSetSelectionItemList.horizontalHeader().setStretchLastSection(True)
        mainWindow.smashggSetSelectionItemList.horizontalHeader(
        ).setSectionResizeMode(QHeaderView.Stretch)
        mainWindow.smashggSetSelectionItemList.resizeColumnsToContents()

        btOk = QPushButton("OK")
        layout.addWidget(btOk)
        btOk.clicked.connect(
            lambda x: TSHTournamentDataProvider.SetFromSmashGGSelected(
                mainWindow)
        )

        mainWindow.smashGGSetSelecDialog.show()
        mainWindow.smashGGSetSelecDialog.resize(1200, 500)

    def SetFromSmashGGSelected(mainWindow):
        row = 0

        if len(mainWindow.smashggSetSelectionItemList.selectionModel().selectedRows()) > 0:
            row = mainWindow.smashggSetSelectionItemList.selectionModel().selectedRows()[
                0].row()
        setId = mainWindow.smashggSetSelectionItemList.model().index(
            row, 5).data(Qt.ItemDataRole.UserRole)
        mainWindow.smashGGSetSelecDialog.close()

        mainWindow.signals.UpdateSetData.emit(setId)
        mainWindow.signals.NewSetSelected.emit(setId.get("id"))

    def GetMatch(mainWindow, setId):
        data = TSHTournamentDataProvider.provider.GetMatch(setId)
        mainWindow.signals.UpdateSetData.emit(data)


if SettingsManager.Get("TOURNAMENT_URL"):
    TSHTournamentDataProvider.SetTournament(
        SettingsManager.Get("TOURNAMENT_URL"))
