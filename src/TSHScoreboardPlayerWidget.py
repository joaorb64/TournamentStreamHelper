import os
import re
import traceback
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .Helpers.TSHLocaleHelper import TSHLocaleHelper
import copy


class TSHScoreboardPlayerWidgetSignals(QObject):
    characters_changed = pyqtSignal()
    playerId_changed = pyqtSignal()
    player1Id_changed = pyqtSignal()
    player2Id_changed = pyqtSignal()
    dataChanged = pyqtSignal()


class TSHScoreboardPlayerWidget(QGroupBox):
    countries = None
    countryModel = None
    characterModel = None

    signals = TSHScoreboardPlayerWidgetSignals()

    def __init__(self, index=0, teamNumber=0, path="", *args):
        super().__init__(*args)

        self.instanceSignals = TSHScoreboardPlayerWidgetSignals()

        self.path = path

        self.index = index
        self.teamNumber = teamNumber

        self.losers = False

        uic.loadUi("src/layout/TSHScoreboardPlayer.ui", self)

        self.character_container = self.findChild(QWidget, "characters")

        self.LoadCountries()

        TSHCountryHelper.signals.countriesUpdated.connect(self.LoadCountries)

        self.character_elements = []

        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setSpacing(4)
        self.layout().addLayout(bottom_buttons_layout, 99, 0, 1, 3)

        self.save_bt = QPushButton(
            QApplication.translate("app", "Save new player"))
        self.save_bt.setFont(QFont(self.save_bt.font().family(), 9))
        # self.save_bt.setFont(self.parent.font_small)
        self.save_bt.setIcon(QIcon('assets/icons/save.svg'))
        bottom_buttons_layout.addWidget(self.save_bt)
        self.save_bt.clicked.connect(self.SavePlayerToDB)
        self.findChild(QLineEdit, "name").editingFinished.connect(
            self.ManageSavePlayerToDBText)
        self.findChild(QLineEdit, "team").editingFinished.connect(
            self.ManageSavePlayerToDBText)
        self.save_bt.setMinimumWidth(1)

        self.delete_bt = QPushButton(
            QApplication.translate("app", "Delete player entry"))
        # self.delete_bt.setFont(self.parent.font_small)
        self.delete_bt.setIcon(QIcon('assets/icons/cancel.svg'))
        bottom_buttons_layout.addWidget(self.delete_bt)
        self.delete_bt.setFont(QFont(self.delete_bt.font().family(), 9))
        self.delete_bt.setEnabled(False)
        self.findChild(QLineEdit, "name").editingFinished.connect(
            self.ManageDeletePlayerFromDBActive)
        self.findChild(QLineEdit, "team").editingFinished.connect(
            self.ManageDeletePlayerFromDBActive)
        self.delete_bt.clicked.connect(self.DeletePlayerFromDB)
        self.delete_bt.setMinimumWidth(1)

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

        self.findChild(QLineEdit, "name").textChanged.connect(
            self.ExportMergedName)
        self.findChild(QLineEdit, "team").textChanged.connect(
            self.ExportMergedName)

        self.findChild(QLineEdit, "name").textChanged.connect(
            lambda: self.ExportPlayerImages())
        self.findChild(QLineEdit, "team").textChanged.connect(
            lambda: self.ExportPlayerImages())

        self.findChild(QLineEdit, "name").textChanged.connect(
            lambda: self.ExportPlayerId())

        for c in self.findChildren(QLineEdit):
            c.editingFinished.connect(
                lambda element=c: [
                    StateManager.Set(
                        f"{self.path}.{element.objectName()}", element.text()),
                    self.instanceSignals.dataChanged.emit()
                ])

        for c in self.findChildren(QComboBox):
            c.currentIndexChanged.connect(
                lambda text, element=c: [
                    StateManager.Set(
                        f"{self.path}.{element.objectName()}", element.currentData()
                    ),
                    self.instanceSignals.dataChanged.emit()
                ]
            )
            c.currentIndexChanged.emit(0)

        self.SetCharactersPerPlayer(1)

        TSHScoreboardPlayerWidget.signals.characters_changed.connect(
            self.ReloadCharacters)

        TSHPlayerDB.signals.db_updated.connect(
            self.SetupAutocomplete)
        self.SetupAutocomplete()

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
            except Exception as e:
                print(f"ERROR: Did not find {file}")
                print(traceback.format_exc())
        self.pronoun_model = QStringListModel()
        self.pronoun_completer.setModel(self.pronoun_model)
        self.pronoun_model.setStringList(self.pronoun_list)

    def CharactersChanged(self):
        characters = {}

        for i, (element, character, color) in enumerate(self.character_elements):
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

            data["skin"] = color.currentText()

            characters[i+1] = data

        StateManager.Set(
            f"{self.path}.character", characters)

    def SetLosers(self, value):
        self.losers = value
        self.ExportMergedName()

    def ExportMergedName(self):
        team = self.findChild(QLineEdit, "team").text()
        name = self.findChild(QLineEdit, "name").text()
        merged = ""
        nameOnlyMerged = ""

        if team != "":
            merged += team+" | "

        merged += name
        nameOnlyMerged += name

        if self.losers:
            merged += " [L]"
            nameOnlyMerged += " [L]"

        StateManager.Set(
            f"{self.path}.mergedName", merged)
        StateManager.Set(
            f"{self.path}.mergedOnlyName", nameOnlyMerged)

    def ExportPlayerImages(self, onlineAvatar=None):
        team = self.findChild(QLineEdit, "team").text()
        name = self.findChild(QLineEdit, "name").text()
        merged = ""

        if team != "":
            merged += team+" "

        merged += name

        merged = merged.replace("/", " ")
        merged = merged.replace(":", " ")

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

        # Sponsor logo
        if os.path.exists(f"./user_data/sponsor_logo/{team.upper()}.png"):
            StateManager.Set(
                f"{self.path}.sponsor_logo", f"./user_data/sponsor_logo/{team.upper()}.png")
        else:
            StateManager.Set(
                f"{self.path}.sponsor_logo", None)

    def ExportPlayerId(self, id=None):
        if StateManager.Get(f"{self.path}.id") != id:
            StateManager.Set(
                f"{self.path}.id", id)
            self.instanceSignals.playerId_changed.emit()
            if self.path.startswith("score.team.1"):
                self.instanceSignals.player1Id_changed.emit()
            else:
                self.instanceSignals.player2Id_changed.emit()

    def SwapWith(self, other: "TSHScoreboardPlayerWidget"):
        tmpData = []

        # Save state
        for w in [self, other]:
            data = {}
            for widget in w.findChildren(QWidget):
                if type(widget) == QLineEdit:
                    data[widget.objectName()] = widget.text()
                if type(widget) == QComboBox:
                    data[widget.objectName()] = widget.currentIndex()
            data["online_avatar"] = StateManager.Get(
                f"{w.path}.online_avatar")
            data["id"] = StateManager.Get(
                f"{w.path}.id")
            data["seed"] = StateManager.Get(
                f"{w.path}.seed")
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
            QCoreApplication.processEvents()
            w.ExportPlayerImages(tmpData[i]["online_avatar"])
            w.ExportPlayerId(tmpData[i]["id"])
            StateManager.Set(f"{w.path}.seed", tmpData[i]["seed"])

    def SetIndex(self, index: int, team: int):
        self.findChild(QWidget, "title").setText(
            QApplication.translate("app", "Player {0}").format(index))
        self.index = index
        self.teamNumber = team

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
            player_character.setModel(TSHScoreboardPlayerWidget.characterModel)
            player_character.setIconSize(QSize(24, 24))
            player_character.setFixedHeight(32)
            player_character.setFont(QFont(player_character.font().family(), 9))
            player_character.lineEdit().setFont(QFont(player_character.font().family(), 9))

            player_character_color = QComboBox()
            character_element.layout().addWidget(player_character_color)
            player_character_color.setIconSize(QSize(48, 48))
            player_character_color.setFixedHeight(32)
            player_character_color.setMinimumWidth(64)
            player_character_color.setMaximumWidth(120)
            player_character_color.setFont(QFont(player_character_color.font().family(), 9))
            view = QListView()
            view.setIconSize(QSize(128, 128))
            player_character_color.setView(view)
            # self.player_character_color.activated.connect(self.CharacterChanged)
            # self.CharacterChanged()

            # Move up/down
            btMoveUp = QPushButton()
            btMoveUp.setFixedSize(24, 24)
            btMoveUp.setIcon(QIcon("./assets/icons/arrow_up.svg"))
            character_element.layout().addWidget(btMoveUp)
            btMoveUp.clicked.connect(lambda checked, index=len(self.character_elements): self.SwapCharacters(index, index-1))
            btMoveDown = QPushButton()
            btMoveDown.setFixedSize(24, 24)
            btMoveDown.setIcon(QIcon("./assets/icons/arrow_down.svg"))
            character_element.layout().addWidget(btMoveDown)
            btMoveDown.clicked.connect(lambda checked, index=len(self.character_elements): self.SwapCharacters(index, index+1))

            # Add line to characters
            self.character_container.layout().addWidget(character_element)

            self.character_elements.append(
                [character_element, player_character, player_character_color])

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

            player_character.setCurrentIndex(0)
            player_character_color.setCurrentIndex(0)

            player_character.setObjectName(
                f"character_{len(self.character_elements)}")
            player_character_color.setObjectName(
                f"character_color_{len(self.character_elements)}")

        while len(self.character_elements) > number:
            self.character_elements[-1][0].setParent(None)
            self.character_elements.pop()

        self.CharactersChanged()
    
    def SwapCharacters(self, index1: int, index2: int):
        StateManager.BlockSaving()

        if index2 > len(self.character_elements)-1: index2 = 0

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
            print(e)
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

    def LoadCharacters():
        class CharacterLoaderThread(QThread):
            def run(self):
                try:
                    TSHScoreboardPlayerWidget.characterModel = QStandardItemModel()

                    # Add one empty
                    item = QStandardItem("")
                    TSHScoreboardPlayerWidget.characterModel.appendRow(item)

                    for c in TSHGameAssetManager.instance.characters.keys():
                        item = QStandardItem()
                        item.setData(c, Qt.ItemDataRole.EditRole)
                        item.setIcon(
                            QIcon(QPixmap.fromImage(TSHGameAssetManager.instance.stockIcons[c][0]).scaledToWidth(
                                32, Qt.TransformationMode.SmoothTransformation))
                        )

                        # Load translations
                        display_name = c
                        export_name = c

                        if TSHGameAssetManager.instance.characters[c].get("locale"):
                            locale = TSHLocaleHelper.programLocale
                            if locale.replace("-", "_") in TSHGameAssetManager.instance.characters[c]["locale"]:
                                display_name = TSHGameAssetManager.instance.characters[
                                    c]["locale"][locale.replace("-", "_")]
                            elif re.split("-|_", locale)[0] in TSHGameAssetManager.instance.characters[c]["locale"]:
                                display_name = TSHGameAssetManager.instance.characters[
                                    c]["locale"][re.split("-|_", locale)[0]]
                            elif TSHLocaleHelper.GetRemaps(TSHLocaleHelper.programLocale) in TSHGameAssetManager.instance.characters[c]["locale"]:
                                display_name = TSHGameAssetManager.instance.characters[c]["locale"][TSHLocaleHelper.GetRemaps(
                                    TSHLocaleHelper.programLocale)]

                            locale = TSHLocaleHelper.exportLocale
                            if locale.replace("-", "_") in TSHGameAssetManager.instance.characters[c]["locale"]:
                                export_name = TSHGameAssetManager.instance.characters[
                                    c]["locale"][locale.replace("-", "_")]
                            elif re.split("-|_", locale)[0] in TSHGameAssetManager.instance.characters[c]["locale"]:
                                export_name = TSHGameAssetManager.instance.characters[
                                    c]["locale"][re.split("-|_", locale)[0]]
                            elif TSHLocaleHelper.GetRemaps(TSHLocaleHelper.exportLocale) in TSHGameAssetManager.instance.characters[c]["locale"]:
                                export_name = TSHGameAssetManager.instance.characters[c]["locale"][TSHLocaleHelper.GetRemaps(
                                    TSHLocaleHelper.exportLocale)]

                            if display_name != c:
                                item.setData(
                                    f"{display_name} / {c}", Qt.ItemDataRole.EditRole)

                        data = {
                            "name": export_name,
                            "en_name": c,
                            "display_name": display_name,
                            "codename": TSHGameAssetManager.instance.characters[c].get("codename")
                        }
                        item.setData(data, Qt.ItemDataRole.UserRole)
                        TSHScoreboardPlayerWidget.characterModel.appendRow(
                            item)

                    TSHScoreboardPlayerWidget.characterModel.sort(0)

                    TSHScoreboardPlayerWidget.signals.characters_changed.emit()
                except:
                    print(traceback.format_exc())

        characterLoaderThread = CharacterLoaderThread(
            TSHGameAssetManager.instance)
        characterLoaderThread.start()

    def LoadSkinOptions(self, element, target):
        characterData = element.currentData()

        skins = {}

        if characterData:
            skins = TSHGameAssetManager.instance.skins.get(
                element.currentData().get("en_name"), {})

        sortedSkins = [int(k) for k in skins.keys()]
        sortedSkins.sort()

        target.clear()

        skinModel = QStandardItemModel()

        for skin in sortedSkins:
            assetData = {}
            assetData["assets"] = TSHGameAssetManager.instance.GetCharacterAssets(
                element.currentData().get("codename"), skin)
            if assetData["assets"] == None:
                assetData["assets"] = {}
            item = QStandardItem()

            skinIndex = str(skin)

            # Get skin name
            skinNameData = TSHGameAssetManager.instance.characters.get(element.currentData().get("en_name"), {}).get("skin_name", {})

            skin_name = element.currentData().get("name")
            skin_name_en = element.currentData().get("en_name")

            try:
                locale = TSHLocaleHelper.programLocale
                if locale.replace("-", "_") in skinNameData.get(skinIndex, {}).get("locale", {}):
                    skin_name = skinNameData.get(skinIndex, {}).get("locale", {})[locale.replace("-", "_")]
                elif re.split("-|_", locale)[0] in skinNameData.get(skinIndex, {}).get("locale", {}):
                    skin_name = skinNameData.get(skinIndex, {}).get("locale", {})[re.split("-|_", locale)[0]]
                elif TSHLocaleHelper.GetRemaps(TSHLocaleHelper.exportLocale) in skinNameData.get("locale", {}):
                    skin_name = skinNameData.get(skinIndex, {}).get("locale", {})[TSHLocaleHelper.GetRemaps(
                        TSHLocaleHelper.exportLocale)]
                elif skinNameData.get(skinIndex, {}).get("name"):
                    skin_name = skinNameData.get(skinIndex, {}).get("name")
                
                if skinNameData.get(skinIndex, {}).get("name"):
                    skin_name_en = skinNameData.get(skinIndex, {}).get("name")
            except:
                print(traceback.format_exc())
            
            assetData["name"] = skin_name
            assetData["en_name"] = skin_name_en

            print("assetdata", assetData)

            item.setData(skinIndex, Qt.ItemDataRole.EditRole)
            item.setData(assetData, Qt.ItemDataRole.UserRole)

            # Set to use first asset as a fallback
            key = TSHGameAssetManager.instance.biggestCompletePack
            asset = None
            
            if assetData["assets"].get(key): asset = assetData["assets"][key]
            elif assetData["assets"].get("full"): asset = assetData["assets"]["full"]
            elif assetData["assets"].get("base_files/icon"): asset = assetData["assets"]["base_files/icon"]

            if asset:
                pix = QPixmap.fromImage(QImage(asset["asset"]))
            else:
                pix = QPixmap.fromImage(QImage("./assets/icons/cancel.svg").scaled(16,16))

            targetW = 128
            targetH = 96

            originalW = pix.width()
            originalH = pix.height()

            proportional_zoom = 1
            
            if asset.get("average_size"):
                proportional_zoom = 0
                proportional_zoom = max(
                    proportional_zoom,
                    (targetW / asset.get("average_size", {}).get("x", 0)) * 1.2
                )
                proportional_zoom = max(
                    proportional_zoom,
                    (targetH / asset.get("average_size", {}).get("y", 0)) * 1.2
                )
            
            # For cropped assets, zoom to fill
            # Calculate max zoom
            zoom_x = targetW / originalW
            zoom_y = targetH / originalH

            minZoom = 1
            rescalingFactor = 1
            customZoom = 1

            if asset.get("rescaling_factor"):
                rescalingFactor = asset.get("rescaling_factor")

            uncropped_edge = asset.get("uncropped_edge", [])

            if not uncropped_edge or len(uncropped_edge) == 0:
                if zoom_x > zoom_y:
                    minZoom = zoom_x
                else:
                    minZoom = zoom_y
            else:
                if (
                    "u" in uncropped_edge and
                    "d" in uncropped_edge and
                    "l" in uncropped_edge and
                    "r" in uncropped_edge
                    ):
                    customZoom = 1.2 # Add zoom in for uncropped assets
                    minZoom = customZoom * proportional_zoom * rescalingFactor
                elif (
                    not "l" in uncropped_edge and
                    not "r" in uncropped_edge
                    ):
                    minZoom = zoom_x
                elif (
                    not "u" in uncropped_edge and
                    not "d" in uncropped_edge
                    ):
                    minZoom = zoom_y;
                else:
                    minZoom = customZoom * proportional_zoom * rescalingFactor

            zoom = max(minZoom, customZoom * minZoom);

            # Centering
            xx = 0
            yy = 0

            eyesight = asset.get("eyesight")

            if not eyesight:
                eyesight = {
                    "x": originalW / 2,
                    "y": originalH / 2
                }

            xx = -eyesight["x"] * zoom + targetW / 2

            maxMoveX = targetW - originalW * zoom;

            if not uncropped_edge or not "l" in uncropped_edge:
                if (xx > 0): xx = 0
            
            if not uncropped_edge or not "r" in uncropped_edge:
                if (xx < maxMoveX): xx = maxMoveX

            yy = -eyesight["y"] * zoom + targetH / 2

            maxMoveY = targetH - originalH * zoom;

            if not uncropped_edge or not "u" in uncropped_edge:
                if (yy > 0): yy = 0
            
            if not uncropped_edge or not "d" in uncropped_edge:
                if (yy < maxMoveY): yy = maxMoveY
            
            newImg = QImage(QSize(128, 96), QImage.Format.Format_RGBA64)
            newImg.fill(QColor(0, 0, 0, 0))
            painter = QPainter()
            painter.begin(newImg)

            painter.drawPixmap(
                int(xx),
                int(yy),
                pix.scaled(
                    int(originalW*zoom),
                    int(originalH*zoom),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            painter.end()

            pix = QPixmap.fromImage(newImg)

            item.setIcon(
                QIcon(pix)
            )
            skinModel.appendRow(item)

        target.setModel(skinModel)

    def ReloadCharacters(self):
        for c in self.character_elements:
            c[1].setModel(TSHScoreboardPlayerWidget.characterModel)
            c[1].setIconSize(QSize(24, 24))
            c[1].setFixedHeight(32)

    def SetupAutocomplete(self):
        if TSHPlayerDB.model:
            self.findChild(QLineEdit, "name").setCompleter(QCompleter())
            self.findChild(QLineEdit, "name").completer().activated[QModelIndex].connect(
                lambda x: self.SetData(x.data(Qt.ItemDataRole.UserRole)), Qt.QueuedConnection)
            self.findChild(QLineEdit, "name").completer().setCaseSensitivity(
                Qt.CaseSensitivity.CaseInsensitive)
            self.findChild(QLineEdit, "name").completer(
            ).setFilterMode(Qt.MatchFlag.MatchContains)
            self.findChild(QLineEdit, "name").completer().setModel(
                TSHPlayerDB.model)

            self.ManageSavePlayerToDBText()
            self.ManageDeletePlayerFromDBActive()

    def SetData(self, data, dontLoadFromDB=False, clear=True):
        StateManager.BlockSaving()

        if clear:
            self.Clear()

        # Load player data from DB; will be overwriten by incoming data
        if not dontLoadFromDB and clear:
            tag = data.get(
                "prefix")+" "+data.get("gamerTag") if data.get("prefix") else data.get("gamerTag")

            for i in range(TSHPlayerDB.model.rowCount()):
                item = TSHPlayerDB.model.item(i).data(Qt.ItemDataRole.UserRole)

                dbTag = item.get(
                    "prefix")+" "+item.get("gamerTag") if item.get("prefix") else item.get("gamerTag")

                if tag == dbTag:
                    self.SetData(item, dontLoadFromDB=True)

        if data.get("gamerTag"):
            self.findChild(QWidget, "name").setText(f'{data.get("gamerTag")}')
            self.findChild(QWidget, "name").editingFinished.emit()

        if data.get("prefix"):
            self.findChild(QWidget, "team").setText(f'{data.get("prefix")}')
            self.findChild(QWidget, "team").editingFinished.emit()

        if data.get("name"):
            self.findChild(QWidget, "real_name").setText(f'{data.get("name")}')
            self.findChild(QWidget, "real_name").editingFinished.emit()

        if data.get("avatar"):
            self.ExportPlayerImages(data.get("avatar"))

        if data.get("id"):
            self.ExportPlayerId(data.get("id"))

        if data.get("twitter"):
            self.findChild(QWidget, "twitter").setText(
                f'{data.get("twitter")}')
            self.findChild(QWidget, "twitter").editingFinished.emit()

        if data.get("pronoun"):
            self.findChild(QWidget, "pronoun").setText(
                f'{data.get("pronoun")}')
            self.findChild(QWidget, "pronoun").editingFinished.emit()

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
            countryElement.setCurrentIndex(countryIndex)

        if data.get("state_code"):
            countryElement: QComboBox = self.findChild(
                QComboBox, "country")
            stateElement: QComboBox = self.findChild(QComboBox, "state")
            stateIndex = 0
            for i in range(stateElement.model().rowCount()):
                item = stateElement.model().item(i).data(Qt.ItemDataRole.UserRole)
                if item:
                    if data.get("state_code") == item.get("code"):
                        stateIndex = i
                        break
            stateElement.setCurrentIndex(stateIndex)

        if data.get("mains"):
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
                        characterIndex = 0
                        for i in range(character_element.model().rowCount()):
                            item = character_element.model().item(i).data(Qt.ItemDataRole.UserRole)
                            if item:
                                if item.get("en_name") == main[0]:
                                    characterIndex = i
                                    break
                        character_element.setCurrentIndex(characterIndex)
                        if len(main) > 1:
                            color_element.setCurrentIndex(int(main[1]))
                        else:
                            color_element.setCurrentIndex(0)
        
        if data.get("seed"):
            StateManager.Set(f"{self.path}.seed", data.get("seed"))
                            
        StateManager.ReleaseSaving()

    def GetCurrentPlayerTag(self):
        gamerTag = self.findChild(QWidget, "name").text()
        prefix = self.findChild(QWidget, "team").text()
        return prefix+" "+gamerTag if prefix else gamerTag

    def SavePlayerToDB(self):
        tag = self.GetCurrentPlayerTag()

        playerData = {
            "prefix": self.findChild(QWidget, "team").text(),
            "gamerTag": self.findChild(QWidget, "name").text(),
            "name": self.findChild(QWidget, "real_name").text(),
            "twitter": self.findChild(QWidget, "twitter").text(),
            "pronoun": self.findChild(QWidget, "pronoun").text()
        }

        if TSHGameAssetManager.instance.selectedGame.get("codename"):
            mains = []

            for i, (element, character, color) in enumerate(self.character_elements):
                data = {}

                if character.currentData() is not None:
                    data["name"] = character.currentData().get("en_name")
                else:
                    data["name"] = ""

                data["skin"] = color.currentText()

                if data["skin"] == None:
                    data["skin"] = 0

                if data["name"] != "":
                    mains.append([data.get("name"), data.get("skin")])

            playerData["mains"] = {
                TSHGameAssetManager.instance.selectedGame.get("codename"): mains
            }

        if self.findChild(QComboBox, "country").currentData(Qt.ItemDataRole.UserRole):
            playerData["country_code"] = self.findChild(
                QComboBox, "country").currentData(Qt.ItemDataRole.UserRole).get("code")

        if self.findChild(QComboBox, "state").currentData(Qt.ItemDataRole.UserRole):
            playerData["state_code"] = self.findChild(
                QComboBox, "state").currentData(Qt.ItemDataRole.UserRole).get("code")

        TSHPlayerDB.AddPlayers([playerData], overwrite=True)

        if playerData["pronoun"] not in self.pronoun_list:
            with open("./user_data/pronouns_list.txt", 'at') as pronouns_file:
                pronouns_file.write(playerData["pronoun"] + "\n")
                self.pronoun_list.append(playerData["pronoun"])
                self.pronoun_model.setStringList(self.pronoun_list)

    def ManageSavePlayerToDBText(self):
        tag = self.GetCurrentPlayerTag()

        if tag in TSHPlayerDB.database:
            self.save_bt.setText(
                QApplication.translate("app", "Update player"))
        else:
            self.save_bt.setText(
                QApplication.translate("app", "Save new player"))

    def ManageDeletePlayerFromDBActive(self):
        tag = self.GetCurrentPlayerTag()

        if tag in TSHPlayerDB.database:
            self.delete_bt.setEnabled(True)
        else:
            self.delete_bt.setEnabled(False)

    def DeletePlayerFromDB(self):
        tag = self.GetCurrentPlayerTag()
        TSHPlayerDB.DeletePlayer(tag)

    def Clear(self):
        for c in self.findChildren(QLineEdit):
            c.setText("")
            c.editingFinished.emit()

        for c in self.findChildren(QComboBox):
            c.setCurrentIndex(0)


TSHGameAssetManager.instance.signals.onLoad.connect(
    TSHScoreboardPlayerWidget.LoadCharacters)
