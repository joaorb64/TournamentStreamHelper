#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .Settings.TSHSettingsWindow import TSHSettingsWindow
from .TSHHotkeys import TSHHotkeys
from .TSHPlayerListWidget import TSHPlayerListWidget
from .TSHCommentaryWidget import TSHCommentaryWidget
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHBracketWidget import TSHBracketWidget
from .TSHTournamentInfoWidget import TSHTournamentInfoWidget
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TournamentDataProvider.StartGGDataProvider import StartGGDataProvider
from .TSHAlertNotification import TSHAlertNotification
from .TSHPlayerDB import TSHPlayerDB
from .Workers import *
from .TSHScoreboardWidget import *
from .TSHThumbnailSettingsWidget import *
from src.TSHAssetDownloader import TSHAssetDownloader
from src.TSHAboutWidget import TSHAboutWidget
from src.TSHWebServer import WebServer
from .Helpers.TSHLocaleHelper import TSHLocaleHelper
import shutil
import tarfile
import qdarktheme
import requests
import urllib
import json
import traceback
import time
import os
import unicodedata
import sys
import atexit
import time
import qtpy
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from packaging.version import parse

QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

if parse(qtpy.QT_VERSION).major == 6:
    QImageReader.setAllocationLimit(0)

App = QApplication(sys.argv)
print("QApplication successfully initialized")


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.stderr = open('./assets/log_error.txt', 'w', encoding="utf-8")
    sys.stdout = open('./assets/log.txt', 'w', encoding="utf-8")


def generate_restart_messagebox(main_txt):
    messagebox = QMessageBox()
    messagebox.setWindowTitle(QApplication.translate("app", "Warning"))
    messagebox.setText(
        main_txt + "\n" + QApplication.translate("app", "The program will now close."))
    messagebox.finished.connect(QApplication.exit)
    return (messagebox)


def ExtractUpdate():
    tar = tarfile.open("update.tar.gz")

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


def remove_accents_lower(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


class WindowSignals(QObject):
    StopTimer = Signal()
    ExportStageStrike = Signal(object)
    DetectGame = Signal(int)
    SetupAutocomplete = Signal()
    UiMounted = Signal()


class Window(QMainWindow):
    signals = WindowSignals()

    def __init__(self):
        super().__init__()

        StateManager.BlockSaving()

        TSHLocaleHelper.LoadLocale()
        TSHLocaleHelper.LoadRoundNames()

        self.signals = WindowSignals()

        splash = QSplashScreen(
            QPixmap('assets/icons/icon.png').scaled(128, 128))
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
        thumbnailSetting.setObjectName(
            QApplication.translate("app", "Thumbnail Settings"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, thumbnailSetting)
        self.dockWidgets.append(thumbnailSetting)

        bracket = TSHBracketWidget()
        bracket.setWindowIcon(QIcon('assets/icons/info.svg'))
        bracket.setObjectName(
            QApplication.translate("app", "Bracket"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, bracket)
        self.dockWidgets.append(bracket)

        tournamentInfo = TSHTournamentInfoWidget()
        tournamentInfo.setWindowIcon(QIcon('assets/icons/info.svg'))
        tournamentInfo.setObjectName(
            QApplication.translate("app", "Tournament Info"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, tournamentInfo)
        self.dockWidgets.append(tournamentInfo)

        self.scoreboard = TSHScoreboardWidget()
        self.scoreboard.setWindowIcon(QIcon('assets/icons/list.svg'))
        self.scoreboard.setObjectName(
            QApplication.translate("app", "Scoreboard"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.scoreboard)
        self.dockWidgets.append(self.scoreboard)

        self.stageWidget = TSHScoreboardStageWidget()
        self.stageWidget.setObjectName(
            QApplication.translate("app", "Stage"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.stageWidget)
        self.dockWidgets.append(self.stageWidget)

        self.webserver = WebServer(
            parent=None, scoreboard=self.scoreboard, stageWidget=self.stageWidget)
        self.webserver.start()

        commentary = TSHCommentaryWidget()
        commentary.setWindowIcon(QIcon('assets/icons/mic.svg'))
        commentary.setObjectName(QApplication.translate("app", "Commentary"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, commentary)
        self.dockWidgets.append(commentary)

        playerList = TSHPlayerListWidget()
        playerList.setWindowIcon(QIcon('assets/icons/list.svg'))
        playerList.setObjectName(QApplication.translate("app", "Player List"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, playerList)
        self.dockWidgets.append(playerList)

        self.tabifyDockWidget(self.scoreboard, self.stageWidget)
        self.tabifyDockWidget(self.scoreboard, commentary)
        self.tabifyDockWidget(self.scoreboard, tournamentInfo)
        self.tabifyDockWidget(self.scoreboard, thumbnailSetting)
        self.tabifyDockWidget(self.scoreboard, playerList)
        self.tabifyDockWidget(self.scoreboard, bracket)
        self.scoreboard.raise_()

        # Game
        base_layout = QHBoxLayout()

        group_box = QWidget()
        group_box.setLayout(QVBoxLayout())
        group_box.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Maximum)
        base_layout.layout().addWidget(group_box)

        # Set tournament
        hbox = QHBoxLayout()
        group_box.layout().addLayout(hbox)

        self.setTournamentBt = QPushButton(
            QApplication.translate("app", "Set tournament"))
        hbox.addWidget(self.setTournamentBt)
        self.setTournamentBt.clicked.connect(
            lambda bt=None, s=self: TSHTournamentDataProvider.instance.SetStartggEventSlug(s))

        self.unsetTournamentBt = QPushButton()
        self.unsetTournamentBt.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.unsetTournamentBt.setIcon(QIcon("./assets/icons/cancel.svg"))
        self.unsetTournamentBt.clicked.connect(lambda: [
            TSHTournamentDataProvider.instance.SetTournament(None)
        ])
        hbox.addWidget(self.unsetTournamentBt)

        # Follow startgg user
        hbox = QHBoxLayout()
        group_box.layout().addLayout(hbox)

        self.btLoadPlayerSet = QPushButton(
            QApplication.translate("app", "Load tournament and sets from StartGG user"))
        self.btLoadPlayerSet.setIcon(QIcon("./assets/icons/startgg.svg"))
        self.btLoadPlayerSet.clicked.connect(self.LoadUserSetClicked)
        self.btLoadPlayerSet.setIcon(QIcon("./assets/icons/startgg.svg"))
        hbox.addWidget(self.btLoadPlayerSet)

        TSHTournamentDataProvider.instance.signals.user_updated.connect(
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

        self.UpdateUserSetButton()

        # Settings
        menu_margin = " "*6
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
        menu = QMenu()
        self.optionsBt.setMenu(menu)
        action = menu.addAction(
            QApplication.translate("app", "Always on top"))
        action.setCheckable(True)
        action.toggled.connect(self.ToggleAlwaysOnTop)
        action = self.optionsBt.menu().addAction(
            QApplication.translate("app", "Check for updates"))
        self.updateAction = action
        action.setIcon(QIcon('assets/icons/undo.svg'))
        action.triggered.connect(self.CheckForUpdates)
        action = self.optionsBt.menu().addAction(
            QApplication.translate("app", "Download assets"))
        action.setIcon(QIcon('assets/icons/download.svg'))
        action.triggered.connect(TSHAssetDownloader.instance.DownloadAssets)
        self.downloadAssetsAction = action

        action = self.optionsBt.menu().addAction(
            QApplication.translate("app", "Light mode"))
        action.setCheckable(True)
        self.LoadTheme()
        action.setChecked(SettingsManager.Get("light_mode", False))
        action.toggled.connect(self.ToggleLightMode)

        toggleWidgets = QMenu(QApplication.translate(
            "app", "Toggle widgets") + menu_margin, self.optionsBt.menu())
        self.optionsBt.menu().addMenu(toggleWidgets)
        toggleWidgets.addAction(self.scoreboard.toggleViewAction())
        toggleWidgets.addAction(self.stageWidget.toggleViewAction())
        toggleWidgets.addAction(commentary.toggleViewAction())
        toggleWidgets.addAction(thumbnailSetting.toggleViewAction())
        toggleWidgets.addAction(tournamentInfo.toggleViewAction())
        toggleWidgets.addAction(playerList.toggleViewAction())
        toggleWidgets.addAction(bracket.toggleViewAction())

        self.optionsBt.menu().addSeparator()

        languageSelect = QMenu(QApplication.translate(
            "app", "Program Language") + menu_margin, self.optionsBt.menu())
        self.optionsBt.menu().addMenu(languageSelect)

        languageSelectGroup = QActionGroup(languageSelect)
        languageSelectGroup.setExclusive(True)

        program_language_messagebox = generate_restart_messagebox(
            QApplication.translate("app", "Program language changed successfully."))

        action = languageSelect.addAction(
            QApplication.translate("app", "System language"))
        languageSelectGroup.addAction(action)
        action.setCheckable(True)
        action.setChecked(True)
        action.triggered.connect(lambda x=None: [
            SettingsManager.Set("program_language", "default"),
            program_language_messagebox.exec()
        ])

        for code, language in TSHLocaleHelper.languages.items():
            action = languageSelect.addAction(f"{language[0]} / {language[1]}")
            action.setCheckable(True)
            languageSelectGroup.addAction(action)
            action.triggered.connect(lambda x=None, c=code: [
                SettingsManager.Set("program_language", c),
                program_language_messagebox.exec()
            ])
            if SettingsManager.Get("program_language") == code:
                action.setChecked(True)

        languageSelect = QMenu(QApplication.translate(
            "app", "Game Asset Language") + menu_margin, self.optionsBt.menu())
        self.optionsBt.menu().addMenu(languageSelect)

        languageSelectGroup = QActionGroup(languageSelect)
        languageSelectGroup.setExclusive(True)

        game_asset_language_messagebox = generate_restart_messagebox(
            QApplication.translate("app", "Game Asset Language changed successfully."))

        action = languageSelect.addAction(
            QApplication.translate("app", "Same as program language"))
        languageSelectGroup.addAction(action)
        action.setCheckable(True)
        action.setChecked(True)
        action.triggered.connect(lambda x=None: [
            SettingsManager.Set("game_asset_language", "default"),
            game_asset_language_messagebox.exec()
        ])

        for code, language in TSHLocaleHelper.languages.items():
            action = languageSelect.addAction(f"{language[0]} / {language[1]}")
            action.setCheckable(True)
            languageSelectGroup.addAction(action)
            action.triggered.connect(lambda x=None, c=code: [
                SettingsManager.Set("game_asset_language", c),
                game_asset_language_messagebox.exec()
            ])
            if SettingsManager.Get("game_asset_language") == code:
                action.setChecked(True)

        languageSelect = QMenu(QApplication.translate(
            "app", "Tournament term language") + menu_margin, self.optionsBt.menu())
        self.optionsBt.menu().addMenu(languageSelect)

        languageSelectGroup = QActionGroup(languageSelect)
        languageSelectGroup.setExclusive(True)

        fg_language_messagebox = generate_restart_messagebox(
            QApplication.translate("app", "Tournament term language changed successfully."))

        action = languageSelect.addAction(
            QApplication.translate("app", "Same as program language"))
        languageSelectGroup.addAction(action)
        action.setCheckable(True)
        action.setChecked(True)
        action.triggered.connect(lambda x=None: [
            SettingsManager.Set("fg_term_language", "default"),
            fg_language_messagebox.exec()
        ])

        for code, language in TSHLocaleHelper.languages.items():
            action = languageSelect.addAction(f"{language[0]} / {language[1]}")
            action.setCheckable(True)
            languageSelectGroup.addAction(action)
            action.triggered.connect(lambda x=None, c=code: [
                SettingsManager.Set("fg_term_language", c),
                fg_language_messagebox.exec()
            ])
            if SettingsManager.Get("fg_term_language") == code:
                action.setChecked(True)

        self.optionsBt.menu().addSeparator()

        # Help menu code

        help_messagebox = QMessageBox()
        help_messagebox.setWindowTitle(
            QApplication.translate("app", "Warning"))
        help_messagebox.setText(QApplication.translate(
            "app", "A new window has been opened in your default webbrowser."))

        helpMenu = QMenu(QApplication.translate(
            "app", "Help") + menu_margin, self.optionsBt.menu())
        self.optionsBt.menu().addMenu(helpMenu)
        action = helpMenu.addAction(
            QApplication.translate("app", "Open the Wiki"))
        wiki_url = "https://github.com/joaorb64/TournamentStreamHelper/wiki"
        action.triggered.connect(lambda x=None: [
            QDesktopServices.openUrl(QUrl(wiki_url)),
            help_messagebox.exec()
        ])

        action = helpMenu.addAction(
            QApplication.translate("app", "Report a bug"))
        issues_url = "https://github.com/joaorb64/TournamentStreamHelper/issues"
        action.triggered.connect(lambda x=None: [
            QDesktopServices.openUrl(QUrl(issues_url)),
            help_messagebox.exec()
        ])

        action = helpMenu.addAction(
            QApplication.translate("app", "Ask for Help on Discord"))
        discord_url = "https://discord.gg/X9Sp2FkcHF"
        action.triggered.connect(lambda x=None: [
            QDesktopServices.openUrl(QUrl(discord_url)),
            help_messagebox.exec()
        ])

        helpMenu.addSeparator()

        action = helpMenu.addAction(
            QApplication.translate("app", "Contribute to the Asset Database"))
        asset_url = "https://github.com/joaorb64/StreamHelperAssets/"
        action.triggered.connect(lambda x=None: [
            QDesktopServices.openUrl(QUrl(asset_url)),
            help_messagebox.exec()
        ])

        self.settingsWindow = TSHSettingsWindow(self)

        action = self.optionsBt.menu().addAction(
            QApplication.translate("Settings", "Settings"))
        action.setIcon(QIcon('assets/icons/settings.svg'))
        action.triggered.connect(lambda: self.settingsWindow.show())

        self.aboutWidget = TSHAboutWidget()
        action = self.optionsBt.menu().addAction(
            QApplication.translate("About", "About"))
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
        TSHGameAssetManager.instance.signals.onLoad.connect(
            TSHAssetDownloader.instance.CheckAssetUpdates
        )
        TSHAssetDownloader.instance.signals.AssetUpdates.connect(
            self.OnAssetUpdates
        )
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

        TSHCountryHelper.LoadCountries()
        self.settingsWindow.UiMounted()
        TSHTournamentDataProvider.instance.UiMounted()
        TSHGameAssetManager.instance.UiMounted()
        TSHAlertNotification.instance.UiMounted()
        TSHAssetDownloader.instance.UiMounted()
        TSHHotkeys.instance.UiMounted(self)
        TSHPlayerDB.LoadDB()

        StateManager.ReleaseSaving()

    def SetGame(self):
        index = next((i for i in range(self.gameSelect.model().rowCount()) if self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get(
            "name") or self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get("codename")), None)
        if index is not None:
            self.gameSelect.setCurrentIndex(index)

    def UpdateUserSetButton(self):
        if SettingsManager.Get("StartGG_user"):
            self.btLoadPlayerSet.setText(
                QApplication.translate("app", "Load tournament and sets from StartGG user")+" "+QApplication.translate("punctuation", "(")+f"{SettingsManager.Get('StartGG_user')}"+QApplication.translate("punctuation", ")"))
            self.btLoadPlayerSet.setEnabled(True)
        else:
            self.btLoadPlayerSet.setText(
                QApplication.translate("app", "Load tournament and sets from StartGG user"))
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
                messagebox.setWindowTitle(
                    QApplication.translate("app", "Warning"))
                messagebox.setText(
                    QApplication.translate("app", "Failed to fetch version from github:")+"\n"+str(e))
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
                    buttonReply.setWindowTitle(
                        QApplication.translate("app", "Updater"))
                    buttonReply.setWindowModality(Qt.WindowModal)
                    vbox = QVBoxLayout()
                    buttonReply.setLayout(vbox)

                    buttonReply.layout().addWidget(
                        QLabel(QApplication.translate("app", "New version available:")+" "+myVersion+" → "+currVersion))
                    buttonReply.layout().addWidget(QLabel(release["body"]))
                    buttonReply.layout().addWidget(QLabel(
                        QApplication.translate("app", "Update to latest version?")+"\n"+QApplication.translate("app", "NOTE: WILL BACKUP /layout/ AND OVERWRITE DATA IN ALL OTHER DIRECTORIES")))

                    hbox = QHBoxLayout()
                    vbox.addLayout(hbox)

                    btUpdate = QPushButton(
                        QApplication.translate("app", "Update"))
                    hbox.addWidget(btUpdate)
                    btCancel = QPushButton(
                        QApplication.translate("app", "Cancel"))
                    hbox.addWidget(btCancel)

                    buttonReply.show()

                    def Update():
                        db = QFontDatabase()
                        db.removeAllApplicationFonts()
                        QFontDatabase.removeAllApplicationFonts()
                        self.downloadDialogue = QProgressDialog(
                            QApplication.translate("app", "Downloading update..."), QApplication.translate("app", "Cancel"), 0, 0, self)
                        self.downloadDialogue.setWindowModality(
                            Qt.WindowModality.WindowModal)
                        self.downloadDialogue.show()

                        def worker(progress_callback):
                            with open("update.tar.gz", 'wb') as downloadFile:
                                downloaded = 0

                                response = urllib.request.urlopen(
                                    release["tarball_url"])

                                while (True):
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
                                QApplication.translate("app", "Downloading update...")+" "+str(downloaded/1024/1024)+" MB")

                        def finished():
                            self.downloadDialogue.close()

                            # Register update extraction on program close
                            atexit.register(ExtractUpdate)

                            messagebox = generate_restart_messagebox(
                                QApplication.translate("app", "Update download complete. The program will extract the update upon closing."))

                            messagebox.exec()

                        worker = Worker(worker)
                        worker.signals.progress.connect(progress)
                        worker.signals.finished.connect(finished)
                        self.threadpool.start(worker)

                    btUpdate.clicked.connect(Update)
                    btCancel.clicked.connect(lambda: buttonReply.close())
                else:
                    messagebox = QMessageBox()
                    messagebox.setWindowTitle(
                        QApplication.translate("app", "Info"))
                    messagebox.setText(
                        QApplication.translate("app", "You're already using the latest version"))
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
                        QApplication.translate("app", "Check for updates") + " " + QApplication.translate("punctuation", "[") + QApplication.translate("app", "Update available!") + QApplication.translate("punctuation", "]"))

    # Checks for asset updates after game assets are loaded
    # If updates are available, edit QAction icon
    def OnAssetUpdates(self, updates):
        try:
            if len(updates) > 0:
                baseIcon = self.downloadAssetsAction.icon().pixmap(32, 32)
                updateIcon = QImage(
                    "./assets/icons/update_circle.svg").scaled(12, 12)
                p = QPainter(baseIcon)
                p.drawImage(QPoint(20, 0), updateIcon)
                p.end()
                self.downloadAssetsAction.setIcon(QIcon(baseIcon))
            else:
                baseIcon = self.downloadAssetsAction.icon().pixmap(32, 32)
                self.downloadAssetsAction.setIcon(QIcon(baseIcon))
        except:
            print(traceback.format_exc())

    def ToggleAlwaysOnTop(self, checked):
        if checked:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

    def ToggleLightMode(self, checked):
        if checked:
            qdarktheme.setup_theme("light")
        else:
            qdarktheme.setup_theme()

        SettingsManager.Set("light_mode", checked)

    def LoadTheme(self):
        if SettingsManager.Get("light_mode", False):
            qdarktheme.setup_theme("light")
        else:
            qdarktheme.setup_theme()
