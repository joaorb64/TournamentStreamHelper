from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHPlayerListSlotWidget import TSHPlayerListSlotWidget
from .TSHBracketView import TSHBracketView

class TSHBracketWidgetSignals(QObject):
    UpdateData = pyqtSignal(object)

class TSHBracketWidget(QDockWidget):
    def __init__(self, *args):
        StateManager.BlockSaving()
        super().__init__(*args)

        uic.loadUi("src/layout/TSHBracket.ui", self)

        self.signals = TSHBracketWidgetSignals()

        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        self.mainLayout = self.findChild(QWidget, "dockWidgetContents")
        self.mainLayout.setLayout(QVBoxLayout())

        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)

        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        outerLayout: QWidget = self.findChild(QWidget, "dockWidgetContents")
        self.bracketView = TSHBracketView()
        outerLayout.layout().addWidget(self.bracketView)

        StateManager.ReleaseSaving()