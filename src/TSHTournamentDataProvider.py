import re
import time
import traceback
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import requests
import threading
from .SettingsManager import SettingsManager
from .TSHGameAssetManager import TSHGameAssetManager, TSHGameAssetManagerSignals
from .TournamentDataProvider.TournamentDataProvider import TournamentDataProvider
from .TournamentDataProvider.ChallongeDataProvider import ChallongeDataProvider
from .TournamentDataProvider.StartGGDataProvider import StartGGDataProvider
import json

from .Workers import Worker


class TSHTournamentDataProviderSignals(QObject):
    tournament_changed = pyqtSignal()
    entrants_updated = pyqtSignal()
    tournament_data_updated = pyqtSignal(dict)
    twitch_username_updated = pyqtSignal()
    user_updated = pyqtSignal()
    recent_sets_updated = pyqtSignal(dict)


class TSHTournamentDataProvider:
    instance: "TSHTournamentDataProvider" = None

    def __init__(self) -> None:
        self.provider: TournamentDataProvider = None
        self.signals: TSHTournamentDataProviderSignals = TSHTournamentDataProviderSignals()
        self.entrantsModel: QStandardItemModel = None
        self.threadPool = QThreadPool()

        TSHGameAssetManager.instance.signals.onLoadAssets.connect(
            self.SetGameFromProvider)

    def SetGameFromProvider(self):
        if not self.provider or not self.provider.videogame:
            return

        if "start.gg" in self.provider.url:
            TSHGameAssetManager.instance.SetGameFromStartGGId(
                self.provider.videogame)
        elif "challonge.com" in self.provider.url:
            TSHGameAssetManager.instance.SetGameFromChallongeId(
                self.provider.videogame)
        else:
            print("Unsupported provider...")

    def SetTournament(self, url, initialLoading=False):
        if self.provider and self.provider.url == url:
            return

        if "start.gg" in url:
            TSHTournamentDataProvider.instance.provider = StartGGDataProvider(
                url, self.threadPool, self)
        elif "challonge.com" in url:
            TSHTournamentDataProvider.instance.provider = ChallongeDataProvider(
                url, self.threadPool, self)
        else:
            print("Unsupported provider...")
            return

        tournamentData = TSHTournamentDataProvider.instance.provider.GetTournamentData()
        tournamentData.update({"initial_load": initialLoading})
        TSHTournamentDataProvider.instance.signals.tournament_data_updated.emit(
            tournamentData)

        TSHTournamentDataProvider.instance.provider.GetEntrants()
        TSHTournamentDataProvider.instance.signals.tournament_changed.emit()

        SettingsManager.Set("TOURNAMENT_URL", url)

    def SetStartggEventSlug(self, mainWindow):
        inp = QDialog(mainWindow)

        layout = QVBoxLayout()
        inp.setLayout(layout)

        inp.layout().addWidget(QLabel(
            "Paste the tournament URL. \nFor startgg, the link must contain the /event/ part"
        ))

        lineEdit = QLineEdit()
        okButton = QPushButton("OK")
        validators = [
            QRegularExpression("start.gg/tournament/[^/]+/event/[^/]+"),
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

            if "start.gg" in url:
                matches = re.match(
                    "(.*start.gg/tournament/[^/]*/event/[^/]*)", url)
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

    def SetUserAccount(self, window, startgg=False):
        providerName = "StartGG"
        window_text = ""

        if (self.provider and self.provider.url and "start.gg" in self.provider.url) or startgg:
            window_text = "Paste the URL to the player's startgg profile"
        elif self.provider and self.provider.url and "challonge" in self.provider.url:
            window_text = "Insert the player's name in bracket"
            providerName = self.provider.name
        else:
            print("Invalid tournament data provider")
            return

        text, okPressed = QInputDialog.getText(
            window, "Set player", window_text, QLineEdit.Normal, "")

        if okPressed:
            SettingsManager.Set(providerName+"_user", text)
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

        mainWindow.startGGSetSelecDialog = QDialog(mainWindow)
        mainWindow.startGGSetSelecDialog.setWindowTitle("Select a set")
        mainWindow.startGGSetSelecDialog.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        mainWindow.startGGSetSelecDialog.setLayout(layout)

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

        mainWindow.startggSetSelectionItemList = QTableView()
        layout.addWidget(mainWindow.startggSetSelectionItemList)
        mainWindow.startggSetSelectionItemList.setSortingEnabled(True)
        mainWindow.startggSetSelectionItemList.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        mainWindow.startggSetSelectionItemList.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        mainWindow.startggSetSelectionItemList.setModel(proxyModel)
        mainWindow.startggSetSelectionItemList.setColumnHidden(5, True)
        mainWindow.startggSetSelectionItemList.horizontalHeader().setStretchLastSection(True)
        mainWindow.startggSetSelectionItemList.horizontalHeader(
        ).setSectionResizeMode(QHeaderView.Stretch)
        mainWindow.startggSetSelectionItemList.resizeColumnsToContents()

        btOk = QPushButton("OK")
        layout.addWidget(btOk)
        btOk.clicked.connect(
            lambda x: TSHTournamentDataProvider.instance.LoadSelectedSet(
                mainWindow)
        )

        mainWindow.startGGSetSelecDialog.resize(1200, 500)

        qr = mainWindow.startGGSetSelecDialog.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        print(qr, cp)
        mainWindow.startGGSetSelecDialog.move(qr.topLeft())

        mainWindow.startGGSetSelecDialog.show()

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

        if len(mainWindow.startggSetSelectionItemList.selectionModel().selectedRows()) > 0:
            row = mainWindow.startggSetSelectionItemList.selectionModel().selectedRows()[
                0].row()
        setId = mainWindow.startggSetSelectionItemList.model().index(
            row, 5).data(Qt.ItemDataRole.UserRole)
        mainWindow.startGGSetSelecDialog.close()

        setId["auto_update"] = "set"
        mainWindow.signals.NewSetSelected.emit(setId)

    def GetMatch(self, mainWindow, setId, overwrite=True):
        worker = Worker(self.provider.GetMatch, **
                        {"setId": setId})
        worker.signals.result.connect(lambda data: [
            data.update({"overwrite": overwrite}),
            mainWindow.signals.UpdateSetData.emit(data)
        ])
        self.threadPool.start(worker)

    def GetRecentSets(self, id1, id2):
        worker = Worker(self.provider.GetRecentSets, **{
            "id1": id1, "id2": id2, "callback": self.signals.recent_sets_updated, "requestTime": time.time_ns()
        })
        self.threadPool.start(worker)

    def UiMounted(self):
        if SettingsManager.Get("TOURNAMENT_URL"):
            TSHTournamentDataProvider.instance.SetTournament(
                SettingsManager.Get("TOURNAMENT_URL"), initialLoading=True)
            TSHTournamentDataProvider.instance.signals.twitch_username_updated.emit()
            TSHTournamentDataProvider.instance.signals.user_updated.emit()


TSHTournamentDataProvider.instance = TSHTournamentDataProvider()
