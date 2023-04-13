
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from .TSHPlayerListSlotWidget import TSHPlayerListSlotWidget

from .TSHScoreboardPlayerWidget import TSHScoreboardPlayerWidget
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider

class TSHPlayerListWidgetSignals(QObject):
    UpdateData = pyqtSignal(object)
    DataChanged = pyqtSignal()

class TSHPlayerList(QWidget):
    def __init__(self, *args, base="player_list"):
        StateManager.BlockSaving()
        super().__init__(*args)

        self.signals = TSHPlayerListWidgetSignals()

        self.base = base

        self.slotWidgets: list[TSHPlayerListSlotWidget] = []

        self.playersPerTeam = 0
        self.charactersPerPlayer = 0

        self.setLayout(QVBoxLayout())

        self.childDataChangedLock = False

        scrollArea = QScrollArea()
        scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setWidgetResizable(True)

        self.widgetArea = QWidget()
        self.widgetArea.setLayout(QVBoxLayout())
        self.widgetArea.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum)
        scrollArea.setWidget(self.widgetArea)

        self.layout().addWidget(scrollArea)

        StateManager.Set(base, {})
        StateManager.ReleaseSaving()

    def ChildDataChangedEmit(self):
        if not self.childDataChangedLock:
            self.signals.DataChanged.emit()
    
    def LoadFromStandingsClicked(self):
        TSHTournamentDataProvider.instance.GetStandings(self.slotNumber.value(), self.signals.UpdateData)
    
    def LoadFromStandings(self, data):
        StateManager.BlockSaving()
        if len(data) > 0:
            self.SetSlotNumber(len(data))
            playerNumber = len(data[0].get("players"))
            self.SetPlayersPerTeam(playerNumber)
            
            self.childDataChangedLock = True
            for i, slot in enumerate(self.slotWidgets):
                slot.SetTeamData(data[i])
            self.childDataChangedLock = False
        StateManager.ReleaseSaving()

    def SetSlotNumber(self, number):
        StateManager.BlockSaving()
        while len(self.slotWidgets) < number:
            s = TSHPlayerListSlotWidget(len(self.slotWidgets)+1, self, base=self.base)
            self.slotWidgets.append(s)
            self.widgetArea.layout().addWidget(s)
            s.SetPlayersPerTeam(self.playersPerTeam)
            s.SetCharacterNumber(self.charactersPerPlayer)
            s.signals.dataChanged.connect(self.ChildDataChangedEmit)

            # s.SetCharactersPerPlayer(self.charNumber.value())

            # index = len(self.team1playerWidgets)

            # p.btMoveUp.clicked.connect(lambda x, index=index, p=p: p.SwapWith(
            #     self.team1playerWidgets[index-1 if index > 0 else 0]))
            # p.btMoveDown.clicked.connect(lambda x, index=index, p=p: p.SwapWith(
            #     self.team1playerWidgets[index+1 if index < len(self.team1playerWidgets) - 1 else index]))

        while len(self.slotWidgets) > number:
            s = self.slotWidgets[-1]
            s.setParent(None)
            self.slotWidgets.remove(s)
            StateManager.Unset(f'{self.base}.slot.{s.index}')

        self.signals.DataChanged.emit()
        
        StateManager.ReleaseSaving()

    def SetCharactersPerPlayer(self, value):
        self.charactersPerPlayer = value
        StateManager.BlockSaving()
        self.childDataChangedLock = True
        for s in self.slotWidgets:
            s.SetCharacterNumber(value)
        self.childDataChangedLock = False
        self.signals.DataChanged.emit()
        StateManager.ReleaseSaving()

    def SetPlayersPerTeam(self, number):
        self.playersPerTeam = number
        StateManager.BlockSaving()
        self.childDataChangedLock = True
        for s in self.slotWidgets:
            s.SetPlayersPerTeam(number)
        self.childDataChangedLock = False
        self.signals.DataChanged.emit()
        StateManager.ReleaseSaving()