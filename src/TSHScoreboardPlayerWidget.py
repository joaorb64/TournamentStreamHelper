from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic


class TSHScoreboardPlayerWidget(QGroupBox):

    def __init__(self, *args):
        super().__init__(*args)

        uic.loadUi("src/layout/TSHScoreboardPlayer.ui", self)

        self.character_container = self.findChild(QWidget, "characters")

        self.character_elements = []
        self.SetCharactersPerPlayer(1)

        bottom_buttons_layout = QHBoxLayout()
        self.layout().addLayout(bottom_buttons_layout, 999, 0, 1, 3)

        self.save_bt = QPushButton("Save new player")
        # self.save_bt.setFont(self.parent.font_small)
        self.save_bt.setIcon(QIcon('icons/save.svg'))
        bottom_buttons_layout.addWidget(self.save_bt)
        # self.save_bt.clicked.connect(self.SavePlayerToDB)
        # self.player_name.textChanged.connect(
        #    self.ManageSavePlayerToDBText)
        # self.player_org.textChanged.connect(
        #    self.ManageSavePlayerToDBText)

        self.delete_bt = QPushButton("Delete player entry")
        # self.delete_bt.setFont(self.parent.font_small)
        self.delete_bt.setIcon(QIcon('icons/cancel.svg'))
        bottom_buttons_layout.addWidget(self.delete_bt)
        self.delete_bt.setEnabled(False)
        # self.player_name.textChanged.connect(
        #    self.ManageDeletePlayerFromDBActive)
        # self.player_org.textChanged.connect(
        #    self.ManageDeletePlayerFromDBActive)
        # self.delete_bt.clicked.connect(self.DeletePlayerFromDB)

        self.clear_bt = QPushButton("Clear")
        # self.clear_bt.setFont(self.parent.font_small)
        self.clear_bt.setIcon(QIcon('icons/undo.svg'))
        bottom_buttons_layout.addWidget(self.clear_bt)
        # self.clear_bt.clicked.connect(self.Clear)

        # self.LoadCharacters()

    def SetIndex(self, index: int):
        self.findChild(QWidget, "title").setText(f"Player {index}")

    def SetCharactersPerPlayer(self, number):
        while len(self.character_elements) < number:
            character_element = QWidget()
            self.character_elements.append(character_element)
            character_element.setLayout(QHBoxLayout())
            character_element.layout().setSpacing(0)
            character_element.layout().setContentsMargins(0, 0, 0, 0)
            player_character = QComboBox()
            player_character.setEditable(True)
            character_element.layout().addWidget(player_character)
            # self.player_character.activated.connect(self.LoadSkinOptions)
            player_character.setMinimumWidth(120)
            # self.player_character.setFont(self.parent.font_small)
            # self.player_character.lineEdit().setFont(self.parent.font_small)
            # self.player_character.activated.connect(self.CharacterChanged)
            player_character.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            player_character.view().setMinimumWidth(250)
            player_character.completer().setCompletionMode(QCompleter.PopupCompletion)
            player_character.completer().popup().setMinimumWidth(250)

            player_character_color = QComboBox()
            character_element.layout().addWidget(player_character_color)
            player_character_color.setIconSize(QSize(48, 48))
            # self.player_character_color.setMinimumHeight(48)
            player_character_color.setMinimumWidth(120)
            # self.player_character_color.setFont(self.parent.font_small)
            # self.player_character_color.activated.connect(self.CharacterChanged)
            # self.CharacterChanged()
            self.character_container.layout().addWidget(character_element)

        while len(self.character_elements) > number:
            self.character_elements[-1].setParent(None)
            self.character_elements.pop()
