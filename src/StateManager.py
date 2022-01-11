import os
import json
import copy
from deepdiff import DeepDiff, extract
import shutil

from Helpers.TSHDictHelper import deep_get, deep_set, deep_unset


class StateManager:
    state = {}

    def SaveState():
        with open("./out/program_state.json", 'w') as file:
            json.dump(StateManager.state, file, indent=4, sort_keys=True)

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
            filename = "_".join(changeKey[5:].replace(
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
            filename = "_".join(key[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            print("Removed:", filename, item)

            StateManager.RemoveFilesDict(filename, item)

        addedKeys = diff.get("dictionary_item_added", {})

        for key in addedKeys:
            item = extract(StateManager.state, key)

            # Remove "root[" from start and separate keys
            filename = "_".join(key[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            print("Added:", filename, item)

            StateManager.CreateFilesDict(filename, item)

    def CreateFilesDict(path, di):
        if type(di) == dict:
            for k, i in di.items():
                StateManager.CreateFilesDict(
                    path+"_"+str(k).replace("/", "_"), i)
        else:
            print("try to add: ", path)
            if type(di) == str and di.startswith("./"):
                shutil.copyfile(
                    di, f"./out/{path}" + "." + di.rsplit(".", 1)[-1])
            else:
                with open(f"./out/{path}.txt", 'w') as file:
                    file.write(str(di))

    def RemoveFilesDict(path, di):
        if type(di) == dict:
            for k, i in di.items():
                StateManager.RemoveFilesDict(
                    path+"_"+str(k).replace("/", "_"), i)
        else:
            print("try to remove: ", path)
            if type(di) == str and di.startswith("./"):
                try:
                    os.remove(f"./out/{path}" + "." +
                              di.rsplit(".", 1)[-1])
                except:
                    pass
            else:
                try:
                    os.remove(f"./out/{path}.txt")
                except:
                    pass


if not os.path.isfile("./out/program_state.json"):
    StateManager.SaveState()

StateManager.LoadState()
