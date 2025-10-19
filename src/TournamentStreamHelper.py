#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .Helpers.TSHLocaleHelper import TSHLocaleHelper
from .Helpers.TSHDirHelper import TSHResolve
import faulthandler
import shutil
import zipfile
import qdarktheme
import requests
import urllib
import json
import orjson
import traceback
import time
import os
import unicodedata
import socket
import sys
import atexit
import time
import qtpy
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from packaging.version import parse
from loguru import logger
from pathlib import Path
from glob import glob

crashpath = Path('./logs/tsh-crash.log').resolve()
Path.mkdir(crashpath.parent, exist_ok=True)
crashlog = crashpath.open(mode='w')
faulthandler.enable(crashlog)

QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

if parse(qtpy.QT_VERSION).major == 6:
    QImageReader.setAllocationLimit(0)

App = QApplication(sys.argv)

fmt = ("<green>{time:YYYY-MM-DD HH:mm:ss}</green> " +
       "| <level>{level}</level> | " +
       "<yellow>{file}</yellow>:<blue>{function}</blue>:<cyan>{line}</cyan> " +
       "- <level>{message}</level>")

if sys.stdout != None:
    config = {
        "handlers": [
            {"sink": sys.stdout, "format": fmt, "level": "DEBUG"},
        ],
    }
    logger.configure(**config)
else:
    # Handle all uncaught exceptions and forward to loguru
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical("Uncaught exception", exc_info=(
            exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    class LoggerWriter(object):
        def __init__(self, writer):
            self._writer = writer
            self._msg = ''

        def write(self, message):
            self._msg = self._msg + message
            while '\n' in self._msg:
                pos = self._msg.find('\n')
                self._writer(self._msg[:pos])
                self._msg = self._msg[pos+1:]

        def flush(self):
            if self._msg != '':
                self._writer(self._msg)
                self._msg = ''

    sys.stdout = LoggerWriter(logger.info)
    sys.stderr = LoggerWriter(logger.error)

logger.add(
    "./logs/tsh.log",
    format="[{time:YYYY-MM-DD HH:mm:ss}] - {level} - {file}:{function}:{line} | {message}",
    encoding="utf-8",
    level="INFO",
    rotation="20 MB"
)

logger.add(
    "./logs/tsh-error.log",
    format="[{time:YYYY-MM-DD HH:mm:ss}] - {level} - {file}:{function}:{line} | {message}",
    encoding="utf-8",
    level="ERROR",
    rotation="20 MB"
)

try:
    # Setting the icon for individual windows doesn't work on mac (and perhaps linux? unknown)
    App.setWindowIcon(QIcon("assets/icons/icon.png"))
except:
    logger.opt(exception=True).warning("Could not set window icon for QApplication.")


logger.critical("=== TSH IS STARTING ===")

logger.info("QApplication successfully initialized")

from contextlib import contextmanager
@contextmanager
def catchtime(msg = ''):
    from time import perf_counter
    start = perf_counter()
    yield lambda: perf_counter() - start
    logger.info(f'{msg} Time: {perf_counter() - start:.3f} seconds')

# autopep8: off
from .Settings.TSHSettingsWindow import TSHSettingsWindow
from .LayoutOptions.TSHLayoutOptionsWindow import TSHLayoutOptionsWindow
from .TSHHotkeys import TSHHotkeys
from .TSHPlayerListWidget import TSHPlayerListWidget
from .TSHNotesWidget import TSHNotesWidget
from .TSHCommentaryWidget import TSHCommentaryWidget
from .TSHTeamBattleWidget import TSHTeamBattleWidget
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHBracketWidget import TSHBracketWidget
from .TSHTournamentInfoWidget import TSHTournamentInfoWidget
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TournamentDataProvider.StartGGDataProvider import StartGGDataProvider
from .TSHAlertNotification import TSHAlertNotification
from .TSHPlayerDB import TSHPlayerDB
from .Workers import *
from .StateManager import StateManager
from .SettingsManager import SettingsManager
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .Helpers.TSHControllerHelper import TSHControllerHelper
from .TSHScoreboardManager import TSHScoreboardManager
from src.TSHAssetDownloader import TSHAssetDownloader
from src.TSHAboutWidget import TSHAboutWidget
from .TSHScoreboardStageWidget import TSHScoreboardStageWidget
from src.TSHWebServer import WebServer
# autopep8: on

def DownloadLayoutsOnBoot():
    """
    Downloads latest layouts from Github if the folder is empty
    """
    layouts_path = "./layout"
    has_layouts = True
    if os.path.isdir(layouts_path):
        if not os.listdir(layouts_path) or len(os.listdir(layouts_path)) <= 2:
            has_layouts = False
    else:
        if os.path.isfile(layouts_path):
            os.remove(layouts_path)
        os.mkdir(layouts_path)
        has_layouts = False
    if not has_layouts:
        logger.info("Layouts were not detected, downloading from Github...")
        try:
            url = "https://github.com/TournamentStreamHelper/TournamentStreamHelper-layouts/archive/refs/heads/main.zip"
            r = requests.get(url, allow_redirects=True)
            zip_path = './layout/layout.zip.tmp'
            with open(zip_path, 'wb') as zip_file:
                zip_file.write(r.content)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall('./layout')
                list_files = glob(f"./layout/TournamentStreamHelper-layouts-main/*")
                for file_path in list_files:
                    if os.name == 'nt':
                        new_file_path = file_path.replace("TournamentStreamHelper-layouts-main\\", "")
                    else:
                        new_file_path = file_path.replace("TournamentStreamHelper-layouts-main/", "")
                    os.rename(file_path, new_file_path)
                os.rmdir(f"./layout/TournamentStreamHelper-layouts-main")
                os.remove(zip_path)
            except Exception as e:
                logger.error(f"Layouts could not be extracted\nError: {str(e)}")
        except Exception as e:
            logger.error(f"Layouts could not be downloaded\nError: {str(e)}")

def generate_restart_messagebox(main_txt):
    messagebox = QMessageBox()
    messagebox.setWindowTitle(QApplication.translate("app", "Warning"))
    messagebox.setText(
        main_txt + "\n" + QApplication.translate("app", "The program will now close."))
    messagebox.finished.connect(QApplication.exit)
    return (messagebox)


def UpdateProcedure():
    """
        Update Procedure -- backup layouts, register extraction on program close
    """

    try:
        # Backup layouts
        os.rename(
            "./layout", f"./layout_backup_{str(time.time())}")

        # Register update extraction on program close
        atexit.register(ExtractUpdate)

        messagebox = generate_restart_messagebox(
            QApplication.translate(
                "app", "Update download complete. The program will extract the update upon closing.")
            + "\n\n"
            + QApplication.translate(
                "app", "Please ensure the layout folder or its contents aren't open in another application before closing this window.")
            + "\n"
        )

        messagebox.exec()
    except Exception as e:
        # Layout folder backups failed
        logger.error(traceback.format_exc())

        buttonReply = QDialog()
        buttonReply.setWindowTitle(
            QApplication.translate("app", "Warning"))
        vbox = QVBoxLayout()
        buttonReply.setLayout(vbox)

        buttonReply.layout().addWidget(
            QLabel(QApplication.translate(
                "updater",
                "Error while backing up the layout folder:")
            )
        )
        buttonReply.layout().addWidget(QLabel(str(e)))

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        btRetry = QPushButton(
            QApplication.translate("updater", "Retry"))
        hbox.addWidget(btRetry)
        btCancel = QPushButton(
            QApplication.translate("updater", "Cancel"))
        hbox.addWidget(btCancel)

        btRetry.clicked.connect(lambda: [
            buttonReply.close(),
            UpdateProcedure()
        ])

        btCancel.clicked.connect(
            lambda: buttonReply.close()
        )

        buttonReply.exec()


def ExtractUpdate():
    try:
        updateLog = []
        with zipfile.ZipFile("update.zip", "r") as z:
            # backup exe
            os.rename("./TSH.exe", "./TSH_old.exe")

            for filename in z.namelist():
                if "/" in filename:
                    fullname = filename.split("/", 1)[1]
                    if fullname.endswith("/"):
                        updateLog.append(f"Create directory {fullname}")
                        try:
                            os.makedirs(os.path.dirname(fullname), exist_ok=True)
                        except Exception:
                            updateLog.append(f"Failed to create {filename} - {traceback.format_exc()}")
                    else:
                        updateLog.append(f"Extract {filename} -> {fullname}")
                        try:
                            z.extract(filename, path=os.path.dirname(fullname))
                        except Exception:
                            updateLog.append(f"Failed to extract {filename} - {traceback.format_exc()}")

            try:
                with open("assets/update_log.txt", "w") as f:
                    f.writelines(updateLog)
            except:
                logger.error(traceback.format_exc())

        os.remove("update.zip")
    except Exception as e:
        logger.error(traceback.format_exc())


def remove_accents_lower(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


class WindowSignals(QObject):
    StopTimer = Signal()
    ExportStageStrike = Signal(object)
    DetectGame = Signal(int)
    SetupAutocomplete = Signal()
    UiMounted = Signal()
    GameChanged = Signal()


class Window(QMainWindow):
    signals = WindowSignals()

    def __init__(self, loop=None):
        super().__init__()

        StateManager.loop = loop
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
                open(TSHResolve('./assets/versions.json'), encoding='utf-8')).get("program", "?")
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

        if not SettingsManager.Get("general.disable_thumbnail_widget", False):
            from .TSHThumbnailSettingsWidget import TSHThumbnailSettingsWidget
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

        teamBattle = TSHTeamBattleWidget()
        teamBattle.setWindowIcon(QIcon('assets/icons/info.svg'))
        teamBattle.setObjectName(
            QApplication.translate("app", "Crew/Team Battle"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, teamBattle)
        self.dockWidgets.append(teamBattle)

        self.scoreboard = TSHScoreboardManager.instance
        self.scoreboard.setWindowIcon(QIcon('assets/icons/list.svg'))
        self.scoreboard.setObjectName(
            QApplication.translate("app", "Scoreboard Manager"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.scoreboard)
        self.dockWidgets.append(self.scoreboard)
        TSHScoreboardManager.instance.setWindowTitle(
            QApplication.translate("app", "Scoreboard Manager"))

        self.stageWidget = TSHScoreboardStageWidget()
        self.stageWidget.setObjectName(
            QApplication.translate("app", "Stage"))
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.stageWidget)
        self.dockWidgets.append(self.stageWidget)

        commentary = TSHCommentaryWidget()
        commentary.setWindowIcon(QIcon('assets/icons/mic.svg'))
        commentary.setObjectName(QApplication.translate("app", "Commentary"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, commentary)
        self.dockWidgets.append(commentary)

        self.webserver = WebServer(
            parent=self, stageWidget=self.stageWidget, commentaryWidget=commentary)
        self.webserver.start()
        self.signals.GameChanged.connect(self.webserver.ws_program_state)
        self.signals.GameChanged.connect(self.webserver.ws_get_characters)
        self.stageWidget.stageStrikeLogic.signals.state_updated.connect(self.webserver.ws_ruleset)

        playerList = TSHPlayerListWidget()
        playerList.setWindowIcon(QIcon('assets/icons/list.svg'))
        playerList.setObjectName(QApplication.translate("app", "Player List"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, playerList)
        self.dockWidgets.append(playerList)
        
        notes = TSHNotesWidget()
        notes.setObjectName(QApplication.translate("app", "Additional Notes"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, notes)
        self.dockWidgets.append(notes)

        self.tabifyDockWidget(self.scoreboard, self.stageWidget)
        self.tabifyDockWidget(self.scoreboard, commentary)
        self.tabifyDockWidget(self.scoreboard, tournamentInfo)
        self.tabifyDockWidget(self.scoreboard, teamBattle)
        if not SettingsManager.Get("general.disable_thumbnail_widget", False):
            self.tabifyDockWidget(self.scoreboard, thumbnailSetting)
        self.tabifyDockWidget(self.scoreboard, playerList)
        self.tabifyDockWidget(self.scoreboard, bracket)
        self.tabifyDockWidget(self.scoreboard, notes)
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
        if not SettingsManager.Get("general.hide_track_player", False):
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
        
        # Completed Sets Feature
        hbox = QHBoxLayout()
        group_box.layout().addLayout(hbox)
        self.btPullCompletedSets = QPushButton(
            QApplication.translate("app", "Pull Latest Completed Sets from StartGG"))
        self.btPullCompletedSets.setIcon(QIcon("./assets/icons/startgg.svg"))
        self.btPullCompletedSets.clicked.connect(TSHTournamentDataProvider.instance.GetCompletedSets)
        hbox.addWidget(self.btPullCompletedSets)
        # label_margin = " "*18
        # label = QLabel(
        #     label_margin + QApplication.translate("app", "Time until Completed Sets refresh:") + " ")
        # label.setSizePolicy(QSizePolicy.Policy.Fixed,
        #                     QSizePolicy.Policy.Minimum)
        # hbox.addWidget(label)
        # self.labelSetsTimer = QLabel(QApplication.translate("app", "Disabled"))
        # self.labelSetsTimer.setSizePolicy(QSizePolicy.Policy.Fixed,
        #                     QSizePolicy.Policy.Minimum)
        # hbox.addWidget(self.labelSetsTimer)
        # self.btStopSetsPull = QPushButton()
        # self.btStopSetsPull.setSizePolicy(
        #     QSizePolicy.Maximum, QSizePolicy.Maximum)
        # self.btStopSetsPull.setIcon(QIcon("./assets/icons/cancel.svg"))
        # hbox.addWidget(self.btStopSetsPull)

        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.UpdateLastSetsButton)
        TSHTournamentDataProvider.instance.signals.completed_sets_updated.connect(
            self.LoadCompletedSetsClicked
        )

        self.UpdateLastSetsButton()

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
        if not SettingsManager.Get("general.disable_thumbnail_widget", False):
            toggleWidgets.addAction(thumbnailSetting.toggleViewAction())
        toggleWidgets.addAction(tournamentInfo.toggleViewAction())
        toggleWidgets.addAction(teamBattle.toggleViewAction())
        toggleWidgets.addAction(playerList.toggleViewAction())
        toggleWidgets.addAction(bracket.toggleViewAction())
        toggleWidgets.addAction(notes.toggleViewAction())

        self.optionsBt.menu().addSeparator()

        # self.layoutOptions = TSHLayoutOptionsWindow(self)

        # action = self.optionsBt.menu().addAction(
        #     QApplication.translate("LayoutOptions", "Layout Options"))
        # action.setIcon(QIcon('assets/icons/settings.svg'))
        # action.triggered.connect(lambda: self.layoutOptions.show())

        action = self.optionsBt.menu().addAction(
            QApplication.translate("app", "Migrate Layout"))
        action.triggered.connect(self.MigrateWindow)

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
            QApplication.translate("app", "Look for Help on the forum"))
        help_url = "https://github.com/joaorb64/TournamentStreamHelper/discussions/categories/q-a"
        action.triggered.connect(lambda x=None: [
            QDesktopServices.openUrl(QUrl(help_url)),
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
        
        self.optionsBt.menu().addSeparator()

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

        # Game Select and Scoreboard Count
        hbox = QHBoxLayout()
        group_box.layout().addLayout(hbox)

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
        TSHTournamentDataProvider.instance.signals.tournament_url_update.connect(
            self.Signal_GameChange)

        label_margin = " "*5

        # Modded content UI
        self.moddedContentWidget = QWidget()
        moddedContentLayout = QHBoxLayout()
        self.moddedContentWidget.setLayout(moddedContentLayout)
        self.moddedContentCheck = QCheckBox()
        self.moddedContentWidget.setVisible(False)
        self.moddedContentCheck.setChecked(False)
        moddedContentCheckLabel = QLabel()
        moddedContentCheckLabel.setText(label_margin + QApplication.translate("app", "Modded content"))
        self.moddedContentWidget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        moddedContentLayout.addWidget(moddedContentCheckLabel)
        moddedContentLayout.addWidget(self.moddedContentCheck)

        TSHGameAssetManager.instance.signals.onLoad.connect(lambda x=None: [
            self.moddedContentWidget.setVisible(TSHGameAssetManager.instance.has_modded_content),
            self.moddedContentCheck.setChecked(StateManager.Get("game").get("mods_active", False))
        ])

        self.moddedContentCheck.stateChanged.connect(lambda x=None: [
            print("Checked: "+ str(self.moddedContentCheck.isChecked())),
            TSHGameAssetManager.instance.LoadGameAssets(self.gameSelect.currentData(), mods_active=self.moddedContentCheck.isChecked(), mods_reload_mode=True)
        ]
        )

        self.gameSelect.activated.connect(
            lambda x=None: self.moddedContentCheck.setChecked(False))
        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            lambda x=None: self.moddedContentCheck.setChecked(False))

        pre_base_layout.addLayout(base_layout)
        hbox.addWidget(self.gameSelect)
        hbox.addWidget(self.moddedContentWidget)

        self.scoreboardAmount = QSpinBox()
        self.scoreboardAmount.setMaximumWidth(100)
        self.scoreboardAmount.lineEdit().setReadOnly(True)
        self.scoreboardAmount.setMinimum(1)
        self.scoreboardAmount.setMaximum(10)

        self.scoreboardAmount.valueChanged.connect(
            lambda val:
            TSHScoreboardManager.instance.signals.ScoreboardAmountChanged.emit(
                val)
        )

        label = QLabel(
            label_margin + QApplication.translate("app", "Number of Scoreboards"))
        label.setSizePolicy(QSizePolicy.Policy.Fixed,
                            QSizePolicy.Policy.Minimum)

        self.btLoadModifyTabName = QPushButton(
            QApplication.translate("app", "Modify Tab Name"))
        self.btLoadModifyTabName.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.btLoadModifyTabName.clicked.connect(self.ChangeTab)

        hbox.addWidget(label)
        hbox.addWidget(self.scoreboardAmount)
        hbox.addWidget(self.btLoadModifyTabName)

        TSHScoreboardManager.instance.UpdateAmount(1)

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
        # self.layoutOptions.UiMounted()
        TSHTournamentDataProvider.instance.UiMounted()
        TSHGameAssetManager.instance.UiMounted()
        TSHAlertNotification.instance.UiMounted()
        TSHAssetDownloader.instance.UiMounted()
        TSHHotkeys.instance.UiMounted(self)
        TSHPlayerDB.signals.db_updated.connect(
            self.webserver.ws_playerdb
        )
        TSHPlayerDB.LoadDB()

        StateManager.ReleaseSaving()

        TSHScoreboardManager.instance.signals.ScoreboardAmountChanged.connect(
            self.ToggleTopOption)
        StateManager.Unset("completed_sets")

        DownloadLayoutsOnBoot()

    def SetGame(self, mods_active = False):
        index = next((i for i in range(self.gameSelect.model().rowCount()) if self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get(
            "name") or self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get("codename")), None)
        if index is not None:
            self.gameSelect.setCurrentIndex(index)
            self.signals.GameChanged.emit()

    def Signal_GameChange(self, url):
        if url == "":
            self.gameSelect.setCurrentIndex(0)
            TSHGameAssetManager.instance.selectedGame = {}

    def UpdateUserSetButton(self):
        if SettingsManager.Get("StartGG_user"):
            self.btLoadPlayerSet.setText(
                QApplication.translate("app", "Load tournament and sets from StartGG user")+" "+QApplication.translate("punctuation", "(")+f"{SettingsManager.Get('StartGG_user')}"+QApplication.translate("punctuation", ")"))
            self.btLoadPlayerSet.setEnabled(True)
        else:
            self.btLoadPlayerSet.setText(
                QApplication.translate("app", "Load tournament and sets from StartGG user"))
            self.btLoadPlayerSet.setEnabled(False)
    
    def UpdateLastSetsButton(self):
        if TSHTournamentDataProvider.instance and TSHTournamentDataProvider.instance.provider and TSHTournamentDataProvider.instance.provider.name == "StartGG":
            self.btPullCompletedSets.setEnabled(True)
        else:
            self.btPullCompletedSets.setEnabled(False)

    def LoadUserSetClicked(self):
        self.scoreboard.lastSetSelected = None
        if SettingsManager.Get("StartGG_user"):
            TSHTournamentDataProvider.instance.provider = StartGGDataProvider(
                "start.gg/",
                TSHTournamentDataProvider.instance.threadPool,
                TSHTournamentDataProvider.instance
            )
            TSHTournamentDataProvider.instance.LoadUserSet(
                self.scoreboard.GetScoreboard(1), SettingsManager.Get("StartGG_user"))
    
    def LoadCompletedSetsClicked(self, data):
        StateManager.Set("completed_sets", {index+1: set for index, set in enumerate(data)})

    def LoadUserSetOptionsClicked(self):
        TSHTournamentDataProvider.instance.SetUserAccount(
            self.scoreboard, startgg=True)

    def closeEvent(self, event):
        logger.info("Shutting down...")
        self.qtSettings.setValue("geometry", self.saveGeometry())
        self.qtSettings.setValue("windowState", self.saveState())

        tmpDir = TSHResolve("tmp")
        if os.path.isdir(tmpDir):
            shutil.rmtree(tmpDir)

        try:
            crashlog.close()
            if crashpath.stat().st_size == 0:
                crashpath.unlink()
        except:
            pass

        # For whatever reason, the webserver thread won't respond to the quit() signal nicely.
        # This is usually unsafe, but there's no easy way to terminate the flask server,
        # so we hard-kill its thread as we're shutting down to prevent exit-crashes.
        #
        # Given that this webserver is local in scope, it's reasonable to not do any
        # connection-draining process.
        try:
            web_socket_fd = os.environ.get('WERKZEUG_SOCKET_FD', None)
            if web_socket_fd:
                sock = socket.socket(fileno=int(web_socket_fd))
                sock.close()
        except Exception as e:
            logger.warning("Error closing web socket on shutdown", exc_info=True)

        self.webserver.terminate()
        self.webserver.wait()

    def ReloadGames(self):
        logger.info("Reload games")
        with StateManager.SaveBlock():
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
        def detect_smashgg_id_match(games, game, id):
            result = str(games[game].get("smashgg_game_id", "")) == str(id)
            if not result:
                alternates = games[game].get("alternate_versions")
                alternates_ids = []
                for alternate in alternates:
                    if alternate.get("smashgg_game_id"):
                        alternates_ids.append(str(alternate.get("smashgg_game_id")))
                result = str(id) in alternates_ids
            return(result)

        game = next(
            (i+1 for i, game in enumerate(self.games)
             if detect_smashgg_id_match(self.games,game,id)),
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
            release = orjson.loads(response.text)
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
                open(TSHResolve('./assets/versions.json'), encoding='utf-8'))
        except Exception as e:
            logger.error("Local version file not found")

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
                        QApplication.translate("app", "Update to latest version?")+"\n\n"+QApplication.translate("app", "NOTE: This will open a new tab in your browser and close TournamentStreamHelper.")))

                    hbox = QHBoxLayout()
                    vbox.addLayout(hbox)

                    btUpdate = QPushButton(
                        QApplication.translate("app", "Update"))
                    hbox.addWidget(btUpdate)
                    btCancel = QPushButton(
                        QApplication.translate("app", "Cancel"))
                    hbox.addWidget(btCancel)

                    buttonReply.show()

                    def Update_Old(): # Deprecated
                        db = QFontDatabase()
                        db.removeAllApplicationFonts()
                        QFontDatabase.removeAllApplicationFonts()
                        self.downloadDialogue = QProgressDialog(
                            QApplication.translate("app", "Downloading update..."), QApplication.translate("app", "Cancel"), 0, 0, self)
                        self.downloadDialogue.setWindowModality(
                            Qt.WindowModality.WindowModal)
                        self.downloadDialogue.show()

                        def worker(progress_callback, cancel_event):
                            with open("./update.zip", 'wb') as downloadFile:
                                downloaded = 0

                                dl_url = release["zipball_url"]

                                if os.name == 'nt':
                                    assets = release["assets"] if "assets" in release else []
                                    for i in range(len(assets)):
                                        if assets[i]["name"] == "release.zip":
                                            dl_url = assets[i]["url"]
                                            break

                                response = urllib.request.urlopen(dl_url)

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

                            # Update procedure
                            UpdateProcedure()

                        worker = Worker(worker)
                        worker.signals.progress.connect(progress)
                        worker.signals.finished.connect(finished)
                        self.threadpool.start(worker)

                    def Update(): # Opens the releases page in the web browser
                        latest_release_url = "https://github.com/joaorb64/TournamentStreamHelper/releases/latest"
                        QDesktopServices.openUrl(QUrl(latest_release_url))
                        QCoreApplication.quit()

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
            logger.error(traceback.format_exc())

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

    def ToggleTopOption(self):
        if not SettingsManager.Get("general.hide_track_player", False):
            if TSHScoreboardManager.instance.GetTabAmount() > 1:
                self.btLoadPlayerSet.setHidden(True)
                self.btLoadPlayerSetOptions.setHidden(True)
            else:
                self.btLoadPlayerSet.setHidden(False)
                self.btLoadPlayerSetOptions.setHidden(False)

    def ChangeTab(self):
        tabNameWindow = QDialog(self)
        tabNameWindow.setWindowTitle(
            QApplication.translate("app", "Change Tab Title"))
        tabNameWindow.setMinimumWidth(400)
        vbox = QVBoxLayout()
        tabNameWindow.setLayout(vbox)
        hbox = QHBoxLayout()
        label = QLabel(QApplication.translate("app", "Scoreboard Number"))
        number = QSpinBox()
        number.setMinimum(1)
        number.setMaximum(TSHScoreboardManager.instance.GetTabAmount())
        hbox.addWidget(label)
        hbox.addWidget(number)
        vbox.addLayout(hbox)
        name = QLineEdit()
        vbox.addWidget(name)

        setSelection = QPushButton(
            text=QApplication.translate("app", "Set Tab Title"))

        def UpdateTabName():
            TSHScoreboardManager.instance.SetTabName(
                number.value(), name.text())
            tabNameWindow.close()

        setSelection.clicked.connect(UpdateTabName)

        vbox.addWidget(setSelection)

        tabNameWindow.show()

    def MigrateWindow(self):
        migrateWindow = QDialog(self)
        migrateWindow.setWindowTitle(
            QApplication.translate("app", "Migrate Scoreboard Layout"))
        migrateWindow.setMinimumWidth(800)
        vbox = QVBoxLayout()
        migrateWindow.setLayout(vbox)
        hbox = QHBoxLayout()
        label = QLabel(QApplication.translate("app", "File Path"))
        filePath = QLineEdit()
        fileExplorer = QPushButton(
            text=QApplication.translate("app", "Find File..."))
        hbox.addWidget(label)
        hbox.addWidget(filePath)
        hbox.addWidget(fileExplorer)
        vbox.addLayout(hbox)

        migrate = QPushButton(
            text=QApplication.translate("app", "Migrate Layout"))

        def open_dialog():
            fname, _ok = QFileDialog.getOpenFileName(
                migrateWindow,
                QApplication.translate("app", "Open Layout Javascript File"),
                os.getcwd(),
                QApplication.translate("app", "Javascript File") + "  (*.js)",
            )
            if fname:
                filePath.setText(str(fname))

        fileExplorer.clicked.connect(open_dialog)

        def MigrateLayout():
            data = None
            with open(filePath.text(), 'r') as file:
                data = file.read()

                data = data.replace("data.score.", "data.score[1].")
                data = data.replace("oldData.score.", "oldData.score[1].")
                data = data.replace(
                    "_.get(data, \"score.stage_strike.", "_.get(data, \"score.1.stage_strike.")
                data = data.replace(
                    "_.get(oldData, \"score.stage_strike.", "_.get(oldData, \"score.1.stage_strike.")
                data = data.replace(
                    "source: `score.team.${t + 1}`", "source: `score.1.team.${t + 1}`")
                data = data.replace(
                    "data.score[1].ruleset", "data.score.ruleset")

            with open(filePath.text(), 'w') as file:
                file.write(data)

            logger.info("Completed Layout Migration at: " + filePath.text())

            completeDialog = QDialog(migrateWindow)
            completeDialog.setWindowTitle(
                QApplication.translate("app", "Migration Complete"))
            completeDialog.setMinimumWidth(500)
            vbox2 = QVBoxLayout()
            completeDialog.setLayout(vbox2)
            completeText = QLabel(QApplication.translate(
                "app", "Layout Migration has completed!"))
            completeText.setAlignment(Qt.AlignmentFlag.AlignCenter)
            closeButton = QPushButton(
                text=QApplication.translate("app", "Close Window"))
            vbox2.addWidget(completeText)
            vbox2.addWidget(closeButton)
            closeButton.clicked.connect(completeDialog.close)
            completeDialog.show()

        migrate.clicked.connect(MigrateLayout)

        vbox.addWidget(migrate)

        migrateWindow.show()
