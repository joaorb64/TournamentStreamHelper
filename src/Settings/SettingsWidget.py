from PyQt5.QtWidgets import *
from ..TSHHotkeys import TSHHotkeys
from ..SettingsManager import SettingsManager

class SettingsWidget(QWidget):
    def __init__(self, settingsBase = "", settings = []):
        super().__init__()

        self.settingsBase = settingsBase

        # Create a layout for the widget and add the label
        layout = QGridLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)

        # Set the layout for the widget
        self.setLayout(layout)

        for setting in settings:
            self.AddSetting(*setting)

    def AddSetting(self, name: str, setting: str, type: str, defaultValue, callback=lambda: None):
        lastRow = self.layout().rowCount()

        self.layout().addWidget(QLabel(name), lastRow, 0)

        resetButton = QPushButton(QApplication.translate("settings", "Default"))
        
        if type == "checkbox":
            settingWidget = QCheckBox()
            settingWidget.setChecked(SettingsManager.Get(self.settingsBase+"."+setting, defaultValue))
            settingWidget.stateChanged.connect(lambda val: SettingsManager.Set(self.settingsBase+"."+setting, settingWidget.isChecked()))
            resetButton.clicked.connect(lambda bt, settingWidget=settingWidget:
                settingWidget.setChecked(defaultValue)
            )
        elif type == "hotkey":
            settingWidget = QKeySequenceEdit()
            settingWidget.keySequenceChanged.connect(lambda keySequence, settingWidget=settingWidget:
                settingWidget.setKeySequence(keySequence.toString().split(",")[0]) if keySequence.count() > 0 else None
            )
            settingWidget.setKeySequence(SettingsManager.Get(self.settingsBase+"."+setting, defaultValue))
            settingWidget.keySequenceChanged.connect(
                lambda sequence, setting=setting: [
                    SettingsManager.Set(self.settingsBase+"."+setting, sequence.toString()),
                    callback()
                ]
            )
            resetButton.clicked.connect(
                lambda bt, setting=setting, settingWidget=settingWidget:[
                    settingWidget.setKeySequence(defaultValue),
                    callback()
                ]
            )
        
        self.layout().addWidget(settingWidget, lastRow, 1)
        self.layout().addWidget(resetButton, lastRow, 2)