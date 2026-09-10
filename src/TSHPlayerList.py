
from loguru import logger
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy import uic
from .TSHPlayerListSlotWidget import TSHPlayerListSlotWidget

from .StateManager import StateManager
from .TSHTournamentDataProvider import TSHTournamentDataProvider


class TSHPlayerListWidgetSignals(QObject):
    UpdateData = Signal(object)
    DataChanged = Signal()


class TSHPlayerList(QWidget):
    def __init__(self, *args, base="player_list"):
        with StateManager.SaveBlock():
            super().__init__(*args)
            self.SetupUi(base)

    def SetupUi(self, base):
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

    def ChildDataChangedEmit(self):
        if not self.childDataChangedLock:
            self.signals.DataChanged.emit()

    def LoadFromStandingsClicked(self):
        TSHTournamentDataProvider.instance.GetStandings(
            self.slotNumber.value(), self.signals.UpdateData)

    def LoadFromStandings(self, data):
        data = data or []

        with StateManager.SaveBlock():
            if len(data) > 0:
                self.SetSlotNumber(len(data))
                playerNumber = len(data[0].get("players") or [])
                self.SetPlayersPerTeam(playerNumber)

                self.childDataChangedLock = True
                try:
                    for i, slot in enumerate(self.slotWidgets):
                        # SetSlotNumber can leave a different amount of slots
                        # than there is data (e.g. a slot failed to be removed)
                        if i >= len(data):
                            break
                        slot.SetTeamData(data[i])
                finally:
                    self.childDataChangedLock = False

    def SetSlotNumber(self, number):
        with StateManager.SaveBlock():
            self.DoSetSlotNumber(number)

    def DoSetSlotNumber(self, number):
        while len(self.slotWidgets) < number:
            s = TSHPlayerListSlotWidget(
                len(self.slotWidgets)+1, self, base=self.base)
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

    def SetCharactersPerPlayer(self, value):
        # logger.info("TSHPlayerList#SetCharactersPerPlayer")
        self.charactersPerPlayer = value
        with StateManager.SaveBlock():
            self.childDataChangedLock = True
            try:
                for s in self.slotWidgets:
                    s.SetCharacterNumber(value)
            finally:
                self.childDataChangedLock = False
            self.signals.DataChanged.emit()

    def SetScoresVisible(self, value):
        for s in self.slotWidgets:
            if value == Qt.Unchecked:
                s.scoreWidget.setVisible(False)
            else:
                s.scoreWidget.setVisible(True)

    def SetPlayersPerTeam(self, number):
        # logger.info("TSHPlayerList#SetPlayersPerTeam")
        self.playersPerTeam = number
        with StateManager.SaveBlock():
            self.childDataChangedLock = True
            try:
                for s in self.slotWidgets:
                    s.SetPlayersPerTeam(number)
            finally:
                self.childDataChangedLock = False
            self.signals.DataChanged.emit()
