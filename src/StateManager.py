import os
import json
import copy
import traceback
from deepdiff import DeepDiff, extract
import shutil
import threading
import requests

from Helpers.TSHDictHelper import deep_get, deep_set, deep_unset


class StateManager:
    state = {}

    def SaveState():
        with open("./out/program_state.json", 'w', encoding='utf-8') as file:
            json.dump(StateManager.state, file, indent=4, sort_keys=True)

    def LoadState():
        with open("./out/program_state.json", 'r', encoding='utf-8') as file:
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

    def Get(key: str, default=None):
        return deep_get(StateManager.state, key, default)

    def ExportText(oldState):
        diff = DeepDiff(oldState, StateManager.state)
        # print(diff)

        mergedDiffs = list(diff.get("values_changed", {}).items())
        mergedDiffs.extend(list(diff.get("type_changes", {}).items()))

        # print(mergedDiffs)

        for changeKey, change in mergedDiffs:
            # Remove "root[" from start and separate keys
            filename = "/".join(changeKey[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            # print(filename)

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

            # print("Removed:", filename, item)

            StateManager.RemoveFilesDict(filename, item)

        addedKeys = diff.get("dictionary_item_added", {})

        for key in addedKeys:
            item = extract(StateManager.state, key)

            # Remove "root[" from start and separate keys
            path = "/".join(key[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            # print("Added:", path, item)

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
            # print("try to add: ", path)
            if type(di) == str and di.startswith("./"):
                if os.path.exists(f"./out/{path}" + "." + di.rsplit(".", 1)[-1]):
                    os.remove(f"./out/{path}" + "." + di.rsplit(".", 1)[-1])
                shutil.copyfile(
                    di, f"./out/{path}" + "." + di.rsplit(".", 1)[-1])
            elif type(di) == str and di.startswith("http") and (di.endswith(".png") or di.endswith(".jpg")):
                try:
                    if os.path.exists(f"./out/{path}" + "." + di.rsplit(".", 1)[-1]):
                        os.remove(f"./out/{path}" + "." +
                                  di.rsplit(".", 1)[-1])

                    def downloadImage(url, dlpath):
                        r = requests.get(url, stream=True)
                        if r.status_code == 200:
                            with open(dlpath, 'wb') as f:
                                r.raw.decode_content = True
                                shutil.copyfileobj(r.raw, f)
                                f.flush()

                    t = threading.Thread(
                        target=downloadImage,
                        args=[
                            di,
                            f"./out/{path}" + "." + di.rsplit(".", 1)[-1]
                        ]
                    )
                    t.start()
                except Exception as e:
                    print(traceback.format_exc())
            else:
                with open(f"./out/{path}.txt", 'w', encoding='utf-8') as file:
                    file.write(str(di))

    def RemoveFilesDict(path, di):
        pathdirs = "/".join(path.split("/")[0:-1])

        if type(di) == dict:
            for k, i in di.items():
                StateManager.RemoveFilesDict(
                    path+"/"+str(k).replace("/", "_"), i)
        else:
            if type(di) == str and (di.startswith("./") or di.startswith("http")):
                try:
                    removeFile = f"./out/{path}" + \
                        "." + di.rsplit(".", 1)[-1]
                    # print("try to remove: ", removeFile)
                    os.remove(removeFile)
                except:
                    print(traceback.format_exc())
            else:
                try:
                    removeFile = f"./out/{path}.txt"
                    # print("try to remove: ", removeFile)
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
