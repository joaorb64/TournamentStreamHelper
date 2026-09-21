from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import QIcon, QAction
from qtpy import uic
from typing import List
from loguru import logger
from .SettingsManager import SettingsManager
from .StateManager import StateManager
from .TSHTeamBattleModeEnum import TSHTeamBattleModeEnum
from .Helpers.TSHDirHelper import TSHResolve
from .Helpers.TSHSponsorHelper import TSHSponsorHelper
from .TSHTeamPlayerWidget import TSHTeamPlayerWidget
from .TSHColorButton import TSHColorButton
from.Helpers.TSHLocaleHelper import TSHLocaleHelper
from .Helpers.TSHVersionHelper import add_beta_label

class TSHTeamBattleSignals(QObject):
    # GENERAL SIGNALS
    reset_all_stocks       = Signal()
    reset_everything       = Signal()
    dynamicSpinner_changed = Signal()

    # TEAM 1 SIGNALS
    team1_next_active_player    = Signal()
    team1_stock_up              = Signal()
    team1_stock_down            = Signal()
    team1_active_player_changed = Signal(int)

    # TEAM 2 SIGNALS
    team2_next_active_player    = Signal()
    team2_stock_up              = Signal()
    team2_stock_down            = Signal()
    team2_active_player_changed = Signal(int)

# =====================================================
# FUTURE TODOs
# =====================================================
# TODO: Handle player spinner reset when a new active player is selected on opposing team in FIRST_TO
# TODO: Handle triggering "deaths" for the other team when in FIRST_TO and the other team reaches the correct score
# TODO: Add a setting to be able to set the initial value of a stock pool or a first to match up (quicker setup I guess?)
# TODO: Track current active players for both teams via index
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

    playerWidgets: List[TSHTeamPlayerWidget]      = []
    team1playerWidgets: List[TSHTeamPlayerWidget] = []
    team2playerWidgets: List[TSHTeamPlayerWidget] = []

    currentActiveIndexTeam1: int = 0
    currentActiveIndexTeam2: int = 0

    def __init__(self, *args):
        super().__init__(*args)
        logger.info("BATTLE START")
        self.signals = TSHTeamBattleSignals()

        StateManager.Unset("team_battle")

        self.setWindowTitle(add_beta_label(QApplication.translate("app", "Crew/Team Battle"), "team_battle"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())
        self.setWindowFlags(Qt.WindowType.Window)

        self.playerNumber = QSpinBox()
        self.playerNumber.setObjectName("playerNumber")
        self.playerNumber.setFixedWidth(50)
        self.playerNumber.valueChanged.connect(
            lambda val: self.SetPlayersPerTeam(val))

        self.characterNumber = QSpinBox()
        self.characterNumber.setFixedWidth(50)
        self.characterNumber.valueChanged.connect(self.SetCharacterNumber)

        self.lifeLabel = QLabel(QApplication.translate("app", "Stocks"))
        self.livesNumber = QSpinBox()
        self.livesNumber.setFixedWidth(50)
        self.livesNumber.valueChanged.connect(self.SetSpinnerForPlayers)
        self.livesNumber.valueChanged.connect(self.TotalScoreExport)

        self.modeCombo = QComboBox()
        self.modeCombo.currentIndexChanged.connect(self.SwitchBattleMode)
        for mode in TSHTeamBattleModeEnum:
            self.modeCombo.addItem(mode.translated())

        self.phaseCombo = QComboBox()
        self.phaseCombo.setObjectName("phaseCombo")
        self.phaseCombo.setEditable(True)
        self.phaseCombo.currentIndexChanged.connect(self.PhaseExport)
        self.phaseCombo.lineEdit().editingFinished.connect(self.PhaseExport)
        self.phaseCombo.addItem("")
        TSHLocaleHelper.LoadPhaseNamesToWidget(self.phaseCombo)

        self.matchCombo = QComboBox()
        self.matchCombo.setObjectName("matchCombo")
        self.matchCombo.setEditable(True)
        self.matchCombo.currentIndexChanged.connect(self.MatchExport)
        self.matchCombo.lineEdit().editingFinished.connect(self.MatchExport)
        self.matchCombo.addItem("")
        TSHLocaleHelper.LoadMatchNamesToWidget(self.matchCombo)

        resetValues = QPushButton(QApplication.translate("app", "Reset Player Mode Values"))
        resetValues.setFixedHeight(24)
        resetValues.clicked.connect(self.ResetAllStocks)

        resetEverything = QPushButton(QApplication.translate("app", "Reset Battle Mode"))
        resetEverything.setFixedHeight(24)
        resetEverything.clicked.connect(self.ResetEverything)

        # Top toolbar row
        row = QWidget()
        rowLayout = QHBoxLayout(row)
        rowLayout.setContentsMargins(4, 2, 4, 2)
        rowLayout.setSpacing(10)
        row.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        self.widget.layout().addWidget(row, 0, Qt.AlignmentFlag.AlignTop)

        # Group 1: Match Rules (Players, Characters, Mode, Stocks)
        rulesCol = QWidget()
        rulesLayout = QGridLayout(rulesCol)
        rulesLayout.setContentsMargins(0, 0, 0, 0)
        rulesLayout.setHorizontalSpacing(6)
        rulesLayout.setVerticalSpacing(3)

        playerLabel = QLabel(QApplication.translate("app", "Players"))
        charLabel = QLabel(QApplication.translate("app", "Characters"))
        modeLabel = QLabel(QApplication.translate("app", "Mode"))

        rulesLayout.addWidget(playerLabel, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        rulesLayout.addWidget(self.playerNumber, 0, 1, Qt.AlignmentFlag.AlignVCenter)
        rulesLayout.addWidget(modeLabel, 0, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        rulesLayout.addWidget(self.modeCombo, 0, 3, Qt.AlignmentFlag.AlignVCenter)

        rulesLayout.addWidget(charLabel, 1, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        rulesLayout.addWidget(self.characterNumber, 1, 1, Qt.AlignmentFlag.AlignVCenter)
        rulesLayout.addWidget(self.lifeLabel, 1, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        rulesLayout.addWidget(self.livesNumber, 1, 3, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        rowLayout.addWidget(rulesCol)

        # Group 2: Tournament Info (Phase, Match)
        infoCol = QWidget()
        infoLayout = QGridLayout(infoCol)
        infoLayout.setContentsMargins(0, 0, 0, 0)
        infoLayout.setHorizontalSpacing(6)
        infoLayout.setVerticalSpacing(3)

        phaseLabel = QLabel(QApplication.translate("app", "Phase"))
        matchLabel = QLabel(QApplication.translate("app", "Match"))

        infoLayout.addWidget(phaseLabel, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        infoLayout.addWidget(self.phaseCombo, 0, 1, Qt.AlignmentFlag.AlignVCenter)
        infoLayout.addWidget(matchLabel, 1, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        infoLayout.addWidget(self.matchCombo, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        rowLayout.addWidget(infoCol)

        # Group 3: Actions & Visibility
        actionsCol = QWidget()
        actionsLayout = QGridLayout(actionsCol)
        actionsLayout.setContentsMargins(0, 0, 0, 0)
        actionsLayout.setHorizontalSpacing(6)
        actionsLayout.setVerticalSpacing(3)

        self.eyeBt = QToolButton()
        self.eyeBt.setIcon(QIcon('assets/icons/eye.svg'))
        self.eyeBt.setFixedSize(26, 26)
        self.eyeBt.setIconSize(QSize(18, 18))
        self.eyeBt.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu()
        self.eyeBt.setMenu(menu)

        menu.addSection(QApplication.translate("app", "Players"))

        self.elements = [
            [QApplication.translate("app", "Twitter"),                ["twitter", "twitterLabel"],           "show_social"],
            [QApplication.translate("app", "Location"),               ["locationLabel", "state", "country"], "show_location"],
            [QApplication.translate("app", "Characters"),             ["characters"],                        "show_characters"],
            [QApplication.translate("app", "Pronouns"),               ["pronoun"],                           "show_pronouns"],
        ]
        for element in self.elements:
            action: QAction = self.eyeBt.menu().addAction(element[0])
            action.setCheckable(True)
            action.setChecked(SettingsManager.Get(f"display_options.{element[2]}", True))
            action.toggled.connect(
                lambda toggled, action=action, element=element: [
                    self.ToggleElements(action, element[1]),
                    SettingsManager.Set(f"display_options.{element[2]}", toggled)
                ]
            )

        actionsLayout.addWidget(resetValues, 0, 0)
        actionsLayout.addWidget(self.eyeBt, 0, 1, 2, 1, Qt.AlignmentFlag.AlignVCenter)
        actionsLayout.addWidget(resetEverything, 1, 0)

        rowLayout.addWidget(actionsCol)
        rowLayout.addStretch()

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
        DEFAULT_TEAM1_COLOR = SettingsManager.Get("general.team_1_default_color", "#fe3636")
        self.colorButton1 = TSHColorButton(color=DEFAULT_TEAM1_COLOR, ignore_same_color=False)
        self.team1column.findChild(QHBoxLayout, "team_header").layout().insertWidget(0, self.colorButton1)
        self.colorButton1.colorChanged.connect(
            lambda color: StateManager.Set(f"team_battle.team.{1}.color", color))
        self.colorButton1.setColor(DEFAULT_TEAM1_COLOR)
        self.team1score = QSpinBox()
        self.team1column.findChild(QHBoxLayout, "team_header").layout().addWidget(self.team1score)
        self.team1score.valueChanged.connect(self.Team1TotalScoreExport)
        self.team1score.valueChanged.emit(0)
        self.widgetArea.layout().addWidget(self.team1column)

        self.team2column = uic.loadUi(TSHResolve("src/layout/TSHBattleTeam.ui"))
        self.team2column.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.team2column.findChild(QLineEdit, "teamName").editingFinished.connect(self.Team2SponsorExport)
        DEFAULT_TEAM2_COLOR = SettingsManager.Get("general.team_2_default_color", "#2e89ff")
        self.colorButton2 = TSHColorButton(color=DEFAULT_TEAM2_COLOR, ignore_same_color=False)
        self.team2column.findChild(QHBoxLayout, "team_header").layout().insertWidget(0, self.colorButton2)
        self.colorButton2.colorChanged.connect(
            lambda color: StateManager.Set(f"team_battle.team.{2}.color", color))
        self.colorButton2.setColor(DEFAULT_TEAM2_COLOR)
        self.team2score = QSpinBox()
        self.team2column.findChild(QHBoxLayout, "team_header").layout().addWidget(self.team2score)
        self.team2score.valueChanged.connect(self.Team2TotalScoreExport)
        self.team2score.valueChanged.emit(0)
        self.widgetArea.layout().addWidget(self.team2column)

        self.widget.layout().addWidget(scrollArea, 1)
        
        self.team1score.valueChanged.connect(self.Team1TotalScoreExport)
        self.team2score.valueChanged.connect(self.Team2TotalScoreExport)

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
            self.lifeLabel.setText(QApplication.translate("app", "Stocks"))
            self.livesNumber.setValue(0)
            for pw in self.playerWidgets:
                pw.SetBattleMode(self.battleMode)
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            self.lifeLabel.setText(QApplication.translate("app", "First To"))
            self.livesNumber.setValue(0)
            for pw in self.playerWidgets:
                pw.SetBattleMode(self.battleMode)
        StateManager.Set("team_battle.battle_mode", self.battleMode.name)
    
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

            self.ApplyVisibility(p)
            
            self.signals.dynamicSpinner_changed.connect(p.instanceSignals.dynamicSpinner_changed)

            index = len(self.team1playerWidgets)

            p.btMoveUp.clicked.connect(lambda index, p=p: p.SwapWith(
                self.team1playerWidgets[max(0, self.team1playerWidgets.index(p) - 1)]))
            p.btMoveDown.clicked.connect(lambda index, p=p: p.SwapWith(
                self.team1playerWidgets[min(len(self.team1playerWidgets) - 1, self.team1playerWidgets.index(p) + 1)]))

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

            self.ApplyVisibility(p)
            
            self.signals.dynamicSpinner_changed.connect(p.instanceSignals.dynamicSpinner_changed)

            index = len(self.team2playerWidgets)

            p.btMoveUp.clicked.connect(lambda index, p=p: p.SwapWith(
                self.team2playerWidgets[max(0, self.team2playerWidgets.index(p) - 1)]))
            p.btMoveDown.clicked.connect(lambda index, p=p: p.SwapWith(
                self.team2playerWidgets[min(len(self.team2playerWidgets) - 1, self.team2playerWidgets.index(p) + 1)]))

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
        
        self.SwitchBattleMode()
        self.SetSpinnerForPlayers()

    # =====================================================
    # NEXT ACTIVE PLAYERS
    # =====================================================
    def Team1NextUp(self):
        # TODO: Have this jump to the next player when the current player is "eliminated"
        return
    
    def Team2NextUp(self):
        # TODO: Have this jump to the next player when the current player is "eliminated"
        return

    def ToggleElements(self, action: QAction, elements):
        for pw in self.playerWidgets:
            for element in elements:
                w = pw.findChild(QWidget, element)
                if w:
                    w.setVisible(action.isChecked())

    def ApplyVisibility(self, pw):
        if hasattr(self, "elements"):
            for element in self.elements:
                visible = SettingsManager.Get(f"display_options.{element[2]}", True)
                for el in element[1]:
                    w = pw.findChild(QWidget, el)
                    if w:
                        w.setVisible(visible)

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
        StateManager.Set(path + ".sponsor", team)
        TSHSponsorHelper.ExportValidSponsors(team, path)
    
    def Team2SponsorExport(self):
        path = f"team_battle.team.{2}"
        team = self.team2column.findChild(QLineEdit, "teamName").text()
        StateManager.Set(path + ".sponsor", team)
        TSHSponsorHelper.ExportValidSponsors(team, path)
    
    def PhaseExport(self):
        StateManager.Set("team_battle.phase", self.phaseCombo.currentText())
    
    def MatchExport(self):
        StateManager.Set("team_battle.match", self.matchCombo.currentText())
    
    def TotalScoreExport(self):
        self.Team1TotalScoreExport()
        self.Team2TotalScoreExport()
    
    def Team1TotalScoreExport(self):
        scoreCount = 0
        for player in self.team1playerWidgets:
            scoreCount += player.GetSpinnerValue()
        StateManager.Set("team_battle.team1_spinner-total", scoreCount)
        StateManager.Set("team_battle.team1_total-score", self.team1score.value())
    
    def Team2TotalScoreExport(self):
        scoreCount = 0
        for player in self.team2playerWidgets:
            scoreCount += player.GetSpinnerValue()
        StateManager.Set("team_battle.team2_spinner-total", scoreCount)
        StateManager.Set("team_battle.team2_total-score", self.team2score.value())