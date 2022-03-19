from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from pathlib import Path
import sys, os

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

        # SEPARATORS
        self.VSpacer = self.settings.findChild(QSpinBox, "widthSpacer")
        self.VColor = self.settings.findChild(QPushButton, "colorSpacer")

        self.VSpacer.valueChanged.connect(lambda: self.SaveSettings(key="separator", subKey="width", val=self.VSpacer.value()))
        # open color select & save
        self.VColor.clicked.connect(self.ColorPicker)

        # CHECK BOX
        self.phase_name = self.settings.findChild(QCheckBox, "phaseNameCheck")
        self.team_name = self.settings.findChild(QCheckBox, "teamNameCheck")
        self.sponsor = self.settings.findChild(QCheckBox, "sponsorCheck")

        self.phase_name.stateChanged.connect(lambda: self.SaveSettings(key="display_phase", val=self.phase_name.isChecked()))
        self.team_name.stateChanged.connect(lambda: self.SaveSettings(key="use_team_names", val=self.team_name.isChecked()))
        self.sponsor.stateChanged.connect(lambda: self.SaveSettings(key="use_sponsors", val=self.sponsor.isChecked()))

        # FONTS
        self.selectFontPlayer = self.settings.findChild(QComboBox, "comboBoxFont")
        self.selectTypeFontPlayer = self.settings.findChild(QComboBox, "comboBoxFontType")
        self.selectFontPhase = self.settings.findChild(QComboBox, "comboBoxFontPhase")
        self.selectTypeFontPhase = self.settings.findChild(QComboBox, "comboBoxFontTypePhase")

        # PREVIEW
        self.preview = self.settings.findChild(QLabel, "thumbnailPreview")

        # -- load settings at init
        settings = SettingsManager.Get("thumbnail")
        if settings is not None :
            print(f'found thumbnail settings ! {settings}')
            settings = SettingsManager.Get("thumbnail")
        else:
            settings = {
                "foreground_path": "./assets/thumbnail_base/foreground.png",
                "background_path": "./assets/thumbnail_base/background.png",
                "display_phase": True,
                "use_team_names": False,
                "use_sponsors": True,
                "main_icon_path": "./assets/icons/icon.png",
                "separator": {
                    "width": 5,
                    "color": "#7F7F7F"
                }
            }
            settings["side_icon_list"] = ["", ""]
            settings["font_list"] = [{
                                        "name": "Open Sans",
                                        "type": "Type 1",
                                        "fontPath": "./assets/font/OpenSans/OpenSans-Bold.ttf"
                                    }, {
                                        "name": "Open Sans",
                                        "type": "Type 2",
                                        "fontPath": "./assets/font/OpenSans/OpenSans-Semibold.ttf"
                                    }]
            SettingsManager.Set("thumbnail", settings)

        self.phase_name.setChecked(settings["display_phase"])
        self.team_name.setChecked(settings["use_team_names"])
        self.sponsor.setChecked(settings["use_sponsors"])

        # TODO each one regenarate the preview, move it before signals and do generation once at the end ?
        self.VSpacer.setValue(settings["separator"]["width"])
        self.VColor.setStyleSheet("background-color: %s" % settings["separator"]["color"])

        # Load OpenSans
        QFontDatabase.addApplicationFont("./assets/font/OpenSans/OpenSans-Bold.ttf")
        QFontDatabase.addApplicationFont("./assets/font/OpenSans/OpenSans-Semibold.ttf")
        font_id = QFontDatabase.addApplicationFont("./assets/font/OpenSans/OpenSans-Bold.ttf")
        font_opensans_bold = QFontDatabase.applicationFontFamilies(font_id)[0]
        font_id = QFontDatabase.addApplicationFont("./assets/font/OpenSans/OpenSans-Semibold.ttf")
        font_opensans_semi_bold = QFontDatabase.applicationFontFamilies(font_id)[0]

        unloadable, self.family_to_path = self.getFontPaths()
        # add Open Sans
        self.family_to_path["Open Sans"] = ['./assets/font/OpenSans/OpenSans-Bold.ttf', './assets/font/OpenSans/OpenSans-Semibold.ttf']
        # TODO sort ?
        # add all fonts available
        for k, v in self.family_to_path.items():
            self.selectFontPlayer.addItem(k, v)
            self.selectFontPhase.addItem(k, v)

        # listener
        self.selectFontPlayer.currentIndexChanged.connect(lambda: self.SetTypeFont(0, self.selectFontPlayer, self.selectTypeFontPlayer))
        self.selectFontPhase.currentIndexChanged.connect(lambda: self.SetTypeFont(1, self.selectFontPhase, self.selectTypeFontPhase))

        # select setting
        self.selectFontPlayer.setCurrentIndex(self.selectFontPlayer.findText(settings["font_list"][0]["name"]))
        self.selectFontPhase.setCurrentIndex(self.selectFontPhase.findText(settings["font_list"][1]["name"]))

        self.selectTypeFontPlayer.setCurrentIndex(self.selectTypeFontPlayer.findText(settings["font_list"][0]["type"]))
        self.selectTypeFontPhase.setCurrentIndex(self.selectTypeFontPhase.findText(settings["font_list"][1]["type"]))

        # listener type font
        self.selectTypeFontPlayer.currentIndexChanged.connect(lambda: self.SaveFont("font_list",
                self.selectFontPlayer.currentText(), self.selectTypeFontPlayer.currentText(), self.selectTypeFontPlayer.currentData(), 0))
        self.selectTypeFontPhase.currentIndexChanged.connect(lambda: self.SaveFont("font_list",
               self.selectFontPhase.currentText(), self.selectTypeFontPhase.currentText(), self.selectTypeFontPhase.currentData(), 1))

        tmp_path = "./tmp/thumbnail"
        tmp_file = f"{tmp_path}/template.jpg"
        Path(tmp_path).mkdir(parents=True, exist_ok=True)

        # if preview not there
        if not os.path.isfile(tmp_file):
            tmp_file = thumbnail.generate(isPreview = True, settingsManager = SettingsManager)
        self.preview.setPixmap(QPixmap(tmp_file))

    def SaveIcons(self, key, index):
        path = QFileDialog.getOpenFileName()[0]

        self.SaveSettings(key=key, subKey=index, val=path)

    def SaveImage(self, key):
        path = QFileDialog.getOpenFileName()[0]
        self.SaveSettings(key=key, val=path)

    def SaveFont(self, key, font, type, fontPath, index):
        try:
            if font and fontPath:
                fontSetting = {
                    "name": font,
                    "type": type,
                    "fontPath": fontPath
                }
                self.SaveSettings(key=key, subKey=index, val=fontSetting)
        except Exception as e:
            print("error save font")
            print(e)

    def ColorPicker(self):
        try:
            # HEX color
            color = QColorDialog.getColor().name()
            # set button color
            self.VColor.setStyleSheet("background-color: %s" % color)

            self.SaveSettings(key="separator", subKey="color", val=color)
        except Exception as e:
            print(e)

    def SaveSettings(self, key, val, subKey=None, generatePreview = True):
        try:
            settings = SettingsManager.Get("thumbnail")

            if subKey is not None:
                print(f'\t- save {val} in {key}.{subKey}')
                settings[key][subKey] = val
            else:
                print(f'\t- save {val} in {key}')
                settings[key] = val

            SettingsManager.Set("thumbnail", settings)
        except Exception as e:
            print(e)

        if generatePreview:
            self.GeneratePreview()

    def SetTypeFont(self, index, cbFont, cbType):
        print(f'set type font {cbFont.currentData()}')
        types = cbFont.currentData()
        cbType.clear()

        for i in range(len(types)):
            cbType.addItem(f'Type {i + 1}', types[i])

    def getFontPaths(self):
        font_paths = QStandardPaths.standardLocations(QStandardPaths.FontsLocation)
        if sys.platform == "win32":
            font_paths.append(f"{os.getenv('LOCALAPPDATA')}\\Microsoft\\Windows\\Fonts")

        unloadable = []
        family_to_path = {}

        db = QFontDatabase()
        for fpath in font_paths:  # go through all font paths
            for filename in os.listdir(fpath):  # go through all files at each path
                path = os.path.join(fpath, filename)

                idx = db.addApplicationFont(path)  # add font path

                if idx < 0:
                    unloadable.append(path)  # font wasn't loaded if idx is -1
                else:
                    names = db.applicationFontFamilies(idx)  # load back font family name

                    for n in names:
                        if n in family_to_path:
                            family_to_path[n].append(path)
                        else:
                            family_to_path[n] = [path]
                    # this isn't a 1:1 mapping, for example
                    # 'C:/Windows/Fonts/HTOWERT.TTF' (regular) and
                    # 'C:/Windows/Fonts/HTOWERTI.TTF' (italic) are different
                    # but applicationFontFamilies will return 'High Tower Text' for both
        return unloadable, family_to_path

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