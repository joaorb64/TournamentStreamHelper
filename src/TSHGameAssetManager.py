import os
import json
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re


class TSHGameAssetManagerSignals(QObject):
    onLoad = pyqtSignal()


class TSHGameAssetManager():
    instance: "TSHGameAssetManager" = None

    def __init__(self) -> None:
        self.signals = TSHGameAssetManagerSignals()
        self.games = {}
        self.LoadGames()

    def LoadGames(self):
        self.games = {}

        gameDirs = os.listdir("./assets/games/")

        for game in gameDirs:
            if os.path.isfile("./assets/games/"+game+"/base_files/config.json"):
                f = open("./assets/games/"+game +
                         "/base_files/config.json", encoding='utf-8')
                self.games[game] = json.load(f)

                self.games[game]["assets"] = {}
                self.games[game]["path"] = "./assets/games/"+game+"/"

                assetDirs = os.listdir("./assets/games/"+game)
                assetDirs += ["base_files/" +
                              f for f in os.listdir("./assets/games/"+game+"/base_files/")]

                for dir in assetDirs:
                    if os.path.isdir("./assets/games/"+game+"/"+dir):
                        if os.path.isfile("./assets/games/"+game+"/"+dir+"/config.json"):
                            print("Found asset config for ["+game+"]["+dir+"]")
                            f = open("./assets/games/"+game+"/"+dir +
                                     "/config.json", encoding='utf-8')
                            self.games[game]["assets"][dir] = \
                                json.load(f)
                        else:
                            print("No config file for "+game+" - "+dir)
            else:
                print("Game config for "+game+" doesn't exist.")

        for game in self.games:
            print(game)

    def LoadGameAssets(self, game=None):
        if len(self.games.keys()) == 0:
            return

        if game == None:
            game = list(self.games.keys())[0]
        else:
            if game != 0:
                game = list(self.games.keys())[game-1]
            else:
                game = ""

        print("Changed to game: "+game)

        gameObj = self.games.get(game, {})
        self.selectedGame = gameObj

        if gameObj != None:
            self.characters = gameObj.get("character_to_codename", {})

            assetsKey = ""
            if len(list(gameObj.get("assets", {}).keys())) > 0:
                assetsKey = list(gameObj.get("assets", {}).keys())[0]

            for asset in list(gameObj.get("assets", {}).keys()):
                if "icon" in gameObj["assets"][asset].get("type", ""):
                    assetsKey = asset
                    break

            assetsObj = gameObj.get("assets", {}).get(assetsKey, None)
            files = sorted(os.listdir('./assets/games/'+game+'/'+assetsKey))

            self.stockIcons = {}

            for c in self.characters.keys():
                self.stockIcons[c] = {}

                filteredFiles = \
                    [f for f in files if f.startswith(assetsObj.get(
                        "prefix", "")+self.characters[c].get("codename")+assetsObj.get("postfix", ""))]

                if len(filteredFiles) == 0:
                    self.stockIcons[c][0] = QImage('./icons/cancel.svg')

                for i, f in enumerate(filteredFiles):
                    numberStart = f.rfind(
                        assetsObj.get("postfix", "")) + len(assetsObj.get("postfix", ""))
                    numberEnd = f.rfind(".")
                    number = 0
                    try:
                        number = int(f[numberStart:numberEnd])
                    except:
                        print(f)
                        pass
                    self.stockIcons[c][number] = QImage(
                        './assets/games/'+game+'/'+assetsKey+'/'+f)

            self.skins = {}

            for c in self.characters.keys():
                self.skins[c] = {}
                for assetsKey in list(gameObj["assets"].keys()):
                    asset = gameObj["assets"][assetsKey]

                    files = sorted(os.listdir(
                        './assets/games/'+game+'/'+assetsKey))

                    filteredFiles = \
                        [f for f in files if f.startswith(asset.get(
                            "prefix", "")+self.characters[c].get("codename")+asset.get("postfix", ""))]

                    for f in filteredFiles:
                        numberStart = f.rfind(
                            asset.get("postfix", "")) + len(asset.get("postfix", ""))
                        numberEnd = f.rfind(".")
                        number = 0
                        try:
                            number = int(f[numberStart:numberEnd])
                        except:
                            pass
                        self.skins[c][number] = True
                print("Character "+c+" has "+str(len(self.skins[c]))+" skins")

            assetsKey = ""
            if len(list(gameObj.get("assets", {}).keys())) > 0:
                assetsKey = list(gameObj.get("assets", {}).keys())[0]

            for asset in list(gameObj.get("assets", {}).keys()):
                if "portrait" in gameObj["assets"][asset].get("type", []):
                    assetsKey = asset
                    break
                if "icon" in gameObj["assets"][asset].get("type", []):
                    assetsKey = asset

            assetsObj = gameObj.get("assets", {}).get(assetsKey)
            files = sorted(os.listdir('./assets/games/'+game+'/'+assetsKey))

            self.portraits = {}

            for c in self.characters.keys():
                self.portraits[c] = {}

                filteredFiles = \
                    [f for f in files if f.startswith(assetsObj.get(
                        "prefix", "")+self.characters[c].get("codename")+assetsObj.get("postfix", ""))]

                if len(filteredFiles) == 0:
                    self.portraits[c][0] = QImage('./icons/cancel.svg')

                filteredFiles.sort(key=lambda x: int(re.search(
                    r'(\d+)\D+$', x).group(1)) or 1)

                for i, f in enumerate(filteredFiles):
                    self.portraits[c][i] = QImage(
                        './assets/games/'+game+'/'+assetsKey+'/'+f)

            assetsKey = ""
            if len(list(gameObj.get("assets", {}).keys())) > 0:
                assetsKey = list(gameObj.get("assets", {}).keys())[0]

            for asset in list(gameObj.get("assets", {}).keys()):
                if "stage_icon" in gameObj["assets"][asset].get("type", ""):
                    assetsKey = asset
                    break

            assetsObj = gameObj.get("assets", {}).get(assetsKey)
            files = sorted(os.listdir('./assets/games/'+game+'/'+assetsKey))

            self.stages = gameObj.get("stage_to_codename", {})

            for stage in self.stages:
                self.stages[stage]["filename"] = assetsObj.get(
                    "prefix", "")+self.stages[stage].get("codename", "")+assetsObj.get("postfix", "")

            for s in self.stages.keys():
                self.stages[s]["name"] = s

        self.signals.onLoad.emit()

        # self.programState["asset_path"] = self.selectedGame.get("path")
        # self.programState["game"] = game

        # self.SetupAutocomplete()

        # if self.settings.get("autosave") == True:
        #    self.ExportProgramState()

        # self.gameSelect.clear()

        # self.gameSelect.addItem("")

        # for game in self.games:
        #    self.gameSelect.addItem(self.games[game]["name"])


if TSHGameAssetManager.instance == None:
    TSHGameAssetManager.instance = TSHGameAssetManager()
