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

        self.setLayout(QVBoxLayout())
        self.rulesetsBox = QComboBox()
        self.layout().addWidget(self.rulesetsBox)

        self.LoadSmashggRulesets()

        TSHGameAssetManager.instance.signals.onLoad.connect(self.SetupOptions)

    def SetupOptions(self):
        self.rulesetsBox.clear()

        for ruleset in self.smashggRulesets:
            if str(ruleset.get("videogameId")) == str(TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id")):
                self.rulesetsBox.addItem(ruleset.get("name"))
                print(ruleset)

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
