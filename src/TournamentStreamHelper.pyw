#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from TSHCommentaryWidget import TSHCommentaryWidget
from TSHGameAssetManager import TSHGameAssetManager


try:
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
    import threading
    import re

    import csv

    import copy

    from collections import Counter

    import unicodedata

    from PlayerColumn import *
    from Workers import *
    from TSHScoreboardWidget import *
except ImportError as error:
    print(error)
    print("Couldn't find all needed libraries. Please run 'install_requirements.bat' on Windows or 'sudo pip3 install -r requirements.txt' on Linux")
    exit()

#sys.stderr = open('./log_error.txt', 'w')


def remove_accents_lower(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


class WindowSignals(QObject):
    StopTimer = pyqtSignal()
    ExportStageStrike = pyqtSignal(object)
    DetectGame = pyqtSignal(int)
    SetupAutocomplete = pyqtSignal()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.signals = WindowSignals()
        self.signals.StopTimer.connect(self.StopTimer)
        self.signals.ExportStageStrike.connect(self.ExportStageStrike)
        self.signals.DetectGame.connect(self.DetectGameFromId)
        self.signals.SetupAutocomplete.connect(self.SetupAutocomplete)

        splash = QSplashScreen(self, QPixmap(
            'icons/icon.png').scaled(128, 128))
        splash.show()

        time.sleep(0.1)

        App.processEvents()

        self.programState = {}
        self.savedProgramState = {}
        self.programStateDiff = {}

        self.setWindowIcon(QIcon('icons/icon.png'))

        if not os.path.exists("out/"):
            os.mkdir("out/")

        if not os.path.exists("assets/games"):
            os.mkdir("assets/games")

        f = open('powerrankings_to_smashgg.json', encoding='utf-8')
        self.powerrankings_to_smashgg = json.load(f)

        # try:
        #     url = 'https://api.smash.gg/characters'
        #     r = requests.get(url, allow_redirects=True)
        #     open('./assets/characters.json', 'wb').write(r.content)
        # except Exception as e:
        #     print("Could not update /assets/characters.json: "+str(e))

        # f = open('assets/characters.json', encoding='utf-8')
        # self.smashgg_character_data = json.load(f)["entities"]

        # try:
        #     url = 'https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/countries%2Bstates%2Bcities.json'
        #     r = requests.get(url, allow_redirects=True)
        #     open('./assets/countries+states+cities.json', 'wb').write(r.content)
        # except Exception as e:
        #     print("Could not update /assets/countries+states+cities.json: "+str(e))

        try:
            f = open('./assets/countries+states+cities.json', encoding='utf-8')
            self.countries_json = json.load(f)
            print("countries+states+cities loaded")

            self.countries = {}

            for c in self.countries_json:
                self.countries[c["iso2"]] = {
                    "name": c["name"],
                    "states": {}
                }

                for s in c["states"]:
                    self.countries[c["iso2"]]["states"][s["state_code"]] = {
                        "state_code": s["state_code"],
                        "state_name": s["name"]
                    }

            self.cities = {}

            for country in self.countries_json:
                for state in country["states"]:
                    for c in state["cities"]:
                        if country["iso2"] not in self.cities:
                            self.cities[country["iso2"]] = {}
                        city_name = remove_accents_lower(c["name"])
                        if city_name not in self.cities[country["iso2"]]:
                            self.cities[country["iso2"]
                                        ][city_name] = state["state_code"]
        except Exception as e:
            print(traceback.format_exc())
            exit()

        try:
            f = open('settings.json', encoding='utf-8')
            self.settings = json.load(f)
            print("Settings loaded")
        except Exception as e:
            self.settings = {}
            self.SaveSettings()
            print("Settings created")

        self.font_small = QFont(
            "./assets/font/RobotoCondensed.ttf", pointSize=8)

        self.threadpool = QThreadPool()
        self.saveMutex = QMutex()

        self.player_layouts = []

        self.allplayers = None
        self.local_players = None

        try:
            version = json.load(
                open('versions.json', encoding='utf-8')).get("program", "?")
        except Exception as e:
            version = "?"

        self.setGeometry(300, 300, 800, 100)
        self.setWindowTitle("TournamentStreamHelper v"+version)

        self.setDockOptions(
            QMainWindow.DockOption.AllowTabbedDocks)

        self.setTabPosition(
            Qt.DockWidgetArea.AllDockWidgetAreas, QTabWidget.TabPosition.North)

        # Layout base com status no topo
        central_widget = QWidget()
        pre_base_layout = QVBoxLayout()
        central_widget.setLayout(pre_base_layout)
        self.setCentralWidget(central_widget)

        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, TSHScoreboardWidget())

        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, TSHCommentaryWidget(), Qt.Orientation.Vertical)

        pre_base_layout.setSpacing(0)
        pre_base_layout.setContentsMargins(QMargins(0, 0, 0, 0))

        # Game
        group_box = QHBoxLayout()
        group_box.setSpacing(8)
        group_box.setContentsMargins(4, 4, 4, 4)

        gameLabel = QLabel("Game: ")
        gameLabel.setFont(self.font_small)
        gameLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_box.addWidget(gameLabel)

        self.gameSelect = QComboBox()
        self.gameSelect.setFont(self.font_small)
        self.gameSelect.activated.connect(
            TSHGameAssetManager.instance.LoadGameAssets)

        pre_base_layout.addLayout(group_box)
        group_box.addWidget(self.gameSelect)

        self.selectedGame = {}
        self.characters = {}
        self.stockIcons = {}
        self.portraits = {}
        self.stages = {}
        self.stage_images = {}
        self.skins = {}

        # Status
        group_box = QHBoxLayout()
        group_box.setSpacing(8)
        group_box.setContentsMargins(4, 4, 4, 4)

        self.statusLabel = QLabel("Manual")
        self.statusLabel.setFont(self.font_small)
        group_box.addWidget(self.statusLabel)

        self.statusLabelTime = QLabel("")
        self.statusLabelTime.setFont(self.font_small)
        self.statusLabelTime.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_box.addWidget(self.statusLabelTime)

        self.statusLabelTimeCancel = QPushButton()
        self.statusLabelTimeCancel.setIcon(QIcon('icons/cancel.svg'))
        self.statusLabelTimeCancel.setIconSize(QSize(12, 12))
        self.statusLabelTimeCancel.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_box.addWidget(self.statusLabelTimeCancel)
        self.statusLabelTimeCancel.hide()
        self.statusLabelTimeCancel.clicked.connect(self.StopTimer)

        self.timeLeftTimer = None
        self.autoTimer = None
        self.smashggSetAutoUpdateId = None

        pre_base_layout.addLayout(group_box)

        # Layout base
        self.base_layout = QBoxLayout(QBoxLayout.LeftToRight)

        pre_base_layout.addLayout(self.base_layout)

        # Botoes no final
        layout_end = QGridLayout()
        # self.base_layout.addLayout(layout_end)

        # Settings
        self.optionsBt = QToolButton()
        self.optionsBt.setIcon(QIcon('icons/menu.svg'))
        self.optionsBt.setText("Settings")
        self.optionsBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.optionsBt.setPopupMode(QToolButton.InstantPopup)
        layout_end.addWidget(self.optionsBt, 0, 0, 1, 2)
        self.optionsBt.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.optionsBt.setMenu(QMenu())
        action = self.optionsBt.menu().addAction("Always on top")
        action.setCheckable(True)
        action.toggled.connect(self.ToggleAlwaysOnTop)
        action = self.optionsBt.menu().addAction("Competitor mode")
        action.toggled.connect(self.ToggleCompetitorMode)
        action.setCheckable(True)
        if self.settings.get("competitor_mode", False):
            action.setChecked(True)
            # self.player_layouts[0].group_box.hide()
        action = self.optionsBt.menu().addAction("Check for updates")
        self.updateAction = action
        action.setIcon(QIcon('icons/undo.svg'))
        action.triggered.connect(self.CheckForUpdates)
        action = self.optionsBt.menu().addAction("Download assets")
        action.setIcon(QIcon('icons/download.svg'))
        action.triggered.connect(self.DownloadAssets)
        action = self.optionsBt.menu().addAction("Change layout orientation")
        action.setIcon(QIcon('icons/swap.svg'))
        action.triggered.connect(self.ChangeLayoutOrientation)

        # Downloads
        self.downloadsBt = QToolButton()
        self.downloadsBt.setIcon(QIcon('icons/download.svg'))
        self.downloadsBt.setText("Download autocomplete data")
        self.downloadsBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.downloadsBt.setPopupMode(QToolButton.InstantPopup)
        layout_end.addWidget(self.downloadsBt, 1, 0, 1, 2)
        self.downloadsBt.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.downloadsBt.setMenu(QMenu())
        action = self.downloadsBt.menu().addAction(
            "Autocomplete data from PowerRankings")
        action.setIcon(QIcon('icons/pr.svg'))
        action.triggered.connect(self.DownloadDataFromPowerRankingsClicked)
        action = self.downloadsBt.menu().addAction(
            "Autocomplete data from current SmashGG tournament")
        action.setIcon(QIcon('icons/smashgg.svg'))
        action.triggered.connect(self.LoadPlayersFromSmashGGTournamentClicked)

        # Set from stream queue
        self.getFromStreamQueueBt = QToolButton()
        self.getFromStreamQueueBt.setText("Get from queue")
        self.getFromStreamQueueBt.setIcon(QIcon('icons/twitch.svg'))
        self.getFromStreamQueueBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout_end.addWidget(self.getFromStreamQueueBt, 2, 0, 1, 1)
        self.getFromStreamQueueBt.clicked.connect(
            self.LoadSetsFromSmashGGTournamentQueueClicked)
        self.getFromStreamQueueBt.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.getFromStreamQueueBt.setPopupMode(QToolButton.MenuButtonPopup)
        self.getFromStreamQueueBt.setMenu(QMenu())

        self.setTwitchUsernameAction = QAction(
            "Set Twitch username (" +
            str(self.settings.get("twitch_username", None)) + ")"
        )
        self.getFromStreamQueueBt.menu().addAction(self.setTwitchUsernameAction)
        self.setTwitchUsernameAction.triggered.connect(self.SetTwitchUsername)

        action = self.getFromStreamQueueBt.menu().addAction("Auto")
        action.toggled.connect(self.ToggleAutoTwitchQueueMode)
        action.setCheckable(True)
        if self.settings.get("twitch_auto_mode", False):
            action.setChecked(True)
            self.SetTimer("Auto (StreamQueue)",
                          self.LoadSetsFromSmashGGTournamentQueueClicked)

        # Load set from SmashGG tournament
        self.smashggSelectSetBt = QToolButton()
        self.smashggSelectSetBt.setText("Select set")
        self.smashggSelectSetBt.setIcon(QIcon('icons/smashgg.svg'))
        self.smashggSelectSetBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout_end.addWidget(self.smashggSelectSetBt, 2, 1, 1, 1)
        self.smashggSelectSetBt.clicked.connect(
            self.LoadSetsFromSmashGGTournament)
        self.smashggSelectSetBt.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.smashggSelectSetBt.setPopupMode(QToolButton.MenuButtonPopup)
        self.smashggSelectSetBt.setMenu(QMenu())

        action = self.smashggSelectSetBt.menu().addAction("Set SmashGG key")
        action.triggered.connect(self.SetSmashggKey)

        self.smashggTournamentSlug = QAction(
            "Set tournament slug (" +
            str(self.settings.get("SMASHGG_TOURNAMENT_SLUG", None)) + ")"
        )
        self.smashggSelectSetBt.menu().addAction(self.smashggTournamentSlug)
        self.smashggTournamentSlug.triggered.connect(self.SetSmashggEventSlug)

        if self.settings.get("competitor_mode", False):
            self.getFromStreamQueueBt.hide()
            self.smashggSelectSetBt.hide()

        # Competitor mode smashgg button
        self.competitorModeSmashggBt = QToolButton()
        self.competitorModeSmashggBt.setText("Update from SmashGG set")
        self.competitorModeSmashggBt.setIcon(QIcon('icons/smashgg.svg'))
        self.competitorModeSmashggBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout_end.addWidget(self.competitorModeSmashggBt, 2, 0, 1, 2)
        self.competitorModeSmashggBt.clicked.connect(
            self.LoadUserSetFromSmashGGTournament)
        self.competitorModeSmashggBt.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.competitorModeSmashggBt.setPopupMode(QToolButton.MenuButtonPopup)
        self.competitorModeSmashggBt.setMenu(QMenu())

        action = self.competitorModeSmashggBt.menu().addAction("Set SmashGG key")
        action.triggered.connect(self.SetSmashggKey)

        self.smashggUserId = QAction(
            "Set user id (" +
            str(self.settings.get("smashgg_user_id", None)) + ")"
        )
        self.competitorModeSmashggBt.menu().addAction(self.smashggUserId)
        self.smashggUserId.triggered.connect(self.SetSmashggUserId)

        action = self.competitorModeSmashggBt.menu().addAction("Auto")
        action.toggled.connect(self.ToggleAutoCompetitorSmashGGMode)
        action.setCheckable(True)
        if self.settings.get("competitor_smashgg_auto_mode", False) and self.settings.get("competitor_mode", False):
            action.setChecked(True)
            self.SetTimer("Competitor: Auto (SmashGG)",
                          self.LoadUserSetFromSmashGGTournament)

        if self.settings.get("competitor_mode", False) == False:
            self.competitorModeSmashggBt.hide()

        # save button
        self.saveBt = QToolButton()
        self.saveBt.setText("Save and export")
        self.saveBt.setIcon(QIcon('icons/save.svg'))
        self.saveBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        pal = self.saveBt.palette()
        pal.setColor(QPalette.Button, QColor(Qt.green))
        self.saveBt.setPalette(pal)
        layout_end.addWidget(self.saveBt, 3, 0, 2, 2)
        self.saveBt.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.saveBt.setPopupMode(QToolButton.MenuButtonPopup)
        self.saveBt.clicked.connect(self.SaveButtonClicked)

        self.saveBt.setMenu(QMenu())

        action = self.saveBt.menu().addAction("Auto")
        action.setCheckable(True)
        if "autosave" in self.settings:
            if self.settings["autosave"] == True:
                action.setChecked(True)
        action.toggled.connect(self.ToggleAutosave)

        action = self.saveBt.menu().addAction("Add @ to twitter")
        action.setCheckable(True)
        if "twitter_add_at" in self.settings:
            if self.settings["twitter_add_at"] == True:
                action.setChecked(True)
        action.toggled.connect(self.ToggleTwitterAddAt)

        self.playersInverted = False

        self.LoadData()

        self.show()

        self.CheckForUpdates(True)

        splash.finish(self)

        self.ReloadGames()

    def ReloadGames(self):
        self.gameSelect.addItem("")
        for game in TSHGameAssetManager.instance.games.keys():
            self.gameSelect.addItem(game)

    def DetectGameFromId(self, id):
        game = next(
            (i+1 for i, game in enumerate(self.games)
             if str(self.games[game].get("smashgg_game_id", "")) == str(id)),
            None
        )

        if game is not None and self.gameSelect.currentIndex() != game:
            self.gameSelect.setCurrentIndex(game)
            self.LoadGameAssets(game)

    def CheckForUpdates(self, silent=False):
        release = None
        versions = None

        try:
            response = requests.get(
                "https://api.github.com/repos/joaorb64/TournamentStreamHelper/releases/latest")
            release = json.loads(response.text)
        except Exception as e:
            if silent == False:
                messagebox = QMessageBox()
                messagebox.setText(
                    "Failed to fetch version from github:\n"+str(e))
                messagebox.exec()

        try:
            versions = json.load(open('versions.json', encoding='utf-8'))
        except Exception as e:
            print("Local version file not found")

        if versions and release:
            myVersion = versions.get("program", "0.0")
            currVersion = release.get("tag_name", "0.0")

            if silent == False:
                if myVersion < currVersion:
                    buttonReply = QDialog(self)
                    buttonReply.setWindowTitle("Updater")
                    buttonReply.setWindowModality(Qt.WindowModal)
                    vbox = QVBoxLayout()
                    buttonReply.setLayout(vbox)

                    buttonReply.layout().addWidget(
                        QLabel("New update available: "+myVersion+" → "+currVersion))
                    buttonReply.layout().addWidget(QLabel(release["body"]))
                    buttonReply.layout().addWidget(QLabel(
                        "Update to latest version?\nNOTE: WILL BACKUP /layout/ AND OVERWRITE ALL OTHER DATA"))

                    hbox = QHBoxLayout()
                    vbox.addLayout(hbox)

                    btUpdate = QPushButton("Update")
                    hbox.addWidget(btUpdate)
                    btCancel = QPushButton("Cancel")
                    hbox.addWidget(btCancel)

                    buttonReply.show()

                    def Update():
                        self.downloadDialogue = QProgressDialog(
                            "Downloading update... ", "Cancel", 0, 0, self)
                        self.downloadDialogue.show()

                        def worker(progress_callback):
                            with open("update.tar.gz", 'wb') as downloadFile:
                                downloaded = 0

                                response = urllib.request.urlopen(
                                    release["tarball_url"])

                                while(True):
                                    chunk = response.read(1024*1024)

                                    if not chunk:
                                        break

                                    downloaded += len(chunk)
                                    downloadFile.write(chunk)

                                    if self.downloadDialogue.wasCanceled():
                                        return

                                    progress_callback.emit(int(downloaded))
                                downloadFile.close()

                        def progress(downloaded):
                            self.downloadDialogue.setLabelText(
                                "Downloading update... "+str(downloaded/1024/1024)+" MB")

                        def finished():
                            self.downloadDialogue.close()
                            tar = tarfile.open("update.tar.gz")
                            print(tar.getmembers())
                            os.rename(
                                "./layout", f"./layout_backup_{str(time.time())}")
                            os.rename(
                                "./tournament_phases.txt", f"./tournament_phases_backup_{str(time.time())}.txt")
                            for m in tar.getmembers():
                                if "/" in m.name:
                                    m.name = m.name.split("/", 1)[1]
                                    tar.extract(m)
                            tar.close()
                            os.remove("update.tar.gz")

                            with open('versions.json', 'w') as outfile:
                                versions["program"] = currVersion
                                json.dump(versions, outfile)

                            messagebox = QMessageBox()
                            messagebox.setText(
                                "Update complete. The program will now close.")
                            messagebox.finished.connect(QApplication.exit)
                            messagebox.exec()

                        worker = Worker(worker)
                        worker.signals.progress.connect(progress)
                        worker.signals.finished.connect(finished)
                        self.threadpool.start(worker)

                    btUpdate.clicked.connect(Update)
                    btCancel.clicked.connect(lambda: buttonReply.close())
                else:
                    messagebox = QMessageBox()
                    messagebox.setText(
                        "You're already using the latest version")
                    messagebox.exec()
            else:
                if myVersion < currVersion:
                    baseIcon = QPixmap(QImage("icons/menu.svg").scaled(32, 32))
                    updateIcon = QImage(
                        "./icons/update_circle.svg").scaled(12, 12)
                    p = QPainter(baseIcon)
                    p.drawImage(QPoint(20, 0), updateIcon)
                    p.end()
                    self.optionsBt.setIcon(QIcon(baseIcon))
                    self.updateAction.setText(
                        "Check for updates [Update available!]")

    def ChangeLayoutOrientation(self):
        if self.base_layout.direction() == QBoxLayout.TopToBottom:
            self.base_layout.setDirection(QBoxLayout.LeftToRight)
        else:
            self.base_layout.setDirection(QBoxLayout.TopToBottom)
        self.resize(0, 0)
        self.adjustSize()

    def SetTimer(self, name, function):
        self.timeLeftTimer = QTimer()
        self.timeLeftTimer.timeout.connect(self.updateTimerLabel)
        self.timeLeftTimer.start(100)
        self.autoTimer = QTimer()
        self.autoTimer.start(5000)
        self.autoTimer.timeout.connect(function)
        self.statusLabel.setText(name)
        self.statusLabelTimeCancel.show()

    def StopTimer(self):
        if self.timeLeftTimer is not None:
            self.timeLeftTimer.stop()
            self.timeLeftTimer = None
        if self.autoTimer:
            self.autoTimer.stop()
            self.autoTimer = None
        self.smashggSetAutoUpdateId = None
        self.programState["smashgg_set_id"] = None
        self.ExportProgramState()
        self.statusLabelTime.setText("")
        self.statusLabelTimeCancel.hide()
        self.statusLabel.setText("Manual")

    def updateTimerLabel(self):
        if self.autoTimer:
            self.statusLabelTime.setText(
                str(int(self.autoTimer.remainingTime()/1000)))

    def ScoreChanged(self):
        self.programState["score_left"] = self.scoreLeft.value()
        self.programState["score_right"] = self.scoreRight.value()
        self.programState["tournament_phase"] = self.tournament_phase.currentText()
        self.programState["best_of"] = self.bestOf.value()

        if self.settings.get("autosave") == True:
            self.ExportProgramState()
            self.ExportScore()

    def ExportScore(self):
        if "score_left" in self.programStateDiff:
            with open('out/p1_score.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(str(self.scoreLeft.value()))
        if "score_right" in self.programStateDiff:
            with open('out/p2_score.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(str(self.scoreRight.value()))
        if "tournament_phase" in self.programStateDiff:
            with open('out/match_phase.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(self.tournament_phase.currentText())
        if "best_of" in self.programStateDiff:
            with open('out/best_of.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(str(self.bestOf.value()))

    def ExportStageStrike(self, data):
        if data["allStages"] is not None:
            img = QImage(QSize((256+16)*5-16, 256+16), QImage.Format_RGBA64)
            img.fill(qRgba(0, 0, 0, 0))
            painter = QPainter(img)
            try:
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

                iconStageStrike = QImage(
                    './icons/stage_strike.svg').scaled(QSize(64, 64))
                iconStageDSR = QImage(
                    './icons/stage_dsr.svg').scaled(QSize(64, 64))
                iconStageSelected = QImage(
                    './icons/stage_select.svg').scaled(QSize(64, 64))

                perLine = 5

                for i, stage in enumerate(data["allStages"]):
                    x = 0
                    y = 0

                    y = int(i/perLine)*(128+16)

                    targetW = 256
                    targetH = 128

                    elementsInRow = min(
                        len(data["allStages"])-perLine*int(i/perLine), 5)

                    margin = (perLine - elementsInRow) * (256+16) / 2

                    x = (i % 5)*(256+16) + margin

                    stage_image = self.stage_images.get(str(stage), None)
                    painter.drawImage(QRect(x, y, 256, 128), stage_image)

                    if str(stage) in data["strikedStages"] or int(stage) in data["strikedStages"]:
                        if data["dsrStages"] is not None and int(stage) in data["dsrStages"]:
                            painter.drawImage(
                                QPoint(x+190, y+60), iconStageDSR)
                        else:
                            painter.drawImage(
                                QPoint(x+190, y+60), iconStageStrike)

                    if str(stage) == str(data["selectedStage"]):
                        painter.drawImage(
                            QPoint(x+190, y+60), iconStageSelected)

                img.save("./out/stage_strike.png")
                painter.end()
            except:
                pass
            finally:
                painter.end()
        else:
            img = QImage(QSize(256, 256), QImage.Format_RGBA64)
            img.fill(qRgba(0, 0, 0, 0))
            img.save("./out/stage_strike.png")

    def ResetScoreButtonClicked(self):
        self.scoreLeft.setValue(0)
        self.scoreRight.setValue(0)

    def InvertButtonClicked(self):
        nick = self.player_layouts[0].player_name.text()
        prefix = self.player_layouts[0].player_org.text()
        name = self.player_layouts[0].player_real_name.text()
        twitter = self.player_layouts[0].player_twitter.text()
        country = self.player_layouts[0].player_country.currentIndex()
        state = self.player_layouts[0].player_state.currentIndex()
        character = self.player_layouts[0].player_character.currentIndex()
        color = self.player_layouts[0].player_character_color.currentIndex()
        score = self.scoreLeft.value()

        self.player_layouts[0].player_name.setText(
            self.player_layouts[1].player_name.text())
        self.player_layouts[0].player_org.setText(
            self.player_layouts[1].player_org.text())
        self.player_layouts[0].player_real_name.setText(
            self.player_layouts[1].player_real_name.text())
        self.player_layouts[0].player_twitter.setText(
            self.player_layouts[1].player_twitter.text())
        self.player_layouts[0].player_country.setCurrentIndex(
            self.player_layouts[1].player_country.currentIndex())
        self.player_layouts[0].player_state.setCurrentIndex(
            self.player_layouts[1].player_state.currentIndex())
        self.player_layouts[0].player_character.setCurrentIndex(
            self.player_layouts[1].player_character.currentIndex())
        self.player_layouts[0].LoadSkinOptions()
        self.player_layouts[0].player_character_color.setCurrentIndex(
            self.player_layouts[1].player_character_color.currentIndex())
        self.player_layouts[0].CharacterChanged()
        self.scoreLeft.setValue(self.scoreRight.value())

        self.player_layouts[1].player_name.setText(nick)
        self.player_layouts[1].player_org.setText(prefix)
        self.player_layouts[1].player_real_name.setText(name)
        self.player_layouts[1].player_twitter.setText(twitter)
        self.player_layouts[1].player_country.setCurrentIndex(country)
        self.player_layouts[1].player_state.setCurrentIndex(state)
        self.player_layouts[1].player_character.setCurrentIndex(character)
        self.player_layouts[1].LoadSkinOptions()
        self.player_layouts[1].player_character_color.setCurrentIndex(color)
        self.player_layouts[1].CharacterChanged()
        self.scoreRight.setValue(score)

        self.playersInverted = not self.playersInverted

    def DownloadAssets(self):
        assets = self.DownloadAssetsFetch()

        if assets is None:
            return

        self.preDownloadDialogue = QDialog(self)
        self.preDownloadDialogue.setWindowTitle("Download assets")
        self.preDownloadDialogue.setWindowModality(Qt.WindowModal)
        self.preDownloadDialogue.setLayout(QVBoxLayout())
        self.preDownloadDialogue.show()

        select = QComboBox()
        self.preDownloadDialogue.layout().addWidget(select)

        model = QStandardItemModel()

        proxyModel = QSortFilterProxyModel()
        proxyModel.setSourceModel(model)
        proxyModel.setFilterKeyColumn(-1)
        proxyModel.setFilterCaseSensitivity(False)

        def filterList(text):
            proxyModel.setFilterFixedString(text)

        searchBar = QLineEdit()
        searchBar.setPlaceholderText("Filter...")
        self.preDownloadDialogue.layout().addWidget(searchBar)
        searchBar.textEdited.connect(filterList)

        downloadList = QTableView()
        self.preDownloadDialogue.layout().addWidget(downloadList)
        downloadList.setSortingEnabled(True)
        downloadList.setSelectionBehavior(QAbstractItemView.SelectRows)
        downloadList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        downloadList.setModel(proxyModel)
        downloadList.verticalHeader().hide()
        self.preDownloadDialogue.resize(1200, 500)
        downloadList.horizontalHeader().setStretchLastSection(True)
        downloadList.setWordWrap(True)
        downloadList.resizeColumnsToContents()
        downloadList.resizeRowsToContents()

        for game in assets:
            select.addItem(assets[game]["name"])

        def ReloadGameAssets(index=None):
            nonlocal self

            if index == None:
                index = select.currentIndex()

            model.clear()
            model.setHorizontalHeaderLabels([
                "game", "asset_id", "Name", "Description", "Credits", "Installed version", "Latest version", "Size"
            ])
            downloadList.hideColumn(0)
            downloadList.hideColumn(1)
            downloadList.horizontalHeader().setStretchLastSection(True)
            downloadList.setWordWrap(True)
            downloadList.resizeColumnsToContents()
            downloadList.resizeRowsToContents()

            key = list(assets.keys())[index]

            for asset in assets[key]["assets"]:
                dlSize = "{:.2f}".format(sum(
                    [f.get("size", 0) for f in list(
                        assets[key]["assets"][asset]["files"].values())]
                )/1024/1024) + " MB"

                currVersion = str(self.games.get(key, {}).get(
                    "assets", {}).get(asset, {}).get("version"))
                print(currVersion)
                version = str(assets[key]["assets"][asset].get("version"))

                if currVersion != version:
                    version += " [!]"

                model.appendRow([
                    QStandardItem(key),
                    QStandardItem(asset),
                    QStandardItem(assets[key]["assets"][asset].get("name")),
                    QStandardItem(assets[key]["assets"]
                                  [asset].get("description")),
                    QStandardItem(assets[key]["assets"][asset].get("credits")),
                    QStandardItem(currVersion),
                    QStandardItem(version),
                    QStandardItem(dlSize)
                ])

            downloadList.horizontalHeader().setStretchLastSection(True)
            downloadList.resizeColumnsToContents()
            downloadList.resizeRowsToContents()

        self.reloadDownloadsList = ReloadGameAssets
        select.activated.connect(ReloadGameAssets)
        ReloadGameAssets(0)

        btOk = QPushButton("Download")
        self.preDownloadDialogue.layout().addWidget(btOk)

        def DownloadStart():
            nonlocal self
            row = downloadList.selectionModel().selectedRows()[0].row()
            game = downloadList.model().index(row, 0).data()
            key = downloadList.model().index(row, 1).data()

            filesToDownload = assets[game]["assets"][key]["files"]

            for f in filesToDownload:
                filesToDownload[f]["path"] = \
                    "https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/" + \
                    filesToDownload[f]["name"]
                filesToDownload[f]["extractpath"] = "./assets/games/"+game

            self.downloadDialogue = QProgressDialog(
                "Downloading assets", "Cancel", 0, 100, self)
            self.downloadDialogue.show()
            worker = Worker(self.DownloadAssetsWorker, *
                            [list(filesToDownload.values())])
            worker.signals.progress.connect(self.DownloadAssetsProgress)
            worker.signals.finished.connect(self.DownloadAssetsFinished)
            self.threadpool.start(worker)

        btOk.clicked.connect(DownloadStart)

    def DownloadAssetsFetch(self):
        assets = None
        try:
            response = requests.get(
                "https://raw.githubusercontent.com/joaorb64/StreamHelperAssets/main/assets.json")
            assets = json.loads(response.text)
        except Exception as e:
            messagebox = QMessageBox()
            messagebox.setText("Failed to fetch github:\n"+str(e))
            messagebox.exec()
        return assets

    def DownloadAssetsWorker(self, files, progress_callback):
        totalSize = sum(f["size"] for f in files)
        downloaded = 0

        for f in files:
            with open("assets/games/"+f["name"], 'wb') as downloadFile:
                print("Downloading "+f["name"])
                progress_callback.emit("Downloading "+f["name"]+"...")

                response = urllib.request.urlopen(f["path"])

                while(True):
                    chunk = response.read(1024*1024)

                    if not chunk:
                        break

                    downloaded += len(chunk)
                    downloadFile.write(chunk)

                    if self.downloadDialogue.wasCanceled():
                        return

                    progress_callback.emit(int(downloaded/totalSize*100))
                downloadFile.close()

                print("OK")

        progress_callback.emit(100)

        filenames = ["./assets/games/"+f["name"] for f in files]
        mergedFile = "./assets/games/"+files[0]["name"].split(".")[0]+'.7z'

        is7z = next((f for f in files if ".7z" in f["name"]), None)

        if is7z:
            with open(mergedFile, 'ab') as outfile:
                for fname in filenames:
                    with open(fname, 'rb') as infile:
                        outfile.write(infile.read())

            print("Extracting "+mergedFile)
            progress_callback.emit("Extracting "+mergedFile)

            with py7zr.SevenZipFile(mergedFile, 'r') as parent_zip:
                parent_zip.extractall(files[0]["extractpath"])

            for f in files:
                os.remove("./assets/games/"+f["name"])

            os.remove(mergedFile)
        else:
            for f in files:
                if os.path.isfile(f["extractpath"]+"/"+f["name"]):
                    os.remove(f["extractpath"]+"/"+f["name"])
                shutil.move("./assets/games/"+f["name"], f["extractpath"])

        print("OK")

    def DownloadAssetsProgress(self, n):
        if type(n) == int:
            self.downloadDialogue.setValue(n)

            if n == 100:
                self.downloadDialogue.setMaximum(0)
                self.downloadDialogue.setValue(0)
        else:
            self.downloadDialogue.setLabelText(n)

    def DownloadAssetsFinished(self):
        TSHGameAssetManager.instance.LoadGames()
        self.downloadDialogue.close()
        self.reloadDownloadsList()

    def DownloadDataFromPowerRankingsClicked(self):
        worker = Worker(self.DownloadDataFromPowerRankings)
        worker.signals.finished.connect(self.DownloadButtonComplete)
        worker.signals.progress.connect(self.DownloadButtonProgress)

        self.downloadDialogue = QProgressDialog(
            "Downloading PowerRankings data", "Cancel", 0, 100, self)
        self.downloadDialogue.show()

        self.threadpool.start(worker)

    def DownloadButtonProgress(self, n):
        progress = n[0]/n[1]*100

        self.downloadDialogue.setValue(progress)

        if progress == 100:
            self.downloadDialogue.setMaximum(0)
            self.downloadDialogue.setValue(0)

    def DownloadButtonComplete(self):
        self.LoadData()
        self.downloadDialogue.close()

    def SetupAutocomplete(self):
        # auto complete options
        names = []
        autocompleter_names = []
        autocompleter_mains = []
        autocompleter_players = []
        autocompleter_skins = []

        ap = []

        if self.allplayers is not None and self.allplayers.get("players") is not None:
            for p in self.allplayers["players"]:
                if "mains" in p and len(p["mains"]) > 0:
                    if p["mains"][0] in self.powerrankings_to_smashgg.keys():
                        p["mains"][0] = self.powerrankings_to_smashgg[p["mains"][0]]
                    else:
                        p["mains"][0] = "Random Character"
                ap.append(p)

        if self.local_players is not None:
            for p in self.local_players.values():
                p["from_local"] = True
                ap.append(p)

        self.mergedPlayers = ap

        for i, p in enumerate(ap):
            name = ""
            if("org" in p.keys() and p["org"] != ""):
                name += str(p["org"]) + " "
            name += str(p["name"])
            if("country_code" in p.keys() and p["country_code"] != ""):
                name += " ("+p["country_code"]+")"
            autocompleter_names.append(name)
            names.append(str(p["name"]))

            if("mains" in p.keys() and p["mains"] != None and
                    len(p["mains"]) > 0 and
                    p["mains"][0] in self.characters.keys()):
                autocompleter_mains.append(p["mains"][0])
            else:
                autocompleter_mains.append("Random Character")

            skin = 0

            if "skins" in p.keys():
                if "mains" in p.keys() and p["mains"] != None and len(p["mains"]) > 0:
                    skin = p["skins"].get(p["mains"][0], 0)
                    if type(skin) != int:
                        skin = 0

            autocompleter_skins.append(skin)
            autocompleter_players.append(p)

        model = QStandardItemModel()

        model.appendRow(
            [QStandardItem(""), QStandardItem(""), QStandardItem("")])

        for i, n in enumerate(names):
            item = QStandardItem(autocompleter_names[i])

            icon = None
            iconSet = self.stockIcons.get(autocompleter_mains[i], {})

            if autocompleter_skins[i] in iconSet:
                icon = iconSet[autocompleter_skins[i]]
            elif len(iconSet) > 0:
                icon = list(iconSet.values())[0]

            if icon is not None:
                pixmap = QPixmap.fromImage(icon)
                item.setIcon(QIcon(pixmap.scaledToWidth(
                    24, Qt.TransformationMode.SmoothTransformation)))
            else:
                item.setIcon(self.stockIcons.get(autocompleter_mains[i], {}).get(
                    str(autocompleter_skins[i]), QIcon('./icons/cancel.svg')))

            item.setData(autocompleter_players[i])
            model.appendRow([
                item,
                QStandardItem(n),
                QStandardItem(str(i))]
            )

        for p in self.player_layouts:
            completer = p.player_name.completer()

            if not completer:
                completer = QCompleter()
                p.player_name.setCompleter(completer)

            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setModel(model)
            # p.player_name.setModel(model)
            completer.activated[QModelIndex].connect(
                p.AutocompleteSelected, Qt.QueuedConnection)
            completer.popup().setMinimumWidth(500)
            completer.popup().setIconSize(QSize(24, 24))
            completer.setCompletionColumn(0)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            # p.player_name.currentIndexChanged.connect(p.AutocompleteSelected)
        print("Autocomplete reloaded")

    def LoadData(self):
        try:
            f = open('powerrankings_player_data.json', encoding='utf-8')
            self.allplayers = json.load(f)
            print("Powerrankings data loaded")
        except Exception as e:
            self.allplayers = None
            print(traceback.format_exc())

        self.LoadLocalPlayers()

        self.SetupAutocomplete()

    def LoadLocalPlayers(self):
        try:
            self.local_players = {}

            if os.path.exists("./local_players.csv") == False:
                with open('./local_players.csv', 'w', encoding='utf-8') as outfile:
                    spamwriter = csv.writer(outfile)
                    spamwriter.writerow(["org", "name", "full_name", "country_code", "state",
                                        "twitter", "main", "color (0-7)"])

            with open('local_players.csv', 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # skip header
                for row in reader:
                    # print(row)
                    # 0 org,1 name,2 full_name,3 country_code,4 state,5 twitter,6 main,7 color
                    key = row[0]+" "+row[1] if row[0] != "" else row[1]
                    # print(key)
                    self.local_players[key] = {
                        "org": row[0],
                        "name": row[1],
                        "full_name": row[2],
                        "country_code": row[3],
                        "state": row[4],
                        "twitter": row[5],
                        "mains": [row[6]] if row[6] != "" else [],
                        "skins": {
                            row[6]: int(row[7])
                        }
                    }
        except Exception as e:
            print(traceback.format_exc())

    def SaveDB(self):
        with open('local_players.csv', 'w', encoding="utf-8", newline='') as outfile:
            # 0 org,1 name,2 full_name,3 country_code,4 state,5 twitter,6 main,7 color
            spamwriter = csv.writer(outfile)
            spamwriter.writerow(["org", "name", "full_name", "country_code", "state",
                                "twitter", "main", "color (0-7)"])
            for player in self.local_players.values():
                main = player.get("mains", [""])[0] if len(
                    player.get("mains", [""])) > 0 else ""
                skin = 0 if ("skins" not in player or len(player["skins"]) == 0) else str(
                    list(player["skins"].values())[0])
                spamwriter.writerow([
                    player.get("org", ""), player.get("name", ""), player.get(
                        "full_name", ""), player.get("country_code", ""),
                    player.get("state", ""), player.get(
                        "twitter", ""), main, skin
                ])
        self.SetupAutocomplete()

    def ToggleAlwaysOnTop(self, checked):
        if checked:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

    def ToggleCompetitorMode(self, checked):
        if checked:
            self.settings["competitor_mode"] = True
            try:
                # self.player_layouts[0].group_box.hide()
                self.getFromStreamQueueBt.hide()
                self.smashggSelectSetBt.hide()
                self.competitorModeSmashggBt.show()
            except Exception as e:
                print(traceback.format_exc())
        else:
            try:
                self.settings["competitor_mode"] = False
                self.player_layouts[0].group_box.show()
                self.getFromStreamQueueBt.show()
                self.smashggSelectSetBt.show()
                self.competitorModeSmashggBt.hide()
            except Exception as e:
                print(traceback.format_exc())
        self.StopTimer()
        self.SaveSettings()

    def ToggleAutoTwitchQueueMode(self, checked):
        if checked:
            self.settings["twitch_auto_mode"] = True
            self.SetTimer("Auto (StreamQueue)",
                          self.LoadSetsFromSmashGGTournamentQueueClicked)
        else:
            self.settings["twitch_auto_mode"] = False
            self.StopTimer()
        self.SaveSettings()

    def ToggleAutoCompetitorSmashGGMode(self, checked):
        if checked:
            self.settings["competitor_smashgg_auto_mode"] = True
            self.SetTimer("Competitor: Auto (SmashGG)",
                          self.LoadUserSetFromSmashGGTournament)
        else:
            self.settings["competitor_smashgg_auto_mode"] = False
            self.StopTimer()
        self.SaveSettings()

    def ToggleAutosave(self, checked):
        if checked:
            self.settings["autosave"] = True
        else:
            self.settings["autosave"] = False
        self.SaveSettings()

    def ToggleTwitterAddAt(self, checked):
        if checked:
            self.settings["twitter_add_at"] = True
        else:
            self.settings["twitter_add_at"] = False
        self.SaveSettings()

    def CalculateProgramStateDiff(self):
        diff = [k for k in self.programState.keys() if self.programState[k]
                != self.savedProgramState.get(k, None)]
        self.programStateDiff = diff

    def ExportProgramState(self):
        self.saveMutex.lock()

        diff = [k for k in self.programState.keys() if self.programState[k]
                != self.savedProgramState.get(k, None)]

        print(diff)

        for k in diff:
            print("["+k+"] "+str(self.savedProgramState.get(k)) +
                  " → "+str(self.programState.get(k)))

        with open('./out/program_state.json', 'w') as outfile:
            json.dump(self.programState, outfile, indent=4)
            self.savedProgramState = copy.deepcopy(self.programState)
            self.programStateDiff = diff
        self.saveMutex.unlock()

    def SaveButtonClicked(self):
        self.ExportProgramState()
        for p in self.player_layouts:
            p.ExportName()
            p.ExportRealName()
            p.ExportTwitter()
            p.ExportCountry()
            p.ExportState()
            p.ExportCharacter()
        self.ExportScore()

    def DownloadDataFromPowerRankings(self, progress_callback):
        with open('powerrankings_player_data.json', 'wb') as f:
            print("Download start")

            response = requests.get(
                'https://raw.githubusercontent.com/joaorb64/tournament_api/multigames/out/ssbu/allplayers.json', stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None:  # no content length header
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = [dl, total_length]
                    progress_callback.emit(done)
                f.close()

            print("Download successful")

    def SaveSettings(self):
        with open('settings.json', 'w', encoding='utf-8') as outfile:
            json.dump(self.settings, outfile, indent=4, sort_keys=True)

    def SetTwitchUsername(self):
        text, okPressed = QInputDialog.getText(
            self, "Set Twitch username", "Username: ", QLineEdit.Normal, "")
        if okPressed:
            self.settings["twitch_username"] = text
            self.SaveSettings()
            self.setTwitchUsernameAction.setText(
                "Set Twitch username (" +
                self.settings.get("twitch_username", None) + ")"
            )

    def SetSmashggKey(self):
        text, okPressed = QInputDialog.getText(
            self,
            "Set SmashGG key",
            '''
            - Go over to smash.gg, login;
            - Click on your profile image > Developer settings;
            - Click on "Create new token";
            - Paste the code you obtained here.
            ''',
            QLineEdit.Normal,
            ""
        )
        if okPressed:
            self.settings["SMASHGG_KEY"] = text.strip()
            self.SaveSettings()

    def SetSmashggEventSlug(self):
        inp = QDialog(self)

        layout = QVBoxLayout()
        inp.setLayout(layout)

        inp.layout().addWidget(QLabel(
            "Paste the URL to an event on SmashGG (must contain the /event/ part)"
        ))

        lineEdit = QLineEdit()
        okButton = QPushButton("OK")
        validator = QRegularExpression("tournament/[^/]*/event/[^/]*")

        def validateText():
            match = validator.match(lineEdit.text()).capturedTexts()
            if len(match) > 0:
                okButton.setDisabled(False)
            else:
                okButton.setDisabled(True)

        lineEdit.textEdited.connect(validateText)

        inp.layout().addWidget(lineEdit)

        okButton.clicked.connect(inp.accept)
        okButton.setDisabled(True)
        inp.layout().addWidget(okButton)

        inp.setWindowTitle('Set SmashGG tournament slug')
        inp.resize(600, 10)

        if inp.exec_() == QDialog.Accepted:
            match = validator.match(lineEdit.text()).capturedTexts()
            self.settings["SMASHGG_TOURNAMENT_SLUG"] = match[0]
            self.SaveSettings()
            self.smashggTournamentSlug.setText(
                "Set tournament slug (" + str(self.settings.get(
                    "SMASHGG_TOURNAMENT_SLUG", None)) + ")"
            )
            self.LoadPlayersFromSmashGGTournamentStart(
                self.settings.get("SMASHGG_TOURNAMENT_SLUG", None))

        inp.deleteLater()

    def SetSmashggUserId(self):
        inp = QDialog(self)

        inp.setLayout(QVBoxLayout())

        lineEdit = QLineEdit()
        lineEdit.setInputMask("user/HHHHHHHH;_")

        inp.layout().addWidget(lineEdit)

        okButton = QPushButton("OK")
        okButton.clicked.connect(inp.accept)
        inp.layout().addWidget(okButton)

        inp.setWindowTitle('Set SmashGG user id')

        if inp.exec_() == QDialog.Accepted:
            self.settings["smashgg_user_id"] = lineEdit.text().strip()
            self.SaveSettings()
            self.smashggUserId.setText(
                "Set user id (" +
                str(self.settings.get("smashgg_user_id", None)) + ")"
            )

        inp.deleteLater()

    def LoadPlayersFromSmashGGTournamentClicked(self):
        if self.settings.get("SMASHGG_KEY", None) is None:
            self.SetSmashggKey()

        if self.settings.get("SMASHGG_TOURNAMENT_SLUG", None) is None:
            self.SetSmashggEventSlug()

        self.LoadPlayersFromSmashGGTournamentStart(
            self.settings.get("SMASHGG_TOURNAMENT_SLUG", None))

    def LoadPlayersFromSmashGGTournamentStart(self, slug):
        if slug is None or slug == "":
            return

        worker = Worker(
            self.LoadPlayersFromSmashGGTournamentWorker, **{"slug": slug})
        worker.signals.progress.connect(
            self.LoadPlayersFromSmashGGTournamentProgress)
        worker.signals.finished.connect(
            self.LoadPlayersFromSmashGGTournamentFinished)
        self.threadpool.start(worker)

    def LoadPlayersFromSmashGGTournamentWorker(self, progress_callback, slug):
        if self.settings.get("SMASHGG_KEY", None) is None:
            self.SetSmashggKey()

        page = 1
        players = []

        while True:
            r = requests.post(
                'https://api.smash.gg/gql/alpha',
                headers={
                    'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
                },
                json={
                    'query': '''
                    query evento($eventSlug: String!) {
                        event(slug: $eventSlug) {
                            videogame {
                                id
                            }
                            entrants(query: {page: '''+str(page)+''', perPage: 15}) {
                                pageInfo {
                                    totalPages
                                }
                                nodes{
                                    name
                                    participants {
                                        user {
                                            id
                                            name
                                            authorizations(types: [TWITTER]) {
                                                type
                                                externalUsername
                                            }
                                            location {
                                                city
                                                state
                                                country
                                            }
                                            images(type: "profile") {
                                                url
                                            }
                                        }
                                        player {
                                            id
                                            gamerTag
                                            prefix
                                            sets(page: 1, perPage: 1) {
                                                nodes {
                                                    games {
                                                        selections {
                                                            entrant {
                                                                participants {
                                                                    player {
                                                                        id
                                                                    }
                                                                }
                                                            }
                                                            selectionValue
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }''',
                    'variables': {
                        "eventSlug": slug
                    },
                }
            )
            resp = json.loads(r.text)

            totalPages = resp["data"]["event"]["entrants"]["pageInfo"]["totalPages"]

            if resp is None or \
                    resp.get("data") is None or \
                    resp["data"].get("event") is None or \
                    resp["data"]["event"].get("entrants") is None:
                print(resp)
                return

            data_entrants = resp["data"]["event"]["entrants"]["nodes"]

            for entrant in data_entrants:
                user = entrant["participants"][0]["user"]
                player = entrant["participants"][0]["player"]

                player_obj = self.LoadSmashGGPlayer(user, player)

                players.append(player_obj)

                for p in players:
                    print(p)
                    key = (p["org"]+" " if (p["org"] != "" and
                                            p["org"] != None) else "") + p["name"]
                    self.local_players[key] = p
                players = []

            page += 1

            progress_callback.emit(page/totalPages*100)

            if page >= totalPages:
                break

    def LoadSmashGGPlayer(self, user, player, entrantId=None, selectedChars=[]):
        player_obj = {}

        if user is None and player is None:
            return {}

        if user is not None:
            player_obj["smashgg_id"] = user["id"]
            player_obj["smashgg_slug"] = user["slug"]
            player_obj["full_name"] = user["name"]

            if user["authorizations"] is not None:
                for authorization in user["authorizations"]:
                    player_obj[authorization["type"].lower(
                    )] = authorization["externalUsername"]

            if user["location"] is not None:
                if user["location"]["city"] is not None:
                    player_obj["city"] = user["location"]["city"]
                if user["location"]["country"] is not None:
                    player_obj["country"] = user["location"]["country"]

            if user["images"] is not None:
                if len(user["images"]) > 0:
                    player_obj["smashgg_image"] = user["images"][0]["url"]

        if player is not None:
            player_obj["name"] = player["gamerTag"]
            player_obj["org"] = player["prefix"] if player["prefix"] != None else ""

            if str(entrantId) in selectedChars:
                found = None
                if len(selectedChars[str(entrantId)]) > 0:
                    found = next((c for c in self.smashgg_character_data["character"] if c["id"] == selectedChars[str(
                        entrantId)][0]), None)
                if found:
                    print(found["name"])
                    player_obj["mains"] = [found["name"]]
            else:
                # character usage, mains
                if player["sets"] is not None and \
                        player["sets"]["nodes"] is not None:
                    selections = Counter()

                    for set_ in player["sets"]["nodes"]:
                        if set_["games"] is None:
                            continue
                        for game in set_["games"]:
                            if game["selections"] is None:
                                continue
                            for selection in game["selections"]:
                                if selection.get("entrant"):
                                    if selection.get("entrant").get("participants"):
                                        if len(selection.get("entrant").get("participants")) > 0:
                                            if selection.get("entrant").get("participants") is None:
                                                continue
                                            if selection.get("entrant").get("participants")[0] is None:
                                                continue
                                            if selection.get("entrant").get("participants")[0]["player"] is None:
                                                continue
                                            participant_id = selection.get("entrant").get(
                                                "participants")[0]["player"]["id"]
                                            if player["id"] == participant_id:
                                                if selection["selectionValue"] is not None:
                                                    selections[selection["selectionValue"]] += 1

                    mains = []

                    most_common = selections.most_common(1)

                    for character in selections.most_common(2):
                        if(character[1] > most_common[0][1]/3.0):
                            found = next(
                                (c for c in self.smashgg_character_data["character"] if c["id"] == character[0]), None)
                            if found:
                                mains.append(found["name"])

                    if len(mains) > 0:
                        player_obj["mains"] = mains
                    elif self.allplayers is not None and user is not None:
                        found = next(
                            (p for p in self.allplayers.get("players", [])
                             if p.get("smashgg_id") == user.get("id")),
                            None
                        )
                        if found and len(found.get("mains")) > 0:
                            player_obj["mains"] = found["mains"]

        countries = self.countries_json

        # match state
        if "country" in player_obj.keys() and player_obj["country"] is not None:
            country = next(
                (c for c in countries if remove_accents_lower(
                    c["name"]) == remove_accents_lower(player_obj["country"])),
                None
            )

            if country is not None:
                player_obj["country_code"] = country["iso2"]

                if "state" in user.keys() and len(user["state"]) > 0:
                    player_obj["state"] = user["state"]
                elif "city" in player_obj.keys() and player_obj["city"] is not None:
                    # State explicit?
                    split = player_obj["city"].split(" ")

                    for part in split:
                        state = next(
                            (st for st in country["states"] if remove_accents_lower(
                                st["state_code"]) == remove_accents_lower(part)),
                            None
                        )
                        if state is not None:
                            player_obj["state"] = state["state_code"]
                            break

                    if "state" not in player_obj.keys() or player_obj["state"] is None:
                        # no, so get by City
                        state = self.cities.get(player_obj["country_code"], {}).get(
                            remove_accents_lower(player_obj["city"]), None)

                        if state is not None:
                            player_obj["state"] = state

        return player_obj

    def LoadPlayersFromSmashGGTournamentProgress(self, n):
        print(f"Downloading players from tournament... {n}%")
        self.SaveDB()
        self.signals.SetupAutocomplete.emit()

    def LoadPlayersFromSmashGGTournamentFinished(self):
        self.SaveDB()
        self.signals.SetupAutocomplete.emit()

    def LoadSetsFromSmashGGTournament(self):
        if self.settings.get("SMASHGG_KEY", None) is None:
            self.SetSmashggKey()

        key = self.settings.get("SMASHGG_KEY", None)

        if self.settings.get("SMASHGG_TOURNAMENT_SLUG", None) is None:
            self.SetSmashggEventSlug()

        slug = self.settings.get("SMASHGG_TOURNAMENT_SLUG", None)

        if slug == None:
            return

        sets = []
        page = 1

        while(True):
            try:
                r = requests.post(
                    'https://api.smash.gg/gql/alpha',
                    headers={
                        'Authorization': 'Bearer'+key,
                    },
                    json={
                        'query': '''
                        query evento($eventSlug: String!) {
                            event(slug: $eventSlug) {
                                videogame {
                                    id
                                }
                                sets(page: '''+str(page)+''', perPage: 64, sortType: MAGIC, filters: {hideEmpty: true, state: [0, 1, 2, 6]}) {
                                    nodes {
                                        id
                                        state
                                        fullRoundText
                                        slots {
                                            entrant {
                                                participants {
                                                    gamerTag
                                                }                                        
                                            }
                                        }
                                        phaseGroup {
                                            phase {
                                                name
                                            }
                                        }
                                        stream {
                                            streamName
                                            streamSource
                                        }
                                    }
                                    pageInfo {
                                        totalPages
                                    }
                                }
                            }
                        }''',
                        'variables': {
                            "eventSlug": slug
                        },
                    }
                )
                resp = json.loads(r.text)

                gameId = resp.get("data", {}).get("event", {}).get(
                    "videogame", {}).get("id", None)
                if resp is not None and gameId:
                    self.signals.DetectGame.emit(gameId)

                if resp is None or \
                        resp.get("data") is None or \
                        resp["data"].get("event") is None or \
                        resp["data"]["event"].get("sets") is None:
                    print(resp)

                sets += resp["data"]["event"]["sets"]["nodes"]

                if page >= resp["data"]["event"]["sets"]["pageInfo"]["totalPages"]:
                    break

                page += 1
            except Exception as e:
                print(traceback.format_exc())
                return

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            ["Stream", "Wave", "Set", "Player 1", "Player 2"])

        if sets is not None:
            for s in sets:
                if s["slots"][0].get("entrant", None) and s["slots"][1].get("entrant", None):
                    model.appendRow([
                        QStandardItem(s.get("stream", {}).get(
                            "streamName", "") if s.get("stream") != None else ""),
                        QStandardItem(s.get("phaseGroup", {}).get(
                            "phase", {}).get("name", "")),
                        QStandardItem(s["fullRoundText"]),
                        QStandardItem(s["slots"][0]["entrant"]
                                      ["participants"][0]["gamerTag"]),
                        QStandardItem(s["slots"][1]["entrant"]
                                      ["participants"][0]["gamerTag"]),
                        QStandardItem(str(s["id"]))
                    ])

        self.smashGGSetSelecDialog = QDialog(self)
        self.smashGGSetSelecDialog.setWindowTitle("Select a set")
        self.smashGGSetSelecDialog.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        self.smashGGSetSelecDialog.setLayout(layout)

        proxyModel = QSortFilterProxyModel()
        proxyModel.setSourceModel(model)
        proxyModel.setFilterKeyColumn(-1)
        proxyModel.setFilterCaseSensitivity(False)

        def filterList(text):
            proxyModel.setFilterFixedString(text)

        searchBar = QLineEdit()
        searchBar.setPlaceholderText("Filter...")
        layout.addWidget(searchBar)
        searchBar.textEdited.connect(filterList)

        self.smashggSetSelectionItemList = QTableView()
        layout.addWidget(self.smashggSetSelectionItemList)
        self.smashggSetSelectionItemList.setSortingEnabled(True)
        self.smashggSetSelectionItemList.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.smashggSetSelectionItemList.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.smashggSetSelectionItemList.setModel(proxyModel)
        self.smashggSetSelectionItemList.setColumnHidden(5, True)
        self.smashggSetSelectionItemList.horizontalHeader().setStretchLastSection(True)
        self.smashggSetSelectionItemList.horizontalHeader(
        ).setSectionResizeMode(QHeaderView.Stretch)
        self.smashggSetSelectionItemList.resizeColumnsToContents()

        btOk = QPushButton("OK")
        layout.addWidget(btOk)
        btOk.clicked.connect(self.SetFromSmashGGSelected)

        self.smashGGSetSelecDialog.show()
        self.smashGGSetSelecDialog.resize(1200, 500)

    def SetFromSmashGGSelected(self):
        row = self.smashggSetSelectionItemList.selectionModel().selectedRows()[
            0].row()
        setId = self.smashggSetSelectionItemList.model().index(row, 5).data()
        self.LoadPlayersFromSmashGGSet(setId)
        self.smashGGSetSelecDialog.close()

        self.smashggSetAutoUpdateId = setId
        self.SetTimer("Auto (SmashGG Set: "+setId+")",
                      self.UpdateDataFromSmashGGSet)

    def LoadSetsFromSmashGGTournamentQueueClicked(self):
        if self.getFromStreamQueueBt.isHidden():
            return

        if self.settings.get("twitch_username", None) == None:
            self.SetTwitchUsername()

        twitch_username = self.settings["twitch_username"]

        if self.settings.get("SMASHGG_TOURNAMENT_SLUG", None) is None:
            self.SetSmashggEventSlug()

        slug = self.settings["SMASHGG_TOURNAMENT_SLUG"]

        if self.settings.get("SMASHGG_KEY", None) is None:
            self.SetSmashggKey()

        r = requests.post(
            'https://api.smash.gg/gql/alpha',
            headers={
                'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
            },
            json={
                'query': '''
                query evento($eventSlug: String!) {
                    event(slug: $eventSlug) {
                        videogame {
                            id
                        }
                        tournament {
                            streamQueue {
                                sets {
                                    id
                                    fullRoundText
                                    slots {
                                        entrant {
                                            participants {
                                                gamerTag
                                            }                                        
                                        }
                                    }
                                }
                                stream {
                                    streamName
                                    streamSource
                                }
                            }
                        }
                    }
                }''',
                'variables': {
                    "eventSlug": slug
                },
            }
        )
        resp = json.loads(r.text)

        gameId = resp.get("data", {}).get("event", {}).get(
            "videogame", {}).get("id", None)
        if resp is not None and gameId:
            self.signals.DetectGame.emit(gameId)

        streamSets = resp["data"]["event"]["tournament"]["streamQueue"]

        if streamSets is not None:
            for s in streamSets:
                if s["stream"]["streamName"].lower() == twitch_username.lower():
                    if s["sets"][0]["slots"][0].get("entrant", None) is not None and \
                            s["sets"][0]["slots"][1].get("entrant", None) is not None:
                        self.LoadPlayersFromSmashGGSet(s["sets"][0]["id"])

    def LoadUserSetFromSmashGGTournament(self):
        if self.competitorModeSmashggBt.isHidden():
            return

        if self.settings.get("smashgg_user_id", None) == None:
            self.SetSmashggUserId()

        smashgg_username = self.settings["smashgg_user_id"]

        slug = self.settings["SMASHGG_TOURNAMENT_SLUG"]

        if self.settings.get("SMASHGG_KEY", None) is None:
            self.SetSmashggKey()

        def myFun(self, progress_callback):
            if self.smashggSetAutoUpdateId is None:
                r = requests.post(
                    'https://api.smash.gg/gql/alpha',
                    headers={
                        'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
                    },
                    json={
                        'query': '''
                        query user($playerSlug: String!) {
                            user(slug: $playerSlug) {
                                player {
                                    sets(page: 1, perPage: 1) {
                                        nodes{
                                            id
                                        }
                                    }
                                }
                            }
                        }''',
                        'variables': {
                            "playerSlug": smashgg_username
                        },
                    }
                )
                resp = json.loads(r.text)

                sets = resp.get("data", {}).get("user", {}).get(
                    "player", {}).get("sets", {}).get("nodes", [])

                if len(sets) == 0:
                    return

                self.smashggSetAutoUpdateId = sets[0]["id"]
                progress_callback.emit(0)
            else:
                self.UpdateDataFromSmashGGSet()

        def myFun2(progress):
            self.LoadPlayersFromSmashGGSet()

        worker = Worker(myFun, *{self})
        worker.signals.progress.connect(myFun2)
        self.threadpool.start(worker)

    def LoadPlayersFromSmashGGSet(self, setId=None):
        if setId == None:
            setId = self.smashggSetAutoUpdateId

        if setId == None:
            return

        if self.settings.get("SMASHGG_KEY", None) is None:
            self.SetSmashggKey()

        def myFun(self, progress_callback, setId):
            pool = QThreadPool()

            def fun1(self, progress_callback):
                print("Try old smashgg api")
                r = requests.get(
                    f'https://smash.gg/api/-/gg_api./set/{setId};bustCache=true;expand=["setTask"];fetchMostRecentCached=true',
                    {
                        "extensions": {"cacheControl": {"version": 1, "noCache": True}},
                        "cacheControl": {"version": 1, "noCache": True},
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache"
                    }
                )
                self.respTasks = json.loads(r.text)
                print("Got response from old smashgg api")

            def fun2(self, progress_callback):
                print("Try new smashgg api")
                r = requests.post(
                    'https://api.smash.gg/gql/alpha',
                    headers={
                        'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
                    },
                    json={
                        'query': '''
                        query set($setId: ID!) {
                            set(id: $setId) {
                                event {
                                    hasTasks
                                    videogame {
                                        id
                                    }
                                }
                                fullRoundText
                                state
                                totalGames
                                slots {
                                    entrant {
                                        id
                                        participants {
                                            id
                                            user {
                                                id
                                                slug
                                                name
                                                authorizations(types: [TWITTER]) {
                                                    type
                                                    externalUsername
                                                }
                                                location {
                                                    city
                                                    country
                                                    state
                                                }
                                                images(type: "profile") {
                                                    url
                                                }
                                            }
                                            player {
                                                id
                                                gamerTag
                                                prefix
                                                sets(page: 1, perPage: 1) {
                                                    nodes {
                                                        games {
                                                            selections {
                                                                entrant {
                                                                    participants {
                                                                        player {
                                                                            id
                                                                        }
                                                                    }
                                                                }
                                                                selectionValue
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                                games {
                                    selections {
                                        entrant {
                                            id
                                            participants {
                                                player {
                                                    id
                                                }
                                            }
                                        }
                                        selectionValue
                                    }
                                    winnerId
                                }
                            }
                        }''',
                        'variables': {
                            "setId": setId
                        },
                    }
                )
                self.setData = json.loads(r.text)
                gameId = self.setData.get("data", {}).get("set", {}).get(
                    "event", {}).get("videogame", {}).get("id", None)
                if self.setData is not None and gameId:
                    self.signals.DetectGame.emit(gameId)
                print("Got response from new smashgg api")

            worker1 = Worker(fun1, *{self})
            pool.start(worker1)
            worker2 = Worker(fun2, *{self})
            pool.start(worker2)

            res = pool.waitForDone(5000)

            if res == False:
                pool.cancel(worker1)
                pool.cancel(worker2)
            else:
                print("Finished")
                return

        def myFun2():
            print("hey3")
            nonlocal self
            try:
                tasks = self.respTasks.get("entities", {}).get("setTask", [])
                setData = self.respTasks.get("entities", {}).get("sets", {})

                selectedChars = {}

                for task in reversed(tasks):
                    if task.get("action") == "setup_character" or task.get("action") == "setup_strike":
                        selectedChars = task.get(
                            "metadata", {}).get("charSelections", {})
                        break

                latestWinner = None

                for task in reversed(tasks):
                    if len(task.get("metadata", [])) == 0:
                        continue
                    if task.get("metadata", {}).get("report", {}).get("winnerId", None) is not None:
                        latestWinner = int(task.get("metadata", {}).get(
                            "report", {}).get("winnerId"))
                        break

                allStages = None
                strikedStages = None
                selectedStage = None
                dsrStages = None
                playerTurn = None

                for task in reversed(tasks):
                    if task.get("action") in ["setup_strike", "setup_stage", "setup_character", "setup_ban", "report"]:
                        if len(task.get("metadata", [])) == 0:
                            continue

                        base = task.get("metadata", {})

                        if task.get("action") == "report":
                            base = base.get("report", {})

                        print(base)

                        if base.get("strikeStages", None) is not None:
                            allStages = base.get("strikeStages")
                        elif base.get("banStages", None) is not None:
                            allStages = base.get("banStages")

                        if base.get("strikeList", None) is not None:
                            strikedStages = base.get("strikeList")
                        elif base.get("banList", None) is not None:
                            strikedStages = base.get("banList")

                        if base.get("stageSelection", None) is not None:
                            selectedStage = base.get("stageSelection")
                        elif base.get("stageId", None) is not None:
                            selectedStage = base.get("stageId")

                        if (base.get("useDSR") or base.get("useMDSR")) and base.get("stageWins"):

                            loser = next(
                                (p for p in base.get("stageWins").keys()
                                 if int(p) != int(latestWinner)),
                                None
                            )

                            if loser is not None:
                                dsrStages = []
                                dsrStages = [int(s) for s in base.get(
                                    "stageWins")[loser]]

                        if allStages == None and strikedStages == None and selectedStage == None:
                            continue

                        if allStages == None:
                            continue

                        break

                changed = False

                try:
                    stageStrikeState = {
                        "stages": {st: self.stages[st] for st in [next(s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id")) == str(stage)) for stage in allStages]} if allStages != None else {},
                        "striked": [next(s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id")) == str(stage)) for stage in strikedStages] if strikedStages != None else [],
                        "selected": next((s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id")) == str(selectedStage)), ""),
                        "dsr": [next(s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id")) == str(stage)) for stage in dsrStages] if dsrStages != None else [],
                        "playerTurn": playerTurn
                    }
                except:
                    print(traceback.format_exc())
                    stageStrikeState = {}

                if "stage_strike" in self.programState:
                    if json.dumps(stageStrikeState) != json.dumps(self.programState["stage_strike"]):
                        changed = True
                else:
                    changed = True

                if changed:
                    self.signals.ExportStageStrike.emit({
                        "allStages": allStages,
                        "strikedStages": strikedStages,
                        "dsrStages": dsrStages,
                        "selectedStage": selectedStage
                    })

                self.programState["stage_strike"] = stageStrikeState
                self.ExportProgramState()

                resp = self.setData

                if resp["data"]["set"].get("state", 0) == 3:
                    if self.autoTimer != None and self.smashggSetAutoUpdateId != None:
                        print("Set ended")
                        if not self.settings.get("competitor_mode", False):
                            self.signals.StopTimer.emit()
                        else:
                            self.smashggSetAutoUpdateId = None

                if resp["data"]["set"]["event"]["hasTasks"] == False:
                    if self.autoTimer != None and self.smashggSetAutoUpdateId != None:
                        print("Event has no tasks")
                        if not self.settings.get("competitor_mode", False):
                            self.signals.StopTimer.emit()
                        else:
                            self.smashggSetAutoUpdateId = None

                # Set phase name
                self.tournament_phase.setCurrentText(
                    resp["data"]["set"]["fullRoundText"])

                id0 = 0
                id1 = 1

                # Get first player
                user = resp["data"]["set"]["slots"][0]["entrant"]["participants"][0]["user"]
                player = resp["data"]["set"]["slots"][0]["entrant"]["participants"][0]["player"]
                entrant = resp["data"]["set"]["slots"][0]["entrant"]

                player_obj = self.LoadSmashGGPlayer(
                    user, player, entrant.get("id", None), selectedChars)

                if self.settings.get("competitor_mode", False) and \
                        len(self.settings.get("smashgg_user_id", "")) > 0:
                    if user.get("slug", None) != self.settings.get("smashgg_user_id", ""):
                        id0 = 1
                        id1 = 0

                if self.playersInverted:
                    id0 = 1
                    id1 = 0

                self.player_layouts[id0].signals.UpdatePlayer.emit(player_obj)

                print("--------")
                print(entrant["id"])
                print(resp["data"]["set"].get("games", None))

                # Update score
                score = 0
                if resp["data"]["set"].get("games", None) != None:
                    score = len([game for game in resp["data"]["set"].get(
                        "games", {}) if game.get("winnerId", -1) == entrant.get("id", None)])
                [self.scoreLeft, self.scoreRight][id0].setValue(score)

                # Get second player
                user = resp["data"]["set"]["slots"][1]["entrant"]["participants"][0]["user"]
                player = resp["data"]["set"]["slots"][1]["entrant"]["participants"][0]["player"]
                entrant = resp["data"]["set"]["slots"][1]["entrant"]
                player_obj = self.LoadSmashGGPlayer(
                    user, player, entrant.get("id", None), selectedChars)

                self.player_layouts[id1].signals.UpdatePlayer.emit(player_obj)

                # Update score
                score = 0
                if resp["data"]["set"].get("games", None) != None:
                    score = len([game for game in resp["data"]["set"].get(
                        "games", {}) if game.get("winnerId", -1) == entrant.get("id", None)])
                [self.scoreLeft, self.scoreRight][id1].setValue(score)

                # Update bestOf
                self.bestOf.setValue(setData.get("bestOf", 0))

                # Update losers
                if setData.get("isGF", False) == True:
                    # :P
                    if "Reset" not in setData.get("fullRoundText", ""):
                        self.player_layouts[id0].losersCheckbox.setCheckState(
                            0)
                        self.player_layouts[id1].losersCheckbox.setCheckState(
                            2)
                    else:
                        self.player_layouts[id0].losersCheckbox.setCheckState(
                            2)
                        self.player_layouts[id1].losersCheckbox.setCheckState(
                            2)
                else:
                    self.player_layouts[id0].losersCheckbox.setCheckState(0)
                    self.player_layouts[id1].losersCheckbox.setCheckState(0)

            except Exception as e:
                print(traceback.format_exc())

        worker = Worker(myFun, *{self}, **{"setId": setId})
        worker.signals.finished.connect(myFun2)
        self.threadpool.start(worker)

    def UpdateDataFromSmashGGSet(self, setId=None):
        if setId == None:
            setId = self.smashggSetAutoUpdateId

        if setId == None:
            return

        if self.settings.get("SMASHGG_KEY", None) is None:
            self.SetSmashggKey()

        def myFun(self, progress_callback, setId):
            pool = QThreadPool()

            def fun1(self, progress_callback):
                print("Try old smashgg api")
                r = requests.get(
                    f'https://smash.gg/api/-/gg_api./set/{setId};bustCache=true;expand=["setTask"];fetchMostRecentCached=true',
                    {
                        "extensions": {"cacheControl": {"version": 1, "noCache": True}},
                        "cacheControl": {"version": 1, "noCache": True},
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache"
                    }
                )
                self.respTasks = json.loads(r.text)
                print("Got response from old smashgg api")

            def fun2(self, progress_callback):
                print("Try new smashgg api")
                r = requests.post(
                    'https://api.smash.gg/gql/alpha',
                    headers={
                        'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
                    },
                    json={
                        'query': '''
                        query set($setId: ID!) {
                            set(id: $setId) {
                                event {
                                    hasTasks
                                    videogame {
                                        id
                                    }
                                }
                                state
                                slots {
                                    entrant {
                                        id
                                        participants {
                                            id
                                            user {
                                                id
                                                slug
                                            }
                                        }
                                    }
                                }
                                games {
                                    selections {
                                        entrant {
                                            id
                                            participants {
                                                player {
                                                    id
                                                }
                                            }
                                        }
                                        selectionValue
                                    }
                                    winnerId
                                }
                            }
                        }''',
                        'variables': {
                            "setId": setId
                        },
                    }
                )
                self.setData = json.loads(r.text)
                print(self.setData)
                print("Got response from new smashgg api")
                gameId = self.setData.get("data", {}).get("set", {}).get(
                    "event", {}).get("videogame", {}).get("id", None)
                if gameId:
                    self.signals.DetectGame.emit(gameId)

            worker1 = Worker(fun1, *{self})
            pool.start(worker1)
            worker2 = Worker(fun2, *{self})
            pool.start(worker2)

            res = pool.waitForDone(5000)

            if res == False:
                pool.cancel(worker1)
                pool.cancel(worker2)
            else:
                return

        def myFun2():
            print("Hey2")
            nonlocal self
            try:
                tasks = self.respTasks.get("entities", {}).get("setTask", [])

                selectedChars = {}

                for task in reversed(tasks):
                    if task.get("action") == "setup_character" or task.get("action") == "setup_strike":
                        selectedChars = task.get(
                            "metadata", {}).get("charSelections", {})
                        break

                latestWinner = None

                for task in reversed(tasks):
                    if len(task.get("metadata", [])) == 0:
                        continue
                    if task.get("metadata", {}).get("report", {}).get("winnerId", None) is not None:
                        latestWinner = int(task.get("metadata", {}).get(
                            "report", {}).get("winnerId"))
                        break

                allStages = None
                strikedStages = None
                selectedStage = None
                dsrStages = None
                playerTurn = None

                for task in reversed(tasks):
                    if task.get("action") in ["setup_strike", "setup_stage", "setup_character", "setup_ban", "report"]:
                        if len(task.get("metadata", [])) == 0:
                            continue

                        base = task.get("metadata", {})

                        if task.get("action") == "report":
                            base = base.get("report", {})

                        print(base)

                        if base.get("strikeStages", None) is not None:
                            allStages = base.get("strikeStages")
                        elif base.get("banStages", None) is not None:
                            allStages = base.get("banStages")

                        if base.get("strikeList", None) is not None:
                            strikedStages = base.get("strikeList")
                        elif base.get("banList", None) is not None:
                            strikedStages = base.get("banList")

                        if base.get("stageSelection", None) is not None:
                            selectedStage = base.get("stageSelection")
                        elif base.get("stageId", None) is not None:
                            selectedStage = base.get("stageId")

                        if (base.get("useDSR") or base.get("useMDSR")) and base.get("stageWins"):

                            loser = next(
                                (p for p in base.get("stageWins").keys()
                                 if int(p) != int(latestWinner)),
                                None
                            )

                            if loser is not None:
                                dsrStages = []
                                dsrStages = [int(s) for s in base.get(
                                    "stageWins")[loser]]

                        if allStages == None and strikedStages == None and selectedStage == None:
                            continue

                        if allStages == None:
                            continue

                        break

                changed = False

                try:
                    stageStrikeState = {
                        "stages": {st: self.stages[st] for st in [next(s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id", None)) == str(stage)) for stage in allStages]} if allStages != None else {},
                        "striked": [next(s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id")) == str(stage)) for stage in strikedStages] if strikedStages != None else [],
                        "selected": next((s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id")) == str(selectedStage)), ""),
                        "dsr": [next(s for s in self.stages.keys() if str(self.stages[s].get("smashgg_id")) == str(stage)) for stage in dsrStages] if dsrStages != None else [],
                        "playerTurn": playerTurn
                    }
                except:
                    print(traceback.format_exc())
                    stageStrikeState = {}

                if "stage_strike" in self.programState:
                    if json.dumps(stageStrikeState) != json.dumps(self.programState["stage_strike"]):
                        changed = True
                else:
                    changed = True

                if changed:
                    self.signals.ExportStageStrike.emit({
                        "allStages": allStages,
                        "strikedStages": strikedStages,
                        "dsrStages": dsrStages,
                        "selectedStage": selectedStage
                    })

                self.programState["stage_strike"] = stageStrikeState
                self.ExportProgramState()

                resp = self.setData

                if resp["data"]["set"].get("state", 0) == 3:
                    if self.autoTimer != None and self.smashggSetAutoUpdateId != None:
                        print("Set ended")
                        if not self.settings.get("competitor_mode", False):
                            self.signals.StopTimer.emit()
                        else:
                            self.smashggSetAutoUpdateId = None

                if resp["data"]["set"]["event"]["hasTasks"] == False:
                    if self.autoTimer != None and self.smashggSetAutoUpdateId != None:
                        print("Event has no tasks")
                        if not self.settings.get("competitor_mode", False):
                            self.signals.StopTimer.emit()
                        else:
                            self.smashggSetAutoUpdateId = None

                id0 = 0
                id1 = 1

                # Get first player
                user = resp["data"]["set"]["slots"][0]["entrant"]["participants"][0]["user"]
                entrant = resp["data"]["set"]["slots"][0]["entrant"]

                character = None

                if str(entrant.get("id", None)) in selectedChars:
                    found = None
                    if len(selectedChars[str(entrant["id"])]) > 0:
                        found = next((c for c in self.smashgg_character_data["character"] if c["id"] == selectedChars[str(
                            entrant["id"])][0]), None)
                    if found:
                        character = found["name"]

                if self.settings.get("competitor_mode", False) and \
                        len(self.settings.get("smashgg_user_id", "")) > 0:
                    if user.get("slug", None) != self.settings.get("smashgg_user_id", ""):
                        id0 = 1
                        id1 = 0

                if self.playersInverted:
                    id0 = 1
                    id1 = 0

                if self.player_layouts[id0].player_character.currentText() != character and character != None:
                    self.player_layouts[id0].signals.UpdateCharacter.emit(
                        character)

                print("--------")
                print(entrant["id"])
                print(resp["data"]["set"].get("games", None))

                # Update score
                score = 0
                if resp["data"]["set"].get("games", None) != None:
                    score = len([game for game in resp["data"]["set"].get(
                        "games", {}) if game.get("winnerId", -1) == entrant.get("id", None)])
                [self.scoreLeft, self.scoreRight][id0].setValue(score)

                # Get second player
                user = resp["data"]["set"]["slots"][1]["entrant"]["participants"][0]["user"]
                entrant = resp["data"]["set"]["slots"][1]["entrant"]

                character = None

                if str(entrant.get("id", None)) in selectedChars:
                    found = None
                    if len(selectedChars[str(entrant["id"])]) > 0:
                        found = next((c for c in self.smashgg_character_data["character"] if c["id"] == selectedChars[str(
                            entrant["id"])][0]), None)
                    if found:
                        character = found["name"]

                if self.player_layouts[id1].player_character.currentText() != character and character != None:
                    self.player_layouts[id1].signals.UpdateCharacter.emit(
                        character)

                # Update score
                score = 0
                if resp["data"]["set"].get("games", None) != None:
                    score = len([game for game in resp["data"]["set"].get(
                        "games", {}) if game.get("winnerId", -1) == entrant.get("id", None)])
                [self.scoreLeft, self.scoreRight][id1].setValue(score)
            except Exception as e:
                print(traceback.format_exc())

        worker = Worker(myFun, *{self}, **{"setId": setId})
        worker.signals.finished.connect(myFun2)
        self.threadpool.start(worker)


App = QApplication(sys.argv)

if os.path.isfile("./program_assets/style.qss"):
    with open("./program_assets/style.qss", "r") as f:
        App.setStyleSheet(f.read())
else:
    print("Stylesheet file not found\n")

window = Window()
sys.exit(App.exec_())
