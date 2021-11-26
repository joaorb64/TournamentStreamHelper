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
        # self.commentatorNumber.valueChanged.connect(self.SetPlayersPerTeam)

        StateManager.Set("commentary", {})
        self.commentatorNumber.setValue(2)
