import os
import json
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .StateManager import StateManager
import re
import traceback
import threading
from .Helpers.TSHLocaleHelper import TSHLocaleHelper

import requests


class TSHGameAssetManagerSignals(QObject):
    onLoad = pyqtSignal()
    onLoadAssets = pyqtSignal()


class TSHGameAssetManager(QObject):
    instance: "TSHGameAssetManager" = None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.signals = TSHGameAssetManagerSignals()
        self.games = {}
        self.characters = {}
        self.selectedGame = {}
        self.stockIcons = {}
        StateManager.Set(f"game", {})
        self.assetsLoaderLock = QMutex()
        self.assetsLoaderThread = None
        self.thumbnailSettingsLoaded = False

    def UiMounted(self):
        self.DownloadStartGGCharacters()
        self.LoadGames()

    def DownloadStartGGCharacters(self):
        class DownloaderThread(QThread):
            def run(self):
                try:
                    url = 'https://api.start.gg/characters'
                    r = requests.get(url, allow_redirects=True)
                    open('./assets/characters.json', 'wb').write(r.content)
                    print("startgg characters file updated")
                except Exception as e:
                    print("Could not update /assets/characters.json: "+str(e))
        thread = DownloaderThread(self)
        thread.start()

    def LoadGames(self):
        class GameLoaderThread(QThread):
            def run(self):
                self.parent().games = {}

                gameDirs = os.listdir("./user_data/games/")

                for game in gameDirs:
                    if os.path.isfile("./user_data/games/"+game+"/base_files/config.json"):
                        f = open("./user_data/games/"+game +
                                 "/base_files/config.json", encoding='utf-8')
                        self.parent().games[game] = json.load(f)

                        if os.path.isfile("./user_data/games/"+game+"/base_files/logo.png"):
                            self.parent().games[game]["logo"] = QIcon(
                                "./user_data/games/"+game+"/base_files/logo.png")

                        self.parent().games[game]["assets"] = {}
                        self.parent(
                        ).games[game]["path"] = "./user_data/games/"+game+"/"

                        assetDirs = os.listdir("./user_data/games/"+game)
                        assetDirs += ["base_files/" +
                                      f for f in os.listdir("./user_data/games/"+game+"/base_files/")]

                        for dir in assetDirs:
                            if os.path.isdir("./user_data/games/"+game+"/"+dir):
                                if os.path.isfile("./user_data/games/"+game+"/"+dir+"/config.json"):
                                    print(
                                        "Found asset config for ["+game+"]["+dir+"]")
                                    f = open("./user_data/games/"+game+"/"+dir +
                                             "/config.json", encoding='utf-8')
                                    self.parent().games[game]["assets"][dir] = \
                                        json.load(f)
                                else:
                                    print("No config file for "+game+" - "+dir)

                        # Load translated names
                        # Translate game name
                        locale = TSHLocaleHelper.programLocale
                        if locale.replace('-', '_') in self.parent().games[game].get("locale", {}):
                            game_name = self.parent(
                            ).games[game]["locale"][locale.replace('-', '_')].get("name")
                            if game_name:
                                self.parent(
                                ).games[game]["name"] = game_name
                        elif locale.split('-')[0] in self.parent().games[game].get("locale", {}):
                            game_name = self.parent(
                            ).games[game]["locale"][locale.split('-')[0]].get("name")
                            if game_name:
                                self.parent(
                                ).games[game]["name"] = game_name
                    else:
                        print("Game config for "+game+" doesn't exist.")
                # print(self.parent().games)
                self.parent().signals.onLoadAssets.emit()

        gameLoaderThread = GameLoaderThread(self)
        gameLoaderThread.start()

    def SetGameFromStartGGId(self, gameid):
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
        class AssetsLoaderThread(QThread):
            def __init__(self, parent=...) -> None:
                super().__init__(parent)
                self.game = None
                self.lock = None

            def run(self):
                self.lock.lock()
                try:
                    game = self.game

                    if len(self.parent().games.keys()) == 0:
                        return

                    if game == 0 or game == None:
                        game = ""
                    else:
                        game = list(self.parent().games.keys())[game-1]

                    # Game is already loaded
                    if game == self.parent().selectedGame.get("codename"):
                        return

                    print("Changed to game: "+game)

                    gameObj = self.parent().games.get(game, {})
                    self.parent().selectedGame = gameObj
                    gameObj["codename"] = game

                    if gameObj != None:
                        self.parent().characters = gameObj.get("character_to_codename", {})

                        assetsKey = ""
                        if len(list(gameObj.get("assets", {}).keys())) > 0:
                            assetsKey = list(gameObj.get(
                                "assets", {}).keys())[0]

                        for asset in list(gameObj.get("assets", {}).keys()):
                            if "icon" in gameObj["assets"][asset].get("type", ""):
                                assetsKey = asset
                                break

                        assetsObj = gameObj.get(
                            "assets", {}).get(assetsKey, None)
                        files = sorted(os.listdir(
                            './user_data/games/'+game+'/'+assetsKey))

                        self.parent().stockIcons = {}

                        for c in self.parent().characters.keys():
                            self.parent().stockIcons[c] = {}

                            filteredFiles = \
                                [f for f in files if f.startswith(assetsObj.get(
                                    "prefix", "")+self.parent().characters[c].get("codename")+assetsObj.get("postfix", ""))]

                            if len(filteredFiles) == 0:
                                self.parent().stockIcons[c][0] = QImage(
                                    './assets/icons/cancel.svg')

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
                                self.parent().stockIcons[c][number] = QImage(
                                    './user_data/games/'+game+'/'+assetsKey+'/'+f)

                        print("Loaded stock icons")

                        self.parent().skins = {}

                        widths = {}
                        heights = {}

                        for c in self.parent().characters.keys():
                            self.parent().skins[c] = {}
                            for assetsKey in list(gameObj["assets"].keys()):
                                asset = gameObj["assets"][assetsKey]

                                files = sorted(os.listdir(
                                    './user_data/games/'+game+'/'+assetsKey))

                                filteredFiles = \
                                    [f for f in files if f.startswith(asset.get(
                                        "prefix", "")+self.parent().characters[c].get("codename")+asset.get("postfix", ""))]

                                for f in filteredFiles:
                                    numberStart = f.rfind(
                                        asset.get("postfix", "")) + len(asset.get("postfix", ""))
                                    numberEnd = f.rfind(".")
                                    number = 0
                                    try:
                                        number = int(f[numberStart:numberEnd])
                                    except:
                                        pass
                                    self.parent().skins[c][number] = True
                                
                                    # Get image dimensions
                                    imgfile = QImageReader('./user_data/games/'+game+'/'+assetsKey+'/'+f)

                                    size = imgfile.size()

                                    if not assetsKey in widths:
                                        widths[assetsKey] = []

                                    if size.width() != -1:
                                        widths[assetsKey].append(size.width())

                                    if not assetsKey in heights:
                                        heights[assetsKey] = []

                                    if size.height() != -1:
                                        heights[assetsKey].append(size.height())
                            print("Character "+c+" has " +
                                  str(len(self.parent().skins[c]))+" skins")
                        
                        # Set average size
                        for assetsKey in list(gameObj["assets"].keys()):
                            if assetsKey != "base_files":
                                try:
                                    if len(widths[assetsKey]) > 0 and len(heights[assetsKey]) > 0:
                                        gameObj["assets"][assetsKey]["average_size"] = {
                                            "x": sum(widths[assetsKey])/len(widths[assetsKey]),
                                            "y": sum(heights[assetsKey])/len(heights[assetsKey])
                                        }
                                except:
                                    print(traceback.format_exc())

                        assetsKey = ""
                        if len(list(gameObj.get("assets", {}).keys())) > 0:
                            assetsKey = list(gameObj.get(
                                "assets", {}).keys())[0]

                        for asset in list(gameObj.get("assets", {}).keys()):
                            if "portrait" in gameObj["assets"][asset].get("type", []):
                                assetsKey = asset
                                break
                            if "icon" in gameObj["assets"][asset].get("type", []):
                                assetsKey = asset

                        assetsKey = None

                        for asset in list(gameObj.get("assets", {}).keys()):
                            if "stage_icon" in gameObj["assets"][asset].get("type", ""):
                                assetsKey = asset
                                break

                        self.parent().stages = gameObj.get("stage_to_codename", {})

                        if assetsKey:
                            assetsObj = gameObj.get(
                                "assets", {}).get(assetsKey)
                            files = sorted(os.listdir(
                                './user_data/games/'+game+'/'+assetsKey))

                            for stage in self.parent().stages:
                                self.parent().stages[stage]["path"] = './user_data/games/'+game+'/'+assetsKey+'/'+assetsObj.get(
                                    "prefix", "")+self.parent().stages[stage].get("codename", "")+assetsObj.get("postfix", "")+".png"

                        for s in self.parent().stages.keys():
                            self.parent().stages[s]["name"] = s

                    StateManager.Set(f"game", {
                        "name": self.parent().selectedGame.get("name"),
                        "smashgg_id": self.parent().selectedGame.get("smashgg_game_id"),
                        "codename": self.parent().selectedGame.get("codename"),
                    })

                    self.parent().signals.onLoad.emit()
                except:
                    print(traceback.format_exc())
                finally:
                    self.lock.unlock()

        self.thumbnailSettingsLoaded = False
        self.assetsLoaderThread = AssetsLoaderThread(TSHGameAssetManager.instance)
        self.assetsLoaderThread.game = game
        self.assetsLoaderThread.lock = self.assetsLoaderLock
        self.assetsLoaderThread.start()

        # self.programState["asset_path"] = self.selectedGame.get("path")
        # self.programState["game"] = game

        # self.SetupAutocomplete()

        # if self.settings.get("autosave") == True:
        #    self.ExportProgramState()

        # self.gameSelect.clear()

        # self.gameSelect.addItem("")

        # for game in self.games:
        #    self.gameSelect.addItem(self.games[game]["name"])

    def GetCharacterAssets(self, characterCodename: str, skin: int, assetpack: str = None):
        charFiles = {}

        if self.selectedGame is not None:
            assetsPacks = []

            if assetpack:
                assetsPacks = [assetpack]
            else:
                assetsPacks = self.selectedGame.get("assets", {}).items()

            # For each assets pack
            for assetKey, asset in assetsPacks:
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

                        # If skin exists, load it
                        if skin in skinFiles:
                            charFiles[assetKey]["asset"] = assetPath + \
                                skinFiles[skin]
                        else:
                            # If skin remap exists, load remap
                            if asset.get("skin_mapping", {}).get(characterCodename, {}).get(str(skin)):
                                target = int(asset.get("skin_mapping", {}).get(
                                    characterCodename, {}).get(str(skin)))
                                charFiles[assetKey]["asset"] = assetPath + \
                                    skinFiles[target]
                            # If none is found, default to skin 0
                            else:
                                charFiles[assetKey]["asset"] = assetPath + \
                                    skinFiles[0]

                    if asset.get("eyesights"):
                        eyesights = asset.get("eyesights", {}).get(
                            characterCodename, {})

                        if len(eyesights.keys()) > 0:
                            if str(skin) in eyesights:
                                charFiles[assetKey]["eyesight"] = eyesights.get(
                                    str(skin))
                            else:
                                charFiles[assetKey]["eyesight"] = list(
                                    eyesights.values())[0]
                    
                    if asset.get("rescaling_factor"):
                        rescaling_factor = asset.get("rescaling_factor", {}).get(
                            characterCodename, {})

                        if len(rescaling_factor.keys()) > 0:
                            if str(skin) in rescaling_factor:
                                charFiles[assetKey]["rescaling_factor"] = rescaling_factor.get(
                                    str(skin))
                            else:
                                charFiles[assetKey]["rescaling_factor"] = list(
                                    rescaling_factor.values())[0]
                    
                    if asset.get("unflippable"):
                        unflippable = asset.get("unflippable", {}).get(
                            characterCodename, {})

                        if len(unflippable.keys()) > 0:
                            if str(skin) in unflippable:
                                charFiles[assetKey]["unflippable"] = unflippable.get(
                                    str(skin))
                            else:
                                charFiles[assetKey]["unflippable"] = list(
                                    unflippable.values())[0]
                    
                    if asset.get("metadata"):
                        metadata = {}
                        charFiles[assetKey]['metadata'] = {}
                        for key in asset.get("metadata").keys():
                            metadata[key] = asset.get("metadata", {})[key]["values"].get(
                                characterCodename, {}).get("value", "")
                            charFiles[assetKey]['metadata'][f"{key}_en"] = metadata[key]
                            if TSHLocaleHelper.exportLocale in asset.get("metadata", {})[key]["values"].get(characterCodename, {}).get("locale", {}).keys() or TSHLocaleHelper.exportLocale.split('-')[0] in asset.get("metadata", {})[key]["values"].get(characterCodename, {}).get("locale", {}).keys():
                                try:
                                    metadata[key] = asset.get("metadata", {})[key]["values"].get(characterCodename, {}).get("locale", {})[TSHLocaleHelper.exportLocale]
                                except KeyError:
                                    metadata[key] = asset.get("metadata", {})[key]["values"].get(characterCodename, {}).get("locale", {})[TSHLocaleHelper.exportLocale.split('-')[0]]
                            charFiles[assetKey]['metadata'][key] = metadata[key]

                        # if len(metadata.keys()) > 0:
                        #     if str(skin) in metadata:
                        #         charFiles[assetKey]["metadata"] = metadata.get(
                        #             str(skin))
                        #     else:
                        #         charFiles[assetKey]["metadata"] = list(
                        #             metadata.values())[0]
                    
                    if asset.get("uncropped_edge"):
                        charFiles[assetKey]["uncropped_edge"] = asset.get("uncropped_edge")
                    
                    if asset.get("average_size"):
                        charFiles[assetKey]["average_size"] = asset.get("average_size")
                except Exception as e:
                    print(traceback.format_exc())

        return(charFiles)

    def GetCharacterFromStartGGId(self, smashgg_id: int):
        sggcharacters = json.loads(
            open('./assets/characters.json', 'r').read())

        startggcharacter = next((c for c in sggcharacters.get("entities", {}).get(
            "character", []) if str(c.get("id")) == str(smashgg_id)), None)

        if startggcharacter:
            character = next((c for c in self.characters.items() if c[1].get(
                "smashgg_name") == startggcharacter.get("name")), None)
            if character:
                return character

        return None

    def GetStageFromStartGGId(self, smashgg_id: int):
        stage = next((s for s in self.stages.items() if str(
            s[1].get("smashgg_id")) == str(smashgg_id)), None)
        return stage


if not os.path.exists("./user_data/games"):
    os.makedirs("./user_data/games")

if TSHGameAssetManager.instance == None:
    TSHGameAssetManager.instance = TSHGameAssetManager()
