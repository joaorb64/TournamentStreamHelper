import re
from time import sleep
import traceback
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

from Workers import Worker


class TSHTournamentDataProviderSignals(QObject):
    tournament_changed = pyqtSignal()
    entrants_updated = pyqtSignal()
    tournament_data_updated = pyqtSignal(dict)
    twitch_username_updated = pyqtSignal()
    user_updated = pyqtSignal()


class TSHTournamentDataProvider:
    instance: "TSHTournamentDataProvider" = None

    def __init__(self) -> None:
        self.provider: TournamentDataProvider = None
        self.signals: TSHTournamentDataProviderSignals = TSHTournamentDataProviderSignals()
        self.entrantsModel: QStandardItemModel = None
        self.threadPool = QThreadPool()

    def SetTournament(self, url, initialLoading=False):
        if self.provider and self.provider.url == url:
            return

        if "smash.gg" in url:
            TSHTournamentDataProvider.instance.provider = SmashGGDataProvider(
                url)
        elif "challonge.com" in url:
            TSHTournamentDataProvider.instance.provider = ChallongeDataProvider(
                url)
        else:
            print("Unsupported provider...")

        tournamentData = TSHTournamentDataProvider.instance.provider.GetTournamentData()
        tournamentData.update({"initial_load": initialLoading})
        TSHTournamentDataProvider.instance.signals.tournament_data_updated.emit(
            tournamentData)

        TSHTournamentDataProvider.instance.provider.GetEntrants()
        TSHTournamentDataProvider.instance.signals.tournament_changed.emit()

        SettingsManager.Set("TOURNAMENT_URL", url)

    def SetSmashggEventSlug(self, mainWindow):
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
            QRegularExpression("challonge.com/.+/.+")
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
            url = lineEdit.text()

            if "smash.gg" in url:
                matches = re.match(
                    "(.*smash.gg/tournament/[^/]*/event/[^/]*)", url)
                if matches:
                    url = matches.group(0)
            if "challonge" in url:
                matches = re.match(
                    "(.*challonge.com/[^/]*/[^/]*)", url)
                if matches:
                    url = matches.group(0)

            SettingsManager.Set("TOURNAMENT_URL", url)
            TSHTournamentDataProvider.instance.SetTournament(
                SettingsManager.Get("TOURNAMENT_URL"))

        inp.deleteLater()

    def SetTwitchUsername(self, window):
        text, okPressed = QInputDialog.getText(
            window, "Set Twitch username", "Username: ", QLineEdit.Normal, "")
        if okPressed:
            SettingsManager.Set("twitch_username", text)
            TSHTournamentDataProvider.instance.signals.twitch_username_updated.emit()

    def SetUserAccount(self, window, smashgg=False):
        if self.provider.url:
            window_text = ""
            if "smash.gg" in self.provider.url or smashgg:
                window_text = "Paste the URL to the player's SmashGG profile"
            elif "challonge" in self.provider.url:
                window_text = "Insert the player's name in bracket"
            else:
                print("Invalid tournament data provider")
                return
            text, okPressed = QInputDialog.getText(
                window, "Set player", window_text, QLineEdit.Normal, "")
            if okPressed:
                SettingsManager.Set(self.provider.name+"_user", text)
                TSHTournamentDataProvider.instance.signals.user_updated.emit()

    def LoadSets(self, mainWindow):
        sets = TSHTournamentDataProvider.instance.provider.GetMatches()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            ["Stream", "Wave", "Title", "Player 1", "Player 2"])

        if sets is not None:
            for s in sets:
                dataItem = QStandardItem(str(s.get("id")))
                dataItem.setData(s, Qt.ItemDataRole.UserRole)

                player_names = [s.get("p1_name"), s.get("p2_name")]

                try:
                    # For doubles, use team name + entrants names
                    if len(s.get("entrants", [[]])[0]) > 1:
                        for t, team in enumerate(s.get("entrants")):
                            pnames = []
                            for p, player in enumerate(s.get("entrants")[t]):
                                pnames.append(player.get("gamerTag"))
                            player_names[t] += " ("+", ".join(pnames)+")"
                except Exception as e:
                    traceback.print_exc()

                model.appendRow([
                    QStandardItem(s.get("stream", "")),
                    QStandardItem(s.get("tournament_phase", "")),
                    QStandardItem(s["round_name"]),
                    QStandardItem(player_names[0]),
                    QStandardItem(player_names[1]),
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
            lambda x: TSHTournamentDataProvider.instance.LoadSelectedSet(
                mainWindow)
        )

        mainWindow.smashGGSetSelecDialog.show()
        mainWindow.smashGGSetSelecDialog.resize(1200, 500)

    def LoadStreamSet(self, mainWindow, streamName):
        streamSet = TSHTournamentDataProvider.instance.provider.GetStreamMatchId(
            streamName)

        if not streamSet:
            streamSet = {}

        streamSet["auto_update"] = "stream"
        mainWindow.signals.NewSetSelected.emit(streamSet)

    def LoadUserSet(self, mainWindow, user):
        _set = TSHTournamentDataProvider.instance.provider.GetUserMatchId(user)

        if not _set:
            _set = {}

        _set["auto_update"] = "user"
        mainWindow.signals.NewSetSelected.emit(_set)

    def LoadSelectedSet(self, mainWindow):
        row = 0

        if len(mainWindow.smashggSetSelectionItemList.selectionModel().selectedRows()) > 0:
            row = mainWindow.smashggSetSelectionItemList.selectionModel().selectedRows()[
                0].row()
        setId = mainWindow.smashggSetSelectionItemList.model().index(
            row, 5).data(Qt.ItemDataRole.UserRole)
        mainWindow.smashGGSetSelecDialog.close()

        mainWindow.signals.NewSetSelected.emit(setId)

    def GetMatch(self, mainWindow, setId, overwrite=True):
        worker = Worker(self.provider.GetMatch, **
                        {"setId": setId})
        worker.signals.result.connect(lambda data: [
            data.update({"overwrite": overwrite}),
            mainWindow.signals.UpdateSetData.emit(data)
        ])
        self.threadPool.start(worker)

    def UiMounted(self):
        if SettingsManager.Get("TOURNAMENT_URL"):
            TSHTournamentDataProvider.instance.SetTournament(
                SettingsManager.Get("TOURNAMENT_URL"), initialLoading=True)
            TSHTournamentDataProvider.instance.signals.twitch_username_updated.emit()
            TSHTournamentDataProvider.instance.signals.user_updated.emit()


TSHTournamentDataProvider.instance = TSHTournamentDataProvider()
