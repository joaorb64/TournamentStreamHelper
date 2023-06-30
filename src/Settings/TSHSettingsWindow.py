import sys
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from .SettingsWidget import SettingsWidget
from .SettingsWidget import SETTINGS as SettingsWidgetSettings
from ..TSHHotkeys import TSHHotkeys
import json


def iterate_json_leaves(obj, key=None):
    if isinstance(obj, dict):
        isLeaf = True
        for k, value in obj.items():
            if isinstance(value, dict):
                isLeaf = False
                break
        if isLeaf:
            yield {key: obj}
        else:
            for k, value in obj.items():
                yield from iterate_json_leaves(value, f'{key}.{k}' if key else k)
    else:
        yield obj


class TSHSettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def UiMounted(self):
        self.setWindowTitle(QApplication.translate("Settings", "Settings"))

        # Create a list widget for the selection
        self.selection_list = QListWidget()
        self.selection_list.currentRowChanged.connect(
            self.on_selection_changed)

        # Create a stacked widget for the settings widgets
        self.settings_stack = QStackedWidget()

        # Create a scroll area for the settings stack
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.settings_stack)

        # Create a splitter for the selection and settings
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.selection_list)
        splitter.addWidget(scroll_area)

        # Set the layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Add general settings
        generalSettings = []

        generalSettings.append(SettingsWidgetSettings(**{
            "name": QApplication.translate("settings.general", "Enable profanity filter"),
            "path": "profanity_filter",
            "type": "bool",
            "default": True
        }))

        self.add_setting_widget(QApplication.translate(
            "settings", "General"), SettingsWidget("general", generalSettings))

        # Add hotkey settings
        hotkeySettings = []
        hotkeySettings.append(SettingsWidgetSettings(**{
            "name": QApplication.translate("settings.hotkeys", "Enable hotkeys"),
            "path": "hotkeys_enabled",
            "type": "bool",
            "default": True
        }))

        key_names = {
            "load_set": QApplication.translate("settings.hotkeys", "Load set"),
            "team1_score_up": QApplication.translate("settings.hotkeys", "Team 1 score up"),
            "team1_score_down": QApplication.translate("settings.hotkeys", "Team 1 score down"),
            "team2_score_up": QApplication.translate("settings.hotkeys", "Team 2 score up"),
            "team2_score_down": QApplication.translate("settings.hotkeys", "Team 2 score down"),
            "reset_scores": QApplication.translate("settings.hotkeys", "Reset scores"),
            "swap_teams": QApplication.translate("settings.hotkeys", "Swap teams"),
        }

        for i, (setting, value) in enumerate(TSHHotkeys.instance.keys.items()):
            hotkeySettings.append(SettingsWidgetSettings(**{
                "name": key_names[setting],
                "path": setting,
                "type": "hotkey",
                "default": value,
                "callback": TSHHotkeys.instance.ReloadHotkeys
            }))

        self.add_setting_widget(QApplication.translate(
            "settings", "Hotkeys"), SettingsWidget("hotkeys", hotkeySettings))

        # Layout
        layoutSettings = []

        layoutJson = json.load(open("./layout/settings_map.json"))

        for entry in iterate_json_leaves(layoutJson):
            (key, value) = list(entry.items())[0]
            layoutSettings.append(SettingsWidgetSettings(**{
                "name": key,
                "path": key,
                "type": value.get("type"),
                "default": value.get("default"),
                "options": value.get("options")
            }))

        self.add_setting_widget(QApplication.translate(
            "settings", "Layout"), SettingsWidget("layout", layoutSettings))

        # Layout
        layoutSettings = []

        layoutJson = json.load(open("./layout/settings_map.json"))

        for entry in iterate_json_leaves(layoutJson):
            (key, value) = list(entry.items())[0]
            layoutSettings.append(SettingsWidgetSettings(**{
                "name": key,
                "path": key,
                "type": value.get("type"),
                "default": value.get("default"),
                "options": value.get("options")
            }))

        self.add_setting_widget(QApplication.translate(
            "settings", "Layout"), SettingsWidget("layout", layoutSettings))

        self.resize(1000, 500)
        QApplication.processEvents()
        splitter.setSizes([200, self.width()-200])

    def on_selection_changed(self, index):
        # Get the selected item and its associated widget
        item = self.selection_list.item(index)
        widget = item.data(Qt.UserRole)

        # Set the current widget in the stack
        self.settings_stack.setCurrentWidget(widget)

    def add_setting_widget(self, name, widget):
        # Create a list widget item for the selection
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, widget)
        self.selection_list.addItem(item)

        # Add the setting widget to the stack
        self.settings_stack.addWidget(widget)
