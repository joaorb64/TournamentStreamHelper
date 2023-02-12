import traceback
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
import requests

from src.Helpers.TSHLocaleHelper import TSHLocaleHelper
from src.TSHStageStrikeLogic import TSHStageStrikeLogic
from .Helpers.TSHDictHelper import deep_get
from .StateManager import StateManager
from .TSHWebServer import WebServer
from .TSHGameAssetManager import TSHGameAssetManager
import socket
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class TSHScoreboardStageWidgetSignals(QObject):
    rulesets_changed = pyqtSignal()


class Ruleset():
    def __init__(self) -> None:
        self.name = ""
        self.neutralStages = []
        self.counterpickStages = []
        self.banByMaxGames = {}
        self.useDSR = False
        self.useMDSR = False
        self.banCount = 0
        self.strikeOrder = []
        self.videogame = ""
        self.errors = []


class TSHScoreboardStageWidget(QDockWidget):

    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle(QApplication.translate("app", "Ruleset"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)

        self.innerWidget = QWidget()
        self.setWidget(self.innerWidget)

        self.stageStrikeLogic = TSHStageStrikeLogic()

        self.signals = TSHScoreboardStageWidgetSignals()

        uic.loadUi("src/layout/TSHScoreboardStage.ui", self.innerWidget)

        self.userRulesets = []
        self.startggRulesets = []
        self.stagesModel = QStandardItemModel()

        self.rulesetsBox = self.findChild(QComboBox, "rulesetSelect")
        self.rulesetsBox.activated.connect(self.LoadRuleset)

        self.stagesView = self.findChild(QListView, "allStages")
        self.stagesView.setIconSize(QSize(64, 64))

        self.stagesNeutral = self.findChild(QListView, "neutralStages")
        self.stagesNeutral.setIconSize(QSize(64, 64))

        self.stagesCounterpick = self.findChild(QListView, "counterpickStages")
        self.stagesCounterpick.setIconSize(QSize(64, 64))

        self.rulesetName = self.findChild(QLineEdit, "rulesetName")
        self.rulesetName.textEdited.connect(self.ExportCurrentRuleset)

        self.btAddNeutral = self.findChild(QPushButton, "btAddNeutral")
        self.btAddNeutral.clicked.connect(
            lambda x, view=self.stagesNeutral: self.AddStage(view))
        self.btAddNeutral.setIcon(QIcon("./assets/icons/arrow_right.svg"))

        self.btRemoveNeutral = self.findChild(QPushButton, "btRemoveNeutral")
        self.btRemoveNeutral.clicked.connect(
            lambda x: self.RemoveStage(self.stagesNeutral))
        self.btRemoveNeutral.setIcon(QIcon("./assets/icons/arrow_left.svg"))

        self.btAddCounterpick = self.findChild(QPushButton, "btAddCounterpick")
        self.btAddCounterpick.clicked.connect(
            lambda x, view=self.stagesCounterpick: self.AddStage(view))
        self.btAddCounterpick.setIcon(QIcon("./assets/icons/arrow_right.svg"))

        self.btRemoveCounterpick = self.findChild(
            QPushButton, "btRemoveCounterpick")
        self.btRemoveCounterpick.clicked.connect(
            lambda x: self.RemoveStage(self.stagesCounterpick))
        self.btRemoveCounterpick.setIcon(
            QIcon("./assets/icons/arrow_left.svg"))

        self.noDSR = self.findChild(QRadioButton, "noDSR")
        self.noDSR.clicked.connect(self.ExportCurrentRuleset)
        self.DSR = self.findChild(QRadioButton, "DSR")
        self.DSR.clicked.connect(self.ExportCurrentRuleset)
        self.MDSR = self.findChild(QRadioButton, "MDSR")
        self.MDSR.clicked.connect(self.ExportCurrentRuleset)

        self.strikeOrder = self.findChild(QLineEdit, "strikeOrder")
        self.strikeOrder.textEdited.connect(self.ExportCurrentRuleset)

        self.fixedBanCount = self.findChild(QRadioButton, "fixedBanCount")
        self.fixedBanCount.clicked.connect(self.ExportCurrentRuleset)
        self.variableBanCount = self.findChild(
            QRadioButton, "variableBanCount")
        self.variableBanCount.clicked.connect(self.ExportCurrentRuleset)

        self.banCount = self.findChild(QSpinBox, "banCount")
        self.banCount.valueChanged.connect(self.ExportCurrentRuleset)

        self.banCountByMaxGames = self.findChild(
            QLineEdit, "banCountByMaxGames")
        self.banCountByMaxGames.textEdited.connect(self.ExportCurrentRuleset)

        self.webappLabel = self.findChild(QLabel, "labelIp")
        self.webappLabel.setText(
            QApplication.translate("app", "Open {0} in a browser to stage strike.").format(f"<a href='http://{self.GetIP()}:5000'>http://{self.GetIP()}:5000</a>"))
        self.webappLabel.setOpenExternalLinks(True)

        self.labelValidation = self.findChild(QLabel, "labelValidation")
        self.labelValidation.setText("")

        self.signals.rulesets_changed.connect(self.LoadRulesets)
        self.LoadStartggRulesets()
        self.LoadRuleset()

        TSHGameAssetManager.instance.signals.onLoad.connect(self.SetupOptions)

        StateManager.Set(f"score.ruleset", None)
        self.ExportCurrentRuleset()

        self.btSave = self.findChild(QPushButton, "btSave")
        self.btSave.setIcon(QIcon('assets/icons/save.svg'))
        self.btDelete = self.findChild(QPushButton, "btDelete")
        self.btDelete.setIcon(QIcon('assets/icons/cancel.svg'))
        self.btClear = self.findChild(QPushButton, "btClear")
        self.btClear.setIcon(QIcon('assets/icons/undo.svg'))

        self.rulesetName.textChanged.connect(self.UpdateBottomButtons)
        self.btSave.clicked.connect(self.SaveRuleset)
        self.btDelete.clicked.connect(self.DeleteRuleset)
        self.btClear.clicked.connect(self.ClearRuleset)

        # TSHTournamentDataProvider.instance.signals.tournament_changed.connect()
        # load tournament ruleset

    def GetIP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def AddStage(self, view: QListView):
        selected = self.stagesView.selectedIndexes()

        if len(selected) == 1:
            data = selected[0].data(Qt.ItemDataRole.UserRole)

            for i in range(self.stagesNeutral.model().rowCount()):
                if self.stagesNeutral.model().item(i, 0).data(Qt.ItemDataRole.UserRole).get("name") == data.get("name"):
                    return

            for i in range(self.stagesCounterpick.model().rowCount()):
                if self.stagesCounterpick.model().item(i, 0).data(Qt.ItemDataRole.UserRole).get("name") == data.get("name"):
                    return

            item = self.stagesView.model().itemFromIndex(selected[0]).clone()
            view.model().appendRow(item)
            view.model().sort(0)
            self.ExportCurrentRuleset()

    def RemoveStage(self, view: QListView):
        selected = view.selectedIndexes()

        if len(selected) == 1:
            view.model().removeRow(selected[0].row())
            self.ExportCurrentRuleset()

    def UpdateBottomButtons(self):
        found = next((
            ruleset for ruleset in self.userRulesets if ruleset.get(
                "videogame") == TSHGameAssetManager.instance.selectedGame.get(
                    "codename") and ruleset.get("name") == self.rulesetName.text()), None)

        if found:
            self.btSave.setText(QApplication.translate("app", "Update"))
            self.btDelete.setEnabled(True)
        else:
            self.btSave.setText(QApplication.translate("app", "Save new"))
            self.btDelete.setEnabled(False)

    def SaveRuleset(self):
        found = next((
            ruleset for ruleset in self.userRulesets if ruleset.get(
                "videogame") == TSHGameAssetManager.instance.selectedGame.get(
                    "codename") and ruleset.get("name") == self.rulesetName.text()), None)

        if found:
            self.userRulesets.remove(found)

        self.userRulesets.append(vars(self.GetCurrentRuleset(True)))

        self.SaveRulesetsFile()

    def DeleteRuleset(self):
        found = next((
            ruleset for ruleset in self.userRulesets if ruleset.get(
                "videogame") == TSHGameAssetManager.instance.selectedGame.get(
                    "codename") and ruleset.get("name") == self.rulesetName.text()), None)

        if found:
            self.userRulesets.remove(found)
            self.SaveRulesetsFile()

    def ClearRuleset(self):
        self.LoadRuleset()

    def SaveRulesetsFile(self):
        try:
            with open("./user_data/rulesets.json", 'w', encoding="utf-8") as outfile:
                json.dump(self.userRulesets, outfile, indent=4, sort_keys=True)
        except Exception as e:
            traceback.print_exc()

        self.LoadRulesets()
        self.UpdateBottomButtons()

    def SetupOptions(self):
        self.rulesetsBox.clear()

        self.LoadRulesets()

        self.stagesModel = QStandardItemModel()

        for stage in TSHGameAssetManager.instance.selectedGame.get("stage_to_codename", {}).items():
            # Load stage name translations
            stage[1]["en_name"] = stage[1].get("name")

            # Display name
            display_name = stage[1].get("name")

            locale = TSHLocaleHelper.programLocale
            if locale.replace('-', '_') in stage[1].get("locale", {}):
                display_name = stage[1].get("locale", {})[
                    locale.replace('-', '_')]
            elif locale.split('-')[0] in stage[1].get("locale", {}):
                display_name = stage[1].get("locale", {})[
                    locale.split('-')[0]]
            elif TSHLocaleHelper.GetRemaps(TSHLocaleHelper.programLocale) in stage[1].get("locale", {}):
                display_name = stage[1].get("locale", {})[
                    TSHLocaleHelper.GetRemaps(TSHLocaleHelper.programLocale)]

            stage[1]["display_name"] = display_name

            # Export name
            export_name = stage[1].get("name")

            locale = TSHLocaleHelper.exportLocale
            if locale.replace('-', '_') in stage[1].get("locale", {}):
                export_name = stage[1].get("locale", {})[
                    locale.replace('-', '_')]
            elif locale.split('-')[0] in stage[1].get("locale", {}):
                export_name = stage[1].get("locale", {})[
                    locale.split('-')[0]]
            elif TSHLocaleHelper.GetRemaps(TSHLocaleHelper.exportLocale) in stage[1].get("locale", {}):
                export_name = stage[1].get("locale", {})[
                    TSHLocaleHelper.GetRemaps(TSHLocaleHelper.exportLocale)]

            stage[1]["name"] = export_name

            item = QStandardItem(f'{stage[1].get("display_name")} / {stage[1].get("en_name")}' if stage[1].get(
                "display_name") != stage[1].get("en_name") else stage[1].get("display_name"))
            item.setData(stage[1], Qt.ItemDataRole.UserRole)
            item.setIcon(QIcon(stage[1].get("path")))
            self.stagesModel.appendRow(item)

        self.stagesModel.sort(0)
        self.stagesView.setModel(self.stagesModel)

    def LoadRulesets(self):
        rulesetsModel = QStandardItemModel()

        rulesetsModel.appendRow(QStandardItem(""))

        # Load local rulesets
        try:
            self.userRulesets = json.loads(
                open("./user_data/rulesets.json", encoding="utf-8").read())

            for ruleset in self.userRulesets:
                if ruleset.get("videogame") == TSHGameAssetManager.instance.selectedGame.get("codename"):
                    myRuleset = Ruleset()
                    myRuleset.__dict__.update(ruleset)

                    neutral = []
                    for neutralStage in myRuleset.neutralStages:
                        stage = TSHGameAssetManager.instance.selectedGame.get(
                            "stage_to_codename").get(neutralStage, {})
                        neutral.append(stage)
                    myRuleset.neutralStages = neutral

                    counterpick = []
                    for counterpickStage in myRuleset.counterpickStages:
                        stage = TSHGameAssetManager.instance.selectedGame.get(
                            "stage_to_codename").get(counterpickStage, {})
                        counterpick.append(stage)
                    myRuleset.counterpickStages = counterpick

                    item = QStandardItem(ruleset.get("name"))
                    item.setData(myRuleset, Qt.ItemDataRole.UserRole)
                    item.setIcon(QIcon("./assets/icons/db.svg"))
                    rulesetsModel.appendRow(item)
        except:
            self.userRulesets = []
            traceback.print_exc()

        # Load startgg rulesets
        for ruleset in self.startggRulesets:
            myRuleset = Ruleset()
            if str(ruleset.get("videogameId")) == str(TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id")):
                if not ruleset.get("settings"):
                    ruleset["settings"] = {}
                if not ruleset.get("settings").get("stages"):
                    ruleset["settings"]["stages"] = {}
                if ruleset.get("settings") and ruleset.get("settings", {}).get("stages", {}).get("neutral"):
                    neutral = []
                    for stage in ruleset["settings"]["stages"]["neutral"]:
                        stage = next((s[1] for s in TSHGameAssetManager.instance.selectedGame.get(
                            "stage_to_codename").items() if str(s[1].get("smashgg_id")) == str(stage)), {"smashgg_id": stage})
                        neutral.append(stage)
                    myRuleset.neutralStages = neutral
                if ruleset.get("settings") and ruleset.get("settings", {}).get("stages", {}).get("counterpick"):
                    counterpick = []
                    for stage in ruleset["settings"]["stages"]["counterpick"]:
                        stage = next((s[1] for s in TSHGameAssetManager.instance.selectedGame.get(
                            "stage_to_codename").items() if str(s[1].get("smashgg_id")) == str(stage)), {"smashgg_id": stage})
                        counterpick.append(stage)
                    myRuleset.counterpickStages = counterpick
                myRuleset.name = ruleset.get("name")

                myRuleset.strikeOrder = ruleset.get(
                    "settings", {}).get("strikeOrder")

                if deep_get(ruleset, "settings.additionalFlags") and isinstance(deep_get(ruleset, "settings.additionalFlags"), dict):
                    myRuleset.useDSR = ruleset.get("settings", {}).get(
                        "additionalFlags", {}).get("useDSR", False)
                    myRuleset.useMDSR = ruleset.get("settings", {}).get(
                        "additionalFlags", {}).get("useMDSR", False)

                    myRuleset.banCount = ruleset.get("settings", {}).get(
                        "additionalFlags", {}).get("banCount", 0)

                    myRuleset.banByMaxGames = ruleset.get("settings", {}).get(
                        "additionalFlags", {}).get("banCountByMaxGames", 0)

                item = QStandardItem(ruleset.get("name"))
                item.setData(myRuleset, Qt.ItemDataRole.UserRole)
                item.setIcon(QIcon("./assets/icons/startgg.svg"))
                rulesetsModel.appendRow(item)

        # Update list
        self.rulesetsBox.setModel(rulesetsModel)

    def LoadRuleset(self):
        data = self.rulesetsBox.currentData()

        if data == None:
            data = Ruleset()

        self.rulesetName.setText(data.name)

        if data.useDSR:
            self.DSR.setChecked(True)
        elif data.useMDSR:
            self.MDSR.setChecked(True)
        else:
            self.noDSR.setChecked(True)

        if data.strikeOrder:
            self.strikeOrder.setText(
                ",".join([str(s) for s in data.strikeOrder]))

        if data.banCount:
            self.fixedBanCount.setChecked(True)
            self.banCount.setValue(data.banCount)
            self.banCountByMaxGames.setText("")
        elif data.banByMaxGames:
            self.variableBanCount.setChecked(True)
            self.banCountByMaxGames.setText(
                ",".join([f'{k}:{v}' for k, v in data.banByMaxGames.items()]))
            self.banCount.setValue(0)

        allStages = TSHGameAssetManager.instance.selectedGame.get(
            "stage_to_codename")

        neutralModel = QStandardItemModel()
        if data.neutralStages:
            for stage in data.neutralStages:
                item = QStandardItem(f'{stage.get("display_name")} / {stage.get("en_name")}' if stage.get(
                    "display_name") != stage.get("en_name") else stage.get("display_name"))
                item.setData(stage, Qt.ItemDataRole.UserRole)
                item.setIcon(QIcon(stage.get("path")))
                neutralModel.appendRow(item)
        self.stagesNeutral.setModel(neutralModel)

        counterpickModel = QStandardItemModel()
        if data.counterpickStages:
            for stage in data.counterpickStages:
                item = QStandardItem(f'{stage.get("display_name")} / {stage.get("en_name")}' if stage.get(
                    "display_name") != stage.get("en_name") else stage.get("display_name"))
                item.setData(stage, Qt.ItemDataRole.UserRole)
                item.setIcon(QIcon(stage.get("path")))
                counterpickModel.appendRow(item)
        self.stagesCounterpick.setModel(counterpickModel)

        self.ExportCurrentRuleset()

    def ExportCurrentRuleset(self):
        try:
            ruleset = self.GetCurrentRuleset()
            self.stageStrikeLogic.SetRuleset(ruleset)
            self.ValidateRuleset(ruleset)
            StateManager.Set(f"score.ruleset", vars(ruleset))
        except:
            traceback.print_exc()
    
    def ValidateRuleset(self, ruleset: Ruleset):
        issues = []

        # Validate bans
        if len(ruleset.neutralStages) > 0:
            if sum(ruleset.strikeOrder) != len(ruleset.neutralStages) - 1:
                remaining = (len(ruleset.neutralStages) - 1) - sum(ruleset.strikeOrder)
                issues.append(QApplication.translate("app", "Number striked stages does not match the number of neutral stages. Should strike {0} more stage(s).").format(remaining))

        # Add errors
        for error in ruleset.errors:
            issues.append(error)

        if len(issues) == 0:
            validText = QApplication.translate("app", "The current ruleset is valid!")
            self.labelValidation.setText(f"<span style='color: green'>{validText}</span>")
        else:
            issuesText = "\n".join(issues)
            self.labelValidation.setText(f'<span style="color: red">{issuesText}</span>')

    def GetCurrentRuleset(self, forSaving=False):
        ruleset = Ruleset()

        ruleset.videogame = TSHGameAssetManager.instance.selectedGame.get(
            "codename")
        ruleset.name = self.rulesetName.text()

        ruleset.neutralStages = []
        for i in range(self.stagesNeutral.model().rowCount()):
            if not forSaving:
                ruleset.neutralStages.append(self.stagesNeutral.model().item(
                    i, 0).data(Qt.ItemDataRole.UserRole))
            else:
                ruleset.neutralStages.append(self.stagesNeutral.model().item(
                    i, 0).data(Qt.ItemDataRole.UserRole).get("en_name"))

        ruleset.counterpickStages = []
        for i in range(self.stagesCounterpick.model().rowCount()):
            if not forSaving:
                ruleset.counterpickStages.append(self.stagesCounterpick.model().item(
                    i, 0).data(Qt.ItemDataRole.UserRole))
            else:
                ruleset.counterpickStages.append(self.stagesCounterpick.model().item(
                    i, 0).data(Qt.ItemDataRole.UserRole).get("en_name"))

        ruleset.useDSR = self.DSR.isChecked()
        ruleset.useMDSR = self.MDSR.isChecked()

        if self.fixedBanCount.isChecked():
            ruleset.banCount = self.banCount.value()

        if self.variableBanCount.isChecked():
            try:
                inputText: str = self.banCountByMaxGames.text()
                ruleset.banByMaxGames = {}

                for _set in inputText.split(","):
                    split = _set.split(":")

                    if len(split) == 2:
                        key, value = split
                        ruleset.banByMaxGames[key.strip()] = int(value.strip())
            except:
                ruleset.banByMaxGames = {}
                ruleset.errors.append(QApplication.translate("app", "The text for banByMaxGames is invalid."))
                traceback.print_exc()

        ruleset.strikeOrder = [
            int(n.strip()) for n in self.strikeOrder.text().split(",") if n.strip() != ""
        ]

        return ruleset

    def LoadStartggRulesets(self):
        try:
            class DownloadThread(QThread):
                def run(self):
                    try:
                        data = requests.get(
                            "https://www.start.gg/api/-/gg_api./rulesets"
                        )
                        data = json.loads(data.text)
                        rulesets = deep_get(data, "entities.ruleset")
                        open('./assets/rulesets.json', 'w').write(json.dumps(rulesets))
                        self.parent().startggRulesets = rulesets
                        print("startgg Rulesets downloaded from startgg")
                        self.parent().signals.rulesets_changed.emit()
                    except:
                        print(traceback.format_exc())

                        try:
                            rulesets = json.loads(open('./assets/rulesets.json').read())
                            self.parent().startggRulesets = rulesets
                            print("startgg Rulesets loaded from local file")
                            self.parent().signals.rulesets_changed.emit()
                        except:
                            print(traceback.format_exc())
            downloadThread = DownloadThread(self)
            downloadThread.start()
        except Exception as e:
            traceback.print_exc()

        # https://www.start.gg/api/-/gg_api./rulesets
        # entities > ruleset[]

        # description: null
        # eventSettings: null
        # expand: []
        # gameMode: 1
        # id: 172
        # isDefault: false
        # name: "Community CUP"
        # settings: {gameSetup: true, stages: {neutral: [311, 328, 397, 378, 387], counterpick: [497, 484, 407, 348]},…}
        # type: "standard"
        # videogameId: 1386

        # "additionalFlags":{"banCountByMaxGames":{"3":3,"5":2},"useDSR":true}
        # "additionalFlags":{"banCount":2,"useDSR":true}
        # "additionalFlags":{"useMDSR":true,"banCount":1}

        # settings -> stages -> "strikeOrder":[1,2,1]
        # "strikeOrder":[1,1,1]
