from rlcompleter import Completer
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy import uic
from loguru import logger

from .TSHScoreboardPlayerWidget import TSHScoreboardPlayerWidget
from .Helpers.TSHBadWordFilter import TSHBadWordFilter
from .TSHPlayerDB import TSHPlayerDB
from .SettingsManager import SettingsManager
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager


class TSHCommentaryWidget(QDockWidget):
    ChangeCommDataSignal = Signal(int, object)
    LoadCommFromTagSignal = Signal(int, str, bool)

    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowTitle(QApplication.translate("app", "Commentary"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)

        topOptions = QWidget()
        topOptions.setLayout(QHBoxLayout())
        topOptions.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.widget.layout().addWidget(topOptions)
        
        self.ChangeCommDataSignal.connect(self.SetData)
        self.LoadCommFromTagSignal.connect(self.LoadCommentatorFromTag)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        topOptions.layout().addWidget(col)
        self.commentatorNumber = QSpinBox()
        row = QWidget()
        row.setLayout(QHBoxLayout())
        commsNumber = QLabel(QApplication.translate("app", "Number of commentators"))
        commsNumber.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        row.layout().addWidget(commsNumber)
        row.layout().addWidget(self.commentatorNumber)
        self.commentatorNumber.valueChanged.connect(
            lambda val: self.SetCommentatorNumber(val))
        
        self.characterNumber = QSpinBox()
        charNumber = QLabel(QApplication.translate("app", "Characters per player"))
        charNumber.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        row.layout().addWidget(charNumber)
        row.layout().addWidget(self.characterNumber)
        self.characterNumber.valueChanged.connect(self.SetCharacterNumber)
        
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
            ["Real Name",              ["real_name", "real_nameLabel"],       "show_name"],
            ["Twitter",                ["twitter", "twitterLabel"],           "show_social"],
            ["Location",               ["locationLabel", "state", "country"], "show_location"],
            ["Characters",             ["characters"],                        "show_characters"],
            ["Pronouns",               ["pronoun", "pronounLabel"],           "show_pronouns"],
            ["Controller",             ["controller", "controllerLabel"],     "show_controller"],
            ["Additional information", ["custom_textbox"],                    "show_additional"],
        ]
        self.elements[0][0] = QApplication.translate("app", "Real Name")
        self.elements[1][0] = QApplication.translate("app", "Twitter")
        self.elements[2][0] = QApplication.translate("app", "Location")
        self.elements[3][0] = QApplication.translate("app", "Characters")
        self.elements[4][0] = QApplication.translate("app", "Pronouns")
        self.elements[5][0] = QApplication.translate("app", "Controller")
        self.elements[6][0] = QApplication.translate("app", "Additional information")
        for element in self.elements:
            action: QAction = self.eyeBt.menu().addAction(element[0])
            action.setCheckable(True)
            action.setChecked(SettingsManager.Get(f"display_options.{element[2]}", True))
            action.toggled.connect(
                lambda toggled, action=action, element=element: self.ToggleElements(action, element[1]))
        
        row.layout().addWidget(self.eyeBt)
        col.layout().addWidget(row)

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

        self.commentaryWidgets: list[TSHScoreboardPlayerWidget] = []

        StateManager.Set("commentary", {})
        self.commentatorNumber.setValue(2)
        self.characterNumber.setValue(1)
        
        TSHGameAssetManager.instance.signals.onLoad.connect(
            self.SetDefaultsFromAssets
        )

        for x, element in enumerate(self.elements, start=1):
            action: QAction = self.eyeBt.menu().actions()[x]
            self.ToggleElements(action, element[1])

    def SetData(self, index, data):
        if index > len(self.commentaryWidgets):
            self.SetCommentatorNumber(index+1)
            self.commentatorNumber.setValue(index+1)

        logger.info(index)

        commentatorWidget = self.commentaryWidgets[index]
        logger.info(commentatorWidget)
        commentatorWidget.SetData(data, False, False)

    def LoadCommentatorFromTag(self, index: int, tag: str, no_mains: bool):
        if index > len(self.commentaryWidgets) - 1:
            self.SetCommentatorNumber(index+1)
            self.commentatorNumber.setValue(index+1)

        playerData = TSHPlayerDB.GetPlayerFromTag(tag)
        if playerData:
            widget = self.commentaryWidgets[index]
            widget.SetData(playerData, False, True, no_mains)
            return True
        return False

    def SetCommentatorNumber(self, number):
        while len(self.commentaryWidgets) < number:
            comm = TSHScoreboardPlayerWidget(
                index=len(self.commentaryWidgets)+1,
                teamNumber=0,
                path=f'commentary.{len(self.commentaryWidgets)+1}',
                customName="Commentator"
            )

            comm.btMoveUp.clicked.connect(
                lambda x=None, index=len(self.commentaryWidgets): self.MoveUp(index))

            comm.btMoveDown.clicked.connect(
                lambda x=None, index=len(self.commentaryWidgets): self.MoveDown(index))

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

    def MoveUp(self, index):
        if index > 0:
            self.SwapComms(index, index-1)

    def MoveDown(self, index):
        if index < len(self.commentaryWidgets)-1:
            self.SwapComms(index, index+1)

    def SwapComms(self, index1, index2):
        self.commentaryWidgets[index1].SwapWith(self.commentaryWidgets[index2])

    def ToggleElements(self, action: QAction, elements):
        for pw in self.commentaryWidgets:
            for element in elements:
                pw.findChild(QWidget, element).setVisible(action.isChecked())
    
    def SetCharacterNumber(self, value):
        for pw in self.commentaryWidgets:
            pw.SetCharactersPerPlayer(value)
    
    def SetDefaultsFromAssets(self):
        if StateManager.Get(f'game.defaults'):
            characters = StateManager.Get(f'game.defaults.characters_per_player', 1)
        else:
            characters = 1
        self.characterNumber.setValue(characters)
