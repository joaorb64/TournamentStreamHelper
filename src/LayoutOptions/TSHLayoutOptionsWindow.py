import sys
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from .LayoutOptionsWidget import LayoutOptionsWidget


class TSHLayoutOptionsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def UiMounted(self):
        self.setWindowTitle(QApplication.translate("LayoutOptions", "Layout Options"))

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
        chipOptions = []

        chipOptions.append((
            QApplication.translate("layout_options.seed_display", "Display Player Seed Number"),
            "seed_display",
            "checkbox",
            True
        ))

        chipOptions.append((
            QApplication.translate("layout_options.social_media", "Display Player Social Media"),
            "social_media_display",
            "checkbox",
            True
        ))

        chipOptions.append((
            QApplication.translate("layout_options.country_flag", "Display Player Country Flag"),
            "country_flag_display",
            "checkbox",
            True
        ))

        chipOptions.append((
            QApplication.translate("layout_options.state_flag", "Display Player State Flag"),
            "state_flag_display",
            "checkbox",
            True
        ))

        chipOptions.append((
            QApplication.translate("layout_options.chip_bg_color", "Background Color for Chips"),
            "chip_bg_color",
            "color",
            "#121212"
        ))

        chipOptions.append((
            QApplication.translate("layout_options.chip_bg_gradient", "Make Chips Background Color a Linear Gradient"),
            "chip_bg_color_gradient",
            "checkbox",
            False
        ))

        chipOptions.append((
            QApplication.translate("layout_options.chip_bg_secondary_color", "Secondary Background Color for Chips"),
            "chip_bg_secondary_color",
            "color",
            "#121212"
        ))

        chipOptions.append((
            QApplication.translate("layout_options.chip_bg_gradient_direction", "Background Gradient Direction for Chips"),
            "chip_bg_gradient_direction",
            "dropdown",
            ["to top left", "to top", "to top right", "to left", "to right", "to bottom left", "to bottom", "to bottom right"]
        ))

        self.add_setting_widget(QApplication.translate(
            "layout_options", "Chip Options"), LayoutOptionsWidget("chip-options", chipOptions))

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
