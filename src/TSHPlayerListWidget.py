from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from .TSHPlayerListSlotWidget import TSHPlayerListSlotWidget

from .TSHScoreboardPlayerWidget import TSHScoreboardPlayerWidget
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider

class TSHPlayerListWidgetSignals(QObject):
    UpdateData = pyqtSignal(object)

class TSHPlayerListWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)

        self.signals = TSHPlayerListWidgetSignals()

        self.setWindowTitle(QApplication.translate("app","Player List"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)

        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.widget.setContentsMargins(0, 0, 0, 0)

        topOptions = QWidget()
        topOptions.setLayout(QHBoxLayout())
        topOptions.layout().setSpacing(0)
        topOptions.layout().setContentsMargins(0, 0, 0, 0)
        topOptions.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.widget.layout().addWidget(topOptions)

        row = QWidget()
        row.setLayout(QHBoxLayout())
        row.setContentsMargins(0, 0, 0, 0)
        row.layout().setSpacing(0)
        topOptions.layout().addWidget(row)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.slotNumber = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app","Number of slots")))
        col.layout().addWidget(self.slotNumber)
        self.slotNumber.valueChanged.connect(self.SetSlotNumber)
        row.layout().addWidget(col)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.playerPerTeam = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app","Players per slot")))
        col.layout().addWidget(self.playerPerTeam)
        self.playerPerTeam.valueChanged.connect(self.SetPlayersPerTeam)
        row.layout().addWidget(col)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.charNumber = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app","Characters per player")))
        col.layout().addWidget(self.charNumber)
        self.charNumber.valueChanged.connect(self.SetCharactersPerPlayer)
        row.layout().addWidget(col)

        row = QWidget()
        row.setLayout(QHBoxLayout())
        row.setContentsMargins(0, 0, 0, 0)
        row.layout().setSpacing(0)
        topOptions.layout().addWidget(row)

        self.loadFromStandingsBt = QPushButton("Load tournament standings")
        self.loadFromStandingsBt.clicked.connect(self.LoadFromStandingsClicked)
        row.layout().addWidget(self.loadFromStandingsBt)

        scrollArea = QScrollArea()
        scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setWidgetResizable(True)

        self.widgetArea = QWidget()
        self.widgetArea.setLayout(QVBoxLayout())
        self.widgetArea.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum)
        scrollArea.setWidget(self.widgetArea)

        self.widget.layout().addWidget(scrollArea)

        self.slotWidgets = []

        StateManager.Set("player_list", {})

        self.playerPerTeam.setValue(1)
        self.charNumber.setValue(1)
        self.slotNumber.setValue(8)

        self.signals.UpdateData.connect(self.LoadFromStandings)
    
    def LoadFromStandingsClicked(self):
        TSHTournamentDataProvider.instance.GetStandings(self.slotNumber.value(), self.signals.UpdateData)
    
    def LoadFromStandings(self, data):
        if len(data) > 0:
            playerNumber = len(data[0].get("players"))
            self.SetPlayersPerTeam(playerNumber)
            
            for i, slot in enumerate(self.slotWidgets):
                slot.SetTeamData(data[i])

    def SetSlotNumber(self, number):
        while len(self.slotWidgets) < number:
            s = TSHPlayerListSlotWidget(len(self.slotWidgets)+1, self)
            self.slotWidgets.append(s)
            self.widgetArea.layout().addWidget(s)
            s.SetPlayersPerTeam(self.playerPerTeam.value())

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
            StateManager.Unset(f'player_list.slot.{s.index}')

    def SetCharactersPerPlayer(self, value):
        for s in self.slotWidgets:
            s.SetCharacterNumber(value)

    def SetPlayersPerTeam(self, number):
        for s in self.slotWidgets:
            s.SetPlayersPerTeam(number)
