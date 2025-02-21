from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy import uic
import json
import traceback
from loguru import logger
from .TSHPlayerListSlotWidget import TSHPlayerListSlotWidget

from .TSHScoreboardPlayerWidget import TSHScoreboardPlayerWidget
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHPlayerList import TSHPlayerList
from src.Helpers.TSHAltTextHelper import generate_top_n_alt_text, add_alt_text_tooltip_to_button
import textwrap


class TSHNotesWidget(QDockWidget):
    def __init__(self, *args, base="notes"):
        super().__init__(*args)
        self.setWindowTitle(QApplication.translate("app", "Additional Notes"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)
