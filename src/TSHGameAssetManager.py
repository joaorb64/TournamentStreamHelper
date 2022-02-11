import os
import json
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re
import traceback

import requests


class TSHGameAssetManagerSignals(QObject):
    onLoad = pyqtSignal()
    onLoadAssets = pyqtSignal()


class TSHGameAssetManager():
    instance: "TSHGameAssetManager" = None

    def __init__(self) -> None:
        self.signals = TSHGameAssetManagerSignals()
        self.games = {}
        self.characters = {}
        self.DownloadSmashGGCharacters()
        self.LoadGames()
        self.selectedGame = {}

    def DownloadSmashGGCharacters(self):
        try:
            url = 'https://api.smash.gg/characters'
            r = requests.get(url, allow_redirects=True)
            open('./assets/characters.json', 'wb').write(r.content)
        except Exception as e:
            print("Could not update /assets/characters.json: "+str(e))

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

        self.signals.onLoadAssets.emit()

    def SetGameFromSmashGGId(self, gameid):
        if len(self.games.keys()) == 0:
            return

        for i, game in enumerate(self.games.values()):
            if str(game.get("smashgg_game_id")) == str(gameid):
                self.LoadGameAssets(i+1)
                break

    def SetGameFromChallongeId(self, gameid):
        if len(self.games.keys()) == 0:
            return

        for i, game in enumerate(self.games.values()):
            if str(game.get("challonge_game_id")) == str(gameid):
                self.LoadGameAssets(i+1)
                break

    def LoadGameAssets(self, game: int = 0):
        if len(self.games.keys()) == 0:
            return

        if game == 0:
            game = ""
        else:
            game = list(self.games.keys())[game-1]

        # Game is already loaded
        if game == self.selectedGame.get("codename"):
            return

        print("Changed to game: "+game)

        gameObj = self.games.get(game, {})
        self.selectedGame = gameObj
        gameObj["codename"] = game

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
                self.stages[stage]["path"] = './assets/games/'+game+'/'+assetsKey+'/'+assetsObj.get(
                    "prefix", "")+self.stages[stage].get("codename", "")+assetsObj.get("postfix", "")+".png"

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

    def GetCharacterAssets(self, characterCodename: str, skin: int):
        charFiles = {}

        if self.selectedGame is not None:
            # For each assets pack
            for assetKey, asset in self.selectedGame.get("assets", {}).items():
                try:
                    # Skip stage icon asset packs
                    if type(asset.get("type")) == list:
                        if "stage_icon" in asset.get("type"):
                            continue
                    elif type(asset.get("type")) == str:
                        if asset.get("type") == "stage_icon":
                            continue

                    assetPath = f'{self.selectedGame.get("path")}/{assetKey}/'

                    baseName = asset.get(
                        "prefix", "")+characterCodename+asset.get("postfix", "")

                    skinFileList = [f for f in os.listdir(
                        assetPath) if f.startswith(baseName)]

                    skinFiles = {}

                    for f in skinFileList:
                        skinId = f[len(baseName):].rsplit(".", 1)[0]
                        if skinId == "":
                            skinId = 0
                        else:
                            skinId = int(skinId)
                        skinFiles[skinId] = f

                    if len(skinFiles) > 0:
                        charFiles[assetKey] = {
                            "type": asset.get("type", [])
                        }

                        if skin in skinFiles:
                            charFiles[assetKey]["asset"] = assetPath + \
                                skinFiles[skin]
                        else:
                            charFiles[assetKey]["asset"] = assetPath + \
                                list(skinFiles.values())[0]

                except Exception as e:
                    print(traceback.format_exc())

        return(charFiles)

    def GetCharacterFromSmashGGId(self, smashgg_id: int):
        sggcharacters = json.loads(
            open('./assets/characters.json', 'r').read())

        smashggcharacter = next((c for c in sggcharacters.get("entities", {}).get(
            "character", []) if str(c.get("id")) == str(smashgg_id)), None)

        if smashggcharacter:
            character = next((c for c in self.characters.items() if c[1].get(
                "smashgg_name") == smashggcharacter.get("name")), None)
            if character:
                return character

        return None

    def GetStageFromSmashGGId(self, smashgg_id: int):
        stage = next((s for s in self.stages.items() if str(
            s[1].get("smashgg_id")) == str(smashgg_id)), None)
        return stage


if not os.path.exists("./assets/games"):
    os.makedirs("./assets/games")

if TSHGameAssetManager.instance == None:
    TSHGameAssetManager.instance = TSHGameAssetManager()
