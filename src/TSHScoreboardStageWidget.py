import traceback
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
import requests
from Helpers.TSHCountryHelper import TSHCountryHelper
from Helpers.TSHDictHelper import deep_get
from StateManager import StateManager
from TSHGameAssetManager import TSHGameAssetManager
from TSHPlayerDB import TSHPlayerDB
from TSHTournamentDataProvider import TSHTournamentDataProvider


class TSHScoreboardStageWidget(QObject):
    rulesets_changed = pyqtSignal()


class TSHScoreboardStageWidget(QWidget):
    def __init__(self, *args):
        super().__init__(*args)

        # uic.loadUi("src/layout/TSHScoreboardPlayer.ui", self)

        self.userRulesets = []
        self.smashggRulesets = []
        self.stagesModel = QStandardItemModel()

        self.setLayout(QVBoxLayout())
        self.rulesetsBox = QComboBox()
        self.layout().addWidget(self.rulesetsBox)
        self.rulesetsBox.activated.connect(self.LoadRuleset)

        hbox = QHBoxLayout()
        self.layout().addLayout(hbox)

        self.stagesView = QListView()
        hbox.addWidget(self.stagesView)
        self.stagesView.setIconSize(QSize(64, 64))

        vbox = QVBoxLayout()
        hbox.addLayout(vbox)

        self.stagesNeutral = QListView()
        self.stagesNeutral.setIconSize(QSize(64, 64))
        vbox.addWidget(self.stagesNeutral)
        self.stagesCounterpick = QListView()
        self.stagesCounterpick.setIconSize(QSize(64, 64))
        vbox.addWidget(self.stagesCounterpick)

        self.LoadSmashggRulesets()

        TSHGameAssetManager.instance.signals.onLoad.connect(self.SetupOptions)

        # TSHTournamentDataProvider.instance.signals.tournament_changed.connect()
        # load tournament ruleset

    def SetupOptions(self):
        self.rulesetsBox.clear()

        rulesetsModel = QStandardItemModel()
        for ruleset in self.smashggRulesets:
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
                    ruleset["settings"]["stages"]["neutral"] = neutral
                if ruleset.get("settings") and ruleset.get("settings", {}).get("stages", {}).get("counterpick"):
                    counterpick = []
                    for stage in ruleset["settings"]["stages"]["counterpick"]:
                        stage = next((s[1] for s in TSHGameAssetManager.instance.selectedGame.get(
                            "stage_to_codename").items() if str(s[1].get("smashgg_id")) == str(stage)), {"smashgg_id": stage})
                        counterpick.append(stage)
                    ruleset["settings"]["stages"]["counterpick"] = counterpick
                item = QStandardItem(ruleset.get("name"))
                item.setData(ruleset, Qt.ItemDataRole.UserRole)
                item.setIcon(QIcon("./icons/smashgg.svg"))
                rulesetsModel.appendRow(item)
        self.rulesetsBox.setModel(rulesetsModel)

        self.stagesModel = QStandardItemModel()
        self.stagesModel.appendRow(QStandardItem(""))
        for stage in TSHGameAssetManager.instance.selectedGame.get("stage_to_codename").items():
            item = QStandardItem(stage[1].get("name"))
            item.setData(stage[1], Qt.ItemDataRole.UserRole)
            item.setIcon(QIcon(stage[1].get("path")))
            self.stagesModel.appendRow(item)
        self.stagesView.setModel(self.stagesModel)

    def LoadRuleset(self):
        data = self.rulesetsBox.currentData()

        neutralModel = QStandardItemModel()
        neutralModel.appendRow(QStandardItem(""))
        for stage in data.get("settings").get("stages", {}).get("neutral", []):
            item = QStandardItem(stage.get("name"))
            item.setData(stage, Qt.ItemDataRole.UserRole)
            item.setIcon(QIcon(stage.get("path")))
            neutralModel.appendRow(item)
        self.stagesNeutral.setModel(neutralModel)

        counterpickModel = QStandardItemModel()
        counterpickModel.appendRow(QStandardItem(""))
        for stage in data.get("settings").get("stages", {}).get("counterpick", []):
            item = QStandardItem(stage.get("name"))
            item.setData(stage, Qt.ItemDataRole.UserRole)
            item.setIcon(QIcon(stage.get("path")))
            counterpickModel.appendRow(item)
        self.stagesCounterpick.setModel(counterpickModel)

    def LoadSmashggRulesets(self):
        try:
            data = requests.get(
                "https://smash.gg/api/-/gg_api./rulesets"
            )
            data = json.loads(data.text)
            rulesets = deep_get(data, "entities.ruleset")
            self.smashggRulesets = rulesets
        except Exception as e:
            traceback.print_exc()
        # https://smash.gg/api/-/gg_api./rulesets
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
