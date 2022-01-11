from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

from TSHScoreboardPlayerWidget import *


class TSHCommentaryWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowTitle("Commentary")
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
        self.commentatorNumber = QSpinBox()
        col.layout().addWidget(QLabel("Number of commentators"))
        col.layout().addWidget(self.commentatorNumber)
        self.commentatorNumber.valueChanged.connect(self.SetCommentatorNumber)

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

        self.commentaryWidgets = []

        StateManager.Set("commentary", {})
        self.commentatorNumber.setValue(2)

        TSHTournamentDataProvider.signals.entrants_updated.connect(self.SetupAutocomplete)
        self.SetupAutocomplete()

    def SetCommentatorNumber(self, number):
        while len(self.commentaryWidgets) < number:
            comm = QGroupBox()
            uic.loadUi("src/layout/TSHCommentator.ui", comm)
            comm.setTitle(f"Commentator {len(self.commentaryWidgets)+1}")

            for c in comm.findChildren(QLineEdit):
                c.textChanged.connect(
                    lambda text, element=c, index=len(self.commentaryWidgets)+1: [
                        StateManager.Set(
                            f"commentary.{index}.{element.objectName()}", text)
                    ])
                c.textChanged.emit("")

            self.commentaryWidgets.append(comm)
            self.widgetArea.layout().addWidget(comm)

        while len(self.commentaryWidgets) > number:
            comm = self.commentaryWidgets[-1]
            comm.setParent(None)
            self.commentaryWidgets.remove(comm)

        if StateManager.Get(f'commentary'):
            for k in list(StateManager.Get(f'commentary').keys()):
                if not k.isnumeric() or (k.isnumeric() and int(k) > number):
                    StateManager.Unset(f'commentary.{k}')

    def SetupAutocomplete(self):
        if TSHTournamentDataProvider.entrantsModel:
            for c in self.commentaryWidgets:
                c.findChild(QLineEdit, "name").setCompleter(QCompleter())
                c.findChild(QLineEdit, "name").completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                c.findChild(QLineEdit, "name").completer().setFilterMode(Qt.MatchFlag.MatchContains)
                c.findChild(QLineEdit, "name").completer().setModel(TSHTournamentDataProvider.entrantsModel)