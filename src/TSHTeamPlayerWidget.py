import os
import re
import traceback
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy import uic
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .Helpers.TSHSponsorHelper import TSHSponsorHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTeamBattleModeEnum import TSHTeamBattleModeEnum
from .Helpers.TSHDirHelper import TSHResolve
import threading
from .Helpers.TSHBadWordFilter import TSHBadWordFilter
from loguru import logger


class TSHTeamPlayerWidgetSignals(QObject):
    playerId_changed = Signal()
    dynamicSpinner_changed = Signal()
    activeStatus_changed = Signal(int)
    deathStatus_changed = Signal(int)
    toggleDeathTrigger = Signal(bool)


class TSHTeamPlayerWidget(QGroupBox):
    countries = None
    countryModel = None
    characterModel = None

    dataLock = threading.RLock()

    defaultSpinnerValue = 0
    battleMode: TSHTeamBattleModeEnum = TSHTeamBattleModeEnum.STOCK_POOL
    dynamicSpinner: QSpinBox = None

    def __init__(self, index=0, teamNumber=0, path="", *args):
        super().__init__(*args)

        self.instanceSignals = TSHTeamPlayerWidgetSignals()

        self.path = path

        self.index = index
        self.teamNumber = teamNumber

        self.losers = False

        uic.loadUi(TSHResolve("src/layout/TSHTeamPlayer.ui"), self)

        self.dynamicSpinner = self.findChild(QSpinBox, "dynamicSpinner")

        # custom_textbox_layout = QHBoxLayout()
        # self.custom_textbox = QPlainTextEdit()
        # custom_textbox_layout.addWidget(self.custom_textbox)
        # self.layout().addLayout(custom_textbox_layout, 98, 2, 1, 1)
        # self.custom_textbox.setObjectName("custom_textbox")
        # self.custom_textbox.setMaximumHeight(100)
        # self.custom_textbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        # self.custom_textbox.setPlaceholderText(QApplication.translate("app", "Additional information"))
        # self.custom_textbox.textChanged.connect(
        #         lambda element=self.custom_textbox: [
        #             StateManager.Set(
        #                 f"{self.path}.{element.objectName()}", element.toPlainText()),
        #             self.instanceSignals.dataChanged.emit()
        #         ])

        self.character_container = self.findChild(QWidget, "characters")

        self.LoadCountries()

        TSHCountryHelper.signals.countriesUpdated.connect(self.LoadCountries)

        self.character_elements = []

        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setSpacing(4)
        self.layout().addLayout(bottom_buttons_layout, 99, 0, 1, 3)

        self.clear_bt = QPushButton(QApplication.translate("app", "Clear"))
        self.clear_bt.setFont(QFont(self.clear_bt.font().family(), 9))
        # self.clear_bt.setFont(self.parent.font_small)
        self.clear_bt.setIcon(QIcon('assets/icons/undo.svg'))
        bottom_buttons_layout.addWidget(self.clear_bt)
        self.clear_bt.clicked.connect(self.Clear)
        self.clear_bt.setMinimumWidth(1)

        # Move up/down
        titleContainer = self.findChild(QHBoxLayout, "titleContainer")
        titleContainer.setSpacing(4)
        self.btMoveUp = QPushButton()
        self.btMoveUp.setFixedSize(24, 24)
        self.btMoveUp.setIcon(QIcon("./assets/icons/arrow_up.svg"))
        titleContainer.addWidget(self.btMoveUp)
        self.btMoveDown = QPushButton()
        self.btMoveDown.setFixedSize(24, 24)
        self.btMoveDown.setIcon(QIcon("./assets/icons/arrow_down.svg"))
        titleContainer.addWidget(self.btMoveDown)

        self.SetIndex(index, teamNumber)

        self.lastExportedName = ""

        self.findChild(QLineEdit, "name").editingFinished.connect(
            self.NameChanged)
        self.findChild(QLineEdit, "team").editingFinished.connect(
            self.NameChanged)

        for c in self.findChildren(QLineEdit):
            c.editingFinished.connect(
                lambda element=c: [
                    StateManager.Set(
                        f"{self.path}.{element.objectName() if element.objectName() != 'qt_spinbox_lineedit' else element.parent().objectName()}", element.text()),
                    # self.instanceSignals.dataChanged.emit()
                ])

        for c in self.findChildren(QComboBox):
            c.currentIndexChanged.connect(
                lambda text, element=c: [
                    self.ComboBoxIndexChanged(element)
                ]
            )
            c.currentIndexChanged.emit(0)
        
        self.dynamicSpinner.valueChanged.connect(self.instanceSignals.dynamicSpinner_changed.emit)
        self.dynamicSpinner.valueChanged.connect(self.SpinnerHandling)

        self.SetCharactersPerPlayer(1)

        TSHPlayerDB.signals.db_updated.connect(
            self.SetupAutocomplete)
        self.SetupAutocomplete()

        TSHGameAssetManager.instance.signals.onLoad.connect(
            self.ReloadCharacters)

        self.pronoun_completer = QCompleter()
        self.findChild(QLineEdit, "pronoun").setCompleter(
            self.pronoun_completer)
        self.pronoun_list = []
        for file in ['./user_data/pronouns_list.txt']:
            try:
                with open(file, 'r') as f:
                    for l in f.readlines():
                        processed_line = l.replace("\n", "").strip()
                        if processed_line and processed_line not in self.pronoun_list:
                            self.pronoun_list.append(processed_line)
            except FileNotFoundError:
                with open('./user_data/pronouns_list.txt', 'w') as f:
                    logger.info('creating ./user_data/pronouns_list.txt')
            except Exception as e:
                logger.error(traceback.format_exc())
        self.pronoun_model = QStringListModel()
        self.pronoun_completer.setModel(self.pronoun_model)
        self.pronoun_model.setStringList(self.pronoun_list)

        self.ToggleSponsorDisplay()

    def GetIndex(self):
        return self.index
    
    # =====================================================
    # BATTLE SPECIFIC CALLS
    # =====================================================
    def ToggleSponsorDisplay(self):
        if self.findChild(QLineEdit, "team").isHidden():
            self.findChild(QLineEdit, "team").show()
        else:
            self.findChild(QLineEdit, "team").hide()
    
    def SetBattleMode(self, mode: TSHTeamBattleModeEnum):
        self.battleMode = mode
        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            self.SetDynamicSpinnerLabelText(QApplication.translate("app", "STOCKS/LIVES"))
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            self.SetDynamicSpinnerLabelText(QApplication.translate("app", "GAMES WON"))
    
    def SetDefaultSpinnerValue(self, value: int):
        self.defaultSpinnerValue = value
        self.dynamicSpinner.setMaximum(value)
        self.ResetDynamicSpinner()
    
    # Changes based on battle mode
    def SetDynamicSpinnerLabelText(self, text: str):
        self.findChild(QLabel, "dynamicLabel").setText(text)
    
    def GetSpinnerValue(self):
        return self.dynamicSpinner.value()
    
    def ResetDynamicSpinner(self):
        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            self.dynamicSpinner.setValue(self.defaultSpinnerValue)
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            self.dynamicSpinner.setValue(0)
        self.findChild(QCheckBox, "dead").setChecked(False)

    def IsActive(self):
        return self.findChild(QCheckBox, "activePlayer").isChecked()
    
    def SetActiveStatus(self, status: bool):
        self.findChild(QCheckBox, "activePlayer").setChecked(status)
        self.ExportActiveStatus()
        return
    
    def IsDead(self):
        return self.findChild(QCheckBox, "dead").isChecked()
    
    def SetDeathStatus(self, status: bool):
        self.findChild(QCheckBox, "dead").setChecked(status)
        self.ExportDeathStatus()
        return
    
    def SpinnerHandling(self):
        value = self.dynamicSpinner
        StateManager.Set(f"{self.path}.dynamic_spinner", value.value())
        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            if value.value() <= 0:
                self.SetDeathStatus(True)
            else:
                self.SetDeathStatus(False)

        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            if value.value() >= self.defaultSpinnerValue:
                self.instanceSignals.toggleDeathTrigger.emit(True)
            else:
                self.instanceSignals.toggleDeathTrigger.emit(False)

    def IncreaseCall(self):
        value = self.dynamicSpinner

        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            if value.value() <= 0:
                return
            value.setValue(value.value() - 1)

        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            if value.value() >= self.defaultSpinnerValue:
                return
            value.setValue(value.value() + 1)

    def DecreaseCall(self):
        value = self.dynamicSpinner

        if self.battleMode is TSHTeamBattleModeEnum.STOCK_POOL:
            if value.value() >= self.defaultSpinnerValue:
                return
            value.setValue(value.value() + 1)
        elif self.battleMode is TSHTeamBattleModeEnum.FIRST_TO:
            if value.value() <= 0:
                return
            value.setValue(value.value() - 1)
    
    # =====================================================
    # EXPORT CALLS
    # =====================================================
    def ExportActiveStatus(self):
        StateManager.Set(f"{self.path}.active", self.findChild(QCheckBox, "activePlayer").isChecked())
        return
    
    def ExportDeathStatus(self):
        StateManager.Set(f"{self.path}.dead", self.findChild(QCheckBox, "dead").isChecked())
        return
    
    def CharactersChanged(self, includeMains=False):
        with self.dataLock:
            characters = {}

            for i, (element, character, color, variant) in enumerate(self.character_elements):
                data = character.currentData()

                if data == None:
                    data = {}

                if character.currentData() == None:
                    data = {"name": character.currentText()}

                if color.currentData() and color.currentData().get("name", ""):
                    data["name"] = color.currentData().get("name", "")

                if color.currentData() and color.currentData().get("en_name", ""):
                    data["en_name"] = color.currentData().get("en_name", "")

                if color.currentData() and character.currentData():
                    data["assets"] = color.currentData().get("assets", {})

                if data.get("assets") == None:
                    data["assets"] = {}

                data["skin"] = color.currentIndex()
                if variant.currentData():
                    data["variant"] = variant.currentData()
                else:
                    data["variant"] = {}

                characters[i+1] = data

            StateManager.Set(
                f"{self.path}.character", characters)

            if includeMains:
                StateManager.Set(
                    f"{self.path}.mains", characters)
    
    def ComboBoxIndexChanged(self, element: QComboBox):
        StateManager.Set(
            f"{self.path}.{element.objectName()}", element.currentData())

    def NameChanged(self):
        with self.dataLock:
            team = self.findChild(QLineEdit, "team").text()
            name = self.findChild(QLineEdit, "name").text()
            merged = team + " " + name

            if merged != self.lastExportedName:
                self.ExportMergedName()
                self.ExportPlayerImages()
                # self.ExportPlayerId()

            self.lastExportedName = merged

    def ExportMergedName(self):
        with self.dataLock:
            team = self.findChild(QLineEdit, "team").text()
            name = self.findChild(QLineEdit, "name").text()
            merged = ""
            nameOnlyMerged = ""

            if team != "":
                merged += team+" | "

            merged += name
            nameOnlyMerged += name

            StateManager.Set(
                f"{self.path}.mergedName", merged)
            StateManager.Set(
                f"{self.path}.mergedOnlyName", nameOnlyMerged)

    def ExportPlayerImages(self, onlineAvatar=None):
        with self.dataLock:
            team = self.findChild(QLineEdit, "team").text()
            name = self.findChild(QLineEdit, "name").text()
            merged = ""

            if team != "":
                merged += team+" "

            merged += name

            merged = re.sub(r"[,/|;:<>\\?*]", "_", merged)

            # Online avatar
            StateManager.Set(
                f"{self.path}.online_avatar", onlineAvatar)

            # Local avatar
            if os.path.exists(f"./user_data/player_avatar/{merged}.png"):
                StateManager.Set(
                    f"{self.path}.avatar", f"./user_data/player_avatar/{merged}.png")
            else:
                StateManager.Set(
                    f"{self.path}.avatar", None)
                
            TSHSponsorHelper.ExportValidSponsors(team, self.path)

    def ExportPlayerCity(self, city=None):
        with self.dataLock:
            if StateManager.Get(f"{self.path}.city") != city:
                StateManager.Set(
                    f"{self.path}.city", city)

    def SwapWith(self, other: "TSHTeamPlayerWidget"):
        if self == other:
            logger.info("Swapping player with themselves")
            return
        try:
            StateManager.BlockSaving()
            with self.dataLock:
                with other.dataLock:
                    tmpData = []

                    # Save state
                    for w in [self, other]:
                        data = {}
                        for widget in w.findChildren(QWidget):
                            if type(widget) == QLineEdit:
                                data[widget.objectName()] = widget.text()
                            if type(widget) == QComboBox:
                                data[widget.objectName()] = widget.currentIndex()
                            if type(widget) == QPlainTextEdit:
                                data[widget.objectName()] = widget.toPlainText()
                        data["online_avatar"] = StateManager.Get(
                            f"{w.path}.online_avatar")
                        data["id"] = StateManager.Get(
                            f"{w.path}.id")
                        data["seed"] = StateManager.Get(
                            f"{w.path}.seed")
                        data["city"] = StateManager.Get(
                            f"{w.path}.city")
                        tmpData.append(data)

                    # Load state
                    for i, w in enumerate([other, self]):
                        for objName in tmpData[i]:
                            widget = w.findChild(QWidget, objName)
                            if widget:
                                if type(widget) == QLineEdit:
                                    widget.setText(tmpData[i][objName])
                                    widget.editingFinished.emit()
                                if type(widget) == QComboBox:
                                    widget.setCurrentIndex(tmpData[i][objName])
                                if type(widget) == QPlainTextEdit:
                                    widget.setPlainText(tmpData[i][objName])
                        QCoreApplication.processEvents()
                        w.ExportPlayerImages(tmpData[i]["online_avatar"])
                        # w.ExportPlayerId(tmpData[i]["id"])
                        StateManager.Set(f"{w.path}.seed", tmpData[i]["seed"])
                        StateManager.Set(f"{w.path}.city", tmpData[i]["city"])
        finally:
            StateManager.ReleaseSaving()

    def SetIndex(self, index: int, team: int):
        self.index = index
        self.teamNumber = team

    def SetStocksPerPlayer(self, number):
        while len(self.character_elements) < number:
            character_element = QWidget()
            character_element.setLayout(QHBoxLayout())
            character_element.layout().setSpacing(4)
            character_element.layout().setContentsMargins(0, 0, 0, 0)
            player_character = QComboBox()
            player_character.setEditable(True)
            character_element.layout().addWidget(player_character)
            player_character.setMinimumWidth(60)
            player_character.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            player_character.view().setMinimumWidth(60)
            player_character.completer().setCompletionMode(QCompleter.PopupCompletion)
            player_character.completer().popup().setMinimumWidth(250)
            player_character.setModel(
                TSHGameAssetManager.instance.characterModel)
            player_character.setIconSize(QSize(24, 24))
            player_character.setFixedHeight(32)
            player_character.setFont(
                QFont(player_character.font().family(), 9))
            player_character.lineEdit().setFont(QFont(player_character.font().family(), 9))

            # Add line to characters
            self.character_container.layout().addWidget(character_element)

            player_character.setCurrentIndex(0)

            player_character.setObjectName(
                f"character_{len(self.character_elements)}")

        while len(self.character_elements) > number:
            self.character_elements[-1][0].setParent(None)
            self.character_elements.pop()
        
        if self.character_container.findChild(QComboBox, "variants") is not None:
            if len(TSHGameAssetManager.instance.variants) <= 0:
                for container in self.findChildren(QComboBox, "variants"):
                    container.setVisible(False)
            else:
                for container in self.findChildren(QComboBox, "variants"):
                    container.setVisible(True)

        self.CharactersChanged(includeMains=True)

    def SetCharactersPerPlayer(self, number):
        while len(self.character_elements) < number:
            character_element = QWidget()
            character_element.setLayout(QHBoxLayout())
            character_element.layout().setSpacing(4)
            character_element.layout().setContentsMargins(0, 0, 0, 0)
            player_character = QComboBox()
            player_character.setEditable(True)
            character_element.layout().addWidget(player_character)
            player_character.setMinimumWidth(60)
            player_character.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            player_character.view().setMinimumWidth(60)
            player_character.completer().setCompletionMode(QCompleter.PopupCompletion)
            player_character.completer().popup().setMinimumWidth(250)
            player_character.setModel(
                TSHGameAssetManager.instance.characterModel)
            player_character.setIconSize(QSize(24, 24))
            player_character.setFixedHeight(32)
            player_character.setFont(
                QFont(player_character.font().family(), 9))
            player_character.lineEdit().setFont(QFont(player_character.font().family(), 9))

            player_character_color = QComboBox()
            character_element.layout().addWidget(player_character_color)
            player_character_color.setIconSize(QSize(48, 48))
            player_character_color.setFixedHeight(32)
            player_character_color.setMinimumWidth(64)
            player_character_color.setMaximumWidth(120)
            player_character_color.setFont(
                QFont(player_character_color.font().family(), 9))
            view = QListView()
            view.setIconSize(QSize(128, 128))
            player_character_color.setView(view)
            player_character_color.setEditable(True)
            player_character_color.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            player_character_color.completer().setCompletionMode(QCompleter.PopupCompletion)
            # self.player_character_color.activated.connect(self.CharacterChanged)
            # self.CharacterChanged()

            # Add variant
            player_variant = QComboBox()
            player_variant.setObjectName("variants")
            character_element.layout().addWidget(player_variant)
            player_variant.setIconSize(QSize(24, 24))
            player_variant.setFixedHeight(32)
            player_variant.setMinimumWidth(60)
            player_variant.setMaximumWidth(120)
            player_variant.setFont(
                QFont(player_variant.font().family(), 9))
            player_variant.setModel(
                TSHGameAssetManager.instance.variantModel)
            view = QListView()
            view.setIconSize(QSize(24, 24))
            player_variant.setView(view)
            player_variant.setEditable(True)
            player_variant.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            player_variant.completer().setCompletionMode(QCompleter.PopupCompletion)

            if len(TSHGameAssetManager.instance.variants) <= 0:
                player_variant.setVisible(False)

            # Move up/down
            btMoveUp = QPushButton()
            btMoveUp.setFixedSize(24, 24)
            btMoveUp.setIcon(QIcon("./assets/icons/arrow_up.svg"))
            character_element.layout().addWidget(btMoveUp)
            btMoveUp.clicked.connect(lambda x=None, index=len(
                self.character_elements): self.SwapCharacters(index, index-1))
            btMoveDown = QPushButton()
            btMoveDown.setFixedSize(24, 24)
            btMoveDown.setIcon(QIcon("./assets/icons/arrow_down.svg"))
            character_element.layout().addWidget(btMoveDown)
            btMoveDown.clicked.connect(lambda x=None, index=len(
                self.character_elements): self.SwapCharacters(index, index+1))

            # Add line to characters
            self.character_container.layout().addWidget(character_element)

            self.character_elements.append(
                [character_element, player_character, player_character_color, player_variant])

            player_character.currentIndexChanged.connect(
                lambda x, element=player_character, target=player_character_color: [
                    self.LoadSkinOptions(element, target),
                    self.CharactersChanged()
                ]
            )

            player_character_color.currentIndexChanged.connect(
                lambda index, element=player_character: [
                    self.CharactersChanged()
                ]
            )
            
            player_variant.currentIndexChanged.connect(
                lambda index, element=player_character: [
                    self.CharactersChanged()
                ]
            )

            player_character.setCurrentIndex(0)
            player_character_color.setCurrentIndex(0)
            player_variant.setCurrentIndex(0)

            player_character.setObjectName(
                f"character_{len(self.character_elements)}")
            player_character_color.setObjectName(
                f"character_color_{len(self.character_elements)}")

        while len(self.character_elements) > number:
            self.character_elements[-1][0].setParent(None)
            self.character_elements.pop()
        
        if self.character_container.findChild(QComboBox, "variants") is not None:
            if len(TSHGameAssetManager.instance.variants) <= 0:
                for container in self.findChildren(QComboBox, "variants"):
                    container.setVisible(False)
            else:
                for container in self.findChildren(QComboBox, "variants"):
                    container.setVisible(True)

        self.CharactersChanged(includeMains=True)

    def SwapCharacters(self, index1: int, index2: int):
        StateManager.BlockSaving()

        if index2 > len(self.character_elements)-1:
            index2 = 0

        char1 = self.character_elements[index1]
        char2 = self.character_elements[index2]

        # Save index1 settings
        tmp = [char1[1].currentText(), char1[2].currentIndex()]

        # Set index1 to index2
        # Character
        found = char1[1].findText(char2[1].currentText())
        if found != -1:
            char1[1].setCurrentIndex(found)
        else:
            char1[1].setCurrentText(char2[1].currentText())

        # Color
        char1[2].setCurrentIndex(char2[2].currentIndex())

        # Set index2 to temp (index1)
        # Character
        found = char2[1].findText(tmp[0])
        if found != -1:
            char2[1].setCurrentIndex(found)
        else:
            char2[1].setCurrentText(tmp[0])

        # Color
        char2[2].setCurrentIndex(tmp[1])

        self.CharactersChanged()

        StateManager.ReleaseSaving()

    def LoadCountries(self):
        try:
            if TSHCountryHelper.countryModel == None:
                TSHCountryHelper.LoadCountries()

            countryCompleter = QCompleter(
                TSHCountryHelper.countryModel)

            country: QComboBox = self.findChild(QComboBox, "country")
            country.setCompleter(countryCompleter)
            country.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            country.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            country.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            country.view().setMinimumWidth(60)
            country.completer().setCompletionMode(QCompleter.PopupCompletion)
            country.completer().popup().setMinimumWidth(300)
            country.setModel(TSHCountryHelper.countryModel)
            country.setFont(QFont(country.font().family(), 9))
            country.lineEdit().setFont(QFont(country.font().family(), 9))

            country.currentIndexChanged.connect(self.LoadStates)

            state: QComboBox = self.findChild(QComboBox, "state")
            state.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            state.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            state.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            state.view().setMinimumWidth(60)
            state.completer().setCompletionMode(QCompleter.PopupCompletion)
            state.completer().popup().setMinimumWidth(300)
            state.setFont(QFont(state.font().family(), 9))
            state.lineEdit().setFont(QFont(state.font().family(), 9))

        except Exception as e:
            logger.error(traceback.format_exc())
            exit()

    def LoadStates(self, index):
        country: QComboBox = self.findChild(QComboBox, "country")

        countryData = None
        if country.currentData(Qt.ItemDataRole.UserRole) != None:
            countryData = TSHCountryHelper.countries.get(country.currentData(
                Qt.ItemDataRole.UserRole).get("code"), {})

        stateModel = QStandardItemModel()

        noState = QStandardItem()
        noState.setData({}, Qt.ItemDataRole.UserRole)
        stateModel.appendRow(noState)

        states = countryData.get("states")

        if states is not None:
            for i, state_code in enumerate(states.keys()):
                item = QStandardItem()
                # Windows has some weird thing with files named CON.png. In case a state code is CON,
                # we try to load _CON.png instead
                path = f'./assets/state_flag/{countryData.get("code")}/{"_CON" if state_code == "CON" else state_code}.png'

                if not os.path.exists(path):
                    path = None

                states[state_code].update({
                    "asset": path
                })
                item.setIcon(QIcon(path))
                item.setData(states[state_code], Qt.ItemDataRole.UserRole)
                item.setData(
                    f'{states[state_code]["name"]} ({state_code})', Qt.ItemDataRole.EditRole)
                stateModel.appendRow(item)

        state: QComboBox = self.findChild(QComboBox, "state")
        state.setModel(stateModel)
        state.setCurrentIndex(0)

    def LoadSkinOptions(self, element, target):
        characterData = element.currentData()

        if characterData:
            target.setModel(TSHGameAssetManager.instance.skinModels.get(
                characterData.get("en_name")))
        else:
            target.setModel(QStandardItemModel())

    def ReloadCharacters(self):
        if len(TSHGameAssetManager.instance.variants) <= 0:
            for container in self.findChildren(QComboBox, "variants"):
                container.setVisible(False)
        else:
            for container in self.findChildren(QComboBox, "variants"):
                container.setVisible(True)
        for c in self.character_elements:
            c[1].setModel(TSHGameAssetManager.instance.characterModel)
            c[1].setIconSize(QSize(24, 24))
            c[1].setFixedHeight(32)
            c[3].setModel(TSHGameAssetManager.instance.variantModel)

    def SetupAutocomplete(self):
        if TSHPlayerDB.model:
            self.findChild(QLineEdit, "name").setCompleter(QCompleter())
            self.findChild(QLineEdit, "name").completer().activated[QModelIndex].connect(
                lambda x: self.SetData(x.data(Qt.ItemDataRole.UserRole)) if x is not None else None, Qt.QueuedConnection)
            self.findChild(QLineEdit, "name").completer().setCaseSensitivity(
                Qt.CaseSensitivity.CaseInsensitive)
            self.findChild(QLineEdit, "name").completer(
            ).setFilterMode(Qt.MatchFlag.MatchContains)
            self.findChild(QLineEdit, "name").completer().setModel(
                TSHPlayerDB.model)

    def SetData(self, data, dontLoadFromDB=False, clear=True, no_mains=False):
        self.dataLock.acquire()
        StateManager.BlockSaving()

        logger.debug(f"Setting data for {self.path}: {data}")

        try:
            if clear:
                self.Clear(no_mains=no_mains)

            # Load player data from DB; will be overwriten by incoming data
            if not dontLoadFromDB:
                tag = data.get(
                    "prefix")+" "+data.get("gamerTag") if data.get("prefix") else data.get("gamerTag")

                for i in range(TSHPlayerDB.model.rowCount()):
                    item = TSHPlayerDB.model.item(
                        i).data(Qt.ItemDataRole.UserRole)

                    dbTag = item.get(
                        "prefix")+" "+item.get("gamerTag") if item.get("prefix") else item.get("gamerTag")

                    if tag == dbTag:
                        self.SetData(item, dontLoadFromDB=True,
                                     clear=False, no_mains=no_mains)
                        break

            name = self.findChild(QWidget, "name")
            if data.get("gamerTag") and data.get("gamerTag") != name.text():
                data["gamerTag"] = TSHBadWordFilter.Censor(
                    data["gamerTag"], data.get("country_code"))
                name.setText(f'{data.get("gamerTag")}')
                name.editingFinished.emit()

            team = self.findChild(QWidget, "team")
            if data.get("prefix") and data.get("prefix") != team.text():
                data["prefix"] = TSHBadWordFilter.Censor(
                    data["prefix"], data.get("country_code"))
                team.setText(f'{data.get("prefix")}')
                team.editingFinished.emit()

            if data.get("avatar"):
                self.ExportPlayerImages(data.get("avatar"))

            # if data.get("id"):
            #     self.ExportPlayerId(data.get("id"))

            if data.get("city"):
                self.ExportPlayerCity(data.get("city"))

            twitter = self.findChild(QWidget, "twitter")
            if data.get("twitter") and data.get("twitter") != twitter.text():
                data["twitter"] = TSHBadWordFilter.Censor(
                    data["twitter"], data.get("country_code"))
                twitter.setText(
                    f'{data.get("twitter")}')
                twitter.editingFinished.emit()
            
            # if data.get("custom_textbox") and data.get("custom_textbox") != self.custom_textbox.toPlainText():
            #     data["custom_textbox"] = TSHBadWordFilter.Censor(
            #         data["custom_textbox"], data.get("country_code"))
            #     self.custom_textbox.setPlainText(
            #         f'{data.get("custom_textbox")}'.replace("\\n", "\n"))
            #     self.custom_textbox.textChanged.emit()

            pronoun = self.findChild(QWidget, "pronoun")
            if data.get("pronoun") and data.get("pronoun") != pronoun.text():
                data["pronoun"] = TSHBadWordFilter.Censor(
                    data["pronoun"], data.get("country_code"))
                pronoun.setText(
                    f'{data.get("pronoun")}')
                pronoun.editingFinished.emit()

            if data.get("country_code"):
                countryElement: QComboBox = self.findChild(
                    QComboBox, "country")
                countryIndex = 0
                for i in range(TSHCountryHelper.countryModel.rowCount()):
                    item = TSHCountryHelper.countryModel.item(
                        i).data(Qt.ItemDataRole.UserRole)
                    if item:
                        if data.get("country_code") == item.get("code"):
                            countryIndex = i
                            break
                if countryElement.currentIndex() != countryIndex:
                    countryElement.setCurrentIndex(countryIndex)

            if data.get("state_code"):
                countryElement: QComboBox = self.findChild(
                    QComboBox, "country")
                stateElement: QComboBox = self.findChild(QComboBox, "state")
                stateIndex = 0
                for i in range(stateElement.model().rowCount()):
                    item = stateElement.model().item(i).data(Qt.ItemDataRole.UserRole)
                    if item:
                        if data.get("state_code") == item.get("original_code"):
                            stateIndex = i
                            break
                if stateElement.currentIndex() != stateIndex:
                    stateElement.setCurrentIndex(stateIndex)

            if data.get("controller"):
                controllerElement: QComboBox = self.findChild(
                    QComboBox, "controller")
                controllerIndex = 0
                for i in range(controllerElement.model().rowCount()):
                    item = controllerElement.model().item(i).data(Qt.ItemDataRole.UserRole)
                    if item:
                        if data.get("controller") == item.get("codename"):
                            controllerIndex = i
                            break
                if controllerElement.currentIndex() != controllerIndex:
                    controllerElement.setCurrentIndex(controllerIndex)

            if data.get("mains") and no_mains != True:
                if type(data.get("mains")) == list:
                    for element in self.character_elements:
                        character_element = element[1]
                        characterIndex = 0
                        for i in range(character_element.model().rowCount()):
                            item = character_element.model().item(i).data(Qt.ItemDataRole.UserRole)
                            if item:
                                if item.get("en_name") == data.get("mains")[0]:
                                    characterIndex = i
                                    break
                        character_element.setCurrentIndex(characterIndex)
                elif type(data.get("mains")) == dict:
                    mains = data.get("mains").get(
                        TSHGameAssetManager.instance.selectedGame.get("codename"), [])

                    for i, main in enumerate(mains):
                        if i < len(self.character_elements):
                            character_element = self.character_elements[i][1]
                            color_element = self.character_elements[i][2]
                            variant_element = self.character_elements[i][3]
                            characterIndex = 0
                            for i in range(character_element.model().rowCount()):
                                item = character_element.model().item(i).data(Qt.ItemDataRole.UserRole)
                                if item:
                                    if item.get("en_name") == main[0]:
                                        characterIndex = i
                                        break
                            if character_element.currentIndex() != characterIndex:
                                character_element.setCurrentIndex(
                                    characterIndex)
                            if len(main) > 1:
                                if color_element.currentIndex() != int(main[1]):
                                    color_element.setCurrentIndex(int(main[1]))
                            else:
                                if color_element.currentIndex() != 0:
                                    color_element.setCurrentIndex(0)
                            
                            variantIndex = 0
                            if variant_element:
                                for i in range(variant_element.model().rowCount()):
                                    item = variant_element.model().item(i).data(Qt.ItemDataRole.UserRole)
                                    if item:
                                        if len(main) >= 3 :
                                            if item.get("en_name") == main[2]:
                                                variantIndex = i
                                                break
                                        else:
                                            variantIndex = 0
                                            break
                            else:
                                variantIndex = 0
                            if variant_element.currentIndex() != variantIndex:
                                variant_element.setCurrentIndex(variantIndex)

            if data.get("city"):
                StateManager.Set(f"{self.path}.city", data.get("city"))
        finally:
            StateManager.ReleaseSaving()
            self.dataLock.release()

    def GetCurrentPlayerTag(self):
        gamerTag = self.findChild(QWidget, "name").text()
        prefix = self.findChild(QWidget, "team").text()
        return prefix+" "+gamerTag if prefix else gamerTag

    def Clear(self, no_mains=False):
        StateManager.BlockSaving()
        with self.dataLock:
            for c in self.findChildren(QLineEdit):
                if c.objectName() != "" and c.objectName() != 'qt_spinbox_lineedit':
                    if c.text() != "":
                        c.setText("")
                        c.editingFinished.emit()

            for c in self.findChildren(QSpinBox):
                c.setValue(0)
                c.lineEdit().editingFinished.emit()

            for c in self.findChildren(QPlainTextEdit):
                if c.toPlainText() != "":
                    c.clear()
                    c.textChanged.emit()

            for c in self.findChildren(QComboBox):
                if (no_mains):
                    for charelem in self.character_elements:
                        for i in range(len(charelem)):
                            if charelem[i] == c:
                                break
                        else:
                            c.setCurrentIndex(0)
                        continue  # only executed if the inner loop DID break
                else:
                    c.setCurrentIndex(0)
        StateManager.ReleaseSaving()
