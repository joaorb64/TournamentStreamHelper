import re
import time
import traceback
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
import requests
import threading

from .SettingsManager import SettingsManager
from .TSHGameAssetManager import TSHGameAssetManager, TSHGameAssetManagerSignals
from .TournamentDataProvider.TournamentDataProvider import TournamentDataProvider
from .TournamentDataProvider.ChallongeDataProvider import ChallongeDataProvider
from .TournamentDataProvider.StartGGDataProvider import StartGGDataProvider
from .TournamentDataModifier.TournamentDataModifier import TournamentDataModifier
from .TournamentDataModifier.StartGGDataModifier import StartGGDataModifier
import json 
from loguru import logger

from .Workers import Worker


class TSHTournamentDataManagerSignals(QObject):
    tournament_changed = Signal()
    entrants_updated = Signal()
    tournament_data_updated = Signal(dict)
    twitch_username_updated = Signal()
    user_updated = Signal()
    get_sets_finished = Signal(list)
    tournament_phases_updated = Signal(list)
    tournament_phasegroup_updated = Signal(dict)
    game_changed = Signal(int)
    stream_queue_loaded = Signal(dict)

class TSHTournamentDataManager:
    instance: "TSHTournamentDataManager" = None

    def __init__(self) -> None:
        self.provider: TournamentDataProvider = None
        self.modifier: TournamentDataModifier = None
        self.signals: TSHTournamentDataManagerSignals = TSHTournamentDataManagerSignals()
        self.entrantsModel: QStandardItemModel = None
        self.threadPool = QThreadPool()

        self.signals.game_changed.connect(self.SetGameFromProvider)

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
            logger.error("Unsupported provider...")

    def SetTournament(self, url, initialLoading=False):
        if self.provider and self.provider.url == url:
            return

        if url is not None and "start.gg" in url:
            TSHTournamentDataManager.instance.provider = StartGGDataProvider(
                url, self.threadPool, self)
            TSHTournamentDataModifier.instance.modifier = StartGGDataModifier(
                url, self.threadPool, self)
        elif url is not None and "challonge.com" in url:
            TSHTournamentDataManager.instance.provider = ChallongeDataProvider(
                url, self.threadPool, self)
            TSHTournamentDataManager.instance.modifier = None  
        else:
            logger.error("Unsupported provider...")
            TSHTournamentDataManager.instance.provider = None
            TSHTournamentDataModifier.instance.modifier = None

        SettingsManager.Set("TOURNAMENT_URL", url)

        if self.provider is not None:
            self.GetTournamentData(initialLoading=initialLoading)
            self.GetTournamentPhases()

            TSHTournamentDataManager.instance.provider.GetEntrants()
            TSHTournamentDataManager.instance.signals.tournament_changed.emit()

            TSHTournamentDataManager.instance.SetGameFromProvider()
        else:
            TSHTournamentDataManager.instance.signals.tournament_data_updated.emit({
            })
            TSHTournamentDataManager.instance.signals.tournament_phases_updated.emit([
            ])
            TSHTournamentDataManager.instance.signals.tournament_changed.emit()
            TSHGameAssetManager.instance.LoadGameAssets(0)

    def SetStartggEventSlug(self, mainWindow):
        inp = QDialog(mainWindow)

        layout = QVBoxLayout()
        inp.setLayout(layout)

        inp.layout().addWidget(QLabel(
            QApplication.translate("app", "Paste the tournament URL.")+"\n" + QApplication.translate(
                "app", "For StartGG, the link must contain the /event/ part")
        ))

        lineEdit = QLineEdit()
        okButton = QPushButton("OK")
        validators = [
            QRegularExpression("start.gg/tournament/[^/]+/event[s]?/[^/]+"),
            QRegularExpression("challonge.com/.+")
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

        inp.setWindowTitle(QApplication.translate("app", "Set tournament URL"))
        inp.resize(600, 10)

        if inp.exec_() == QDialog.Accepted:
            url = lineEdit.text()

            if "start.gg" in url:
                matches = re.match(
                    "(.*start.gg/tournament/[^/]*/event[s]?/[^/]*)", url)
                if matches:
                    url = matches.group(0)

                    # Some URLs in startgg have eventS but the API doesn't work with that format
                    url = url.replace("/events/", "/event/")
            if "challonge" in url:
                matches = re.match(
                    "(.*challonge.com/[^/]*/[^/]*)", url)
                if matches:
                    url = matches.group(0)

            SettingsManager.Set("TOURNAMENT_URL", url)
            TSHTournamentDataManager.instance.SetTournament(
                SettingsManager.Get("TOURNAMENT_URL"))

        inp.deleteLater()

    def SetTwitchUsername(self, window):
        text, okPressed = QInputDialog.getText(
            window, QApplication.translate("app", "Set Twitch username"), QApplication.translate("app", "Twitch Username:")+" ", QLineEdit.Normal, "")
        if okPressed:
            SettingsManager.Set("twitch_username", text)
            TSHTournamentDataManager.instance.signals.twitch_username_updated.emit()

    def SetUserAccount(self, window, startgg=False):
        providerName = "StartGG"
        window_text = ""

        if (self.provider and self.provider.url and "start.gg" in self.provider.url) or startgg:
            window_text = QApplication.translate(
                "app", "Paste the URL to the player's StartGG profile")
        elif self.provider and self.provider.url and "challonge" in self.provider.url:
            window_text = QApplication.translate(
                "app", "Insert the player's name in bracket")
            providerName = self.provider.name
        else:
            logger.error(QApplication.translate(
                "app", "Invalid tournament data provider"))
            return

        text, okPressed = QInputDialog.getText(
            window, QApplication.translate("app", "Set player"), window_text, QLineEdit.Normal, "")

        if okPressed:
            SettingsManager.Set(providerName+"_user", text)
            TSHTournamentDataManager.instance.signals.user_updated.emit()

    def CanModify(self):
        return bool(self.modifier)

    def GetTournamentData(self, initialLoading=False):
        worker = Worker(self.provider.GetTournamentData)
        worker.signals.result.connect(lambda tournamentData: [
            tournamentData.update({"initial_load": initialLoading}),
            TSHTournamentDataManager.instance.signals.tournament_data_updated.emit(
                tournamentData)
        ])
        self.threadPool.start(worker)

    def GetTournamentPhases(self):
        worker = Worker(self.provider.GetTournamentPhases)
        worker.signals.result.connect(lambda tournamentPhases: [
            TSHTournamentDataManager.instance.signals.tournament_phases_updated.emit(
                tournamentPhases)
        ])
        self.threadPool.start(worker)

    def GetTournamentPhaseGroup(self, id):
        worker = Worker(self.provider.GetTournamentPhaseGroup, **{"id": id})
        worker.signals.result.connect(lambda phaseGroupData: [
            TSHTournamentDataManager.instance.signals.tournament_phasegroup_updated.emit(
                phaseGroupData)
        ])
        self.threadPool.start(worker)

    def LoadSets(self, showFinished):
        worker = Worker(self.provider.GetMatches, **
                        {"getFinished": showFinished})
        worker.signals.result.connect(lambda data: [
            logger.info(data),
            self.signals.get_sets_finished.emit(data)
        ])
        self.threadPool.start(worker)

    def LoadStreamSet(self, mainWindow, streamName):
        streamSet = TSHTournamentDataManager.instance.provider.GetStreamMatchId(
            streamName)

        if not streamSet:
            return

        streamSet["auto_update"] = "stream"
        mainWindow.signals.NewSetSelected.emit(streamSet)

    def LoadUserSet(self, mainWindow, user):
        _set = TSHTournamentDataManager.instance.provider.GetUserMatchId(user)

        if not _set:
            return

        _set["auto_update"] = "user"
        mainWindow.signals.NewSetSelected.emit(_set)

    def GetMatch(self, mainWindow, setId, overwrite=True):
        worker = Worker(self.provider.GetMatch, **
                        {"setId": setId})
        worker.signals.result.connect(lambda data: [
            data.update({"overwrite": overwrite}),
            mainWindow.signals.UpdateSetData.emit(data)
        ])
        self.threadPool.start(worker)

    def GetRecentSets(self, callback, id1, id2):
        worker = Worker(self.provider.GetRecentSets, **{
            "id1": id1, "id2": id2, "callback": callback, "requestTime": time.time_ns()
        })
        self.threadPool.start(worker)

    def GetStandings(self, playerNumber, callback):
        worker = Worker(self.provider.GetStandings, **{
            "playerNumber": playerNumber
        })
        worker.signals.result.connect(lambda data: [
            callback.emit(data)
        ])
        self.threadPool.start(worker)

    def GetLastSets(self, callback, playerId, playerNumber):
        worker = Worker(self.provider.GetLastSets, **{
            "playerID": playerId[0],
            "playerNumber": playerNumber,
            "callback": callback
        })
        self.threadPool.start(worker)

    def GetPlayerHistoryStandings(self, callback, playerId, playerNumber, gameType):
        worker = Worker(self.provider.GetPlayerHistoryStandings, **{
            "playerID": playerId[0],
            "playerNumber": playerNumber,
            "gameType": gameType,
            "callback": callback
        })
        self.threadPool.start(worker)

    def GetStreamQueue(self):
        worker = Worker(self.provider.GetStreamQueue)
        worker.signals.result.connect(lambda streamQueue: [
            TSHTournamentDataManager.instance.signals.stream_queue_loaded.emit(
                streamQueue)
        ])
        self.threadPool.start(worker)

    def UiMounted(self):
        if SettingsManager.Get("TOURNAMENT_URL"):
            TSHTournamentDataManager.instance.SetTournament(
                SettingsManager.Get("TOURNAMENT_URL"), initialLoading=True)
            TSHTournamentDataManager.instance.signals.twitch_username_updated.emit()
            TSHTournamentDataManager.instance.signals.user_updated.emit()


TSHTournamentDataManager.instance = TSHTournamentDataManager()
