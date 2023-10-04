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
from .TournamentDataModifier.TournamentDataModifer import TournamentDataModifier
from .TournamentDataModifier.StartGGDataModifier import StartGGDataModifier
import json
from loguru import logger

from .Workers import Worker


class TSHTournamentDataModifierSignals(QObject):
    pass


class TSHTournamentDataModifier:
    instance: "TSHTournamentDataModifier" = None

    def __init__(self) -> None:
        self.modifier: TournamentDataModifier = None
        self.signals: TSHTournamentDataModifierSignals = TSHTournamentDataModifierSignals()
        self.threadPool = QThreadPool()

    def SetTournament(self, url, initialLoading=False):
        if self.modifier and self.modifier.url == url:
            return

        if url is not None and "start.gg" in url:
            TSHTournamentDataModifier.instance.modifier = StartGGDataModifier(
                url, self.threadPool, self)
        else:
            logger.error("Unsupported modifier...")
            TSHTournamentDataModifier.instance.modifier = None

        SettingsManager.Set("TOURNAMENT_URL", url)

    def ReportGame(self, window):
        #Spawn a window allowing the user to report a game
        # - Characters for both players
        # - Stage
        # - And of course, who won
        # The idea would be that pressing "OK" would send a modification request using the TournamentDataModifier, but also change the score in the scoreboad
        pass

    def SetSetGames(self, setId, winnerId, games):
        worker = Worker(self.modifier.SetMatchGames, **{
            "id": setId, "winnerId": winnerId, "gameData": games
        })
        worker.signals.result.connect(lambda result: [
        ])
        self.threadPool.start(worker)


TSHTournamentDataModifier.instance = TSHTournamentDataModifier()
