import os
import json
import copy
import traceback
from deepdiff import DeepDiff, extract
import shutil
from PIL import Image, UnidentifiedImageError

from Helpers.TSHDictHelper import deep_get, deep_set, deep_unset


class StateManager:
    state = {}

    def SavePlayerAPNG(team_key: str, player_key: str):
        print(f"Player {player_key}")

        duration = 10000  # in milliseconds

        team = StateManager.state.get("score").get(team_key)
        player = team.get("players").get(player_key)
        characters = player.get("character")

        sources = {}

        if characters:
            for character_key in characters.keys():
                assets = characters.get(character_key).get("assets")
                for asset_key in assets.keys():
                    asset_type = assets.get(asset_key).get("type")[0]
                    asset_path = assets.get(asset_key).get("asset")
                    if sources.get(asset_type):
                        sources[asset_type].append(asset_path)
                    else:
                        sources[asset_type] = [asset_path]

        for asset_type in sources.keys():
            apng_name = f"{asset_type}_apng"
            out_folder = f'./out/score/{team_key}/players/{player_key}/character'
            apng_path = f"{out_folder}/{apng_name}.png"
            html_path = f"{out_folder}/{apng_name}.html"

            asset_list = sources.get(asset_type)
            nb_assets = len(asset_list)

            if nb_assets > 0:
                try:
                    len_slide = float(duration)/nb_assets

                    frames = []
                    for i in asset_list:
                        new_frame = Image.open(i).convert('RGBA')
                        frames.append(new_frame)

                    max_width, max_height = 0, 0
                    for i in range(len(frames)):
                        width, height = frames[i].size
                        if width > max_width:
                            max_width = width
                        if height > max_height:
                            max_height = height

                    for i in range(len(frames)):
                        width, height = frames[i].size
                        if width != max_width or height != max_height:
                            ratio = min(max_width/width, max_height/height)
                            print(ratio)
                            frames[i] = frames[i].resize(
                                (int(width*ratio), int(height*ratio)), Image.ANTIALIAS)

                            new_image = Image.new(
                                'RGBA', (max_height, max_width), (0, 0, 0, 0))
                            upper = (max_height - int(height*ratio)) // 2
                            left = (max_width - int(width*ratio)) // 2
                            new_image.paste(frames[i], (left, upper))
                            frames[i] = new_image

                    frames[0].save(apng_path, format='PNG',
                                append_images=frames[1:],
                                save_all=True,
                                duration=len_slide, loop=0)

                    html_contents = f'<img src="{apng_name}.png">'
                    with open(html_path, 'wt', encoding='utf-8') as html_file:
                        html_file.write(html_contents)
                except UnidentifiedImageError:
                    if os.path.exists(apng_path):
                        os.remove(apng_path)
                    if os.path.exists(html_path):
                        os.remove(html_path)

    def SaveTeamAPNG(team_key: str):
        print(f"Saving APNG for {team_key}")
        team = StateManager.state.get("score").get(team_key)
        players = team.get("players")
        if players:
            for player_key in players.keys():
                StateManager.SavePlayerAPNG(team_key, player_key)

    def SaveAPNG():
        print("Saving APNG files")
        score = StateManager.state.get("score")
        if score:
            for team_key in ["team1", "team2"]:
                team = score.get(team_key)
                if team:
                    StateManager.SaveTeamAPNG(team_key)

    def SaveState():
        with open("./out/program_state.json", 'w') as file:
            json.dump(StateManager.state, file, indent=4, sort_keys=True)
        StateManager.SaveAPNG()

    def LoadState():
        with open("./out/program_state.json", 'r') as file:
            StateManager.state = json.load(file)

    def Set(key: str, value):
        oldState = copy.deepcopy(StateManager.state)
        deep_set(StateManager.state, key, value)
        StateManager.SaveState()
        StateManager.ExportText(oldState)

    def Unset(key: str):
        oldState = copy.deepcopy(StateManager.state)
        deep_unset(StateManager.state, key)
        StateManager.SaveState()
        StateManager.ExportText(oldState)

    def Get(key: str):
        return deep_get(StateManager.state, key)

    def ExportText(oldState):
        diff = DeepDiff(oldState, StateManager.state)
        print(diff)

        mergedDiffs = list(diff.get("values_changed", {}).items())
        mergedDiffs.extend(list(diff.get("type_changes", {}).items()))

        print(mergedDiffs)

        for changeKey, change in mergedDiffs:
            # Remove "root[" from start and separate keys
            filename = "/".join(changeKey[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            print(filename)

            if change.get("new_type") == type(None):
                StateManager.RemoveFilesDict(
                    filename, extract(oldState, changeKey))
            else:
                StateManager.CreateFilesDict(
                    filename, change.get("new_value"))

        removedKeys = diff.get("dictionary_item_removed", {})

        for key in removedKeys:
            item = extract(oldState, key)

            # Remove "root[" from start and separate keys
            filename = "/".join(key[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            print("Removed:", filename, item)

            StateManager.RemoveFilesDict(filename, item)

        addedKeys = diff.get("dictionary_item_added", {})

        for key in addedKeys:
            item = extract(StateManager.state, key)

            # Remove "root[" from start and separate keys
            path = "/".join(key[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            print("Added:", path, item)

            StateManager.CreateFilesDict(path, item)

    def CreateFilesDict(path, di):
        pathdirs = "/".join(path.split("/")[0:-1])

        if not os.path.isdir("./out/"+pathdirs):
            os.mkdir("./out/"+pathdirs)

        if type(di) == dict:
            for k, i in di.items():
                StateManager.CreateFilesDict(
                    path+"/"+str(k).replace("/", "_"), i)
        else:
            print("try to add: ", path)
            if type(di) == str and di.startswith("./"):
                shutil.copyfile(
                    di, f"./out/{path}" + "." + di.rsplit(".", 1)[-1])
            else:
                with open(f"./out/{path}.txt", 'w') as file:
                    file.write(str(di))

    def RemoveFilesDict(path, di):
        pathdirs = "/".join(path.split("/")[0:-1])

        if type(di) == dict:
            for k, i in di.items():
                StateManager.RemoveFilesDict(
                    path+"/"+str(k).replace("/", "_"), i)
        else:
            if type(di) == str and di.startswith("./"):
                try:
                    removeFile = f"./out/{path}" + \
                        "." + di.rsplit(".", 1)[-1]
                    print("try to remove: ", removeFile)
                    os.remove(removeFile)
                except:
                    print(traceback.format_exc())
            else:
                try:
                    removeFile = f"./out/{path}.txt"
                    print("try to remove: ", removeFile)
                    os.remove(removeFile)
                except:
                    print(traceback.format_exc())

        try:
            os.rmdir(f"./out/{pathdirs}")
        except:
            print(traceback.format_exc())


if not os.path.isfile("./out/program_state.json"):
    StateManager.SaveState()

StateManager.LoadState()
