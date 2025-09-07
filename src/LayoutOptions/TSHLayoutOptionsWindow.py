from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from .LayoutOptionsWidget import LayoutOptionsWidget


class TSHLayoutOptionsWindow(QDialog):
    
    chipOptions = []
    bracketOptions = []
    versusOptions = []
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def UiMounted(self):
        self.setWindowTitle(QApplication.translate("LayoutOptions", "Layout Options"))
        
        # Create a combobox for preset selections to quick apply options
        self.presets = QComboBox()
        self.presets.setObjectName("presets")

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

        # Create a Line Edit widget for setting the name of the preset
        preset_name = QHBoxLayout()
        preset_name_label = QLabel()
        preset_name_label.setText(QApplication.translate("layout_options.preset_name", "Preset Name"))
        preset_name.addWidget(preset_name_label)
        self.preset_name = QLineEdit()
        self.preset_name.setObjectName("preset_name")
        preset_name.addWidget(self.preset_name)

        # Create the push buttons to save/update and delete presets
        save_options = QHBoxLayout()
        self.saveBtn = QPushButton()
        self.saveBtn.setIcon(QIcon('assets/icons/save.svg'))
        # self.saveBtn.setText(QApplication.translate("app", "Save new"))
        self.saveBtn.setText(QApplication.translate("app", "Update"))
        save_options.addWidget(self.saveBtn)
        self.deleteBtn = QPushButton()
        self.deleteBtn.setIcon(QIcon('assets/icons/cancel.svg'))
        self.deleteBtn.setText("Delete")
        save_options.addWidget(self.deleteBtn)


        # Set the layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(self.presets)
        layout.addLayout(preset_name)
        layout.addWidget(splitter)
        layout.addLayout(save_options)
        self.setLayout(layout)

        # ================================================================
        # START LAYOUT OPTIONS SECTIONS
        # ================================================================
        GRADIENT_DIRECTIONS = ["TO TOP LEFT", "TO TOP", "TO TOP RIGHT", "TO LEFT", "TO RIGHT", "TO BOTTOM LEFT", "TO BOTTOM", "TO BOTTOM RIGHT"]

        # ================================================================
        # START CHIPS LAYOUT OPTIONS
        # ================================================================

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_pronouns_display", "Display Player Pronouns"),
            "chip_pronouns_display",
            "checkbox",
            True
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_seed_display", "Display Player Seed Number"),
            "chip_seed_display",
            "checkbox",
            True
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_social_media", "Display Player Social Media"),
            "chip_social_media_display",
            "checkbox",
            True
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_country_flag", "Display Player Country Flag"),
            "chip_country_flag_display",
            "checkbox",
            True
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_state_flag", "Display Player State Flag"),
            "chip_state_flag_display",
            "checkbox",
            True
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_text_color", "Text Color for Chips"),
            "chip_text_color",
            "color",
            "#121212"
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_bg_color", "Primary Color for Chips"),
            "chip_bg_color",
            "color",
            "#121212"
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_bg_gradient", "Make Chips Background Color a Linear Gradient"),
            "chip_bg_color_gradient",
            "checkbox",
            False
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_bg_secondary_color", "Secondary Color for Chips"),
            "chip_bg_secondary_color",
            "color",
            "#121212"
        ))

        self.chipOptions.append((
            QApplication.translate("layout_options.chip_bg_gradient_direction", "Background Gradient Direction for Chips"),
            "chip_bg_gradient_direction",
            "dropdown",
            GRADIENT_DIRECTIONS
        ))

        self.add_setting_widget(QApplication.translate(
            "layout_options", "Chip Options"), LayoutOptionsWidget("chip-options", self.chipOptions))

        # ================================================================
        # START BRACKET LAYOUT OPTIONS
        # ================================================================

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_character", "Display Player Avatar"),
            "bracket_avatar_display",
            "checkbox",
            True
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_character", "Display Player Character"),
            "bracket_character_display",
            "checkbox",
            True
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_country_flag", "Display Player Country Flag"),
            "bracket_country_flag_display",
            "checkbox",
            True
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_state_flag", "Display Player State Flag"),
            "bracket_state_flag_display",
            "checkbox",
            True
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_score_color", "Primary Color for Player Score"),
            "bracket_score_color",
            "color",
            "#fe3636"
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_score_color_gradient", "Make Score Color a Linear Gradient"),
            "bracket_score_color_gradient",
            "checkbox",
            False
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_score_gradient_direction", "Background Gradient Direction for Score"),
            "bracket_score_gradient_direction",
            "dropdown",
            GRADIENT_DIRECTIONS
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_score_secondary_color", "Secondary Color for Player Score"),
            "bracket_score_secondary_color",
            "color",
            "#121212"
        ))
        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_sponsor_color", "Primary Color for Player Sponsor"),
            "bracket_sponsor_color",
            "color",
            "#fe3636"
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_sponsor_color_gradient", "Make Sponsor Color a Linear Gradient"),
            "bracket_sponsor_color_gradient",
            "checkbox",
            False
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_sponsor_gradient_direction", "Background Gradient Direction for Sponsor"),
            "bracket_sponsor_gradient_direction",
            "dropdown",
            GRADIENT_DIRECTIONS
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_sponsor_secondary_color", "Secondary Color for Player Sponsor"),
            "bracket_sponsor_secondary_color",
            "color",
            "#121212"
        ))

        self.bracketOptions.append((
            QApplication.translate("layout_options.bracket_line_color", "Color for Bracket Lines"),
            "bracket_lines_color",
            "color",
            "#000000"
        ))

        self.add_setting_widget(QApplication.translate(
            "layout_options", "Bracket Options"), LayoutOptionsWidget("bracket-options", self.bracketOptions))
        
        # ================================================================
        # START VERSUS LAYOUT OPTIONS
        # ================================================================

        self.versusOptions.append((
            QApplication.translate("layout_options.versus_team1_sponsor_color", "Color for Team 1 Sponsor Color"),
            "versus_team1_sponsor_color",
            "color",
            "#000000"
        ))

        self.add_setting_widget(QApplication.translate(
            "layout_options", "Versus Options"), LayoutOptionsWidget("versus-options", self.versusOptions))

        # ================================================================
        # Setup Window Calls
        # ================================================================
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
