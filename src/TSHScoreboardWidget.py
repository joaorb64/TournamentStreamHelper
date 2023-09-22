import platform
import subprocess

from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy import uic
from typing import List

from src.TSHSelectSetWindow import TSHSelectSetWindow

from .TSHScoreboardPlayerWidget import TSHScoreboardPlayerWidget
from .SettingsManager import SettingsManager
from .StateManager import StateManager
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHStatsUtil import TSHStatsUtil
from .TSHHotkeys import TSHHotkeys

from .thumbnail import main_generate_thumbnail as thumbnail
from .TSHThumbnailSettingsWidget import *


class TSHScoreboardWidgetSignals(QObject):
    UpdateSetData = Signal(object)
    NewSetSelected = Signal(object)
    SetSelection = Signal()
    StreamSetSelection = Signal()
    UserSetSelection = Signal()
    CommandScoreChange = Signal(int, int)
    SwapTeams = Signal()
    ChangeSetData = Signal(dict)


class TSHScoreboardWidget(QWidget):
    def __init__(self, scoreboardNumber=1, *args):
        super().__init__(*args)

        self.scoreboardNumber = scoreboardNumber

        StateManager.Set(f"score.{self.scoreboardNumber}", {})
        StateManager.Set(f"score.{self.scoreboardNumber}.last_sets.1", {})
        StateManager.Set(f"score.{self.scoreboardNumber}.last_sets.2", {})
        StateManager.Set(f"score.{self.scoreboardNumber}.history_sets.1", {})
        StateManager.Set(f"score.{self.scoreboardNumber}.history_sets.2", {})

        self.signals = TSHScoreboardWidgetSignals()
        self.signals.UpdateSetData.connect(self.UpdateSetData)
        self.signals.NewSetSelected.connect(self.NewSetSelected)
        self.signals.SetSelection.connect(self.LoadSetClicked)
        self.signals.StreamSetSelection.connect(self.LoadStreamSetClicked)
        self.signals.UserSetSelection.connect(self.LoadUserSetClicked)
        self.signals.ChangeSetData.connect(self.ChangeSetData)

        if self.scoreboardNumber == 1:
            TSHHotkeys.signals.load_set.connect(self.LoadSetClicked)
            TSHHotkeys.signals.swap_teams.connect(self.SwapTeams)
            TSHHotkeys.signals.reset_scores.connect(self.ResetScore)

            TSHHotkeys.signals.team1_score_up.connect(lambda: [
                self.CommandScoreChange(0, 1)
            ])

            TSHHotkeys.signals.team1_score_down.connect(lambda: [
                self.CommandScoreChange(0, -1)
            ])

            TSHHotkeys.signals.team2_score_up.connect(lambda: [
                self.CommandScoreChange(1, 1)
            ])

            TSHHotkeys.signals.team2_score_down.connect(lambda: [
                self.CommandScoreChange(1, -1)
            ])

        self.signals.CommandScoreChange.connect(self.CommandScoreChange)
        self.signals.SwapTeams.connect(self.SwapTeams)

        self.stats = TSHStatsUtil(self.scoreboardNumber, self)

        self.lastSetSelected = None

        self.autoUpdateTimer: QTimer = None
        self.timeLeftTimer: QTimer = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setLayout(QVBoxLayout())

        self.innerWidget = QWidget()
        self.innerWidget.setLayout(QVBoxLayout())

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.innerWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setStyleSheet(
            "QTabWidget::pane { margin: 0px,0px,0px,0px }")

        self.layout().addWidget(self.scrollArea)

        topOptions = QWidget()
        topOptions.setLayout(QHBoxLayout())
        topOptions.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.innerWidget.layout().addWidget(topOptions)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        topOptions.layout().addWidget(col)
        self.charNumber = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app", "Characters per player")))
        col.layout().addWidget(self.charNumber)
        self.charNumber.valueChanged.connect(self.SetCharacterNumber)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        topOptions.layout().addWidget(col)
        topOptions.layout().addStretch()
        self.playerNumber = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app", "Players per team")))
        col.layout().addWidget(self.playerNumber)
        self.playerNumber.valueChanged.connect(self.SetPlayersPerTeam)

        # THUMBNAIL
        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        col.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        topOptions.layout().addWidget(col)

        self.thumbnailBtn = QPushButton(
            QApplication.translate("app", "Generate Thumbnail") + " ")
        self.thumbnailBtn.setIcon(QIcon('assets/icons/png_file.svg'))
        self.thumbnailBtn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        col.layout().addWidget(self.thumbnailBtn, Qt.AlignmentFlag.AlignRight)
        # self.thumbnailBtn.setPopupMode(QToolButton.InstantPopup)
        self.thumbnailBtn.clicked.connect(self.GenerateThumbnail)

        # VISIBILITY
        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        col.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        topOptions.layout().addWidget(col)

        self.eyeBt = QToolButton()
        self.eyeBt.setIcon(QIcon('assets/icons/eye.svg'))
        self.eyeBt.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Fixed)
        col.layout().addWidget(self.eyeBt, Qt.AlignmentFlag.AlignRight)
        self.eyeBt.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu()
        self.eyeBt.setMenu(menu)

        menu.addSection("Players")

        self.elements = [
            ["Real Name", ["real_name", "real_nameLabel"]],
            ["Twitter", ["twitter", "twitterLabel"]],
            ["Location", ["locationLabel", "state", "country"]],
            ["Characters", ["characters"]],
            ["Pronouns", ["pronoun", "pronounLabel"]],
        ]
        self.elements[0][0] = QApplication.translate("app", "Real Name")
        self.elements[1][0] = QApplication.translate("app", "Twitter")
        self.elements[2][0] = QApplication.translate("app", "Location")
        self.elements[3][0] = QApplication.translate("app", "Characters")
        self.elements[4][0] = QApplication.translate("app", "Pronouns")
        for element in self.elements:
            action: QAction = self.eyeBt.menu().addAction(element[0])
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(
                lambda toggled, action=action, element=element: self.ToggleElements(action, element[1]))

        self.playerWidgets: List[TSHScoreboardPlayerWidget] = []
        self.team1playerWidgets: List[TSHScoreboardPlayerWidget] = []
        self.team2playerWidgets: List[TSHScoreboardPlayerWidget] = []

        self.team1swaps = []
        self.team2swaps = []

        self.columns = QWidget()
        self.columns.setLayout(QHBoxLayout())
        self.innerWidget.layout().addWidget(self.columns)

        bottomOptions = QWidget()
        bottomOptions.setLayout(QVBoxLayout())
        bottomOptions.layout().setContentsMargins(0, 0, 0, 0)
        bottomOptions.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.innerWidget.layout().addWidget(bottomOptions)

        self.btSelectSet = QPushButton(
            QApplication.translate("app", "Load set"))
        self.btSelectSet.setIcon(QIcon("./assets/icons/list.svg"))
        self.btSelectSet.setEnabled(False)
        bottomOptions.layout().addWidget(self.btSelectSet)
        self.btSelectSet.clicked.connect(self.signals.SetSelection.emit)

        hbox = QHBoxLayout()
        bottomOptions.layout().addLayout(hbox)

        self.btLoadStreamSet = QPushButton(
            QApplication.translate("app", "Load current stream set"))
        self.btLoadStreamSet.setIcon(QIcon("./assets/icons/twitch.svg"))
        self.btLoadStreamSet.setEnabled(False)
        hbox.addWidget(self.btLoadStreamSet)
        self.btLoadStreamSet.clicked.connect(
            self.signals.StreamSetSelection.emit)
        TSHTournamentDataProvider.instance.signals.twitch_username_updated.connect(
            self.UpdateStreamButton)

        self.btLoadStreamSetOptions = QPushButton()
        self.btLoadStreamSetOptions.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.btLoadStreamSetOptions.setIcon(
            QIcon("./assets/icons/settings.svg"))
        self.btLoadStreamSetOptions.clicked.connect(
            self.LoadStreamSetOptionsClicked)
        hbox.addWidget(self.btLoadStreamSetOptions)

        hbox = QHBoxLayout()
        bottomOptions.layout().addLayout(hbox)

        if self.scoreboardNumber <= 1:
            self.btLoadPlayerSet = QPushButton("Load player set")
            self.btLoadPlayerSet.setIcon(QIcon("./assets/icons/person_search.svg"))
            self.btLoadPlayerSet.setEnabled(False)
            self.btLoadPlayerSet.clicked.connect(
                self.signals.UserSetSelection.emit)
            hbox.addWidget(self.btLoadPlayerSet)
            TSHTournamentDataProvider.instance.signals.user_updated.connect(
                self.UpdateUserSetButton)
            TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
                self.UpdateUserSetButton)

            self.btLoadPlayerSetOptions = QPushButton()
            self.btLoadPlayerSetOptions.setSizePolicy(
                QSizePolicy.Maximum, QSizePolicy.Maximum)
            self.btLoadPlayerSetOptions.setIcon(
                QIcon("./assets/icons/settings.svg"))
            self.btLoadPlayerSetOptions.clicked.connect(
                self.LoadUserSetOptionsClicked)
            hbox.addWidget(self.btLoadPlayerSetOptions)

        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.UpdateBottomButtons)
        TSHTournamentDataProvider.instance.signals.tournament_changed.emit()

        self.selectSetWindow = TSHSelectSetWindow(self)

        self.timerLayout = QWidget()
        self.timerLayout.setLayout(QHBoxLayout())
        self.timerLayout.layout().setContentsMargins(0, 0, 0, 0)
        self.timerLayout.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.timerLayout.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottomOptions.layout().addWidget(self.timerLayout)
        self.labelAutoUpdate = QLabel("Auto update")
        self.timerLayout.layout().addWidget(self.labelAutoUpdate)
        self.timerTime = QLabel("0")
        self.timerLayout.layout().addWidget(self.timerTime)
        self.timerCancelBt = QPushButton()
        self.timerCancelBt.setIcon(QIcon('assets/icons/cancel.svg'))
        self.timerCancelBt.setIconSize(QSize(12, 12))
        self.timerCancelBt.clicked.connect(self.StopAutoUpdate)
        self.timerLayout.layout().addWidget(self.timerCancelBt)
        self.timerLayout.setVisible(False)

        self.team1column = uic.loadUi("src/layout/TSHScoreboardTeam.ui")
        self.columns.layout().addWidget(self.team1column)
        self.team1column.findChild(QLabel, "teamLabel").setText(
            QApplication.translate("app", "TEAM {0}").format(1))
        self.team1column.findChild(QScrollArea).setWidget(QWidget())
        self.team1column.findChild(
            QScrollArea).widget().setLayout(QVBoxLayout())

        for c in self.team1column.findChildren(QLineEdit):
            c.editingFinished.connect(
                lambda element=c: [
                    StateManager.Set(
                        f"score.{self.scoreboardNumber}.team.1.{element.objectName()}", element.text())
                ])
            c.editingFinished.emit()

        for c in self.team1column.findChildren(QCheckBox):
            c.toggled.connect(
                lambda state, element=c: [
                    StateManager.Set(
                        f"score.{self.scoreboardNumber}.team.1.{element.objectName()}", state)
                ])
            c.toggled.emit(False)

        self.scoreColumn = uic.loadUi("src/layout/TSHScoreboardScore.ui")
        self.columns.layout().addWidget(self.scoreColumn)

        self.team2column = uic.loadUi("src/layout/TSHScoreboardTeam.ui")
        self.columns.layout().addWidget(self.team2column)
        self.team2column.findChild(QLabel, "teamLabel").setText(
            QApplication.translate("app", "TEAM {0}").format(2))
        self.team2column.findChild(QScrollArea).setWidget(QWidget())
        self.team2column.findChild(
            QScrollArea).widget().setLayout(QVBoxLayout())

        for c in self.team2column.findChildren(QLineEdit):
            c.editingFinished.connect(
                lambda element=c: [
                    StateManager.Set(
                        f"score.{self.scoreboardNumber}.team.2.{element.objectName()}", element.text())
                ])
            c.editingFinished.emit()

        for c in self.team2column.findChildren(QCheckBox):
            c.toggled.connect(
                lambda state, element=c: [
                    StateManager.Set(
                        f"score.{self.scoreboardNumber}.team.2.{element.objectName()}", state)
                ])
            c.toggled.emit(False)

        StateManager.Unset(f'score.{self.scoreboardNumber}.team.1.player')
        StateManager.Unset(f'score.{self.scoreboardNumber}.team.2.player')
        StateManager.Unset(f'score.{self.scoreboardNumber}.stage_strike')
        self.playerNumber.setValue(1)
        self.charNumber.setValue(1)

        for c in self.scoreColumn.findChildren(QComboBox):
            c.lineEdit().editingFinished.connect(
                lambda element=c: [
                    StateManager.Set(
                        f"score.{self.scoreboardNumber}.{element.objectName()}", element.currentText())
                ]
            )
            c.currentIndexChanged.connect(
                lambda x, element=c: [
                    StateManager.Set(
                        f"score.{self.scoreboardNumber}.{element.objectName()}", element.currentText())
                ]
            )
            c.lineEdit().editingFinished.emit()
            c.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scoreColumn.findChild(QSpinBox, "best_of").valueChanged.connect(
            lambda value: [
                StateManager.Set(f"score.{self.scoreboardNumber}.best_of", value),
                StateManager.Set(f"score.{self.scoreboardNumber}.best_of_text", TSHLocaleHelper.matchNames.get(
                    "best_of").format(value) if value > 0 else ""),
            ]
        )
        self.scoreColumn.findChild(QSpinBox, "best_of").valueChanged.emit(0)

        self.scoreColumn.findChild(QSpinBox, "score_left").valueChanged.connect(
            lambda value: StateManager.Set(
                f"score.{self.scoreboardNumber}.team.1.score", value)
        )
        self.scoreColumn.findChild(
            QSpinBox, "score_left").valueChanged.emit(0)

        self.scoreColumn.findChild(QSpinBox, "score_right").valueChanged.connect(
            lambda value: StateManager.Set(
                f"score.{self.scoreboardNumber}.team.2.score", value)
        )
        self.scoreColumn.findChild(
            QSpinBox, "score_right").valueChanged.emit(0)

        self.team1column.findChild(QLineEdit, "teamName").editingFinished.connect(
            lambda: self.ExportTeamLogo(
                "1", self.team1column.findChild(QLineEdit, "teamName").text())
        )
        self.team2column.findChild(QLineEdit, "teamName").editingFinished.connect(
            lambda: self.ExportTeamLogo(
                "2", self.team2column.findChild(QLineEdit, "teamName").text())
        )

        self.teamsSwapped = False

        self.scoreColumn.findChild(
            QPushButton, "btSwapTeams").clicked.connect(self.SwapTeams)
        self.scoreColumn.findChild(
            QPushButton, "btSwapTeams").setIcon(QIcon('assets/icons/swap.svg'))

        self.scoreColumn.findChild(
            QPushButton, "btResetScore").clicked.connect(self.ResetScore)
        self.scoreColumn.findChild(
            QPushButton, "btResetScore").setIcon(QIcon('assets/icons/undo.svg'))

        # Add default and user tournament phase title files
        self.scoreColumn.findChild(QComboBox, "phase").addItem("")

        for phaseString in TSHLocaleHelper.phaseNames.values():
            if "{0}" in phaseString:
                for letter in ["A", "B", "C", "D"]:
                    if self.scoreColumn.findChild(QComboBox, "phase").findText(phaseString.format(letter)) < 0:
                        self.scoreColumn.findChild(QComboBox, "phase").addItem(
                            phaseString.format(letter))
            else:
                if self.scoreColumn.findChild(QComboBox, "phase").findText(phaseString) < 0:
                    self.scoreColumn.findChild(
                        QComboBox, "phase").addItem(phaseString)

        self.scoreColumn.findChild(QComboBox, "match").addItem("")

        for key in TSHLocaleHelper.matchNames.keys():
            matchString = TSHLocaleHelper.matchNames[key]
            if "{0}" in matchString:
                for number in range(5):
                    if key == "best_of":
                        if self.scoreColumn.findChild(QComboBox, "match").findText(matchString.format(str(2*number+1))) < 0:
                            self.scoreColumn.findChild(QComboBox, "match").addItem(
                                matchString.format(str(2*number+1)))
                    else:
                        if self.scoreColumn.findChild(QComboBox, "match").findText(matchString.format(str(number+1))) < 0:
                            self.scoreColumn.findChild(QComboBox, "match").addItem(
                                matchString.format(str(number+1)))
            else:
                if self.scoreColumn.findChild(QComboBox, "match").findText(matchString) < 0:
                    self.scoreColumn.findChild(
                        QComboBox, "match").addItem(matchString)
        
        if self.scoreboardNumber > 1:
            self.UpdateStreamButton()

    def ExportTeamLogo(self, team, value):
        if os.path.exists(f"./user_data/team_logo/{value.lower()}.png"):
            StateManager.Set(f"score.{self.scoreboardNumber}.team.{team}.logo",
                             f"./user_data/team_logo/{value.lower()}.png")
        else:
            StateManager.Set(f"score.{self.scoreboardNumber}.team.{team}.logo", None)

    def GenerateThumbnail(self):
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon('assets/icons/icon.png'))
        msgBox.setWindowTitle(QApplication.translate(
            "thumb_app", "TSH - Thumbnail"))
        try:
            thumbnailPath = thumbnail.generate(settingsManager=SettingsManager, scoreboardNumber=self.scoreboardNumber)
            msgBox.setText(QApplication.translate(
                "thumb_app", "The thumbnail has been generated here:") + " ")
            msgBox.setIcon(QMessageBox.NoIcon)
            msgBox.setInformativeText(thumbnailPath)

            thumbnail_settings = SettingsManager.Get("thumbnail_config")
            if thumbnail_settings.get("open_explorer"):
                outThumbDir = f"{os.getcwd()}/out/thumbnails/"
                if platform.system() == "Windows":
                    thumbnailPath = thumbnailPath[2:].replace("/", "\\")
                    outThumbDir = f"{os.getcwd()}\\{thumbnailPath}"
                    # os.startfile(outThumbDir)
                    subprocess.Popen(r'explorer /select,"'+outThumbDir+'"')
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", outThumbDir])
                else:
                    subprocess.Popen(["xdg-open", outThumbDir])
            else:
                msgBox.exec()
        except Exception as e:
            msgBox.setText(QApplication.translate("app", "Warning"))
            msgBox.setInformativeText(str(e))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.exec()

    def ToggleElements(self, action: QAction, elements):
        for pw in self.playerWidgets:
            for element in elements:
                pw.findChild(QWidget, element).setVisible(action.isChecked())

    def UpdateBottomButtons(self):
        if TSHTournamentDataProvider.instance.provider and TSHTournamentDataProvider.instance.provider.url:
            self.btSelectSet.setText(
                QApplication.translate("app", "Load set from {0}").format(TSHTournamentDataProvider.instance.provider.url))
            self.btSelectSet.setEnabled(True)
            self.btLoadStreamSet.setEnabled(True)
            if self.scoreboardNumber <= 1:
                self.btLoadPlayerSet.setEnabled(True)
        else:
            self.btSelectSet.setText(
                QApplication.translate("app", "Load set"))
            self.btSelectSet.setEnabled(False)

    def SetCharacterNumber(self, value):
        for pw in self.playerWidgets:
            pw.SetCharactersPerPlayer(value)

    def SetPlayersPerTeam(self, number):
        while len(self.team1playerWidgets) < number:
            p = TSHScoreboardPlayerWidget(
                index=len(self.team1playerWidgets)+1,
                teamNumber=1,
                path=f'score.{self.scoreboardNumber}.team.{1}.player.{len(self.team1playerWidgets)+1}',
                scoreboardNumber=self.scoreboardNumber)
            self.playerWidgets.append(p)

            self.team1column.findChild(
                QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.charNumber.value())
            self.team1column.findChild(
                QCheckBox, "losers").toggled.connect(p.SetLosers)

            index = len(self.team1playerWidgets)

            p.btMoveUp.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team1playerWidgets[index-1 if index > 0 else 0]))
            p.btMoveDown.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team1playerWidgets[index+1 if index < len(self.team1playerWidgets) - 1 else index]))

            p.instanceSignals.playerId_changed.connect(
                self.stats.signals.RecentSetsSignal.emit)
            p.instanceSignals.player1Id_changed.connect(
                self.stats.signals.LastSetsP1Signal.emit)
            p.instanceSignals.player1Id_changed.connect(
                self.stats.signals.PlayerHistoryStandingsP1Signal.emit)

            self.team1playerWidgets.append(p)

            p = TSHScoreboardPlayerWidget(
                index=len(self.team2playerWidgets)+1,
                teamNumber=2,
                path=f'score.{self.scoreboardNumber}.team.{2}.player.{len(self.team2playerWidgets)+1}',
                scoreboardNumber=self.scoreboardNumber)
            self.playerWidgets.append(p)
            
            self.team2column.findChild(
                QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.charNumber.value())
            self.team2column.findChild(
                QCheckBox, "losers").toggled.connect(p.SetLosers)

            index = len(self.team2playerWidgets)

            p.btMoveUp.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team2playerWidgets[index-1 if index > 0 else 0]))
            p.btMoveDown.clicked.connect(lambda index=index, p=p: p.SwapWith(
                self.team2playerWidgets[index+1 if index < len(self.team2playerWidgets) - 1 else index]))

            p.instanceSignals.playerId_changed.connect(
                self.stats.signals.RecentSetsSignal.emit)
            p.instanceSignals.player2Id_changed.connect(
                self.stats.signals.LastSetsP2Signal.emit)
            p.instanceSignals.player2Id_changed.connect(
                self.stats.signals.PlayerHistoryStandingsP2Signal.emit)

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
            if StateManager.Get(f'score.{self.scoreboardNumber}.team.{team}'):
                for k in list(StateManager.Get(f'score.{self.scoreboardNumber}.team.{team}.player').keys()):
                    if int(k) > number:
                        StateManager.Unset(f'score.{self.scoreboardNumber}.team.{team}.player.{k}')

        if number > 1:
            self.team1column.findChild(QLineEdit, "teamName").setVisible(True)
            self.team2column.findChild(QLineEdit, "teamName").setVisible(True)
        else:
            self.team1column.findChild(QLineEdit, "teamName").setVisible(False)
            self.team1column.findChild(QLineEdit, "teamName").setText("")
            self.team1column.findChild(
                QLineEdit, "teamName").editingFinished.emit()
            self.team2column.findChild(QLineEdit, "teamName").setVisible(False)
            self.team2column.findChild(QLineEdit, "teamName").setText("")
            self.team2column.findChild(
                QLineEdit, "teamName").editingFinished.emit()

        for x, element in enumerate(self.elements, start=1):
            action: QAction = self.eyeBt.menu().actions()[x]
            self.ToggleElements(action, element[1])

    def SwapTeams(self):
        StateManager.BlockSaving()

        # Lock all player widgets
        for p in self.playerWidgets:
            p.dataLock.acquire()

        try:
            for i, p in enumerate(self.team1playerWidgets):
                p.SwapWith(self.team2playerWidgets[i])

            # Scores
            scoreLeft = self.scoreColumn.findChild(
                QSpinBox, "score_left").value()
            self.scoreColumn.findChild(QSpinBox, "score_left").setValue(
                self.scoreColumn.findChild(QSpinBox, "score_right").value())
            self.scoreColumn.findChild(
                QSpinBox, "score_right").setValue(scoreLeft)

            # Losers
            losersLeft = self.team1column.findChild(
                QCheckBox, "losers").isChecked()
            self.team1column.findChild(QCheckBox, "losers").setChecked(
                self.team2column.findChild(QCheckBox, "losers").isChecked())
            self.team2column.findChild(
                QCheckBox, "losers").setChecked(losersLeft)

            # Team Names
            teamNameLeft = self.team1column.findChild(
                QLineEdit, "teamName").text()
            self.team1column.findChild(QLineEdit, "teamName").setText(
                self.team2column.findChild(QLineEdit, "teamName").text())
            self.team2column.findChild(
                QLineEdit, "teamName").setText(teamNameLeft)
            self.team1column.findChild(
                QLineEdit, "teamName").editingFinished.emit()
            self.team2column.findChild(
                QLineEdit, "teamName").editingFinished.emit()

            self.teamsSwapped = not self.teamsSwapped

        finally:
            StateManager.Set(f"score.{self.scoreboardNumber}.teamsSwapped", self.teamsSwapped)

            for p in self.playerWidgets:
                p.dataLock.release()

            StateManager.ReleaseSaving()

    def ResetScore(self):
        self.scoreColumn.findChild(QSpinBox, "score_left").setValue(0)
        self.scoreColumn.findChild(QSpinBox, "score_right").setValue(0)

    def AutoUpdate(self, data):
        TSHTournamentDataProvider.instance.GetMatch(
            self, data.get("id"), overwrite=False)
        TSHTournamentDataProvider.instance.GetStreamQueue()

    def NewSetSelected(self, data):
        if not SettingsManager.Get("general.disable_autoupdate", False):
            self.StopAutoUpdate()
            self.autoUpdateTimer = QTimer()
            self.autoUpdateTimer.start(5000)
            self.timeLeftTimer = QTimer()
            self.timeLeftTimer.start(100)
            self.timeLeftTimer.timeout.connect(self.UpdateTimeLeftTimer)
            self.timerLayout.setVisible(True)

            if data.get("auto_update") == "set":
                self.labelAutoUpdate.setText("Auto update (Set)")
            elif data.get("auto_update") == "stream":
                self.labelAutoUpdate.setText("Auto update (Stream)")
            elif data.get("auto_update") == "user":
                self.labelAutoUpdate.setText("Auto update (User)")
            else:
                self.labelAutoUpdate.setText("Auto update")

        # Lock all player widgets
        for p in self.playerWidgets:
            p.dataLock.acquire()
        StateManager.BlockSaving()

        try:
            TSHTournamentDataProvider.instance.GetStreamQueue()

            if data.get("id") != None and data.get("id") != self.lastSetSelected:
                StateManager.Unset(f'score.{self.scoreboardNumber}.stage_strike')
                self.lastSetSelected = data.get("id")
                self.CommandClearAll()
                self.ClearScore()

                # Force user to be P1 on set change
                if data.get("auto_update") == "user":
                    if (data.get("reverse") and not self.teamsSwapped) or \
                            not data.get("reverse") and self.teamsSwapped:
                        self.teamsSwapped = not self.teamsSwapped
                        StateManager.Set(
                            f"score.{self.scoreboardNumber}.teamsSwapped", self.teamsSwapped)

                TSHTournamentDataProvider.instance.GetMatch(
                    self, data["id"], overwrite=True)

            if not SettingsManager.Get("general.disable_autoupdate", False):
                self.autoUpdateTimer.timeout.connect(
                    lambda setId=data: self.AutoUpdate(data))

                if data.get("auto_update") == "stream":
                    self.autoUpdateTimer.timeout.connect(
                        lambda setId=data: TSHTournamentDataProvider.instance.LoadStreamSet(self, SettingsManager.Get("twitch_username")))

                if data.get("auto_update") == "user":
                    self.autoUpdateTimer.timeout.connect(
                        lambda setId=data: TSHTournamentDataProvider.instance.LoadUserSet(
                            self, SettingsManager.Get(TSHTournamentDataProvider.instance.provider.name+"_user")))
        finally:
            for p in self.playerWidgets:
                p.dataLock.release()
            StateManager.ReleaseSaving()

    def StopAutoUpdate(self):
        if self.autoUpdateTimer != None:
            self.autoUpdateTimer.stop()
            self.autoUpdateTimer = None
        if self.timeLeftTimer != None:
            self.timeLeftTimer.stop()
            self.timeLeftTimer = None
        self.timerLayout.setVisible(False)

    def UpdateTimeLeftTimer(self):
        if self.autoUpdateTimer:
            self.timerTime.setText(
                str(int(self.autoUpdateTimer.remainingTime()/1000)))

    def LoadSetClicked(self):
        self.selectSetWindow.LoadSets()
        self.selectSetWindow.show()

    def LoadStreamSetClicked(self):
        self.lastSetSelected = None
        TSHTournamentDataProvider.instance.LoadStreamSet(
            self, SettingsManager.Get("twitch_username"))

    def LoadStreamSetOptionsClicked(self):
        TSHTournamentDataProvider.instance.SetTwitchUsername(self)

    def UpdateStreamButton(self):
        if SettingsManager.Get("twitch_username"):
            self.btLoadStreamSet.setText(
                QApplication.translate("app",  "Load current stream set") + " "+QApplication.translate("punctuation", "(")+SettingsManager.Get("twitch_username")+QApplication.translate("punctuation", ")"))
            self.btLoadStreamSet.setEnabled(True)
            StateManager.Set(f"currentStream",
                             SettingsManager.Get("twitch_username"))
        else:
            self.btLoadStreamSet.setText(
                QApplication.translate("app", "Load current stream set"))
            self.btLoadStreamSet.setEnabled(False)

    def UpdateUserSetButton(self):
        provider = None
        if TSHTournamentDataProvider.instance.provider:
            provider = TSHTournamentDataProvider.instance.provider.name
        if provider and SettingsManager.Get(provider+"_user"):
            self.btLoadPlayerSet.setText(
                QApplication.translate("app", "Load user set ({0})").format(SettingsManager.Get(provider+'_user')))
            self.btLoadPlayerSet.setEnabled(True)
        else:
            self.btLoadPlayerSet.setText(
                QApplication.translate("app", "Load user set"))
            self.btLoadPlayerSet.setEnabled(False)

    def LoadUserSetClicked(self):
        self.lastSetSelected = None
        provider = None
        if TSHTournamentDataProvider.instance.provider:
            provider = TSHTournamentDataProvider.instance.provider.name
        if provider and SettingsManager.Get(provider+"_user"):
            TSHTournamentDataProvider.instance.LoadUserSet(
                self, SettingsManager.Get(provider+"_user"))

    def LoadUserSetOptionsClicked(self):
        TSHTournamentDataProvider.instance.SetUserAccount(self)

    # Used for score change commands
    # Change <team>(0, 1) score by <change>(+X, -X)
    def CommandScoreChange(self, team: int, change: int):
        if team in (0, 1):
            scoreContainers = [
                self.scoreColumn.findChild(QSpinBox, "score_left"),
                self.scoreColumn.findChild(QSpinBox, "score_right")
            ]
            scoreContainers[team].setValue(
                scoreContainers[team].value()+change)

    def CommandClearAll(self):
        for t, team in enumerate([self.team1playerWidgets, self.team2playerWidgets]):
            for i, p in enumerate(team):
                p.Clear()

    def ClearScore(self):
        for c in self.scoreColumn.findChildren(QComboBox):
            c.setCurrentText("")
            c.lineEdit().editingFinished.emit()

        self.scoreColumn.findChild(QSpinBox, "score_left").setValue(0)
        self.scoreColumn.findChild(QSpinBox, "score_right").setValue(0)

        self.team1column.findChild(QCheckBox, "losers").setChecked(False)
        self.team2column.findChild(QCheckBox, "losers").setChecked(False)

    # Modifies the current set data. Does not check for id, so do not call this with data that may lead to another hbox incident
    def ChangeSetData(self, data):
        StateManager.BlockSaving()

        try:
            if data.get("round_name"):
                self.scoreColumn.findChild(
                    QComboBox, "match").setCurrentText(data.get("round_name"))
                self.scoreColumn.findChild(
                    QComboBox, "match").lineEdit().editingFinished.emit()

            if data.get("tournament_phase"):
                self.scoreColumn.findChild(
                    QComboBox, "phase").setCurrentText(data.get("tournament_phase"))
                self.scoreColumn.findChild(
                    QComboBox, "phase").lineEdit().editingFinished.emit()

            scoreContainers = [
                self.scoreColumn.findChild(QSpinBox, "score_left"),
                self.scoreColumn.findChild(QSpinBox, "score_right")
            ]
            if self.teamsSwapped:
                scoreContainers.reverse()

            if data.get("reset_score"):
                scoreContainers[0].setValue(0)
                scoreContainers[1].setValue(0)

            if data.get("team1score"):
                scoreContainers[0].setValue(data.get("team1score"))
            if data.get("team2score"):
                scoreContainers[1].setValue(data.get("team2score"))
            if data.get("bestOf"):
                self.scoreColumn.findChild(
                    QSpinBox, "best_of").setValue(data.get("bestOf"))

            losersContainers = [
                self.team1column.findChild(QCheckBox, "losers"),
                self.team2column.findChild(QCheckBox, "losers")
            ]
            if self.teamsSwapped:
                losersContainers.reverse()

            if data.get("team1losers") is not None:
                losersContainers[0].setChecked(data.get("team1losers"))
            if data.get("team2losers") is not None:
                losersContainers[1].setChecked(data.get("team2losers"))

            if data.get("entrants"):
                self.playerNumber.setValue(
                    len(max(data.get("entrants"), key=lambda x: len(x))))

                # Lock all player widgets
                for p in self.playerWidgets:
                    p.dataLock.acquire()

                try:
                    for t, team in enumerate(data.get("entrants")):
                        teamInstances = [self.team1playerWidgets,
                                         self.team2playerWidgets]
                        if self.teamsSwapped:
                            teamInstances.reverse()
                        teamInstance = teamInstances[t]

                        if len(team) > 1:
                            teamColumns = [self.team1column, self.team2column]
                            teamNames = [
                                data.get("p1_name"), data.get("p2_name")]
                            teamColumns[t].findChild(
                                QLineEdit, "teamName").setText(teamNames[t])
                            teamColumns[t].findChild(
                                QLineEdit, "teamName").editingFinished.emit()

                        for p, player in enumerate(team):
                            if data.get("overwrite"):
                                teamInstance[p].SetData(player, False, True)

                            if data.get("has_selection_data"):
                                player = {
                                    "mains": player.get("mains")
                                }
                                teamInstance[p].SetData(player, True, False)
                finally:
                    for p in self.playerWidgets:
                        p.dataLock.release()
            else:
                try:
                    # Lock all player widgets
                    for p in self.playerWidgets:
                        p.dataLock.acquire()

                    if not data.get("team") or not data.get("player"):
                        return

                    team = int(data.get("team"))-1
                    player = int(data.get("player"))-1

                    teamInstances = [self.team1playerWidgets,
                                     self.team2playerWidgets]
                    teamInstance = teamInstances[team]

                    teamInstance[player].SetData(
                        data.get("data"), False, False)
                finally:
                    for p in self.playerWidgets:
                        p.dataLock.release()

            if data.get("stage_strike"):
                StateManager.Set(f"score.{self.scoreboardNumber}.stage_strike",
                                 data.get("stage_strike"))
                StateManager.Set(f"score.ruleset", data.get("ruleset"))

            if data.get("bracket_type"):
                StateManager.Set(f"score.bracket_type",
                                 data.get("bracket_type"))
                self.stats.signals.UpsetFactorCalculation.emit()
        finally:
            StateManager.ReleaseSaving()

    def UpdateSetData(self, data):
        # Do not update the scoreboard on empty data
        if data is None or len(data) == 0 or data.get("id") == None:
            return

        # If you switched sets and it was still finishing an async update call
        # Avoid loading data from the previous set
        if str(data.get("id")) != str(self.lastSetSelected):
            return

        self.ChangeSetData(data)
