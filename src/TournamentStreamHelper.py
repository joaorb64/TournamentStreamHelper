#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import PyQt5
from PyQt5 import QtGui, QtWidgets, QtCore

from src.TSHAboutWidget import TSHAboutWidget
from src.TSHAssetDownloader import TSHAssetDownloader
from .TSHThumbnailSettingsWidget import *
from .TSHScoreboardWidget import *
from .Workers import *
from .TSHPlayerDB import TSHPlayerDB
from .TSHAlertNotification import TSHAlertNotification
from .TournamentDataProvider.StartGGDataProvider import StartGGDataProvider
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHTournamentInfoWidget import TSHTournamentInfoWidget
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHCommentaryWidget import TSHCommentaryWidget
from .TSHPlayerListWidget import TSHPlayerListWidget
from qdarkstyle import palette
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import shutil
import tarfile
import py7zr

import qdarkstyle

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

App = QApplication(sys.argv)

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.stderr = open('./assets/log_error.txt', 'w', encoding="utf-8")
    sys.stdout = open('./assets/log.txt', 'w', encoding="utf-8")


def remove_accents_lower(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


class WindowSignals(QObject):
    StopTimer = pyqtSignal()
    ExportStageStrike = pyqtSignal(object)
    DetectGame = pyqtSignal(int)
    SetupAutocomplete = pyqtSignal()
    UiMounted = pyqtSignal()


class Window(QMainWindow):
    signals = WindowSignals()

    def __init__(self):
        super().__init__()

        self.signals = WindowSignals()

        splash = QSplashScreen(self, QPixmap(
            'assets/icons/icon.png').scaled(128, 128))
        splash.show()

        time.sleep(0.1)

        App.processEvents()

        self.programState = {}
        self.savedProgramState = {}
        self.programStateDiff = {}

        self.setWindowIcon(QIcon('assets/icons/icon.png'))

        if not os.path.exists("out/"):
            os.mkdir("out/")

        if not os.path.exists("./user_data/games"):
            os.makedirs("./user_data/games")

        if os.path.exists("./TSH_old.exe"):
            os.remove("./TSH_old.exe")

        self.font_small = QFont(
            "./assets/font/RobotoCondensed.ttf", pointSize=8)

        self.threadpool = QThreadPool()
        self.saveMutex = QMutex()

        self.player_layouts = []

        self.allplayers = None
        self.local_players = None

        try:
            version = json.load(
                open('./assets/versions.json', encoding='utf-8')).get("program", "?")
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
        central_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.dockWidgets = []

        thumbnailSetting = TSHThumbnailSettingsWidget()
        thumbnailSetting.setObjectName("Thumbnail Settings")
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, thumbnailSetting)
        self.dockWidgets.append(thumbnailSetting)

        tournamentInfo = TSHTournamentInfoWidget()
        tournamentInfo.setWindowIcon(QIcon('assets/icons/info.svg'))
        tournamentInfo.setObjectName("Tournament Info")
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, tournamentInfo)
        self.dockWidgets.append(tournamentInfo)

        self.scoreboard = TSHScoreboardWidget()
        self.scoreboard.setWindowIcon(QIcon('assets/icons/list.svg'))
        self.scoreboard.setObjectName("Scoreboard")
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.scoreboard)
        self.dockWidgets.append(self.scoreboard)

        commentary = TSHCommentaryWidget()
        commentary.setWindowIcon(QIcon('assets/icons/mic.svg'))
        commentary.setObjectName("Commentary")
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, commentary)
        self.dockWidgets.append(commentary)

        playerList = TSHPlayerListWidget()
        playerList.setWindowIcon(QIcon('assets/icons/list.svg'))
        playerList.setObjectName("Player List")
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, playerList)
        self.dockWidgets.append(playerList)

        self.tabifyDockWidget(self.scoreboard, commentary)
        self.tabifyDockWidget(self.scoreboard, tournamentInfo)
        self.tabifyDockWidget(self.scoreboard, thumbnailSetting)
        self.tabifyDockWidget(self.scoreboard, playerList)
        self.scoreboard.raise_()

        # pre_base_layout.setSpacing(0)
        # pre_base_layout.setContentsMargins(QMargins(0, 0, 0, 0))

        # Game
        base_layout = QHBoxLayout()

        group_box = QWidget()
        group_box.setLayout(QVBoxLayout())
        group_box.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Maximum)
        base_layout.layout().addWidget(group_box)

        self.setTournamentBt = QPushButton("Set tournament")
        group_box.layout().addWidget(self.setTournamentBt)
        self.setTournamentBt.clicked.connect(
            lambda bt, s=self: TSHTournamentDataProvider.instance.SetStartggEventSlug(s))

        # Follow startgg user
        hbox = QHBoxLayout()
        group_box.layout().addLayout(hbox)

        self.btLoadPlayerSet = QPushButton("Load startgg user set")
        self.btLoadPlayerSet.setIcon(QIcon("./assets/icons/startgg.svg"))
        self.btLoadPlayerSet.setEnabled(False)
        self.btLoadPlayerSet.clicked.connect(self.LoadUserSetClicked)
        self.btLoadPlayerSet.setIcon(QIcon("./assets/icons/startgg.svg"))
        hbox.addWidget(self.btLoadPlayerSet)
        TSHTournamentDataProvider.instance.signals.user_updated.connect(
            self.UpdateUserSetButton)
        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.UpdateUserSetButton)

        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.UpdateUserSetButton)

        self.btLoadPlayerSetOptions = QPushButton()
        self.btLoadPlayerSetOptions.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.btLoadPlayerSetOptions.setIcon(
            QIcon("./assets/icons/settings.svg"))
        self.btLoadPlayerSetOptions.clicked.connect(
            self.LoadUserSetOptionsClicked)
        hbox.addWidget(self.btLoadPlayerSetOptions)

        # Settings
        self.optionsBt = QToolButton()
        self.optionsBt.setIcon(QIcon('assets/icons/menu.svg'))
        self.optionsBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.optionsBt.setPopupMode(QToolButton.InstantPopup)
        base_layout.addWidget(self.optionsBt)
        self.optionsBt.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.optionsBt.setFixedSize(QSize(32, 32))
        self.optionsBt.setIconSize(QSize(32, 32))
        self.optionsBt.setMenu(QMenu())
        action = self.optionsBt.menu().addAction("Always on top")
        action.setCheckable(True)
        action.toggled.connect(self.ToggleAlwaysOnTop)
        action = self.optionsBt.menu().addAction("Check for updates")
        self.updateAction = action
        action.setIcon(QIcon('assets/icons/undo.svg'))
        action.triggered.connect(self.CheckForUpdates)
        action = self.optionsBt.menu().addAction("Download assets")
        action.setIcon(QIcon('assets/icons/download.svg'))
        action.triggered.connect(TSHAssetDownloader.instance.DownloadAssets)

        action = self.optionsBt.menu().addAction("Light mode")
        action.setCheckable(True)
        self.LoadTheme()
        action.setChecked(SettingsManager.Get("light_mode", False))
        action.toggled.connect(self.ToggleLightMode)

        toggleWidgets = QMenu("Toggle widgets", self.optionsBt.menu())
        self.optionsBt.menu().addMenu(toggleWidgets)
        toggleWidgets.addAction(self.scoreboard.toggleViewAction())
        toggleWidgets.addAction(commentary.toggleViewAction())
        toggleWidgets.addAction(thumbnailSetting.toggleViewAction())
        toggleWidgets.addAction(tournamentInfo.toggleViewAction())
        toggleWidgets.addAction(playerList.toggleViewAction())

        self.aboutWidget = TSHAboutWidget()
        action = self.optionsBt.menu().addAction("About")
        action.setIcon(QIcon('assets/icons/info.svg'))
        action.triggered.connect(lambda: self.aboutWidget.show())

        self.gameSelect = QComboBox()
        self.gameSelect.setEditable(True)
        self.gameSelect.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.gameSelect.completer().setCompletionMode(QCompleter.PopupCompletion)
        proxyModel = QSortFilterProxyModel()
        proxyModel.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        proxyModel.setSourceModel(self.gameSelect.model())
        self.gameSelect.model().setParent(proxyModel)
        self.gameSelect.setModel(proxyModel)
        self.gameSelect.setFont(self.font_small)
        self.gameSelect.activated.connect(
            lambda x: TSHGameAssetManager.instance.LoadGameAssets(self.gameSelect.currentData()))
        TSHGameAssetManager.instance.signals.onLoad.connect(
            self.SetGame)
        TSHGameAssetManager.instance.signals.onLoadAssets.connect(
            self.ReloadGames)
        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.SetGame)

        pre_base_layout.addLayout(base_layout)
        group_box.layout().addWidget(self.gameSelect)

        self.CheckForUpdates(True)
        self.ReloadGames()

        self.qtSettings = QSettings("joao_shino", "TournamentStreamHelper")

        if self.qtSettings.value("geometry"):
            self.restoreGeometry(self.qtSettings.value("geometry"))

        if self.qtSettings.value("windowState"):
            self.restoreState(self.qtSettings.value("windowState"))

        splash.finish(self)
        self.show()

        TSHTournamentDataProvider.instance.UiMounted()
        TSHGameAssetManager.instance.UiMounted()
        TSHAlertNotification.instance.UiMounted()
        TSHPlayerDB.LoadDB()

    def SetGame(self):
        index = next((i for i in range(self.gameSelect.model().rowCount()) if self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get(
            "name") or self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get("codename")), None)
        if index is not None:
            self.gameSelect.setCurrentIndex(index)

    def UpdateUserSetButton(self):
        if SettingsManager.Get("StartGG_user"):
            self.btLoadPlayerSet.setText(
                f"Load tournament and sets from startgg user ({SettingsManager.Get('StartGG_user')})")
            self.btLoadPlayerSet.setEnabled(True)
        else:
            self.btLoadPlayerSet.setText(
                "Load tournament and sets from startgg user")
            self.btLoadPlayerSet.setEnabled(False)

    def LoadUserSetClicked(self):
        self.scoreboard.lastSetSelected = None
        if SettingsManager.Get("StartGG_user"):
            TSHTournamentDataProvider.instance.provider = StartGGDataProvider(
                "start.gg/",
                TSHTournamentDataProvider.instance.threadPool,
                TSHTournamentDataProvider.instance
            )
            TSHTournamentDataProvider.instance.LoadUserSet(
                self.scoreboard, SettingsManager.Get("StartGG_user"))

    def LoadUserSetOptionsClicked(self):
        TSHTournamentDataProvider.instance.SetUserAccount(
            self.scoreboard, startgg=True)

    def closeEvent(self, event):
        self.qtSettings.setValue("geometry", self.saveGeometry())
        self.qtSettings.setValue("windowState", self.saveState())
        if os.path.isdir("./tmp"):
            shutil.rmtree("./tmp")

    def ReloadGames(self):
        print("Reload games")
        self.gameSelect.setModel(QStandardItemModel())
        self.gameSelect.addItem("", 0)
        for i, game in enumerate(TSHGameAssetManager.instance.games.items()):
            if game[1].get("name"):
                self.gameSelect.addItem(game[1].get(
                    "logo", QIcon()), game[1].get("name"), i+1)
            else:
                self.gameSelect.addItem(
                    game[1].get("logo", QIcon()), game[0], i+1)
        self.gameSelect.setIconSize(QSize(64, 64))
        self.gameSelect.setFixedHeight(32)
        view = QListView()
        view.setIconSize(QSize(64, 64))
        view.setStyleSheet("QListView::item { height: 32px; }")
        self.gameSelect.setView(view)
        self.gameSelect.model().sort(0)
        self.SetGame()

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
            versions = json.load(
                open('./assets/versions.json', encoding='utf-8'))
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
                        "Update to latest version?\nNOTE: WILL BACKUP /layout/ AND OVERWRITE ALL OTHER DATA INSIDE /assets/"))

                    hbox = QHBoxLayout()
                    vbox.addLayout(hbox)

                    btUpdate = QPushButton("Update")
                    hbox.addWidget(btUpdate)
                    btCancel = QPushButton("Cancel")
                    hbox.addWidget(btCancel)

                    buttonReply.show()

                    def Update():
                        db = QFontDatabase()
                        db.removeAllApplicationFonts()
                        self.downloadDialogue = QProgressDialog(
                            "Downloading update... ", "Cancel", 0, 0, self)
                        self.downloadDialogue.setWindowModality(
                            Qt.WindowModality.WindowModal)
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

                            # backup layouts
                            os.rename(
                                "./layout", f"./layout_backup_{str(time.time())}")

                            # backup exe
                            os.rename("./TSH.exe", "./TSH_old.exe")

                            for m in tar.getmembers():
                                if "/" in m.name:
                                    m.name = m.name.split("/", 1)[1]
                                    tar.extract(m)
                            tar.close()
                            os.remove("update.tar.gz")

                            with open('./assets/versions.json', 'w') as outfile:
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
                    baseIcon = QPixmap(
                        QImage("assets/icons/menu.svg").scaled(32, 32))
                    updateIcon = QImage(
                        "./assets/icons/update_circle.svg").scaled(12, 12)
                    p = QPainter(baseIcon)
                    p.drawImage(QPoint(20, 0), updateIcon)
                    p.end()
                    self.optionsBt.setIcon(QIcon(baseIcon))
                    self.updateAction.setText(
                        "Check for updates [Update available!]")

    def ToggleAlwaysOnTop(self, checked):
        if checked:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

    def ToggleLightMode(self, checked):
        if checked:
            App.setStyleSheet(qdarkstyle.load_stylesheet(
                palette=qdarkstyle.LightPalette))
        else:
            App.setStyleSheet(qdarkstyle.load_stylesheet(
                palette=qdarkstyle.DarkPalette))

        SettingsManager.Set("light_mode", checked)

    def LoadTheme(self):
        if SettingsManager.Get("light_mode", False):
            App.setStyleSheet(qdarkstyle.load_stylesheet(
                palette=qdarkstyle.LightPalette))
        else:
            App.setStyleSheet(qdarkstyle.load_stylesheet(
                palette=qdarkstyle.DarkPalette))


window = Window()
sys.exit(App.exec_())
