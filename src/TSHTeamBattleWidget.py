from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy import uic
from typing import List
from loguru import logger
from .StateManager import StateManager
from .Helpers.TSHDirHelper import TSHResolve
from .TSHTeamPlayerWidget import TSHTeamPlayerWidget

from enum import Enum

# Enum for Selecting Widget Mode (Mainly for dropdown and switch statements)
class TSHTeamBattleModeEnum(Enum):
    STOCK_POOL = QApplication.translate("app", "Stock Pool (Smash)")
    FIRST_TO = QApplication.translate("app", "First To (Best Of X Team Individuals)")

class TSHTeamBattleSignals(QObject):
    # GENERAL SIGNALS
    reset_all_stocks = Signal()
    reset_everything = Signal()

    # TEAM 1 SIGNALS
    team1_next_active_player = Signal()
    team1_reset_player_stocks = Signal()
    team1_stock_up = Signal()
    team1_stock_down = Signal()
    team1_active_player_changed = Signal(int)

    # TEAM 2 SIGNALS
    team2_next_active_player = Signal()
    team2_reset_player_stocks = Signal()
    team2_stock_up = Signal()
    team2_stock_down = Signal()
    team2_active_player_changed = Signal(int)

class TSHTeamBattleWidget(QDockWidget):

    def __init__(self, *args):
        super().__init__(*args)
        logger.info("BATTLE START")
        self.signals = TSHTeamBattleSignals()

        self.setWindowTitle(QApplication.translate("app", "Crew/Team Battle"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())
        self.setWindowFlags(Qt.WindowType.Window)
        
        self.playerWidgets: List[TSHTeamPlayerWidget] = []
        self.team1playerWidgets: List[TSHTeamPlayerWidget] = []
        self.team2playerWidgets: List[TSHTeamPlayerWidget] = []

        self.playerNumber = QSpinBox()
        self.playerNumber.setObjectName("playerNumber")
        row = QWidget()
        row.setLayout(QHBoxLayout())
        row.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.widget.layout().addWidget(row)

        playerColumn = QWidget()
        playerColumn.setLayout(QVBoxLayout())
        playerLabel = QLabel(QApplication.translate("app", "Number of Players"))
        playerLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        playerColumn.layout().addWidget(playerLabel)
        playerColumn.layout().addWidget(self.playerNumber)
        self.playerNumber.valueChanged.connect(
            lambda val: self.SetPlayersPerTeam(val))
        self.playerNumber.setValue(1)
        row.layout().addWidget(playerColumn)
        
        characterColumn = QWidget()
        characterColumn.setLayout(QVBoxLayout())
        charNumber = QLabel(QApplication.translate("app", "Characters per Player"))
        charNumber.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.characterNumber = QSpinBox()
        characterColumn.layout().addWidget(charNumber)
        characterColumn.layout().addWidget(self.characterNumber)
        self.characterNumber.valueChanged.connect(self.SetCharacterNumber)
        row.layout().addWidget(characterColumn)

        lifeColumn = QWidget()
        lifeColumn.setLayout(QVBoxLayout())
        lifeNumber = QLabel(QApplication.translate("app", "Lives/Stocks per Player"))
        lifeNumber.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.livesNumber = QSpinBox()
        lifeColumn.layout().addWidget(lifeNumber)
        lifeColumn.layout().addWidget(self.livesNumber)
        row.layout().addWidget(lifeColumn)

        scrollArea = QScrollArea()
        scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        scrollArea.setFrameShape(QFrame.Shape.Panel)
        scrollArea.setWidgetResizable(True)

        self.widgetArea = QWidget()
        self.widgetArea.setLayout(QHBoxLayout())
        self.widgetArea.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)
        scrollArea.setWidget(self.widgetArea)

        self.team1column = uic.loadUi(TSHResolve("src/layout/TSHBattleTeam.ui"))
        self.team1column.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.team2column = uic.loadUi(TSHResolve("src/layout/TSHBattleTeam.ui"))
        self.team2column.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.widgetArea.layout().addWidget(self.team1column)
        self.widgetArea.layout().addWidget(self.team2column)

        self.widget.layout().addWidget(scrollArea)

        self.findChild(QSpinBox, "playerNumber").valueChanged.emit(1)

        self.team1column.findChild(QCheckBox, "separateSponsors").toggled.connect(self.ToggleSponsorsForTeam1)
        self.team2column.findChild(QCheckBox, "separateSponsors").toggled.connect(self.ToggleSponsorsForTeam2)

        # Hook into Signals for Control
        self.signals.reset_all_stocks.connect(self.ResetAllStocks)
        self.signals.reset_everything.connect(self.ResetEverything)

        self.signals.team1_stock_up.connect(self.T1_Stock_Up)
        self.signals.team1_stock_down.connect(self.T1_Stock_Down)
        self.signals.team2_stock_up.connect(self.T2_Stock_Up)
        self.signals.team2_stock_down.connect(self.T2_Stock_Down)

    # =====================================================
    # GENERAL CONTROL METHODS
    # =====================================================
    def SwitchBattleMode(self):
        mode = TSHTeamBattleModeEnum[self.findChild(QComboBox, "battleMode").value()]

        if mode is TSHTeamBattleModeEnum.STOCK_POOL:
            return
        elif mode is TSHTeamBattleModeEnum.FIRST_TO:
            return
        else:
            return
    
    def ResetAllStocks(self):
        logger.info("RESET ALL STOCKS")

    def ResetEverything(self):
        logger.info("RESET EVERYTHING")
    
    def SetCharacterNumber(self, value):
        for pw in self.playerWidgets:
            pw.SetCharactersPerPlayer(value)
    
    def SetPlayersPerTeam(self, number):
        # logger.info(f"TSHScoreboardWidget#SetPlayersPerTeam({number})")
        while len(self.team1playerWidgets) < number:
            p = TSHTeamPlayerWidget(
                index=len(self.team1playerWidgets)+1,
                teamNumber=1,
                path=f'team_battle.team.{1}.player.{len(self.team1playerWidgets)+1}')
            self.playerWidgets.append(p)

            self.team1column.findChild(
                QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.characterNumber.value())

            if self.team1column.findChild(QCheckBox, "separateSponsors").isChecked():
                p.ToggleSponsorDisplay()

            index = len(self.team1playerWidgets)

            p.btMoveUp.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team1playerWidgets[index-1 if index > 0 else 0]))
            p.btMoveDown.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team1playerWidgets[index+1 if index < len(self.team1playerWidgets) - 1 else index]))

            self.team1playerWidgets.append(p)

            p = TSHTeamPlayerWidget(
                index=len(self.team2playerWidgets)+1,
                teamNumber=2,
                path=f'team_battle.team.{2}.player.{len(self.team2playerWidgets)+1}')
            self.playerWidgets.append(p)

            self.team2column.findChild(
                QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.characterNumber.value())

            if self.team2column.findChild(QCheckBox, "separateSponsors").isChecked():
                p.ToggleSponsorDisplay()

            index = len(self.team2playerWidgets)

            p.btMoveUp.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team2playerWidgets[index-1 if index > 0 else 0]))
            p.btMoveDown.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team2playerWidgets[index+1 if index < len(self.team2playerWidgets) - 1 else index]))

            self.team2playerWidgets.append(p)

        while len(self.team1playerWidgets) > number:
            team1player = self.team1playerWidgets[-1]
            StateManager.Unset(team1player.path)
            team1player.setParent(None)
            self.playerWidgets.remove(team1player)
            self.team1playerWidgets.remove(team1player)
            team1player.deleteLater()

            team2player = self.team2playerWidgets[-1]
            StateManager.Unset(team2player.path)
            team2player.setParent(None)
            self.playerWidgets.remove(team2player)
            self.team2playerWidgets.remove(team2player)
            team2player.deleteLater()

        for team in [1, 2]:
            if StateManager.Get(f'team_battle.team.{team}'):
                for k in list(StateManager.Get(f'team_battle.team.{team}.player').keys()):
                    if int(k) > number:
                        StateManager.Unset(
                            f'team_battle.team.{team}.player.{k}')

        # for x, element in enumerate(self.elements, start=1):
        #     action: QAction = self.eyeBt.menu().actions()[x]
        #     self.ToggleElements(action, element[1])
    
    def ToggleSponsorsForTeam1(self):
        for player in self.team1playerWidgets:
            player.ToggleSponsorDisplay()
    
    def ToggleSponsorsForTeam2(self):
        for player in self.team2playerWidgets:
            player.ToggleSponsorDisplay()


    # =====================================================
    # NEXT ACTIVE PLAYERS
    # =====================================================
    def Team1NextUp(self):
        # Have this jump to the next player when the current player "dies"
        return
    
    def Team2NextUp(self):
        # Have this jump to the next player when the current player "dies"
        return

    # =====================================================
    # TEAM 1 STOCK CONTROL
    # =====================================================
    def T1_Stock_Up(self):
        mode = TSHTeamBattleModeEnum[self.findChild(QComboBox, "battleMode").value()]

        if mode is TSHTeamBattleModeEnum.STOCK_POOL:
            # Tick Down Stock for Team 2
            return
        elif mode is TSHTeamBattleModeEnum.FIRST_TO:
            # Tick Up Score for Team 1
            return
        else:
            return
        
    def T1_Stock_Down(self):
        mode = TSHTeamBattleModeEnum[self.findChild(QComboBox, "battleMode").value()]

        if mode is TSHTeamBattleModeEnum.STOCK_POOL:
            # Tick Up Stock for Team 2
            return
        elif mode is TSHTeamBattleModeEnum.FIRST_TO:
            # Tick Down Score for Team 1
            return
        else:
            return

    # =====================================================
    # TEAM 2 STOCK CONTROL
    # =====================================================
    def T2_Stock_Up(self):
        mode = TSHTeamBattleModeEnum[self.findChild(QComboBox, "battleMode").value()]

        if mode is TSHTeamBattleModeEnum.STOCK_POOL:
            # Tick Down Stock for Team 1
            return
        elif mode is TSHTeamBattleModeEnum.FIRST_TO:
            # Tick Up Score for Team 2
            return
        else:
            return
        
    def T2_Stock_Down(self):
        mode = TSHTeamBattleModeEnum[self.findChild(QComboBox, "battleMode").value()]

        if mode is TSHTeamBattleModeEnum.STOCK_POOL:
            # Tick Up Stock for Team 1
            return
        elif mode is TSHTeamBattleModeEnum.FIRST_TO:
            # Tick Down Score for Team 2
            return
        else:
            return