from multiprocessing import Lock
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from pathlib import Path
import sys
import os

from .thumbnail import main_generate_thumbnail as thumbnail
from .SettingsManager import *
from .TSHGameAssetManager import *
from .Workers import Worker


class PreviewWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Ignored
        )
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap

        super().setPixmap(self._pixmap.scaled(
            self.width(),
            self.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def resizeEvent(self, QResizeEvent):
        super().resizeEvent(QResizeEvent)
        if self._pixmap:
            self.setPixmap(self._pixmap)


class TSHThumbnailSettingsWidgetSignals(QObject):
    updatePreview = pyqtSignal(str)


class TSHThumbnailSettingsWidget(QDockWidget):
    def resetDisplay(self, settings, force_defaults=False):
        self.VSpacer.setValue(settings["separator"]["width"])
        self.VColor.setStyleSheet("background-color: %s" %
                                  settings["separator"]["color"])
        self.phase_name.setChecked(settings["display_phase"])
        self.team_name.setChecked(settings["use_team_names"])
        self.sponsor.setChecked(settings["use_sponsors"])
        self.flip_p2.setChecked(settings["flip_p2"])
        self.flip_p1.setChecked(settings["flip_p1"])
        self.open_explorer.setChecked(settings["open_explorer"])
        self.selectFontPlayer.setCurrentIndex(
            self.selectFontPlayer.findText(settings["font_list"][0]["name"]))
        self.selectFontPhase.setCurrentIndex(
            self.selectFontPhase.findText(settings["font_list"][1]["name"]))
        if force_defaults:
            self.selectTypeFontPhase.setCurrentIndex(
                self.selectTypeFontPhase.findText(QApplication.translate("app","Bold Italic")))
            self.selectTypeFontPlayer.setCurrentIndex(
                self.selectTypeFontPlayer.findText(QApplication.translate("app","Bold")))
        else:
            self.selectTypeFontPhase.setCurrentIndex(
                self.selectTypeFontPhase.findText(QApplication.translate("app",settings["font_list"][1]["fontPath"])))
            self.selectTypeFontPlayer.setCurrentIndex(
                self.selectTypeFontPlayer.findText(QApplication.translate("app",settings["font_list"][0]["fontPath"])))
        self.playerFontColor.setStyleSheet(
            "background-color: %s" % settings["font_color"][0])
        self.phaseFontColor.setStyleSheet(
            "background-color: %s" % settings["font_color"][1])
        self.colorPlayerOutline.setEnabled(settings["font_outline_enabled"][0])
        if settings["font_outline_enabled"][0]:
            self.colorPlayerOutline.setStyleSheet(
                "background-color: %s" % settings["font_outline_color"][0])
            self.colorPlayerOutline.setText("")
        else:
            self.colorPlayerOutline.setStyleSheet("")
            self.colorPlayerOutline.setText("Disabled")
        self.colorPhaseOutline.setEnabled(settings["font_outline_enabled"][1])
        if settings["font_outline_enabled"][1]:
            self.colorPhaseOutline.setStyleSheet(
                "background-color: %s" % settings["font_outline_color"][1])
            self.colorPhaseOutline.setText("")
        else:
            self.colorPhaseOutline.setStyleSheet("")
            self.colorPhaseOutline.setText("Disabled")
        self.enablePlayerOutline.setChecked(
            settings["font_outline_enabled"][0])
        self.enablePhaseOutline.setChecked(settings["font_outline_enabled"][1])
        game_codename = TSHGameAssetManager.instance.selectedGame.get(
            "codename")
        if game_codename:
            self.zoom.setValue(settings.get(f"zoom/{game_codename}", 100))

    def setDefaults(self, button_mode=False):
        settings = {
            "display_phase": True,
            "use_team_names": False,
            "use_sponsors": True,
            "flip_p1": False,
            "flip_p2": False,
            "open_explorer": True,
            "main_icon_path": "./assets/icons/icon.png",
            "separator": {
                "width": 5,
                "color": "#18181b"
            },
            "thumbnail_type": "./assets/thumbnail_base/thumbnail_types/type_a.json"
        }
        with open(settings["thumbnail_type"], 'rt') as thumbnail_type_file:
            thumbnail_type_desc = json.loads(thumbnail_type_file.read())
            settings["foreground_path"] = thumbnail_type_desc["default_foreground"]
            settings["background_path"] = thumbnail_type_desc["default_background"]
        settings["side_icon_list"] = ["", ""]
        settings["font_list"] = [{
            "name": "Open Sans",
            "type": "Bold",
            "fontPath": "Bold"
        }, {
            "name": "Open Sans",
            "type": "Bold Italic",
            "fontPath": "Bold Italic"
        }]
        settings["font_color"] = [
            "#FFFFFF", "#FFFFFF"
        ]
        settings["font_outline_color"] = [
            "#000000", "#000000"
        ]
        settings["font_outline_enabled"] = [
            True, True
        ]
        SettingsManager.Set("thumbnail", settings)

        if button_mode:
            self.resetDisplay(settings, force_defaults=True)
            self.SetAssetPack(reset=True)
            self.GeneratePreview()

    def __init__(self, *args):
        super().__init__(*args)

        self.signals = TSHThumbnailSettingsWidgetSignals()
        self.signals.updatePreview.connect(self.UpdatePreview)

        self.thumbnailGenerationThread = QThreadPool()
        self.thumbnailGenerationThread.setMaxThreadCount(1)
        self.lock = Lock()

        self.setWindowTitle(QApplication.translate("app","Thumbnail Settings"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.settings = uic.loadUi("src/layout/TSHThumbnailSettings.ui")
        self.widget.layout().addWidget(self.settings)

        # SET DEFAULTS
        self.setDefaultsButton = self.settings.findChild(
            QPushButton, "resetToDefault")
        self.setDefaultsButton.clicked.connect(
            lambda: self.setDefaults(button_mode=True))

        # IMG
        self.foreground = self.settings.findChild(
            QPushButton, "customForeground")
        self.background = self.settings.findChild(
            QPushButton, "customBackground")
        self.mainIcon = self.settings.findChild(QPushButton, "customMainIcon")
        self.topLeftIcon = self.settings.findChild(
            QPushButton, "customTopLeftIcon")
        self.topRightIcon = self.settings.findChild(
            QPushButton, "customTopRightIcon")

        self.foreground.clicked.connect(
            lambda: self.SaveImage("foreground_path"))
        self.background.clicked.connect(
            lambda: self.SaveImage("background_path"))
        self.mainIcon.clicked.connect(lambda: self.SaveImage("main_icon_path"))
        self.topLeftIcon.clicked.connect(
            lambda: self.SaveIcons("side_icon_list", 0))
        self.topRightIcon.clicked.connect(
            lambda: self.SaveIcons("side_icon_list", 1))

        # SEPARATORS
        self.VSpacer = self.settings.findChild(QSpinBox, "widthSpacer")
        self.VColor = self.settings.findChild(QPushButton, "colorSpacer")

        self.VSpacer.valueChanged.connect(lambda: self.SaveSettings(
            key="separator", subKey="width", val=self.VSpacer.value()))
        # open color select & save
        self.VColor.clicked.connect(lambda: self.ColorPicker(
            self.VColor, key="separator", subKey="color"))

        # CHECK BOX
        self.phase_name = self.settings.findChild(QCheckBox, "phaseNameCheck")
        self.team_name = self.settings.findChild(QCheckBox, "teamNameCheck")
        self.sponsor = self.settings.findChild(QCheckBox, "sponsorCheck")
        self.flip_p2 = self.settings.findChild(QCheckBox, "flipP2Check")
        self.flip_p1 = self.settings.findChild(QCheckBox, "flipP1Check")
        self.open_explorer = self.settings.findChild(
            QCheckBox, "openExplorerCheck")

        self.zoom = self.settings.findChild(QSpinBox, "zoom")

        self.phase_name.stateChanged.connect(lambda: self.SaveSettings(
            key="display_phase", val=self.phase_name.isChecked()))
        self.team_name.stateChanged.connect(lambda: self.SaveSettings(
            key="use_team_names", val=self.team_name.isChecked()))
        self.sponsor.stateChanged.connect(lambda: self.SaveSettings(
            key="use_sponsors", val=self.sponsor.isChecked()))
        self.flip_p2.stateChanged.connect(lambda: self.SaveSettings(
            key="flip_p2", val=self.flip_p2.isChecked()))
        self.flip_p1.stateChanged.connect(lambda: self.SaveSettings(
            key="flip_p1", val=self.flip_p1.isChecked()))
        self.open_explorer.stateChanged.connect(lambda: self.SaveSettings(
            key="open_explorer", val=self.open_explorer.isChecked()))

        self.zoom.valueChanged.connect(lambda val: self.SetZoomSetting())

        # FONTS
        self.selectFontPlayer = self.settings.findChild(
            QComboBox, "comboBoxFont")
        self.selectTypeFontPlayer = self.settings.findChild(
            QComboBox, "comboBoxFontType")
        self.selectFontPhase = self.settings.findChild(
            QComboBox, "comboBoxFontPhase")
        self.selectTypeFontPhase = self.settings.findChild(
            QComboBox, "comboBoxFontTypePhase")
        self.playerFontColor = self.settings.findChild(
            QPushButton, "colorPlayerFontColor")
        self.phaseFontColor = self.settings.findChild(
            QPushButton, "colorPhaseFontColor")
        self.colorPlayerOutline = self.settings.findChild(
            QPushButton, "colorPlayerOutline")
        self.colorPhaseOutline = self.settings.findChild(
            QPushButton, "colorPhaseOutline")
        self.enablePlayerOutline = self.settings.findChild(
            QCheckBox, "enablePlayerOutline")
        self.enablePhaseOutline = self.settings.findChild(
            QCheckBox, "enablePhaseOutline")

        self.playerFontColor.clicked.connect(lambda: self.ColorPicker(
            button=self.playerFontColor, key="font_color", subKey=0))
        self.phaseFontColor.clicked.connect(lambda: self.ColorPicker(
            button=self.phaseFontColor, key="font_color", subKey=1))
        self.colorPlayerOutline.clicked.connect(lambda: self.ColorPicker(
            button=self.colorPlayerOutline, key="font_outline_color", subKey=0))
        self.colorPhaseOutline.clicked.connect(lambda: self.ColorPicker(
            button=self.colorPhaseOutline, key="font_outline_color", subKey=1))
        self.enablePlayerOutline.stateChanged.connect(
            lambda: self.enableOutline(index=0, val=self.enablePlayerOutline.isChecked()))
        self.enablePhaseOutline.stateChanged.connect(
            lambda: self.enableOutline(index=1, val=self.enablePhaseOutline.isChecked()))

        # PREVIEW
        previewContainer = self.settings.findChild(QWidget, "thumbnailPreview")
        self.preview = PreviewWidget()
        previewContainer.layout().addWidget(self.preview)

        self.updatePreview = self.settings.findChild(
            QPushButton, "btUpdatePreview")
        self.updatePreview.clicked.connect(self.GeneratePreview)

        # -- load settings at init
        settings = SettingsManager.Get("thumbnail")
        if settings is not None:
            print(f'found thumbnail settings ! {settings}')
        else:
            self.setDefaults()
        settings = SettingsManager.Get("thumbnail")

        # Load OpenSans
        QFontDatabase.addApplicationFont(
            "./assets/font/OpenSans/OpenSans-Bold.ttf")
        QFontDatabase.addApplicationFont(
            "./assets/font/OpenSans/OpenSans-Semibold.ttf")
        font_id = QFontDatabase.addApplicationFont(
            "./assets/font/OpenSans/OpenSans-Bold.ttf")

        unloadable, self.family_to_path = self.getFontPaths()
        # add Open Sans
        self.family_to_path["Open Sans"] = [
            './assets/font/OpenSans/OpenSans-Bold.ttf', './assets/font/OpenSans/OpenSans-Semibold.ttf']
        # add all fonts available
        for k, v in sorted(self.family_to_path.items()):
            self.selectFontPlayer.addItem(k, v)
            self.selectFontPhase.addItem(k, v)

        # listener
        self.selectFontPlayer.currentIndexChanged.connect(
            lambda: self.SetTypeFont(0, self.selectFontPlayer, self.selectTypeFontPlayer))
        self.selectFontPhase.currentIndexChanged.connect(
            lambda: self.SetTypeFont(1, self.selectFontPhase, self.selectTypeFontPhase))

        # update display
        self.resetDisplay(settings)

        # listener type font
        self.selectTypeFontPlayer.currentIndexChanged.connect(lambda: self.SaveFont(
            "font_list",
            self.selectFontPlayer.currentText(),
            self.selectTypeFontPlayer.currentText(),
            self.selectTypeFontPlayer.currentData(),
            0
        ))
        self.selectTypeFontPhase.currentIndexChanged.connect(lambda: self.SaveFont(
            "font_list",
            self.selectFontPhase.currentText(),
            self.selectTypeFontPhase.currentText(),
            self.selectTypeFontPhase.currentData(),
            1
        ))

        # Asset Pack
        self.selectRenderLabel = self.settings.findChild(QLabel, "label_asset")
        self.selectRenderType = self.settings.findChild(
            QComboBox, "comboBoxAsset")
        # add item (assets pack) when choosing game
        TSHGameAssetManager.instance.signals.onLoad.connect(self.SetAssetPack)
        self.selectRenderType.currentIndexChanged.connect(self.SetAssetSetting)

        tmp_path = "./tmp/thumbnail"
        tmp_file = f"{tmp_path}/template.jpg"
        Path(tmp_path).mkdir(parents=True, exist_ok=True)

        # if preview not there
        if not os.path.isfile(tmp_file):
            tmp_file = thumbnail.generate(
                isPreview=True, settingsManager=SettingsManager, gameAssetManager=TSHGameAssetManager)
        self.preview.setPixmap(QPixmap(tmp_file))

    def enableOutline(self, index=0, val=True):
        self.SaveSettings(key="font_outline_enabled", subKey=index, val=val)

        settings = SettingsManager.Get("thumbnail")
        self.colorPlayerOutline.setEnabled(settings["font_outline_enabled"][0])
        if settings["font_outline_enabled"][0]:
            self.colorPlayerOutline.setStyleSheet(
                "background-color: %s" % settings["font_outline_color"][0])
            self.colorPlayerOutline.setText("")
        else:
            self.colorPlayerOutline.setStyleSheet("")
            self.colorPlayerOutline.setText("Disabled")
        self.colorPhaseOutline.setEnabled(settings["font_outline_enabled"][1])
        if settings["font_outline_enabled"][1]:
            self.colorPhaseOutline.setStyleSheet(
                "background-color: %s" % settings["font_outline_color"][1])
            self.colorPhaseOutline.setText("")
        else:
            self.colorPhaseOutline.setStyleSheet("")
            self.colorPhaseOutline.setText("Disabled")

    def SaveIcons(self, key, index):
        path = QFileDialog.getOpenFileName()[0]
        if path:
            self.SaveSettings(key=key, subKey=index, val=path)

    def SaveImage(self, key):
        path = QFileDialog.getOpenFileName()[0]
        if path:
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

    def ColorPicker(self, button, key="separator", subKey="color"):
        try:
            # HEX color
            color_result = QColorDialog.getColor()
            if color_result.isValid():
                color = color_result.name()
                # set button color
                button.setStyleSheet("background-color: %s" % color)
                self.SaveSettings(key=key, subKey=subKey, val=color)
        except Exception as e:
            print(e)

    def SaveSettings(self, key, val, subKey=None, generatePreview=True):
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
        types = ["Regular", "Bold", "Italic", "Bold Italic"]
        types_localised = ["Regular", "Bold", "Italic", "Bold Italic"]
        types_localised[0] = QApplication.translate("app","Regular")
        types_localised[1] = QApplication.translate("app","Bold")
        types_localised[2] = QApplication.translate("app","Italic")
        types_localised[3] = QApplication.translate("app","Bold Italic")

        cbType.clear()

        for i in range(len(types)):
            cbType.addItem(types_localised[i], types[i])

    def getFontPaths(self):
        font_paths = QStandardPaths.standardLocations(
            QStandardPaths.FontsLocation)
        if sys.platform == "win32":
            font_paths.append(
                f"{os.getenv('LOCALAPPDATA')}\\Microsoft\\Windows\\Fonts")

        unloadable = []
        family_to_path = {}

        db = QFontDatabase()
        for fpath in font_paths:  # go through all font paths
            if os.path.exists(fpath):
                # go through all files at each path
                for root, dirs, files in os.walk(fpath):
                    for file in files:
                        path = os.path.join(root, file)

                        idx = db.addApplicationFont(path)  # add font path

                        if idx < 0:
                            # font wasn't loaded if idx is -1
                            unloadable.append(path)
                        else:
                            names = db.applicationFontFamilies(
                                idx)  # load back font family name

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
        settings = SettingsManager.Get("thumbnail")
        if not settings.get("thumbnail_type"):
            settings["thumbnail_type"] = "./assets/thumbnail_base/thumbnail_types/type_a.json"
            with open(settings["thumbnail_type"], 'rt') as thumbnail_type_file:
                thumbnail_type_desc = json.loads(thumbnail_type_file.read())
                settings["foreground_path"] = thumbnail_type_desc["default_foreground"]
                settings["background_path"] = thumbnail_type_desc["default_background"]
            SettingsManager.Set("thumbnail", settings)
        for font_index in range(len(settings["font_list"])):
            if "type" in settings["font_list"][font_index]["type"].lower():
                settings["font_list"][font_index]["type"] = QApplication.translate("app","Bold")
                settings["font_list"][font_index]["filePath"] = "Bold"
                SettingsManager.Set("thumbnail", settings)

        try:
            worker = Worker(self.GeneratePreviewDo)
            self.thumbnailGenerationThread.start(worker)
        except Exception as e:
            print(e)
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon('assets/icons/icon.png'))
            msgBox.setWindowTitle(QApplication.translate("thumb_app", "TSH - Thumbnail"))
            msgBox.setText(QApplication.translate("app", "Warning"))
            msgBox.setInformativeText(str(e))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.exec()

    def GeneratePreviewDo(self, progress_callback):
        if self.thumbnailGenerationThread.activeThreadCount() > 1:
            return

        with self.lock:
            tmp_file = thumbnail.generate(
                isPreview=True, settingsManager=SettingsManager, gameAssetManager=TSHGameAssetManager)
            self.signals.updatePreview.emit(tmp_file)

    def UpdatePreview(self, file):
        self.preview.setPixmap(QPixmap(file))

    def SetAssetPack(self, reset=False):
        self.selectRenderLabel.clear()
        self.selectRenderType.clear()
        if (TSHGameAssetManager.instance.selectedGame.get("name")):
            game_name = TSHGameAssetManager.instance.selectedGame.get("name")
        else:
            game_name = "(No game selected)"
        label_text = f'<html><head/><body><p><span style=" font-weight:700;">{game_name}</span></p></body></html>'
        self.selectRenderLabel.setText(label_text)
        if (TSHGameAssetManager.instance.selectedGame.get("assets")):
            asset_dict = {}
            for key, val in TSHGameAssetManager.instance.selectedGame.get("assets").items():
                # don't use base_files, because don't contains asset, only folder (?)
                if key == "base_files":
                    continue
                # Skip stage icon assets
                if isinstance(val.get("type"), list) and "stage_icon" in val.get("type"):
                    continue
                if val.get("name"):
                    self.selectRenderType.addItem(val.get("name"), key)
                    asset_dict[key] = val.get("name")
                else:
                    self.selectRenderType.addItem(key, key)
                    asset_dict[key] = key
            # select setting
            settings = SettingsManager.Get("thumbnail")
            try:
                if reset:
                    raise(KeyError("Reset to default"))
                game_codename = TSHGameAssetManager.instance.selectedGame.get(
                    "codename")
                if game_codename:
                    self.selectRenderType.setCurrentIndex(self.selectRenderType.findText(
                        asset_dict[settings[f"asset/{game_codename}"]]))
                    self.zoom.setValue(
                        settings.get(f"zoom/{game_codename}", 100))
                else:
                    self.selectRenderType.setCurrentIndex(0)
            except KeyError:
                if "full" in asset_dict.keys():
                    self.selectRenderType.setCurrentIndex(
                        self.selectRenderType.findText(asset_dict["full"]))
                else:
                    self.selectRenderType.setCurrentIndex(
                        self.selectRenderType.findText(asset_dict["base_files/icon"]))
                self.SetAssetSetting(force=True)
            TSHGameAssetManager.instance.thumbnailSettingsLoaded = True

    def SetZoomSetting(self, force=False):
        if TSHGameAssetManager.instance.thumbnailSettingsLoaded or force:
            try:
                game_codename = TSHGameAssetManager.instance.selectedGame.get(
                    "codename")
                TSHThumbnailSettingsWidget.SaveSettings(
                    self, key=f"zoom/{game_codename}", val=self.zoom.value(), generatePreview=True)
            except Exception as e:
                print(e)

    def SetAssetSetting(self, force=False):
        if TSHGameAssetManager.instance.thumbnailSettingsLoaded or force:
            try:
                game_codename = TSHGameAssetManager.instance.selectedGame.get(
                    "codename")
                if self.selectRenderType.currentData():
                    TSHThumbnailSettingsWidget.SaveSettings(
                        self, key=f"asset/{game_codename}", val=self.selectRenderType.currentData(), generatePreview=True)
            except Exception as e:
                print(e)
