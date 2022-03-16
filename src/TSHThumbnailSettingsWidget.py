from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from pathlib import Path
import os

from .thumbnail import main_generate_thumbnail as thumbnail
from .SettingsManager import *

class TSHThumbnailSettingsWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("Thumbnail Settings")
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.settings = uic.loadUi("src/layout/TSHThumbnailSettings.ui")
        self.widget.layout().addWidget(self.settings)

        # IMG
        self.foreground = self.settings.findChild(QPushButton, "customForeground")
        self.background = self.settings.findChild(QPushButton, "customBackground")
        self.mainIcon = self.settings.findChild(QPushButton, "customMainIcon")
        self.topLeftIcon = self.settings.findChild(QPushButton, "customTopLeftIcon")
        self.topRightIcon = self.settings.findChild(QPushButton, "customTopRightIcon")

        self.foreground.clicked.connect(lambda:self.SaveImage("foreground_path"))
        self.background.clicked.connect(lambda:self.SaveImage("background_path"))
        self.mainIcon.clicked.connect(lambda:self.SaveImage("main_icon_path"))
        self.topLeftIcon.clicked.connect(lambda:self.SaveIcons("side_icon_list", 0))
        self.topRightIcon.clicked.connect(lambda:self.SaveIcons("side_icon_list", 1))

        # CHECK BOX
        self.phase_name = self.settings.findChild(QCheckBox, "phaseNameCheck")
        self.team_name = self.settings.findChild(QCheckBox, "teamNameCheck")
        self.sponsor = self.settings.findChild(QCheckBox, "sponsorCheck")

        self.phase_name.stateChanged.connect(lambda:self.SaveSettings("display_phase", self.phase_name.isChecked()))
        self.team_name.stateChanged.connect(lambda:self.SaveSettings("use_team_names", self.team_name.isChecked()))
        self.sponsor.stateChanged.connect(lambda:self.SaveSettings("use_sponsors", self.sponsor.isChecked()))

        self.preview = self.settings.findChild(QLabel, "thumbnailPreview")

        # -- load settings at init
        settings = SettingsManager.Get("thumbnail")
        if settings is not None :
            print(f'found thumbnail settings ! {settings}')
            settings = SettingsManager.Get("thumbnail")
        else:
            settings = {
                "foreground_path": "./scripts/thumbnail_base/foreground.png",
                "background_path": "./scripts/thumbnail_base/background.png",
                "display_phase": True,
                "use_team_names": False,
                "use_sponsors": True,
                "main_icon_path": "./assets/icons/icon.png",
            }
            settings["side_icon_list"] = ["", ""]
            SettingsManager.Set("thumbnail", settings)

        self.phase_name.setChecked(settings["display_phase"])
        self.team_name.setChecked(settings["use_team_names"])
        self.sponsor.setChecked(settings["use_sponsors"])

        tmp_path = "./tmp/thumbnail"
        tmp_file = f"{tmp_path}/template.jpg"
        Path(tmp_path).mkdir(parents=True, exist_ok=True)

        # if preview not there
        if not os.path.isfile(tmp_file):
            tmp_file = thumbnail.generate(isPreview = True, settingsManager = SettingsManager)
        self.preview.setPixmap(QPixmap(tmp_file))

    # TODO do other way..
    def SaveIcons(self, key, index):
        path = QFileDialog.getOpenFileName()[0]
        print(f'\t- save {path} in {key}')
        settings = SettingsManager.Get("thumbnail")
        settings[key][index] = path

        SettingsManager.Set("thumbnail", settings)

        self.GeneratePreview()

    def SaveImage(self, key):
        path = QFileDialog.getOpenFileName()[0]
        self.SaveSettings(key, path)

    def SaveSettings(self, key, val):
        print(f'\t- save {val} in {key}')
        settings = SettingsManager.Get("thumbnail")
        settings[key] = val
        SettingsManager.Set("thumbnail", settings)

        self.GeneratePreview()

    # re-generate preview
    def GeneratePreview(self):
        try:
            tmp_file = thumbnail.generate(isPreview=True, settingsManager = SettingsManager)
            self.preview.setPixmap(QPixmap(tmp_file))
        except Exception as e:
            print(e)
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon('assets/icons/icon.png'))
            msgBox.setWindowTitle("THS - Thumbnail")
            msgBox.setText("Warning")
            msgBox.setInformativeText(str(e))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.exec()