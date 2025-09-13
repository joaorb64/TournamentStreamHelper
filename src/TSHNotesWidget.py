from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from loguru import logger
from .StateManager import StateManager


class TSHNotesWidget(QDockWidget):
    def __init__(self, *args, base="notes"):
        def create_individual_notes_widget(index):
            widget = QWidget()
            widget.setObjectName(f"notes_widget_{index+1}")
            widget.setLayout(QVBoxLayout())

            notes_title = QLineEdit()
            widget.layout().addWidget(notes_title)
            notes_title.setPlaceholderText(QApplication.translate("notes", "Title"))
            notes_title.editingFinished.connect(
                lambda element=notes_title: StateManager.Set(
                        f"notes.{widget.objectName()}.title", element.text()))
            notes_title.editingFinished.emit()

            notes_contents = QPlainTextEdit()
            widget.layout().addWidget(notes_contents)
            notes_contents.textChanged.connect(
                lambda element=notes_contents: 
                    StateManager.Set(
                        f"notes.{widget.objectName()}.contents", element.toPlainText()))
            notes_contents.textChanged.emit()

            return(widget)
        
        super().__init__(*args)
        self.setWindowTitle(QApplication.translate("app", "Additional Notes"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)

        for i in range(4):
            self.widget.layout().addWidget(create_individual_notes_widget(i))
