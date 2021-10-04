from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import shutil
import tarfile
import py7zr

import requests
import urllib
import json
import traceback
import sys
import time
import os

import csv

import copy

from collections import Counter

import unicodedata

from Workers import *


def removeFileIfExists(file):
    if os.path.exists(file):
        try:
            os.remove(file)
        except Exception as e:
            print(traceback.format_exc())


class PlayerColumnSignals(QObject):
    UpdatePlayer = pyqtSignal(object)
    UpdateCharacter = pyqtSignal(object)


class PlayerColumn():
    def __init__(self, parent, id, inverted=False):
        super().__init__()

        self.signals = PlayerColumnSignals()
        self.signals.UpdatePlayer.connect(self.SetFromPlayerObj)
        self.signals.UpdateCharacter.connect(self.UpdateCharacterFromSetData)

        self.parent = parent
        self.id = id

        self.group_box = QGroupBox()
        self.group_box.setStyleSheet("QGroupBox{padding:0px;}")
        self.group_box.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.group_box.setContentsMargins(QMargins(0, 0, 0, 0))

        self.layout_grid = QGridLayout()
        self.group_box.setLayout(self.layout_grid)
        self.layout_grid.setVerticalSpacing(0)

        self.group_box.setFont(self.parent.font_small)

        self.titleLabel = QLabel("Player "+str(self.id))
        self.titleLabel.setFont(self.parent.font_small)
        self.layout_grid.addWidget(self.titleLabel, 0, 0, 1, 2)

        self.losersCheckbox = QCheckBox("Losers")
        self.losersCheckbox.setFont(self.parent.font_small)
        self.layout_grid.addWidget(
            self.losersCheckbox, 0, 3, 1, 2, Qt.AlignmentFlag.AlignRight)
        self.losersCheckbox.stateChanged.connect(self.NameChanged)

        pos_labels = 0
        pos_forms = 1
        text_alignment = Qt.AlignRight | Qt.AlignVCenter

        if inverted:
            pos_labels = 1
            pos_forms = 0
            text_alignment = Qt.AlignLeft | Qt.AlignVCenter

        nick_label = QLabel("Player")
        nick_label.setFont(self.parent.font_small)
        nick_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(nick_label, 1, pos_labels)
        self.player_name = QLineEdit()
        self.layout_grid.addWidget(self.player_name, 1, pos_forms)
        self.player_name.setMinimumWidth(100)
        self.player_name.setFont(self.parent.font_small)
        self.player_name.textChanged.connect(self.NameChanged)

        prefix_label = QLabel("Prefix")
        prefix_label.setFont(self.parent.font_small)
        prefix_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(prefix_label, 2, pos_labels)
        self.player_org = QLineEdit()
        self.layout_grid.addWidget(self.player_org, 2, pos_forms)
        self.player_org.setFont(self.parent.font_small)
        self.player_org.textChanged.connect(self.NameChanged)
        self.player_org.setMinimumWidth(100)
        self.NameChanged()

        real_name_label = QLabel("Name")
        real_name_label.setFont(self.parent.font_small)
        real_name_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(real_name_label, 3, pos_labels)
        self.player_real_name = QLineEdit()
        self.layout_grid.addWidget(self.player_real_name, 3, pos_forms)
        self.player_real_name.setFont(self.parent.font_small)
        self.player_real_name.textChanged.connect(self.RealNameChanged)
        self.RealNameChanged()
        self.player_real_name.setMinimumWidth(100)

        player_twitter_label = QLabel("Twitter")
        player_twitter_label.setFont(self.parent.font_small)
        player_twitter_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_twitter_label, 4, pos_labels)
        self.player_twitter = QLineEdit()
        self.layout_grid.addWidget(self.player_twitter, 4, pos_forms)
        self.player_twitter.setFont(self.parent.font_small)
        self.player_twitter.textChanged.connect(self.TwitterChanged)
        self.TwitterChanged()
        self.player_twitter.setMinimumWidth(100)

        location_layout = QHBoxLayout()
        self.layout_grid.addLayout(location_layout, 1, pos_forms+2)

        player_country_label = QLabel("Location")
        player_country_label.setFont(self.parent.font_small)
        player_country_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_country_label, 1, pos_labels+2)
        self.player_country = QComboBox()
        self.player_country.addItem("")
        for i, country_code in enumerate(self.parent.countries.keys()):
            item = self.player_country.addItem(QIcon("assets/country_flag/"+country_code.lower(
            )+".png"), self.parent.countries[country_code]["name"]+" ("+country_code+")")
            self.player_country.setItemData(i+1, country_code)
        self.player_country.setEditable(True)
        location_layout.addWidget(self.player_country)
        self.player_country.setMinimumWidth(80)
        self.player_country.setFont(self.parent.font_small)
        self.player_country.lineEdit().setFont(self.parent.font_small)
        self.player_country.currentIndexChanged.connect(self.CountryChanged)
        self.player_country.currentIndexChanged.connect(self.LoadStateOptions)
        self.CountryChanged()
        self.player_country.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.player_country.view().setMinimumWidth(300)
        self.player_country.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.player_country.completer().popup().setMinimumWidth(300)

        self.player_state = QComboBox()
        self.player_state.setEditable(True)
        location_layout.addWidget(self.player_state)
        self.player_state.setMinimumWidth(80)
        self.player_state.setFont(self.parent.font_small)
        self.player_state.lineEdit().setFont(self.parent.font_small)
        self.player_state.activated.connect(self.StateChanged)
        self.StateChanged()
        self.player_state.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.player_state.view().setMinimumWidth(300)
        self.player_state.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.player_state.completer().popup().setMinimumWidth(300)

        player_character_label = QLabel("Character")
        player_character_label.setFont(self.parent.font_small)
        player_character_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_character_label, 2, pos_labels+2)
        self.player_character = QComboBox()
        self.player_character.setEditable(True)
        self.layout_grid.addWidget(self.player_character, 2, pos_forms+2)
        self.player_character.activated.connect(self.LoadSkinOptions)
        self.player_character.setMinimumWidth(120)
        self.player_character.setFont(self.parent.font_small)
        self.player_character.lineEdit().setFont(self.parent.font_small)
        self.player_character.activated.connect(self.CharacterChanged)
        self.player_character.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.player_character.view().setMinimumWidth(250)
        self.player_character.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.player_character.completer().popup().setMinimumWidth(250)

        player_character_color_label = QLabel("Skin")
        player_character_color_label.setFont(self.parent.font_small)
        player_character_color_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(
            player_character_color_label, 3, pos_labels+2)
        self.player_character_color = QComboBox()
        self.layout_grid.addWidget(
            self.player_character_color, 3, pos_forms+2, 2, 1)
        self.player_character_color.setIconSize(QSize(48, 48))
        self.player_character_color.setMinimumHeight(48)
        self.player_character_color.setMinimumWidth(120)
        self.player_character_color.setFont(self.parent.font_small)
        self.player_character_color.activated.connect(self.CharacterChanged)
        self.CharacterChanged()

        bottom_buttons_layout = QHBoxLayout()
        self.layout_grid.addLayout(bottom_buttons_layout, 5, 0, 1, -1)

        self.save_bt = QPushButton("Save new player")
        self.save_bt.setFont(self.parent.font_small)
        self.save_bt.setIcon(QIcon('icons/save.svg'))
        bottom_buttons_layout.addWidget(self.save_bt)
        self.save_bt.clicked.connect(self.SavePlayerToDB)
        self.player_name.textChanged.connect(
            self.ManageSavePlayerToDBText)
        self.player_org.textChanged.connect(
            self.ManageSavePlayerToDBText)

        self.delete_bt = QPushButton("Delete player entry")
        self.delete_bt.setFont(self.parent.font_small)
        self.delete_bt.setIcon(QIcon('icons/cancel.svg'))
        bottom_buttons_layout.addWidget(self.delete_bt)
        self.delete_bt.setEnabled(False)
        self.player_name.textChanged.connect(
            self.ManageDeletePlayerFromDBActive)
        self.player_org.textChanged.connect(
            self.ManageDeletePlayerFromDBActive)
        self.delete_bt.clicked.connect(self.DeletePlayerFromDB)

        self.clear_bt = QPushButton("Clear")
        self.clear_bt.setFont(self.parent.font_small)
        self.clear_bt.setIcon(QIcon('icons/undo.svg'))
        bottom_buttons_layout.addWidget(self.clear_bt)
        self.clear_bt.clicked.connect(self.Clear)

        self.LoadCharacters()

    def LoadCharacters(self):
        self.player_character.clear()
        self.player_character.addItem("")
        for c in self.parent.stockIcons:
            self.player_character.addItem(
                QIcon(QPixmap.fromImage(self.parent.stockIcons[c][0]).scaledToWidth(32, Qt.TransformationMode.SmoothTransformation)), c)
        self.player_character_color.setIconSize(QSize(32, 32))
        self.player_character.setCurrentIndex(0)
        self.player_character_color.clear()

    def Clear(self):
        self.player_name.clear()
        self.player_org.clear()
        self.player_country.setCurrentIndex(0)
        self.player_state.setCurrentIndex(0)
        self.player_character.setCurrentIndex(0)
        self.player_character_color.clear()
        self.player_twitter.clear()
        self.player_real_name.clear()
        self.StateChanged()
        self.CharacterChanged()
        self.ExportState()

    def SavePlayerToDB(self):
        key = (self.player_org.text()+" " if self.player_org.text()
               != "" else "") + self.player_name.text()
        if key == "":
            return
        skin = int(self.player_character_color.currentText()
                   ) if self.player_character_color.currentText() != "" else 0
        self.parent.local_players[key] = {
            "country_code": self.parent.programState['p'+str(self.id)+'_country'],
            "full_name": self.player_real_name.text(),
            "mains": [self.player_character.currentText()],
            "name": self.player_name.text(),
            "org": self.player_org.text(),
            "state": self.parent.programState['p'+str(self.id)+'_state'],
            "twitter": self.player_twitter.text(),
            "skins": {
                self.player_character.currentText(): skin
            }
        }
        self.parent.SaveDB()
        self.ManageDeletePlayerFromDBActive()
        self.ManageSavePlayerToDBText()

    def ManageSavePlayerToDBText(self):
        key = (self.player_org.text()+" " if self.player_org.text()
               != "" else "") + self.player_name.text()
        if key in self.parent.local_players:
            self.save_bt.setText("Update player entry")
        else:
            self.save_bt.setText("Save new player")

    def ManageDeletePlayerFromDBActive(self):
        key = (self.player_org.text()+" " if self.player_org.text()
               != "" else "") + self.player_name.text()
        if key in self.parent.local_players:
            self.delete_bt.setEnabled(True)
        else:
            self.delete_bt.setEnabled(False)

    def DeletePlayerFromDB(self):
        key = (self.player_org.text()+" " if self.player_org.text()
               != "" else "") + self.player_name.text()
        if key in self.parent.local_players:
            del self.parent.local_players[key]
        self.parent.SaveDB()
        self.ManageDeletePlayerFromDBActive()
        self.ManageSavePlayerToDBText()

    def LoadSkinOptions(self, text=None):
        self.player_character_color.clear()
        for c in sorted(self.parent.skins.get(self.player_character.currentText(), [])):
            if self.parent.portraits.get(self.player_character.currentText()).get(c) is not None:
                self.player_character_color.addItem(QIcon(QPixmap.fromImage(self.parent.portraits.get(
                    self.player_character.currentText()).get(c).scaledToWidth(48, Qt.TransformationMode.SmoothTransformation))), str(c))
            else:
                self.player_character_color.addItem(QIcon(QPixmap.fromImage(self.parent.stockIcons.get(
                    self.player_character.currentText()).get(c).scaledToWidth(48, Qt.TransformationMode.SmoothTransformation))), str(c))
        self.player_character_color.setIconSize(QSize(48, 48))
        self.player_character_color.repaint()

    def LoadStateOptions(self, text):
        self.player_state.clear()
        self.player_state.addItem("")

        index = self.player_country.currentIndex()-1

        try:
            if index > 0:
                states = list(self.parent.countries.values())[index]["states"]
                for s in list(states.values()):
                    self.player_state.addItem(QIcon(
                        f"./assets/state_flag/{list(self.parent.countries.keys())[index]}/{s['state_code']}.png"), str(s["state_name"]+" ("+s["state_code"]+")"))
        except Exception as e:
            print(traceback.format_exc())

        self.player_state.setCurrentIndex(0)
        self.StateChanged()
        self.player_state.repaint()

    def NameChanged(self):
        self.parent.programState['p'+str(self.id) +
                                 '_losers'] = self.losersCheckbox.isChecked()
        self.parent.programState['p' +
                                 str(self.id)+'_name'] = self.player_name.text()
        self.parent.programState['p'+str(self.id)+'_name_org'] = \
            (self.player_org.text()+" | "+self.player_name.text()) if len(self.player_org.text()) > 0 else \
            (self.player_name.text())
        self.parent.programState['p' +
                                 str(self.id)+'_org'] = self.player_org.text()

        if self.parent.settings.get("autosave") == True:
            self.parent.ExportProgramState()
            self.ExportName()

    def ExportName(self):
        losers = " [L]" if self.losersCheckbox.isChecked() else ""

        if 'p'+str(self.id)+'_name' in self.parent.programStateDiff or \
                'p'+str(self.id)+'_losers' in self.parent.programStateDiff:
            with open('out/p'+str(self.id)+'_name.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(self.player_name.text()+losers)

        if 'p'+str(self.id)+'_name_org' in self.parent.programStateDiff or \
                'p'+str(self.id)+'_losers' in self.parent.programStateDiff:
            with open('out/p'+str(self.id)+'_name+prefix.txt', 'w', encoding='utf-8') as outfile:
                if len(self.player_org.text()) > 0:
                    outfile.write(self.player_org.text()+" | " +
                                  self.player_name.text()+losers)
                else:
                    outfile.write(self.player_name.text()+losers)

        if 'p'+str(self.id)+'_org' in self.parent.programStateDiff:
            with open('out/p'+str(self.id)+'_prefix.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(self.player_org.text())
            removeFileIfExists('out/p'+str(self.id)+'_sponsor.png')
            if os.path.exists("./sponsor_logos/"+self.player_org.text().lower()+".png"):
                shutil.copy(
                    "./sponsor_logos/"+self.player_org.text().lower()+".png",
                    "out/p"+str(self.id)+"_sponsor.png"
                )

    def RealNameChanged(self):
        self.parent.programState['p'+str(self.id) +
                                 '_real_name'] = self.player_real_name.text()
        if self.parent.settings.get("autosave") == True:
            self.parent.ExportProgramState()
            self.ExportRealName()

    def ExportRealName(self):
        if 'p'+str(self.id)+'_real_name' in self.parent.programStateDiff:
            with open('out/p'+str(self.id)+'_real_name.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(self.player_real_name.text())

    def TwitterChanged(self):
        tt = ""
        if self.player_twitter.text() != "":
            if self.parent.settings.get("twitter_add_at") == True:
                tt = "@"
        tt += self.player_twitter.text()

        self.parent.programState['p'+str(self.id)+'_twitter'] = tt

        if self.parent.settings.get("autosave") == True:
            self.parent.ExportProgramState()
            self.ExportTwitter()

    def ExportTwitter(self):
        if 'p'+str(self.id)+'_twitter' in self.parent.programStateDiff:
            with open('out/p'+str(self.id)+'_twitter.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(
                    self.parent.programState['p'+str(self.id)+'_twitter'])

    def ExportSmashGGAvatar(self):
        if "p"+str(self.id)+"_smashgg_id" in self.parent.programStateDiff:
            try:
                self.parent.saveMutex.lock()

                def myFun(self, progress_callback):
                    if self.player_obj.get("smashgg_image", None) is not None:
                        r = requests.get(
                            self.player_obj["smashgg_image"], stream=True)
                        if r.status_code == 200:
                            with open('out/p'+str(self.id)+'_smashgg_avatar.png', 'wb') as f:
                                r.raw.decode_content = True
                                shutil.copyfileobj(r.raw, f)
                                f.flush()
                    else:
                        removeFileIfExists(
                            'out/p'+str(self.id)+'_smashgg_avatar.png')

                worker = Worker(myFun, *{self})
                self.parent.threadpool.start(worker)
            except Exception as e:
                print(traceback.format_exc())
            finally:
                self.parent.saveMutex.unlock()

    def CountryChanged(self):
        try:
            index = self.player_country.currentIndex()-1
            assert index >= 0

            country = list(self.parent.countries.keys())[index]

            self.parent.programState['p'+str(self.id)+'_country'] = country
            self.parent.programState['p'+str(
                self.id)+'_country_name'] = self.parent.countries[country]["name"]
        except Exception as e:
            self.parent.programState['p'+str(self.id) +
                                     '_country'] = self.player_country.currentText()
            self.parent.programState['p'+str(self.id) +
                                     '_country_name'] = self.player_country.currentText()

        if self.parent.settings.get("autosave") == True:
            self.parent.ExportProgramState()
            self.ExportCountry()

    def ExportCountry(self):
        if 'p'+str(self.id)+'_country' in self.parent.programStateDiff:
            try:
                removeFileIfExists("out/p"+str(self.id)+"_country_flag.png")
                removeFileIfExists("out/p"+str(self.id)+"_country.txt")

                with open('out/p'+str(self.id)+'_country.txt', 'w', encoding='utf-8') as outfile:
                    outfile.write(
                        self.parent.programState['p'+str(self.id)+'_country'])

                with open('out/p'+str(self.id)+'_country_name.txt', 'w', encoding='utf-8') as outfile:
                    outfile.write(
                        self.parent.programState['p'+str(self.id)+'_country_name'])

                if self.player_country.currentText().lower() != "":
                    shutil.copy(
                        "assets/country_flag/" +
                        self.parent.programState['p' +
                                                 str(self.id)+'_country'].lower()+".png",
                        "out/p"+str(self.id)+"_country_flag.png"
                    )
            except Exception as e:
                print(traceback.format_exc())

    def StateChanged(self):
        try:
            countryIndex = self.player_country.currentIndex()-1
            index = self.player_state.currentIndex()-1

            assert index >= 0

            country = list(self.parent.countries.values())[countryIndex]
            state = list(country["states"].values())[index]

            self.parent.programState['p' +
                                     str(self.id)+'_state'] = state["state_code"]
            self.parent.programState['p' +
                                     str(self.id)+'_state_name'] = state["state_name"]
        except Exception as e:
            self.parent.programState['p'+str(self.id) +
                                     '_state'] = self.player_state.currentText()
            self.parent.programState['p'+str(self.id) +
                                     '_state_name'] = self.player_state.currentText()

        if self.parent.settings.get("autosave") == True:
            self.parent.ExportProgramState()
            self.ExportState()

    def ExportState(self):
        if 'p'+str(self.id)+'_state' in self.parent.programStateDiff:
            try:
                removeFileIfExists("out/p"+str(self.id)+"_state_flag.png")
                removeFileIfExists("out/p"+str(self.id)+"_state.txt")

                with open('out/p'+str(self.id)+'_state.txt', 'w', encoding='utf-8') as outfile:
                    outfile.write(
                        self.parent.programState['p'+str(self.id)+'_state'])

                with open('out/p'+str(self.id)+'_state_name.txt', 'w', encoding='utf-8') as outfile:
                    outfile.write(
                        self.parent.programState['p'+str(self.id)+'_state_name'])

                if self.player_country.currentText().lower() != "":
                    shutil.copy(
                        "assets/state_flag/" +
                        self.parent.programState['p'+str(self.id)+'_country'].upper()+"/" +
                        self.parent.programState['p' +
                                                 str(self.id)+'_state'].upper()+".png",
                        "out/p"+str(self.id)+"_state_flag.png"
                    )
            except Exception as e:
                print(traceback.format_exc())

    def CharacterChanged(self):
        self.parent.programState['p'+str(self.id) +
                                 '_character'] = self.player_character.currentText()
        self.parent.programState['p'+str(self.id)+'_character_codename'] = self.parent.characters.get(
            self.player_character.currentText(), {}).get("codename")
        self.parent.programState['p'+str(
            self.id)+'_character_color'] = self.player_character_color.currentText()

        gameId = None

        if self.parent.games is not None and len(self.parent.games) > 0:
            if self.parent.gameSelect.currentIndex() > 0:
                game = self.parent.gameSelect.currentIndex()-1
                gameId = list(self.parent.games.keys())[game]

        self.parent.programState['p'+str(self.id)+'_assets_path'] = {}

        if gameId is not None:
            for assetKey in list(self.parent.games.values())[self.parent.gameSelect.currentIndex()-1].get("assets", {}):
                try:
                    asset = self.parent.games[gameId]["assets"][assetKey]
                    assetPath = './assets/games/'+gameId+'/'+assetKey+'/'

                    characterAssets = []

                    if self.parent.characters.get(self.player_character.currentText()):
                        baseName = asset.get("prefix", "")+self.parent.characters.get(
                            self.player_character.currentText(), {}).get("codename")+asset.get("postfix", "")
                        charFiles = [f for f in os.listdir(
                            assetPath) if f.startswith(baseName)]
                        characterAssets = {}
                        for f in charFiles:
                            skin = f[len(baseName):]
                            skin = skin.rsplit(".", 1)[0]
                            if skin == "":
                                skin = 0
                            else:
                                skin = int(skin)
                            characterAssets[str(skin)] = f
                        print(characterAssets)

                    if len(characterAssets) > 0:
                        color = "0"
                        if str(self.player_character_color.currentIndex()) in characterAssets:
                            color = str(
                                self.player_character_color.currentIndex())
                        else:
                            remap = asset.get("skin_mapping", {}).get(self.parent.characters.get(
                                self.player_character.currentText(), {"codename": ""})["codename"], None)
                            if remap and str(self.player_character_color.currentIndex()) in remap:
                                color = str(
                                    remap[str(self.player_character_color.currentIndex())])

                        self.parent.programState['p'+str(
                            self.id)+'_assets_path'][assetKey] = assetPath+"/"+characterAssets[color]
                except Exception as e:
                    print(traceback.format_exc())

        if self.parent.settings.get("autosave") == True:
            self.parent.ExportProgramState()
            self.ExportCharacter()

    def ExportCharacter(self):
        print(self.parent.programStateDiff)
        if 'p'+str(self.id)+'_character' in self.parent.programStateDiff or 'p'+str(self.id)+'_character_color' in self.parent.programStateDiff:
            self.parent.saveMutex.lock()

            oldCharacterAssets = [f for f in os.listdir(
                "./out") if f.startswith("p"+str(self.id)+"_character_")]
            for f in oldCharacterAssets:
                removeFileIfExists("out/"+f)

            characterAssets = self.parent.programState['p' +
                                                       str(self.id)+'_assets_path']

            if len(characterAssets) > 0:
                for assetKey in characterAssets:
                    try:
                        shutil.copy(
                            characterAssets[assetKey],
                            "./out/p"+str(self.id)+"_character_"+assetKey.split(
                                "/")[-1]+"."+characterAssets[assetKey].rsplit(".", 1)[1]
                        )
                    except Exception as e:
                        print(traceback.format_exc())
            self.parent.saveMutex.unlock()

    def AutocompleteSelected(self, selected):
        if type(selected) == QModelIndex:
            index = int(selected.sibling(selected.row(), 2).data())
        elif type(selected) == int:
            index = selected-1
            if index < 0:
                index = None
        else:
            index = None

        if index is not None:
            self.selectPRPlayer(index)

    def selectPRPlayer(self, index):
        player = self.parent.mergedPlayers[index]
        self.SetFromPlayerObj(player)

    def SetFromPlayerObj(self, player):
        print("Set from player obj")
        self.player_name.setText(player["name"])
        self.player_org.setText(player.get("org", ""))
        self.player_real_name.setText(player.get("full_name", ""))
        self.player_twitter.setText(player.get("twitter", ""))

        self.player_obj = player

        print("Set country")
        if player.get("country_code") is not None and \
                player.get("country_code") != "null" and \
                player.get("country_code") != "":
            country_index = 0
            if player.get("country_code") in list(self.parent.countries.keys()):
                country_index = list(self.parent.countries.keys()).index(
                    player.get("country_code"))+1
            self.player_country.setCurrentIndex(country_index)
            self.LoadStateOptions(player.get("country_code"))
            if player.get("state") is not None and player.get("state") != "null":
                state_index = 0
                states = list(self.parent.countries[player.get(
                    "country_code")]["states"].keys())
                if player.get("state") in states:
                    state_index = states.index(player.get("state"))+1

                self.player_state.setCurrentIndex(state_index)
            else:
                self.player_state.setCurrentIndex(0)
        else:
            self.player_country.setCurrentIndex(0)

        self.StateChanged()

        print("Set main")
        if player.get("mains") is not None and len(player["mains"]) > 0 and player["mains"][0] != "" and \
                player.get("mains", [""])[0] in self.parent.stockIcons:
            self.player_character.setCurrentIndex(
                list(self.parent.stockIcons.keys()).index(player.get("mains", [""])[0])+1)

            self.LoadSkinOptions(player.get("mains", [""])[0])

            print("Set skin")
            if player.get("skins") is not None and player["mains"][0] in player.get("skins"):
                self.player_character_color.setCurrentIndex(
                    player["skins"][player["mains"][0]])
            else:
                self.player_character_color.setCurrentIndex(0)
        elif "Random Character" in self.parent.stockIcons:
            self.player_character.setCurrentIndex(
                list(self.parent.stockIcons.keys()).index("Random Character")+1)
            self.LoadSkinOptions("Random Character")
            self.player_character_color.setCurrentIndex(0)

        self.CharacterChanged()

        print("Update Smashgg Avatar")
        self.parent.programState["p"+str(self.id) +
                                 "_smashgg_id"] = player.get("smashgg_id", None)

        self.ExportSmashGGAvatar()

    def UpdateCharacterFromSetData(self, data):
        print("Character change")
        if data in list(self.parent.stockIcons.keys()):
            self.player_character.setCurrentIndex(
                list(self.parent.stockIcons.keys()).index(data)+1)
            self.LoadSkinOptions(data)
            self.player_character_color.setCurrentIndex(0)
        else:
            self.player_character.setCurrentText(data)
            self.LoadSkinOptions()
            self.player_character_color.setCurrentIndex(0)

        self.CharacterChanged()

    def selectPRPlayerBySmashGGId(self, smashgg_id):
        index = next((i for i, p in enumerate(self.parent.allplayers["players"]) if str(
            p.get("smashgg_id", None)) == smashgg_id), None)
        if index is not None:
            self.selectPRPlayer(index)
