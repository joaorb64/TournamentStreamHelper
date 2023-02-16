from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
import traceback

from .TSHScoreboardPlayerWidget import TSHScoreboardPlayerWidget
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider

class TSHPlayerListSlotWidgetSignals(QObject):
    dataChanged = pyqtSignal()

class TSHPlayerListSlotWidget(QGroupBox):
    def __init__(self, index, playerList, base="player_list", *args):
        super().__init__(*args)
        self.index = index
        self.playerList = playerList

        self.base = base

        self.signals = TSHPlayerListSlotWidgetSignals()

        self.setLayout(QVBoxLayout())
        self.slotName = QLineEdit()
        self.layout().addWidget(self.slotName)

        self.slotName.editingFinished.connect(
            lambda: [
                StateManager.Set(
                    f"{self.base}.slot.{self.index}.name", self.slotName.text())
            ]
        )

        self.list = QWidget()
        self.list.setLayout(QHBoxLayout())
        self.layout().addWidget(self.list)

        self.playerWidgets = []

    def SetPlayersPerTeam(self, number):
        StateManager.BlockSaving()
        while len(self.playerWidgets) < number:
            p = TSHScoreboardPlayerWidget(
                index=len(self.playerWidgets)+1, teamNumber=1, path=f'{self.base}.slot.{self.index}.player.{len(self.playerWidgets)+1}')
            self.playerWidgets.append(p)
            self.list.layout().addWidget(p)

            p.SetCharactersPerPlayer(self.playerList.charactersPerPlayer)

            index = len(self.playerWidgets)-1

            p.btMoveUp.clicked.connect(lambda x, index=index, p=p: p.SwapWith(
                self.playerWidgets[index-1 if index > 0 else 0]))
            p.btMoveDown.clicked.connect(lambda x, index=index, p=p: p.SwapWith(
                self.playerWidgets[index+1 if index < len(self.playerWidgets) - 1 else index]))
            
            p.instanceSignals.dataChanged.connect(self.signals.dataChanged.emit)

        while len(self.playerWidgets) > number:
            p = self.playerWidgets[-1]
            p.setParent(None)
            self.playerWidgets.remove(p)
            StateManager.Unset(p.path)
            p.deleteLater()
        
        StateManager.ReleaseSaving()
        self.signals.dataChanged.emit()

        # if number > 1:
        #     self.team1column.findChild(QLineEdit, "teamName").setVisible(True)
        #     self.team2column.findChild(QLineEdit, "teamName").setVisible(True)
        # else:
        #     self.team1column.findChild(QLineEdit, "teamName").setVisible(False)
        #     self.team1column.findChild(QLineEdit, "teamName").setText("")
        #     self.team2column.findChild(QLineEdit, "teamName").setVisible(False)
        #     self.team2column.findChild(QLineEdit, "teamName").setText("")

    def SetCharacterNumber(self, value):
        StateManager.BlockSaving()
        for pw in self.playerWidgets:
            pw.SetCharactersPerPlayer(value)
        StateManager.ReleaseSaving()
        self.signals.dataChanged.emit()

    def SetTeamData(self, data):
        StateManager.BlockSaving()
        if(data.get("name")):
            self.slotName.setText(data.get("name"))
        else:
            self.slotName.setText("")
        
        for i, pw in enumerate(self.playerWidgets):
            if data.get("players"):
                try:
                    pw.SetData(data.get("players")[i])
                except:
                    pw.Clear()
                    print(traceback.format_exc())
            else:
                pw.Clear()
        StateManager.ReleaseSaving()
        self.signals.dataChanged.emit()