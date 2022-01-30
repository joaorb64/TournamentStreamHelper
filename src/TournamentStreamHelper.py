#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
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

    from qdarkstyle import palette
    from TSHCommentaryWidget import TSHCommentaryWidget
    from TSHGameAssetManager import TSHGameAssetManager
    from TSHTournamentInfoWidget import TSHTournamentInfoWidget
    from TSHTournamentDataProvider import TSHTournamentDataProvider
    from TSHPlayerDB import TSHPlayerDB
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
    UiMounted = pyqtSignal()


class Window(QMainWindow):
    signals = WindowSignals()

    def __init__(self):
        super().__init__()

        self.signals = WindowSignals()

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

        try:
            url = 'https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/countries%2Bstates%2Bcities.json'
            r = requests.get(url, allow_redirects=True)
            open('./assets/countries+states+cities.json', 'wb').write(r.content)
        except Exception as e:
            print("Could not update /assets/countries+states+cities.json: "+str(e))

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
        central_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        tournamentInfo = TSHTournamentInfoWidget()
        tournamentInfo.setObjectName("Tournament Info")
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, tournamentInfo)

        scoreboard = TSHScoreboardWidget()
        scoreboard.setObjectName("Scoreboard")
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, scoreboard)

        commentary = TSHCommentaryWidget()
        commentary.setObjectName("Commentary")
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, commentary)

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
            lambda bt, s=self: TSHTournamentDataProvider.instance.SetSmashggEventSlug(s))

        # Settings
        self.optionsBt = QToolButton()
        self.optionsBt.setIcon(QIcon('icons/menu.svg'))
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

        self.gameSelect = QComboBox()
        self.gameSelect.setFont(self.font_small)
        self.gameSelect.activated.connect(
            TSHGameAssetManager.instance.LoadGameAssets)
        TSHGameAssetManager.instance.signals.onLoad.connect(self.SetGame)

        pre_base_layout.addLayout(base_layout)
        group_box.layout().addWidget(self.gameSelect)

        # pre_base_layout.addLayout(group_box)

        # self.setTwitchUsernameAction = QAction(
        #     "Set Twitch username (" +
        #     str(self.settings.get("twitch_username", None)) + ")"
        # )
        # self.getFromStreamQueueBt.menu().addAction(self.setTwitchUsernameAction)
        # self.setTwitchUsernameAction.triggered.connect(self.SetTwitchUsername)

        # action = self.getFromStreamQueueBt.menu().addAction("Auto")
        # action.toggled.connect(self.ToggleAutoTwitchQueueMode)
        # action.setCheckable(True)
        # if self.settings.get("twitch_auto_mode", False):
        #     action.setChecked(True)
        #     self.SetTimer("Auto (StreamQueue)",
        #                   self.LoadSetsFromSmashGGTournamentQueueClicked)

        # # Load set from SmashGG tournament
        # self.smashggSelectSetBt = QToolButton()
        # self.smashggSelectSetBt.setText("Select set")
        # self.smashggSelectSetBt.setIcon(QIcon('icons/smashgg.svg'))
        # self.smashggSelectSetBt.setToolButtonStyle(
        #     Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # layout_end.addWidget(self.smashggSelectSetBt, 2, 1, 1, 1)
        # self.smashggSelectSetBt.clicked.connect(
        #     self.LoadSetsFromSmashGGTournament)
        # self.smashggSelectSetBt.setSizePolicy(
        #     QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        # self.smashggSelectSetBt.setPopupMode(QToolButton.MenuButtonPopup)
        # self.smashggSelectSetBt.setMenu(QMenu())

        # action = self.smashggSelectSetBt.menu().addAction("Set SmashGG key")
        # action.triggered.connect(self.SetSmashggKey)

        # self.smashggTournamentSlug = QAction(
        #     "Set tournament slug (" +
        #     str(self.settings.get("SMASHGG_TOURNAMENT_SLUG", None)) + ")"
        # )
        # self.smashggSelectSetBt.menu().addAction(self.smashggTournamentSlug)
        # self.smashggTournamentSlug.triggered.connect(self.SetSmashggEventSlug)

        # # Competitor mode smashgg button
        # self.competitorModeSmashggBt = QToolButton()
        # self.competitorModeSmashggBt.setText("Update from SmashGG set")
        # self.competitorModeSmashggBt.setIcon(QIcon('icons/smashgg.svg'))
        # self.competitorModeSmashggBt.setToolButtonStyle(
        #     Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # layout_end.addWidget(self.competitorModeSmashggBt, 2, 0, 1, 2)
        # self.competitorModeSmashggBt.clicked.connect(
        #     self.LoadUserSetFromSmashGGTournament)
        # self.competitorModeSmashggBt.setSizePolicy(
        #     QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        # self.competitorModeSmashggBt.setPopupMode(QToolButton.MenuButtonPopup)
        # self.competitorModeSmashggBt.setMenu(QMenu())

        # action = self.competitorModeSmashggBt.menu().addAction("Set SmashGG key")
        # action.triggered.connect(self.SetSmashggKey)

        # self.smashggUserId = QAction(
        #     "Set user id (" +
        #     str(self.settings.get("smashgg_user_id", None)) + ")"
        # )
        # self.competitorModeSmashggBt.menu().addAction(self.smashggUserId)
        # self.smashggUserId.triggered.connect(self.SetSmashggUserId)

        # action = self.competitorModeSmashggBt.menu().addAction("Auto")
        # action.toggled.connect(self.ToggleAutoCompetitorSmashGGMode)
        # action.setCheckable(True)
        # if self.settings.get("competitor_smashgg_auto_mode", False) and self.settings.get("competitor_mode", False):
        #     action.setChecked(True)
        #     self.SetTimer("Competitor: Auto (SmashGG)",
        #                   self.LoadUserSetFromSmashGGTournament)

        # if self.settings.get("competitor_mode", False) == False:
        #     self.competitorModeSmashggBt.hide()

        # # save button
        # self.saveBt = QToolButton()
        # self.saveBt.setText("Save and export")
        # self.saveBt.setIcon(QIcon('icons/save.svg'))
        # self.saveBt.setToolButtonStyle(
        #     Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # pal = self.saveBt.palette()
        # pal.setColor(QPalette.Button, QColor(Qt.green))
        # self.saveBt.setPalette(pal)
        # layout_end.addWidget(self.saveBt, 3, 0, 2, 2)
        # self.saveBt.setSizePolicy(
        #     QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # self.saveBt.setPopupMode(QToolButton.MenuButtonPopup)
        # self.saveBt.clicked.connect(self.SaveButtonClicked)

        # self.saveBt.setMenu(QMenu())

        # action = self.saveBt.menu().addAction("Auto")
        # action.setCheckable(True)
        # if "autosave" in self.settings:
        #     if self.settings["autosave"] == True:
        #         action.setChecked(True)
        # action.toggled.connect(self.ToggleAutosave)

        # action = self.saveBt.menu().addAction("Add @ to twitter")
        # action.setCheckable(True)
        # if "twitter_add_at" in self.settings:
        #     if self.settings["twitter_add_at"] == True:
        #         action.setChecked(True)
        # action.toggled.connect(self.ToggleTwitterAddAt)

        # self.LoadData()

        self.CheckForUpdates(True)
        self.ReloadGames()

        self.qtSettings = QSettings("joao_shino", "TournamentStreamHelper")

        if self.qtSettings.value("geometry"):
            self.restoreGeometry(self.qtSettings.value("geometry"))

        if self.qtSettings.value("windowState"):
            self.restoreState(self.qtSettings.value("windowState"))

        TSHTournamentDataProvider.instance.UiMounted()

        splash.finish(self)
        self.show()

    def SetGame(self):
        index = next((i for i in range(self.gameSelect.model().rowCount()) if self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get(
            "name") or self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get("codename")), None)
        if index is not None:
            self.gameSelect.setCurrentIndex(index)

    def closeEvent(self, event):
        self.qtSettings.setValue("geometry", self.saveGeometry())
        self.qtSettings.setValue("windowState", self.saveState())

    def ReloadGames(self):
        self.gameSelect.addItem("Select a game", 0)
        for i, game in enumerate(TSHGameAssetManager.instance.games.items()):
            if game[1].get("name"):
                self.gameSelect.addItem(game[1].get("name"), i+1)
            else:
                self.gameSelect.addItem(game[0], i+1)

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

                currVersion = str(TSHGameAssetManager.instance.games.get(key, {}).get(
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


App.setStyleSheet(qdarkstyle.load_stylesheet(
    palette=qdarkstyle.DarkPalette))

# App.setStyleSheet(qdarkstyle.load_stylesheet(
#     palette=qdarkstyle.LightPalette))

window = Window()
sys.exit(App.exec_())
