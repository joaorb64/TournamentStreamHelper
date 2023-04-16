from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
import traceback
from .TSHPlayerListSlotWidget import TSHPlayerListSlotWidget

from .TSHScoreboardPlayerWidget import TSHScoreboardPlayerWidget
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHPlayerList import TSHPlayerList

class TSHPlayerListWidgetSignals(QObject):
    UpdateData = pyqtSignal(object)

class TSHPlayerListWidget(QDockWidget):
    def __init__(self, *args, base="player_list"):
        StateManager.BlockSaving()
        super().__init__(*args)

        self.signals = TSHPlayerListWidgetSignals()

        self.playerList = TSHPlayerList(base=base)

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
        self.slotNumber.valueChanged.connect(self.playerList.SetSlotNumber)
        row.layout().addWidget(col)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.playerPerTeam = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app","Players per slot")))
        col.layout().addWidget(self.playerPerTeam)
        self.playerPerTeam.valueChanged.connect(self.playerList.SetPlayersPerTeam)
        row.layout().addWidget(col)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.charNumber = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app","Characters per player")))
        col.layout().addWidget(self.charNumber)
        self.charNumber.valueChanged.connect(self.playerList.SetCharactersPerPlayer)
        row.layout().addWidget(col)

        row = QWidget()
        row.setLayout(QHBoxLayout())
        row.setContentsMargins(0, 0, 0, 0)
        row.layout().setSpacing(0)
        topOptions.layout().addWidget(row)

        self.loadFromStandingsBt = QPushButton(QApplication.translate("app", "Load tournament standings"))
        self.loadFromStandingsBt.clicked.connect(self.LoadFromStandingsClicked)
        row.layout().addWidget(self.loadFromStandingsBt)

        self.widget.layout().addWidget(self.playerList)

        self.slotWidgets = []

        StateManager.Set("player_list", {})

        self.playerPerTeam.setValue(1)
        self.charNumber.setValue(1)
        self.slotNumber.setValue(8)

        self.signals.UpdateData.connect(self.LoadFromStandings)
        StateManager.ReleaseSaving()
    
    def LoadFromStandingsClicked(self):
        TSHTournamentDataProvider.instance.GetStandings(self.slotNumber.value(), self.signals.UpdateData)
    
    def LoadFromStandings(self, data):
        StateManager.BlockSaving()
        if len(data) > 0:
            playerNumber = len(data[0].get("players"))
            self.playerList.SetPlayersPerTeam(playerNumber)
            
            for i, slot in enumerate(self.playerList.slotWidgets):
                try:
                    slot.SetTeamData(data[i])
                except:
                    slot.Clear()
                    print(traceback.format_exc())
        StateManager.ReleaseSaving()
