from asyncio import start_server
import os
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
from flask import Flask, send_from_directory, request
from Workers import Worker


class TSHScoreboardStageWidget(QObject):
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


class WebServer(QThread):
    app = Flask(__name__, static_folder=os.path.curdir)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.host_name = "0.0.0.0"
        self.port = 5000

    @app.route("/ruleset")
    def main():
        data = StateManager.Get(f"score.ruleset", {})
        data.update({
            "basedir": os.path.abspath(".")
        })
        return data

    @app.route('/post', methods=['POST'])
    def post_route():
        print(request.get_data())
        print(request.get_json(True))
        print(json.loads(request.get_data()))
        StateManager.Set(f"score.stage_strike", json.loads(request.get_data()))
        return "OK"

    @app.route('/', defaults=dict(filename=None))
    @app.route('/<path:filename>', methods=['GET', 'POST'])
    def test(filename):
        filename = filename or 'stage_strike_app/build/index.html'
        print(os.path.abspath("."), filename)
        return send_from_directory(os.path.abspath("."), filename)

    def run(self):
        self.app.run(host=self.host_name, port=self.port,
                     debug=True, use_reloader=False)


class TSHScoreboardStageWidget(QWidget):

    def __init__(self, *args):
        super().__init__(*args)

        self.webserver = WebServer()
        self.webserver.start()

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
        vbox.addWidget(QLabel("Neutral Stages"))
        vbox.addWidget(self.stagesNeutral)
        self.stagesCounterpick = QListView()
        self.stagesCounterpick.setIconSize(QSize(64, 64))
        vbox.addWidget(QLabel("Counterpick Stages"))
        vbox.addWidget(self.stagesCounterpick)

        self.LoadSmashggRulesets()

        TSHGameAssetManager.instance.signals.onLoad.connect(self.SetupOptions)

        StateManager.Set(f"score.ruleset", None)

        # TSHTournamentDataProvider.instance.signals.tournament_changed.connect()
        # load tournament ruleset

    def SetupOptions(self):
        self.rulesetsBox.clear()

        rulesetsModel = QStandardItemModel()

        rulesetsModel.appendRow(QStandardItem(""))

        # Load local rulesets
        try:
            userRulesets = json.loads(open("./user_data/rulesets.json").read())

            for ruleset in userRulesets:
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
                    item.setIcon(QIcon("./icons/db.svg"))
                    rulesetsModel.appendRow(item)
        except:
            traceback.print_exc()

        # Load SmashGG rulesets
        for ruleset in self.smashggRulesets:
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
                item.setIcon(QIcon("./icons/smashgg.svg"))
                rulesetsModel.appendRow(item)

        # Update list
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

        if data == None:
            data = Ruleset()

        allStages = TSHGameAssetManager.instance.selectedGame.get(
            "stage_to_codename")

        neutralModel = QStandardItemModel()
        neutralModel.appendRow(QStandardItem(""))
        if data.neutralStages:
            for stage in data.neutralStages:
                item = QStandardItem(stage.get("name"))
                item.setData(stage, Qt.ItemDataRole.UserRole)
                item.setIcon(QIcon(stage.get("path")))
                neutralModel.appendRow(item)
        self.stagesNeutral.setModel(neutralModel)

        counterpickModel = QStandardItemModel()
        counterpickModel.appendRow(QStandardItem(""))
        if data.counterpickStages:
            for stage in data.counterpickStages:
                item = QStandardItem(stage.get("name"))
                item.setData(stage, Qt.ItemDataRole.UserRole)
                item.setIcon(QIcon(stage.get("path")))
                counterpickModel.appendRow(item)
        self.stagesCounterpick.setModel(counterpickModel)

        StateManager.Set(f"score.ruleset", vars(data))

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
