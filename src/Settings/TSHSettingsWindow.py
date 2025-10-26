from qtpy.QtCore import *
from qtpy.QtWidgets import *
from .SettingsWidget import SettingsWidget
from ..TSHHotkeys import TSHHotkeys
from ..Helpers.TSHVersionHelper import add_beta_label


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

        generalSettings.append((
            QApplication.translate(
                "settings.general", "Webserver Port"),
            "webserver_port",
            "spinbox",
            5000
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.general", "Enable profanity filter"),
            "profanity_filter",
            "checkbox",
            True
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.control_score_from_stage_strike", "Enable score control from the stage striking app"),
            "control_score_from_stage_strike",
            "checkbox",
            True
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.disable_autoupdate", "Disable automatic set updating for the scoreboard"),
            "disable_autoupdate",
            "checkbox",
            False
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.disable_scoreupdate", "Disable automatic score updating for the scoreboard"),
            "disable_scoreupdate",
            "checkbox",
            False
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.disable_export", "Disable TSH file exporting"),
            "disable_export",
            "checkbox",
            False
        ))
        
        generalSettings.append((
            QApplication.translate(
                "settings.disable_overwrite", "Do not override existing values in local_players.csv (takes effect on next restart)"),
            "disable_overwrite",
            "checkbox",
            False
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.hide_track_player", "Hide the StartGG player tracking functionality from TSH (takes effect on next restart)"),
            "hide_track_player",
            "checkbox",
            False
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.disable_country_file_downloading", "Disables attempting to download the country and states file (takes effect on next restart)"),
            "disable_country_file_downloading",
            "checkbox",
            False
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.disable_controller_file_downloading", "Disables attempting to download the controllers file (takes effect on next restart)"),
            "disable_controller_file_downloading",
            "checkbox",
            False
        ))


        generalSettings.append((
            add_beta_label(QApplication.translate(
                "settings.disable_individual_game_tracker", "Disables the individual game tracker (takes effect on next restart)"), "game_tracker"),
            "disable_individual_game_tracker",
            "checkbox",
            True
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.team_1_default_color", "Default Color of Team 1"),
            "team_1_default_color",
            "color",
            "#fe3636"
        ))

        generalSettings.append((
            QApplication.translate(
                "settings.team_2_default_color", "Default Color of Team 2"),
            "team_2_default_color",
            "color",
            "#2e89ff"
        ))

        self.add_setting_widget(QApplication.translate(
            "settings", "General"), SettingsWidget("general", generalSettings))

        # Add hotkey settings
        hotkeySettings = []

        hotkeySettings.append((
            QApplication.translate("settings.hotkeys", "Enable hotkeys"),
            "hotkeys_enabled",
            "checkbox",
            True
        ))

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
            hotkeySettings.append((
                key_names[setting],
                setting,
                "hotkey",
                value,
                TSHHotkeys.instance.ReloadHotkeys
            ))

        self.add_setting_widget(QApplication.translate(
            "settings", "Hotkeys"), SettingsWidget("hotkeys", hotkeySettings))
            
        # Add Display Options settings
        displaySettings = []

        displaySettings.append((
            QApplication.translate(
                "settings.show_name", "Show Real Name"),
            "show_name",
            "checkbox",
            True
        ))

        displaySettings.append((
            QApplication.translate(
                "settings.show_social", "Show Social Media"),
            "show_social",
            "checkbox",
            True
        ))

        displaySettings.append((
            QApplication.translate(
                "settings.show_location", "Show Location"),
            "show_location",
            "checkbox",
            True
        ))

        displaySettings.append((
            QApplication.translate(
                "settings.show_characters", "Show Characters"),
            "show_characters",
            "checkbox",
            True
        ))

        displaySettings.append((
            QApplication.translate(
                "settings.show_pronouns", "Show Pronouns"),
            "show_pronouns",
            "checkbox",
            True
        ))

        displaySettings.append((
            QApplication.translate(
                "settings.show_controller", "Show Controller"),
            "show_controller",
            "checkbox",
            True
        ))

        displaySettings.append((
            QApplication.translate(
                "settings.show_additional", "Show Additional Info"),
            "show_additional",
            "checkbox",
            True
        ))
        
        self.add_setting_widget(QApplication.translate(
            "settings", "Default Display Options"), SettingsWidget("display_options", displaySettings))

        # Add Bluesky settings
        bskySettings = []
        bskySettings.append((
            QApplication.translate(
                "settings.bsky", "Enable Bluesky Features"),
            "enable_bluesky",
            "checkbox",
            True
        ))
        bskySettings.append((
            QApplication.translate(
                "settings.bsky", "Host server"),
            "host",
            "textbox",
            "https://bsky.social"
        ))
        bskySettings.append((
            QApplication.translate(
                "settings.bsky", "Bluesky Handle"),
            "username",
            "textbox",
            ""
        ))
        bskySettings.append((
            QApplication.translate(
                "settings.bsky", "Application Password"),
            "app_password",
            "password",
            "",
            None,
            QApplication.translate(
                "settings.bsky", "You can get an app password by going into your Bluesky settings -> Privacy & Security") + "\n" +
                QApplication.translate(
                "settings.bsky", "Please note that said app password will be stored in plain text on your computer") + "\n\n" +
                QApplication.translate(
                "settings.bsky", "Do not use your regular account password!").upper()
        ))
        
        self.add_setting_widget(QApplication.translate(
            "settings", "Bluesky"), SettingsWidget("bsky_account", bskySettings))

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
