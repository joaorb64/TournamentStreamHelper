import os
import json
import copy
import traceback
from deepdiff import DeepDiff, extract
import shutil
import threading
import requests
from PIL import Image
import time
from loguru import logger
from .Helpers.TSHDictHelper import deep_get, deep_set, deep_unset


class StateManager:
    lastSavedState = {}
    state = {}
    saveBlocked = 0
    webServer = None

    lock = threading.RLock()
    threads = []

    def BlockSaving():
        StateManager.saveBlocked += 1
        logger.critical(
            "Initial Block - Current Blocking Status: " + str(StateManager.saveBlocked))

    def ReleaseSaving():
        StateManager.saveBlocked -= 1
        logger.critical(
            "Release Block - Current Blocking Status: " + str(StateManager.saveBlocked))
        if StateManager.saveBlocked == 0:
            StateManager.SaveState()

    def SaveState():
        if StateManager.saveBlocked == 0:
            with StateManager.lock:
                StateManager.threads = []

                def ExportAll():
                    with open("./out/program_state.json", 'w', encoding='utf-8', buffering=8192) as file:
                        # logger.info("SaveState")
                        StateManager.state.update({"timestamp": time.time()})
                        json.dump(StateManager.state, file,
                                  indent=4, sort_keys=False)
                        StateManager.state.pop("timestamp")

                    StateManager.ExportText(StateManager.lastSavedState)
                    StateManager.lastSavedState = copy.deepcopy(
                        StateManager.state)

                diff = DeepDiff(StateManager.lastSavedState,
                                StateManager.state)

                if len(diff) > 0:
                    try:
                        if StateManager.webServer is not None:
                            StateManager.webServer.emit('program_state', StateManager.state)
                    except Exception as e:
                        logger.error(traceback.format_exc())

                    exportThread = threading.Thread(target=ExportAll)
                    StateManager.threads.append(exportThread)
                    exportThread.start()

                    for t in StateManager.threads:
                        t.join()

    def LoadState():
        try:
            with open("./out/program_state.json", 'r', encoding='utf-8') as file:
                StateManager.state = json.load(file)
        except:
            StateManager.state = {}
            StateManager.SaveState()

    def Set(key: str, value):
        with StateManager.lock:
            oldState = copy.deepcopy(StateManager.state)

            deep_set(StateManager.state, key, value)

            if StateManager.saveBlocked == 0:
                StateManager.SaveState()
                # StateManager.ExportText(oldState)

    def Unset(key: str):
        with StateManager.lock:
            oldState = copy.deepcopy(StateManager.state)
            deep_unset(StateManager.state, key)
            if StateManager.saveBlocked == 0:
                StateManager.SaveState()
                # StateManager.ExportText(oldState)

    def Get(key: str, default=None):
        return deep_get(StateManager.state, key, default)

    def ExportText(oldState):
        # logger.info("ExportState")
        diff = DeepDiff(oldState, StateManager.state)
        # logger.info(diff)

        mergedDiffs = list(diff.get("values_changed", {}).items())
        mergedDiffs.extend(list(diff.get("type_changes", {}).items()))

        # logger.info(mergedDiffs)

        for changeKey, change in mergedDiffs:
            # Remove "root[" from start and separate keys
            filename = "/".join(changeKey[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            # logger.info(filename)

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

            # logger.info("Removed:", filename, item)

            StateManager.RemoveFilesDict(filename, item)

        addedKeys = diff.get("dictionary_item_added", {})

        for key in addedKeys:
            item = extract(StateManager.state, key)

            # Remove "root[" from start and separate keys
            path = "/".join(key[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            # logger.info("Added:", path, item)

            StateManager.CreateFilesDict(path, item)

    def CreateFilesDict(path, di):
        pathdirs = "/".join(path.split("/")[0:-1])

        if not os.path.isdir("./out/"+pathdirs):
            os.makedirs("./out/"+pathdirs)

        if type(di) == dict:
            for k, i in di.items():
                StateManager.CreateFilesDict(
                    path+"/"+str(k).replace("/", "_"), i)
        else:
            # logger.info("try to add: ", path)
            if type(di) == str and di.startswith("./"):
                if os.path.exists(f"./out/{path}" + "." + di.rsplit(".", 1)[-1]):
                    try:
                        os.remove(f"./out/{path}" + "." +
                                  di.rsplit(".", 1)[-1])
                    except Exception as e:
                        logger.error(traceback.format_exc())
                if os.path.exists(di):
                    try:
                        os.link(os.path.abspath(di),
                                f"./out/{path}" + "." + di.rsplit(".", 1)[-1])
                    except Exception as e:
                        logger.error(traceback.format_exc())
            elif type(di) == str and di.startswith("http") and (di.endswith(".png") or di.endswith(".jpg")):
                try:
                    if os.path.exists(f"./out/{path}" + "." + di.rsplit(".", 1)[-1]):
                        try:
                            os.remove(f"./out/{path}" +
                                      "." + di.rsplit(".", 1)[-1])
                        except Exception as e:
                            logger.error(traceback.format_exc())

                    def downloadImage(url, dlpath):
                        try:
                            r = requests.get(url, stream=True)
                            if r.status_code == 200:
                                with open(dlpath, 'wb') as f:
                                    r.raw.decode_content = True
                                    shutil.copyfileobj(r.raw, f)
                                    f.flush()
                            if url.endswith(".jpg"):
                                original = Image.open(dlpath)
                                original.save(dlpath.rsplit(
                                    ".", 1)[0]+".png", format="png")
                                os.remove(dlpath)
                        except Exception as e:
                            logger.error(traceback.format_exc())

                    t = threading.Thread(
                        target=downloadImage,
                        args=[
                            di,
                            f"./out/{path}" + "." + di.rsplit(".", 1)[-1]
                        ]
                    )
                    StateManager.threads.append(t)
                    t.start()
                except Exception as e:
                    logger.error(traceback.format_exc())
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
                    # logger.info("try to remove: ", removeFile)
                    if os.path.exists(removeFile):
                        os.remove(removeFile)
                except:
                    logger.error(traceback.format_exc())
            else:
                try:
                    removeFile = f"./out/{path}.txt"
                    # logger.info("try to remove: ", removeFile)
                    if os.path.exists(removeFile):
                        os.remove(removeFile)
                except:
                    logger.error(traceback.format_exc())

        try:
            # logger.info("Remove path", f"./out/{path}")
            if os.path.exists(f"./out/{path}"):
                shutil.rmtree(f"./out/{path}")
        except:
            logger.error(traceback.format_exc())


if not os.path.exists("./out"):
    os.makedirs("./out/")

if not os.path.isfile("./out/program_state.json"):
    StateManager.SaveState()

StateManager.LoadState()
