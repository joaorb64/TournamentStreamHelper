from qtpy.QtWidgets import *
from ..TSHHotkeys import TSHHotkeys
from ..SettingsManager import SettingsManager
from dataclasses import dataclass
from ..TSHGameAssetManager import TSHGameAssetManager


@dataclass
class SETTINGS:
    name: str = None
    path: str = None
    type: str = None
    default: any = None
    callback: callable = lambda: None
    options: list = None


class SettingsWidget(QWidget):
    def __init__(self, settingsBase="", settings=[]):
        super().__init__()

        self.settingsBase = settingsBase

        # Create a layout for the widget and add the label
        layout = QGridLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)

        # Set the layout for the widget
        self.setLayout(layout)

        # Keep reference of all settings related to assets
        self.assetsSettings = []

        for setting in settings:
            self.AddSetting(setting)

        TSHGameAssetManager.instance.signals.onLoad.connect(self.GamesReloaded)

    def GamesReloaded(self):
        for (gameCombo, assetCombo) in self.assetsSettings:
            gameCombo.clear()

            for (key, val) in TSHGameAssetManager.instance.games.items():
                item = QStandardItem()
                item.setText(f'{val.get("name")} ({key})')
                item.setData(val)
                gameCombo.model().appendRow(item)

    def AddSetting(self, settings: SETTINGS = SETTINGS()):
        lastRow = self.layout().rowCount()

        self.layout().addWidget(QLabel(settings.name), lastRow, 0)

        resetButton = QPushButton(
            QApplication.translate("settings", "Default"))

        settingWidget = None

        if settings.type == "bool":
            settingWidget = QCheckBox()
            settingWidget.setChecked(SettingsManager.Get(
                self.settingsBase+"."+settings.path, settings.default))
            settingWidget.stateChanged.connect(lambda val=None: SettingsManager.Set(
                self.settingsBase+"."+settings.path, settingWidget.isChecked()))
            resetButton.clicked.connect(lambda bt=None, settingWidget=settingWidget:
                                        settingWidget.setChecked(
                                            settings.default)
                                        )
        elif settings.type == "hotkey":
            settingWidget = QKeySequenceEdit()
            settingWidget.keySequenceChanged.connect(lambda keySequence, settingWidget=settingWidget:
                                                     settingWidget.setKeySequence(keySequence.toString().split(",")[
                                                                                  0]) if keySequence.count() > 0 else None
                                                     )
            settingWidget.setKeySequence(SettingsManager.Get(
                self.settingsBase+"."+settings.path, settings.default))
            settingWidget.keySequenceChanged.connect(
                lambda sequence=None, setting=settings.path: [
                    SettingsManager.Set(
                        self.settingsBase+"."+setting, sequence.toString()),
                    settings.callback()
                ]
            )
            resetButton.clicked.connect(
                lambda bt=None, setting=settings.path, settingWidget=settingWidget: [
                    settingWidget.setKeySequence(settings.default),
                    settings.callback()
                ]
            )
        elif settings.type == "combobox":
            settingWidget = QComboBox()

            if settings.options:
                for option in settings.options:
                    settingWidget.addItem(option)

                defaultIndex = settings.options.index(settings.default)
                settingWidget.setCurrentIndex(defaultIndex)

                settingWidget.currentIndexChanged.connect(
                    lambda sequence, setting=settings.path: [
                        SettingsManager.Set(
                            self.settingsBase+"."+setting, settingWidget.currentText()),
                        settings.callback()
                    ]
                )

                resetButton.clicked.connect(
                    lambda bt, setting=settings.path, settingWidget=settingWidget: [
                        settingWidget.setCurrentIndex(defaultIndex),
                        settings.callback()
                    ]
                )
        elif settings.type == "asset":
            settingWidget = QWidget()
            settingWidget.setLayout(QHBoxLayout())
            settingWidget.setContentsMargins(0, 0, 0, 0)
            settingWidget.layout().setContentsMargins(0, 0, 0, 0)
            gameCombo = QComboBox()
            assetCombo = QComboBox()
            settingWidget.layout().addWidget(gameCombo)
            settingWidget.layout().addWidget(assetCombo)
            self.assetsSettings.append((gameCombo, assetCombo))
        else:
            settingWidget = QLabel(
                f'Could not identify "{settings.type}" type for {settings.name}')

        if settingWidget:
            self.layout().addWidget(settingWidget, lastRow, 1)
            self.layout().addWidget(resetButton, lastRow, 2)
