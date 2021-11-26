from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

from TSHScoreboardPlayerWidget import *
from SettingsManager import *
from StateManager import *


class TSHScoreboardWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowTitle("Scoreboard")
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

        self.team1column = uic.loadUi("src/layout/TSHScoreboardTeam.ui")
        self.columns.layout().addWidget(self.team1column)
        self.team1column.findChild(QLabel, "teamLabel").setText("TEAM 1")
        self.team1column.findChild(QScrollArea).setWidget(QWidget())
        self.team1column.findChild(
            QScrollArea).widget().setLayout(QVBoxLayout())

        self.scoreColumn = uic.loadUi("src/layout/TSHScoreboardScore.ui")
        self.columns.layout().addWidget(self.scoreColumn)

        self.team2column = uic.loadUi("src/layout/TSHScoreboardTeam.ui")
        self.columns.layout().addWidget(self.team2column)
        self.team2column.findChild(QLabel, "teamLabel").setText("TEAM 2")
        self.team2column.findChild(QScrollArea).setWidget(QWidget())
        self.team2column.findChild(
            QScrollArea).widget().setLayout(QVBoxLayout())

        StateManager.Set("score", {})
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
                for k in list(StateManager.Get(f'score.team{team}').keys()):
                    if not k.isnumeric() or (k.isnumeric() and int(k) > number):
                        StateManager.Unset(f'score.team{team}.{k}')

        if number > 1:
            self.team1column.findChild(QLineEdit, "teamName").setVisible(True)
            self.team2column.findChild(QLineEdit, "teamName").setVisible(True)
        else:
            self.team1column.findChild(QLineEdit, "teamName").setVisible(False)
            self.team2column.findChild(QLineEdit, "teamName").setVisible(False)
