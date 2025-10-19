from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy import uic
from typing import List
from loguru import logger
from .StateManager import StateManager
from .TSHTeamBattleModeEnum import TSHTeamBattleModeEnum
from .Helpers.TSHDirHelper import TSHResolve
from .Helpers.TSHSponsorHelper import TSHSponsorHelper
from .TSHTeamPlayerWidget import TSHTeamPlayerWidget
from.Helpers.TSHLocaleHelper import TSHLocaleHelper

class TSHTeamBattleSignals(QObject):
    # GENERAL SIGNALS
    reset_all_stocks = Signal()
    reset_everything = Signal()
    dynamicSpinner_changed = Signal()

    # TEAM 1 SIGNALS
    team1_next_active_player = Signal()
    team1_stock_up = Signal()
    team1_stock_down = Signal()
    team1_active_player_changed = Signal(int)

    # TEAM 2 SIGNALS
    team2_next_active_player = Signal()
    team2_stock_up = Signal()
    team2_stock_down = Signal()
    team2_active_player_changed = Signal(int)

# =====================================================
# ACTIVE TODOs
# =====================================================
# TODO: Finish export for phase and match properly
# TODO: Handle player spinner reset when a new active player is selected on opposing team in FIRST_TO
# TODO: Handle triggering "deaths" for the other team when in FIRST_TO and the other team reaches the correct score
# TODO: Add a setting to be able to set the initial value of a stock pool or a first to match up (quicker setup I guess?)
# TODO: Track current active players for both teams via index
# TODO: Calculate and Export Total Score to Output, including remaining stock pool
# TODO: Add a checkbox to determine if we want to auto track to the next player in line when they "die"
# =====================================================
# FOR REMOTE CONTROL
# =====================================================
# TODO: Add Webserver calls to handle remote control (And add new Elgato Stream Deck plugin to main repo)
# TODO: Link signals above to calls
# TODO: Add a handle to one press jump to the next player in line for active (just check to make sure it's within array bounds and not dead, and if it's at the end of the array, loop back around)
# =====================================================
class TSHTeamBattleWidget(QDockWidget):
    battleMode = TSHTeamBattleModeEnum.STOCK_POOL

    playerWidgets: List[TSHTeamPlayerWidget] = []
    team1playerWidgets: List[TSHTeamPlayerWidget] = []
    team2playerWidgets: List[TSHTeamPlayerWidget] = []

    currentActiveIndexTeam1: int = 0
    currentActiveIndexTeam2: int = 0

    def __init__(self, *args):
        super().__init__(*args)
        logger.info("BATTLE START")
        self.signals = TSHTeamBattleSignals()

        StateManager.Unset("team_battle")

        self.setWindowTitle(QApplication.translate("app", "Crew/Team Battle"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())
        self.setWindowFlags(Qt.WindowType.Window)

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
        self.lifeLabel = QLabel()
        self.lifeLabel.setText(QApplication.translate("app", "Lives/Stocks per Player"))
        self.lifeLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.livesNumber = QSpinBox()
        self.livesNumber.valueChanged.connect(self.SetSpinnerForPlayers)
        lifeColumn.layout().addWidget(self.lifeLabel)
        lifeColumn.layout().addWidget(self.livesNumber)
        row.layout().addWidget(lifeColumn)

        modeColumn = QWidget()
        modeColumn.setLayout(QVBoxLayout())
        modeLabel = QLabel(QApplication.translate("app", "Battle Mode"))
        modeLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.modeCombo = QComboBox()
        self.modeCombo.currentIndexChanged.connect(self.SwitchBattleMode)

        for mode in TSHTeamBattleModeEnum:
            self.modeCombo.addItem(mode.value)
        
        modeColumn.layout().addWidget(modeLabel)
        modeColumn.layout().addWidget(self.modeCombo)
        row.layout().addWidget(modeColumn)

        infoColumn = QWidget()
        infoColumn.setLayout(QVBoxLayout())
        phaseRow = QWidget()
        phaseRow.setLayout(QHBoxLayout())
        phaseLabel = QLabel(QApplication.translate("app", "Phase"))
        phaseLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        phaseCombo = QComboBox()
        phaseCombo.setEditable(True)
        phaseRow.layout().addWidget(phaseLabel)
        phaseRow.layout().addWidget(phaseCombo)

        matchRow = QWidget()
        matchRow.setLayout(QHBoxLayout())
        matchLabel = QLabel(QApplication.translate("app", "Match"))
        matchLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        matchCombo = QComboBox()
        matchCombo.setEditable(True)
        matchRow.layout().addWidget(matchLabel)
        matchRow.layout().addWidget(matchCombo)

        phaseCombo.addItem("")

        for phaseString in TSHLocaleHelper.phaseNames.values():
            if "{0}" in phaseString:
                for letter in ["A", "B", "C", "D"]:
                    if phaseCombo.findText(phaseString.format(letter)) < 0:
                        phaseCombo.addItem(phaseString.format(letter))
            else:
                if phaseCombo.findText(phaseString) < 0:
                    phaseCombo.addItem(phaseString)

        matchCombo.addItem("")

        for key in TSHLocaleHelper.matchNames.keys():
            matchString = TSHLocaleHelper.matchNames[key]

            try:
                if "{0}" in matchString and ("qualifier" not in key):
                    for number in range(5):
                        if key == "best_of":
                            if matchCombo.findText(matchString.format(str(2*number+1))) < 0:
                                matchCombo.addItem(matchString.format(str(2*number+1)))
                        else:
                            if matchCombo.findText(matchString.format(str(number+1))) < 0:
                                matchCombo.addItem(matchString.format(str(number+1)))
                else:
                    if matchCombo.findText(matchString) < 0:
                        matchCombo.addItem(matchString)
            except:
                logger.error(
                    f"Unable to generate match strings for {matchString}")

        infoColumn.layout().addWidget(phaseRow)
        infoColumn.layout().addWidget(matchRow)
        infoColumn.layout().setContentsMargins(0, 0, 0, 0)
        row.layout().addWidget(infoColumn)
        
        buttonColumn = QWidget()
        buttonColumn.setLayout(QVBoxLayout())
        buttonColumn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        resetValues = QPushButton(QApplication.translate("app", "Reset Player Mode Values"))
        resetValues.clicked.connect(self.ResetAllStocks)
        resetEverything = QPushButton(QApplication.translate("app", "Reset Battle Mode"))
        resetEverything.clicked.connect(self.ResetEverything)
        buttonColumn.layout().addWidget(resetValues)
        buttonColumn.layout().addWidget(resetEverything)
        row.layout().addWidget(buttonColumn)

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
        self.team1column.findChild(QLineEdit, "teamName").editingFinished.connect(self.Team1SponsorExport)
        self.team2column = uic.loadUi(TSHResolve("src/layout/TSHBattleTeam.ui"))
        self.team2column.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.team2column.findChild(QLineEdit, "teamName").editingFinished.connect(self.Team2SponsorExport)
        self.widgetArea.layout().addWidget(self.team1column)
        self.widgetArea.layout().addWidget(self.team2column)

        self.widget.layout().addWidget(scrollArea)

        self.team1column.findChild(QCheckBox, "separateSponsors").toggled.connect(self.ToggleSponsorsForTeam1)
        self.team2column.findChild(QCheckBox, "separateSponsors").toggled.connect(self.ToggleSponsorsForTeam2)

        # Hook into Signals for Control
        self.signals.reset_all_stocks.connect(self.ResetAllStocks)
        self.signals.reset_everything.connect(self.ResetEverything)
        self.signals.dynamicSpinner_changed.connect(self.TotalScoreExport)

        self.signals.team1_stock_up.connect(self.T1_Stock_Up)
        self.signals.team1_stock_down.connect(self.T1_Stock_Down)
        self.signals.team2_stock_up.connect(self.T2_Stock_Up)
        self.signals.team2_stock_down.connect(self.T2_Stock_Down)
        
        self.playerNumber.setValue(1)
        self.characterNumber.setValue(1)
        self.livesNumber.setValue(0)

    # =====================================================
    # GENERAL CONTROL METHODS
    # =====================================================
    def SwitchBattleMode(self):
        # TODO: Do above with player widgets as well to make sure information displayed is accurate.
        self.battleMode = TSHTeamBattleModeEnum.MatchToMode(self.modeCombo.currentText())
        logger.info(f"Switching Battle Mode to: {self.battleMode.name}")

        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            self.lifeLabel.setText(QApplication.translate("app", "Lives/Stocks per Player"))
            self.livesNumber.setValue(0)
            for pw in self.playerWidgets:
                pw.SetBattleMode(self.battleMode)
            return
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            self.lifeLabel.setText(QApplication.translate("app", "First To Amount"))
            self.livesNumber.setValue(0)
            for pw in self.playerWidgets:
                pw.SetBattleMode(self.battleMode)
            return
    
    def ResetAllStocks(self):
        for pw in self.playerWidgets:
            pw.ResetDynamicSpinner()

    def ResetEverything(self):
        for pw in self.playerWidgets:
            pw.ResetDynamicSpinner()
            pw.Clear()
    
    def ToggleSponsorsForTeam1(self):
        for player in self.team1playerWidgets:
            player.ToggleSponsorDisplay()
    
    def ToggleSponsorsForTeam2(self):
        for player in self.team2playerWidgets:
            player.ToggleSponsorDisplay()
    
    def SetSpinnerForPlayers(self):
        for pw in self.playerWidgets:
            pw.SetDefaultSpinnerValue(self.livesNumber.value())
    
    # =====================================================
    # NECESSARY PLAYER METHODS
    # =====================================================
    def SetCharacterNumber(self, value):
        for pw in self.playerWidgets:
            pw.SetCharactersPerPlayer(value)
    
    def SetPlayersPerTeam(self, number):
        while len(self.team1playerWidgets) < number:
            p = TSHTeamPlayerWidget(
                index=len(self.team1playerWidgets)+1,
                teamNumber=1,
                path=f'team_battle.team.{1}.player.{len(self.team1playerWidgets)+1}')
            self.playerWidgets.append(p)

            self.team1column.findChild(QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.characterNumber.value())

            if self.team1column.findChild(QCheckBox, "separateSponsors").isChecked():
                p.ToggleSponsorDisplay()
            
            self.signals.dynamicSpinner_changed.connect(p.instanceSignals.dynamicSpinner_changed)

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

            self.team2column.findChild(QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.characterNumber.value())

            if self.team2column.findChild(QCheckBox, "separateSponsors").isChecked():
                p.ToggleSponsorDisplay()
            
            self.signals.dynamicSpinner_changed.connect(p.instanceSignals.dynamicSpinner_changed)

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

    # =====================================================
    # NEXT ACTIVE PLAYERS
    # =====================================================
    def Team1NextUp(self):
        # TODO: Have this jump to the next player when the current player "dies"
        return
    
    def Team2NextUp(self):
        # TODO: Have this jump to the next player when the current player "dies"
        return

    # =====================================================
    # TEAM 1 STOCK CONTROL
    # =====================================================
    def T1_Stock_Up(self):
        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            # TODO: Tick Down Stock for Team 2
            return
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            # TODO: Tick Up Score for Team 1
            return
        
    def T1_Stock_Down(self):
        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            # TODO: Tick Up Stock for Team 2
            return
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            # TODO: Tick Down Score for Team 1
            return

    # =====================================================
    # TEAM 2 STOCK CONTROL
    # =====================================================
    def T2_Stock_Up(self):
        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            # TODO: Tick Down Stock for Team 1
            return
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            # TODO: Tick Up Score for Team 2
            return
        
    def T2_Stock_Down(self):
        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            # TODO: Tick Up Stock for Team 1
            return
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            # TODO: Tick Down Score for Team 2
            return
    
    # =====================================================
    # EXPORTS
    # =====================================================

    def Team1SponsorExport(self):
        path = f"team_battle.team.{1}"
        team = self.team1column.findChild(QLineEdit, "teamName").text()
        StateManager.Set(path, team)
        TSHSponsorHelper.ExportValidSponsors(team, path)
    
    def Team2SponsorExport(self):
        path = f"team_battle.team.{2}"
        team = self.team2column.findChild(QLineEdit, "teamName").text()
        StateManager.Set(path, team)
        TSHSponsorHelper.ExportValidSponsors(team, path)
    
    def PhaseExport(self):
        return
    
    def MatchExport(self):
        return
    
    def TotalScoreExport(self):
        self.Team1TotalScoreExport()
        self.Team2TotalScoreExport()
    
    def Team1TotalScoreExport(self):
        return
    
    def Team2TotalScoreExport(self):
        return