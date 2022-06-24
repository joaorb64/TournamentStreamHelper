from cProfile import label
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


class TSHTop8Widget(QDockWidget):
    def __init__(self, match_index, player_index, *args):
        super().__init__(*args)
        self.match_index, self.player_index = match_index, player_index
        self.setWindowTitle("Top 8")
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
        self.playerPerTeam = QSpinBox()
        col.layout().addWidget(QLabel("Players per slot"))
        col.layout().addWidget(self.playerPerTeam)
        self.playerPerTeam.valueChanged.connect(self.SetPlayersPerTeam)
        row.layout().addWidget(col)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.charNumber = QSpinBox()
        col.layout().addWidget(QLabel("Characters per player"))
        col.layout().addWidget(self.charNumber)
        self.charNumber.valueChanged.connect(self.SetCharactersPerPlayer)
        row.layout().addWidget(col)

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

        StateManager.Set("top_8", {})

        self.playerPerTeam.setValue(1)
        self.charNumber.setValue(1)
        # self.SetSlotNumber(4)

        bracket_names = ["Winners Bracket", "Losers Bracket"]
        bracket_codes = ["winner", "loser"]
        for bracket_index in range(len(bracket_names)):
            s = BracketGroup(self, bracket_codes[bracket_index], bracket_names[bracket_index])
            self.slotWidgets.append(s)
            self.widgetArea.layout().addWidget(s)
            s.SetPlayersPerTeam(self.playerPerTeam.value())

    def SetCharactersPerPlayer(self, value):
        for s in self.slotWidgets:
            s.SetCharactersPerPlayer(value)

    def SetPlayersPerTeam(self, number):
        for s in self.slotWidgets:
            s.SetPlayersPerTeam(number)

class ScoreGroup(QWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setLayout(QHBoxLayout())
        self.setContentsMargins(0,0,0,0)
        self.win_widget = QPushButton()
        self.layout().addWidget(self.win_widget)
        self.score_widget = QSpinBox()
        self.layout().addWidget(self.score_widget)
        self.win_value = False
        self.win_widget.clicked.connect(lambda: self.SetWinner(self.win_widget))

    def SetWinner(self, button: QPushButton):
        self.win_value = not self.win_value
        if self.win_value:
            button.setStyleSheet("QPushButton"
                             "{"
                             "background-color : green;"
                             "}"
                             "QPushButton::pressed"
                             "{"
                             "background-color : darkGreen;"
                             "}"
                             )
        else:
            button.setStyleSheet("")

class MatchGroup(QWidget):
    def __init__(self, player_list, match_index="winner_r1_m1", *args):
        super().__init__(*args)
        self.characters_per_player = 1
        self.players_per_team = 1
        self.player_list = player_list
        self.slotWidgets = []
        self.setLayout(QHBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.widgetArea = QWidget()
        self.widgetArea.setLayout(QVBoxLayout())
        self.widgetArea.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.layout().addWidget(self.widgetArea)

        self.score_widgets = []

        self.result_area = QWidget()
        self.result_area.setLayout(QVBoxLayout())
        self.result_area.setContentsMargins(0, 0, 0, 0)
        self.result_area.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.layout().addWidget(self.result_area)

        for i in range(2):
            player_index = f"{match_index}_p{i+1}"
            s = TSHPlayerListSlotWidget(player_index, player_list, state_path="top_8")
            self.slotWidgets.append(s)
            self.widgetArea.layout().addWidget(s)
            s.SetPlayersPerTeam(self.players_per_team)

            score_group = ScoreGroup(match_index, player_index)
            self.result_area.layout().addWidget(score_group)
            self.score_widgets.append(score_group)
    
    def SetCharactersPerPlayer(self, value):
        self.characters_per_player = value
        for s in self.slotWidgets:
            s.SetCharacterNumber(value)

    def SetPlayersPerTeam(self, number):
        self.players_per_team = number
        for s in self.slotWidgets:
            s.SetPlayersPerTeam(number)

class BracketGroup(QWidget):
    def __init__(self, player_list, bracket_index="winner", bracket_name="dummy", *args):
        super().__init__(*args)
        self.characters_per_player = 1
        self.players_per_team = 1
        self.player_list = player_list
        self.slotWidgets = []
        self.setLayout(QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.label = QLabel(bracket_name)
        label_font = QFont()
        label_font.setPointSize(15)
        label_font.setWeight(75)
        label_font.setBold(True)
        self.label.setFont(label_font)
        self.layout().addWidget(self.label)

        for i in range(2):
            match_index = f"{bracket_index}_r1_m{i+1}"
            s = MatchGroup(player_list, match_index)
            self.slotWidgets.append(s)
            self.layout().addWidget(s)
            s.SetPlayersPerTeam(self.players_per_team)
            if i<1:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                self.layout().addWidget(line)
    
    def SetCharactersPerPlayer(self, value):
        self.characters_per_player = value
        for s in self.slotWidgets:
            s.SetCharactersPerPlayer(value)

    def SetPlayersPerTeam(self, number):
        self.players_per_team = number
        for s in self.slotWidgets:
            s.SetPlayersPerTeam(number)
