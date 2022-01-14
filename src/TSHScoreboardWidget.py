from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

from TSHScoreboardPlayerWidget import *
from SettingsManager import *
from StateManager import *
from TSHTournamentDataProvider import TSHTournamentDataProvider


class TSHScoreboardWidgetSignals(QObject):
    UpdateSetData = pyqtSignal(object)


class TSHScoreboardWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)

        self.signals = TSHScoreboardWidgetSignals()
        self.signals.UpdateSetData.connect(self.UpdateSetData)

        self.setWindowTitle("Scoreboard")
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        StateManager.Set("score", {})

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

        col = QWidget()
        col.setLayout(QVBoxLayout())
        topOptions.layout().addWidget(col)
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.charNumber = QSpinBox()
        col.layout().addWidget(QLabel("Characters per player"))
        col.layout().addWidget(self.charNumber)
        self.charNumber.valueChanged.connect(self.SetCharacterNumber)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        topOptions.layout().addWidget(col)
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.playerNumber = QSpinBox()
        col.layout().addWidget(QLabel("Players per team"))
        col.layout().addWidget(self.playerNumber)
        self.playerNumber.valueChanged.connect(self.SetPlayersPerTeam)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        col.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        col.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        topOptions.layout().addWidget(col)
        col.setContentsMargins(0, 0, 0, 0)
        col.layout().setSpacing(0)
        self.eyeBt = QToolButton()
        self.eyeBt.setIcon(QIcon('icons/eye.svg'))
        self.eyeBt.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Fixed)
        col.layout().addWidget(self.eyeBt, Qt.AlignmentFlag.AlignRight)
        self.eyeBt.setPopupMode(QToolButton.InstantPopup)
        self.eyeBt.setMenu(QMenu())

        self.eyeBt.menu().addSection("Players")

        elements = [
            ["Real Name", ["real_name", "real_nameLabel"]],
            ["Twitter", ["twitter", "twitterLabel"]],
            ["Location", ["locationLabel", "state", "country"]],
            ["Characters", ["characters"]]
        ]
        for element in elements:
            action: QAction = self.eyeBt.menu().addAction(element[0])
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(
                lambda toggled, action=action, element=element: self.ToggleElements(action, element[1]))

        self.eyeBt.menu().addSection("Match data")
        action: QAction = self.eyeBt.menu().addAction("Test")

        self.playerWidgets = []
        self.team1playerWidgets = []
        self.team2playerWidgets = []

        self.columns = QWidget()
        self.columns.setLayout(QHBoxLayout())
        self.widget.layout().addWidget(self.columns)

        bottomOptions = QWidget()
        bottomOptions.setLayout(QHBoxLayout())
        bottomOptions.layout().setSpacing(0)
        bottomOptions.layout().setContentsMargins(0, 0, 0, 0)
        bottomOptions.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.widget.layout().addWidget(bottomOptions)

        self.btDownload = QPushButton("Load set")
        self.btDownload.setEnabled(False)
        bottomOptions.layout().addWidget(self.btDownload)
        self.btDownload.clicked.connect(
            lambda x: TSHTournamentDataProvider.LoadSetsFromTournament(self)
        )
        TSHTournamentDataProvider.signals.tournament_changed.connect(
            lambda: [
                self.btDownload.setText(
                    "Load set from "+TSHTournamentDataProvider.provider.url),
                self.btDownload.setEnabled(True)
            ]
        )
        TSHTournamentDataProvider.signals.tournament_changed.emit()

        self.team1column = uic.loadUi("src/layout/TSHScoreboardTeam.ui")
        self.columns.layout().addWidget(self.team1column)
        self.team1column.findChild(QLabel, "teamLabel").setText("TEAM 1")
        self.team1column.findChild(QScrollArea).setWidget(QWidget())
        self.team1column.findChild(
            QScrollArea).widget().setLayout(QVBoxLayout())

        for c in self.team1column.findChildren(QLineEdit):
            c.textChanged.connect(
                lambda text, element=c: [
                    StateManager.Set(
                        f"score.team1.{element.objectName()}", text)
                ])
            c.textChanged.emit("")

        for c in self.team1column.findChildren(QCheckBox):
            c.toggled.connect(
                lambda state, element=c: [
                    StateManager.Set(
                        f"score.team1.{element.objectName()}", state)
                ])
            c.toggled.emit(False)

        self.scoreColumn = uic.loadUi("src/layout/TSHScoreboardScore.ui")
        self.columns.layout().addWidget(self.scoreColumn)

        self.team2column = uic.loadUi("src/layout/TSHScoreboardTeam.ui")
        self.columns.layout().addWidget(self.team2column)
        self.team2column.findChild(QLabel, "teamLabel").setText("TEAM 2")
        self.team2column.findChild(QScrollArea).setWidget(QWidget())
        self.team2column.findChild(
            QScrollArea).widget().setLayout(QVBoxLayout())

        for c in self.team2column.findChildren(QLineEdit):
            c.textChanged.connect(
                lambda text, element=c: [
                    StateManager.Set(
                        f"score.team2.{element.objectName()}", text)
                ])
            c.textChanged.emit("")

        for c in self.team2column.findChildren(QCheckBox):
            c.toggled.connect(
                lambda state, element=c: [
                    StateManager.Set(
                        f"score.team2.{element.objectName()}", state)
                ])
            c.toggled.emit(False)

        self.playerNumber.setValue(1)
        self.charNumber.setValue(1)

        TSHGameAssetManager.instance.signals.onLoad.connect(
            self.LoadCharacters)

        for c in self.findChildren(QLineEdit):
            c.textChanged.connect(
                lambda text, element=c: print(element.objectName(), text))

        for c in self.scoreColumn.findChildren(QComboBox):
            c.editTextChanged.connect(
                lambda text, element=c: [
                    print(
                        element.objectName(),
                        element.currentText()
                    ),
                    StateManager.Set(
                        f"score.{element.objectName()}", element.currentText())
                ]
            )
            c.editTextChanged.emit("")
            c.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)

        for c in self.scoreColumn.findChildren(QSpinBox):
            c.valueChanged.connect(
                lambda value, element=c: [
                    print(
                        element.objectName(),
                        value
                    ),
                    StateManager.Set(
                        f"score.{element.objectName()}", value)
                ]
            )
            c.valueChanged.emit(0)

    def LoadCharacters(self):
        TSHScoreboardPlayerWidget.LoadCharacters()
        for pw in self.playerWidgets:
            pw.ReloadCharacters()

    def ToggleElements(self, action: QAction, elements: list[QWidget]):
        for pw in self.playerWidgets:
            for element in elements:
                pw.findChild(QWidget, element).setVisible(action.isChecked())

    def SetCharacterNumber(self, value):
        for pw in self.playerWidgets:
            pw.SetCharactersPerPlayer(value)

    def SetPlayersPerTeam(self, number):
        while len(self.team1playerWidgets) < number:
            p = TSHScoreboardPlayerWidget(
                index=len(self.team1playerWidgets)+1, teamNumber=1)
            self.playerWidgets.append(p)
            print(self.team1column.findChild(QScrollArea))
            self.team1column.findChild(
                QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.charNumber.value())
            self.team1playerWidgets.append(p)

            p = TSHScoreboardPlayerWidget(
                index=len(self.team2playerWidgets)+1, teamNumber=2)
            self.playerWidgets.append(p)
            self.team2column.findChild(
                QScrollArea).widget().layout().addWidget(p)
            p.SetCharactersPerPlayer(self.charNumber.value())
            self.team2playerWidgets.append(p)

        while len(self.team1playerWidgets) > number:
            team1player = self.team1playerWidgets[-1]
            team1player.setParent(None)
            self.playerWidgets.remove(team1player)
            self.team1playerWidgets.remove(team1player)

            team2player = self.team2playerWidgets[-1]
            team2player.setParent(None)
            self.playerWidgets.remove(team2player)
            self.team2playerWidgets.remove(team2player)

        for team in [1, 2]:
            if StateManager.Get(f'score.team{team}'):
                for k in list(StateManager.Get(f'score.team{team}.players').keys()):
                    if not k.isnumeric() or (k.isnumeric() and int(k) > number):
                        StateManager.Unset(f'score.team{team}.players.{k}')

        if number > 1:
            self.team1column.findChild(QLineEdit, "teamName").setVisible(True)
            self.team2column.findChild(QLineEdit, "teamName").setVisible(True)
        else:
            self.team1column.findChild(QLineEdit, "teamName").setVisible(False)
            self.team1column.findChild(QLineEdit, "teamName").setText("")
            self.team2column.findChild(QLineEdit, "teamName").setVisible(False)
            self.team2column.findChild(QLineEdit, "teamName").setText("")

    def UpdateSetData(self, data):
        print(data)

        if data.get("round_name"):
            self.scoreColumn.findChild(
                QComboBox, "match").setCurrentText(data.get("round_name"))

        if data.get("tournament_phase"):
            self.scoreColumn.findChild(
                QComboBox, "phase").setCurrentText(data.get("tournament_phase"))

        if data.get("entrants"):
            self.playerNumber.setValue(
                len(max(data.get("entrants"), key=lambda x: len(x))))

            for t, team in enumerate(data.get("entrants")):
                teamInstances = [self.team1playerWidgets,
                                 self.team2playerWidgets]
                teamInstance = teamInstances[t]

                if len(team) > 1:
                    teamColumns = [self.team1column, self.team2column]
                    teamNames = [data.get("p1_name"), data.get("p2_name")]
                    teamColumns[t].findChild(
                        QLineEdit, "teamName").setText(teamNames[t])

                for p, player in enumerate(team):
                    teamInstance[p].SetData(
                        player, False, data.get("clear", True))

        if data.get("id"):
            TSHTournamentDataProvider.GetMatch(self, data.get("id"))

        if data.get("stage_strike"):
            StateManager.Set(f"score.stage_strike", data.get("stage_strike"))
