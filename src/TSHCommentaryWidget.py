from rlcompleter import Completer
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy import uic
from loguru import logger

from .TSHScoreboardPlayerWidget import *
from .Helpers.TSHBadWordFilter import TSHBadWordFilter


class TSHCommentaryWidget(QDockWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowTitle(QApplication.translate("app", "Commentary"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)

        topOptions = QWidget()
        topOptions.setLayout(QHBoxLayout())
        topOptions.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.widget.layout().addWidget(topOptions)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        topOptions.layout().addWidget(col)
        self.commentatorNumber = QSpinBox()
        col.layout().addWidget(QLabel(QApplication.translate("app", "Number of commentators")))
        col.layout().addWidget(self.commentatorNumber)
        self.commentatorNumber.valueChanged.connect(
            lambda val: self.SetCommentatorNumber(val))

        scrollArea = QScrollArea()
        scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setWidgetResizable(True)

        self.widgetArea = QWidget()
        self.widgetArea.setLayout(QVBoxLayout())
        self.widgetArea.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum)
        scrollArea.setWidget(self.widgetArea)

        self.widget.layout().addWidget(scrollArea)

        self.commentaryWidgets = []

        StateManager.Set("commentary", {})
        self.commentatorNumber.setValue(2)

        TSHPlayerDB.signals.db_updated.connect(self.SetupAutocomplete)
        self.SetupAutocomplete()

    def SetCommentatorNumber(self, number):
        while len(self.commentaryWidgets) < number:
            comm = QGroupBox()
            uic.loadUi("src/layout/TSHCommentator.ui", comm)
            comm.setTitle(QApplication.translate(
                "app", "Commentator {0}").format(len(self.commentaryWidgets)+1))

            for c in comm.findChildren(QLineEdit):
                c.editingFinished.connect(
                    lambda element=c, index=len(self.commentaryWidgets)+1: [
                        StateManager.Set(
                            f"commentary.{index}.{element.objectName()}", element.text())
                    ])
                c.editingFinished.emit()

            comm.findChild(QPushButton, "btUp").setIcon(
                QIcon("./assets/icons/arrow_up.svg"))
            comm.findChild(QPushButton, "btUp").clicked.connect(
                lambda x=None, index=len(self.commentaryWidgets): self.MoveUp(index))

            comm.findChild(QPushButton, "btDown").setIcon(
                QIcon("./assets/icons/arrow_down.svg"))
            comm.findChild(QPushButton, "btDown").clicked.connect(
                lambda x=None, index=len(self.commentaryWidgets): self.MoveDown(index))

            comm.findChild(QLineEdit, "name").editingFinished.connect(
                lambda c=comm, index=len(self.commentaryWidgets)+1: self.ExportMergedName(c, index))
            comm.findChild(QLineEdit, "team").editingFinished.connect(
                lambda c=comm, index=len(self.commentaryWidgets)+1: self.ExportMergedName(c, index))

            self.commentaryWidgets.append(comm)
            self.widgetArea.layout().addWidget(comm)

        while len(self.commentaryWidgets) > number:
            comm = self.commentaryWidgets[-1]
            comm.setParent(None)
            self.commentaryWidgets.remove(comm)

        self.SetupAutocomplete()

        if StateManager.Get(f'commentary'):
            for k in list(StateManager.Get(f'commentary').keys()):
                if not k.isnumeric() or (k.isnumeric() and int(k) > number):
                    StateManager.Unset(f'commentary.{k}')

    def MoveUp(self, index):
        try:
            StateManager.BlockSaving()
            if index > 0:
                self.SwapComms(index, index-1)
        finally:
            StateManager.ReleaseSaving()

    def MoveDown(self, index):
        try:
            StateManager.BlockSaving()
            if index < len(self.commentaryWidgets)-1:
                self.SwapComms(index, index+1)
        finally:
            StateManager.ReleaseSaving()

    def SwapComms(self, index1, index2):
        saveState = {c.objectName(): c.text()
                     for c in self.commentaryWidgets[index1].findChildren(QLineEdit)}

        for c in self.commentaryWidgets[index2].findChildren(QLineEdit):
            for c2 in self.commentaryWidgets[index2].findChildren(QLineEdit):
                self.commentaryWidgets[index1].findChild(
                    QLineEdit, c.objectName()).setText(c.text())
                self.commentaryWidgets[index1].findChild(
                    QLineEdit, c.objectName()).editingFinished.emit()

            c.setText(saveState[c.objectName()])
            c.editingFinished.emit()

    def ExportMergedName(self, comm, index):
        team = comm.findChild(QLineEdit, "team").text()
        name = comm.findChild(QLineEdit, "name").text()
        merged = ""

        if team != "":
            merged += team+" | "

        merged += name

        StateManager.Set(
            f"commentary.{index}.mergedName", merged)

    def SetupAutocomplete(self):
        if TSHPlayerDB.model:
            for c in self.commentaryWidgets:
                c.findChild(QLineEdit, "name").setCompleter(QCompleter())
                c.findChild(QLineEdit, "name").completer().setCaseSensitivity(
                    Qt.CaseSensitivity.CaseInsensitive)
                c.findChild(QLineEdit, "name").completer(
                ).setFilterMode(Qt.MatchFlag.MatchContains)
                c.findChild(QLineEdit, "name").completer().setModel(
                    TSHPlayerDB.model)
                c.findChild(QLineEdit, "name").completer().activated[QModelIndex].connect(
                    lambda x, c=c: self.SetData(
                        c,
                        x.data(Qt.ItemDataRole.UserRole)), Qt.QueuedConnection
                )
                c.pronoun_completer = QCompleter()
                c.findChild(QLineEdit, "pronoun").setCompleter(
                    c.pronoun_completer)
                c.pronoun_list = []
                for file in ['./user_data/pronouns_list.txt']:
                    try:
                        with open(file, 'r') as f:
                            for l in f.readlines():
                                processed_line = l.replace("\n", "").strip()
                                if processed_line and processed_line not in c.pronoun_list:
                                    c.pronoun_list.append(processed_line)
                    except Exception as e:
                        logger.error(f"ERROR: Did not find {file}")
                        logger.error(traceback.format_exc())
                c.pronoun_model = QStringListModel()
                c.pronoun_completer.setModel(c.pronoun_model)
                c.pronoun_model.setStringList(c.pronoun_list)

    def SetData(self, widget, data):
        if data.get("gamerTag"):
            data["gamerTag"] = TSHBadWordFilter.Censor(
                data["gamerTag"], data.get("country_code"))
        widget.findChild(QLineEdit, "name").setText(data.get("gamerTag", ""))
        widget.findChild(QLineEdit, "name").editingFinished.emit()

        if data.get("team"):
            data["team"] = TSHBadWordFilter.Censor(
                data["team"], data.get("country_code"))
        widget.findChild(QLineEdit, "team").setText(data.get("prefix"))
        widget.findChild(QLineEdit, "team").editingFinished.emit()

        if data.get("real_name"):
            data["real_name"] = TSHBadWordFilter.Censor(
                data["real_name"], data.get("country_code"))
        widget.findChild(QLineEdit, "real_name").setText(data.get("name", ""))
        widget.findChild(QLineEdit, "real_name").editingFinished.emit()

        if data.get("twitter"):
            data["twitter"] = TSHBadWordFilter.Censor(
                data["twitter"], data.get("country_code"))
        widget.findChild(QLineEdit, "twitter").setText(data.get("twitter", ""))
        widget.findChild(QLineEdit, "twitter").editingFinished.emit()

        if data.get("pronoun"):
            data["pronoun"] = TSHBadWordFilter.Censor(data["pronoun"])
        widget.findChild(QLineEdit, "pronoun").setText(data.get("pronoun", ""))
        widget.findChild(QLineEdit, "pronoun").editingFinished.emit()
