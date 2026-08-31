import contextlib
import os

import orjson
import traceback

from deepdiff.helper import DELTA_VIEW
from qtpy.QtCore import QObject, Signal
from deepdiff import DeepDiff, Delta, extract
from functools import partial
import shutil
import threading
import requests
from PIL import Image
import time
from loguru import logger
from .Helpers.TSHDictHelper import deep_get, deep_set, deep_unset, deep_clone
from .SettingsManager import SettingsManager

class StateManagerSignals(QObject):
    state_big_change = Signal()
    state_updated = Signal(dict)

class StateManager:
    lastSavedState = {}
    state = {}
    saveBlocked = 0
    signals = StateManagerSignals()
    changedKeys = []
    deltaIndex = 0

    lock = threading.RLock()
    threads = []
    loop = None

    # Timestamp of the last 0 -> 1 transition of saveBlocked, used by the
    # watchdog to detect a BlockSaving() that never got its ReleaseSaving().
    saveBlockedSince = None

    # If saving stays blocked for longer than this (seconds) while there are
    # pending changes, we assume a block was leaked and force a save.
    DEFAULT_BLOCK_WATCHDOG_SECONDS = 30

    # State paths whose subtrees are excluded from the out/ file export.
    # Use this for large lookup tables that are only useful as JSON (e.g. game.stages).
    EXPORT_EXCLUDED_PREFIXES = (
        "root['game']['stages']",
    )

    @contextlib.contextmanager
    def SaveBlock(watchdog=True):
        StateManager.BlockSaving(watchdog=watchdog)
        try:
            yield
        finally:
            StateManager.ReleaseSaving()

    def BlockSaving(watchdog=True):
        # watchdog=False marks a block that is expected to be long lived (app
        # startup), so the stuck-block watchdog doesn't fire on it.
        with StateManager.lock:
            StateManager.saveBlocked += 1
            if StateManager.saveBlocked == 1:
                StateManager.saveBlockedSince = time.time() if watchdog else None
            if SettingsManager.Get("general.statemanager_logging", False):
                logger.debug("Initial Block - Current Blocking Status: " + str(StateManager.saveBlocked))

    def ReleaseSaving():
        with StateManager.lock:
            StateManager.saveBlocked -= 1
            if SettingsManager.Get("general.statemanager_logging", False):
                logger.debug("Release Block - Current Blocking Status: " + str(StateManager.saveBlocked))

            # More releases than blocks would leave the counter negative, which
            # silently disables every future export just like a leaked block.
            if StateManager.saveBlocked < 0:
                logger.error(
                    "StateManager save block counter went negative "
                    f"({StateManager.saveBlocked}); there is a ReleaseSaving() "
                    "without a matching BlockSaving(). Resetting to 0.")
                StateManager.saveBlocked = 0

            if StateManager.saveBlocked == 0:
                StateManager.saveBlockedSince = None
                StateManager.SaveState()

    def ResetSaveBlock(reason: str):
        """Force saving back to an unblocked state and export immediately.

        Used to recover from an unbalanced BlockSaving() (usually an exception
        thrown between BlockSaving() and ReleaseSaving()), which would
        otherwise stop every export until the application is restarted.
        """
        with StateManager.lock:
            if StateManager.saveBlocked == 0:
                return
            logger.error(
                f"StateManager saving was stuck blocked ({StateManager.saveBlocked}): "
                f"{reason}. Forcing a save.")
            StateManager.saveBlocked = 0
            StateManager.saveBlockedSince = None
            StateManager.SaveState()

    def CheckSaveBlockWatchdog():
        """Recover the export if saving has been blocked for too long."""
        blockedSince = StateManager.saveBlockedSince

        if StateManager.saveBlocked <= 0 or blockedSince is None:
            return

        timeout = SettingsManager.Get(
            "general.statemanager_block_timeout",
            StateManager.DEFAULT_BLOCK_WATCHDOG_SECONDS)

        if timeout <= 0:
            return

        blockedFor = time.time() - blockedSince

        if blockedFor > timeout:
            StateManager.ResetSaveBlock(
                f"saving has been blocked for {blockedFor:.1f}s, which points to a "
                "BlockSaving() without a matching ReleaseSaving()")

    def SaveState():
        if StateManager.saveBlocked != 0:
            return

        with StateManager.lock:
            try:
                StateManager.DoSaveState()
            except Exception as e:
                # An export failure must never escape into a caller that is
                # holding a save block: it would skip that caller's
                # ReleaseSaving() and disable every future export.
                logger.error(traceback.format_exc())

    def DoSaveState():
        StateManager.threads = []

        def EncodeFallback(value):
            # Without this a single value orjson can't handle would stop
            # program_state.json from ever being written again.
            logger.warning(
                f"State contains a {type(value).__name__} value which isn't JSON "
                "serializable; exporting it as text")
            return str(value)

        def ExportAll(ref_diff):
            try:
                StateManager.state.update({"timestamp": time.time()})
                try:
                    encoded = orjson.dumps(
                        StateManager.state, default=EncodeFallback,
                        option=orjson.OPT_NON_STR_KEYS | orjson.OPT_INDENT_2)

                    # Write to a temp file then atomically replace, so a concurrent
                    # reader never sees a truncated file. On Windows the replace can
                    # fail if the browser has the destination open; fall back to a
                    # direct write in that case.
                    tmp_path = "./out/program_state.json.tmp"
                    with open(tmp_path, 'wb') as file:
                        file.write(encoded)
                    try:
                        os.replace(tmp_path, "./out/program_state.json")
                    except PermissionError:
                        os.remove(tmp_path)
                        with open("./out/program_state.json", 'wb') as file:
                            file.write(encoded)
                finally:
                    StateManager.state.pop("timestamp", None)

                if not SettingsManager.Get("general.disable_export", False):
                    StateManager.ExportText(
                        StateManager.lastSavedState, ref_diff)
                StateManager.lastSavedState = deep_clone(
                    StateManager.state)
            except Exception as e:
                # This runs in its own thread; without this the traceback would
                # only reach the thread excepthook.
                logger.error(traceback.format_exc())

        # logger.debug(StateManager.changedKeys)

        changedKeys = list(set(StateManager.changedKeys))

        # Cleared up front: a change we cannot diff must not be retried on every
        # subsequent save, or a single bad key would stall the export for good.
        StateManager.changedKeys = []

        try:
            diff = DeepDiff(
                StateManager.lastSavedState,
                StateManager.state,
                exclude_types=[type(None)],
                include_paths=changedKeys,
                verbose_level=2, # Necessary to see values of added items.
            )
        except Exception as e:
            logger.error(traceback.format_exc())
            diff = None

        if diff is not None:
            try:
                delta = Delta(diff).to_flat_dicts()
                # logger.debug(f"State diff length: {diff_count}")
                if len(delta) > 100:
                    StateManager.deltaIndex += 1
                    StateManager.signals.state_big_change.emit()
                elif len(delta) > 0:
                    StateManager.deltaIndex += 1
                    StateManager.signals.state_updated.emit({
                        'delta_index': StateManager.deltaIndex,
                        'delta': delta
                    })
            except TypeError:
                logger.warning(f"Couldn't serialize diff. Changed Keys: {changedKeys}")
            except Exception as e:
                logger.error(traceback.format_exc())
                # Overlays can still resync from the full state.
                StateManager.deltaIndex += 1
                StateManager.signals.state_big_change.emit()

        # When the diff couldn't be computed we still export, so that
        # program_state.json keeps tracking the live state.
        if diff is None or len(diff) > 0:
            exportThread = threading.Thread(
                target=partial(ExportAll, ref_diff=diff if diff is not None else {}))
            StateManager.threads.append(exportThread)
            exportThread.start()

            for t in StateManager.threads:
                t.join()

    def LoadState():
        try:
            with open("./out/program_state.json", 'rb') as file:
                StateManager.state = orjson.loads(file.read())
                StateManager.signals.state_big_change.emit()
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(traceback.format_exc())
            StateManager.state = {}
            StateManager.signals.state_big_change.emit()
            StateManager.SaveState()

    def Set(key: str, value):
        # import inspect
        # func = inspect.currentframe().f_back.f_code
        # fname = os.path.split(func.co_filename)[1]
        # logger.debug(f"{func.co_name}({fname}:{func.co_firstlineno}) Setting {key} to {value}")
        with StateManager.lock:
            # StateManager.lastSavedState = deep_clone(StateManager.state)

            deep_set(StateManager.state, key, value)

            final_key = "root"
            for k in key.split("."):
                final_key += f"['{k}']"

            StateManager.changedKeys.append(final_key)

            if StateManager.saveBlocked == 0:
                StateManager.SaveState()
                # StateManager.ExportText(oldState)
            else:
                StateManager.CheckSaveBlockWatchdog()

    def Unset(key: str):
        # import inspect
        # func = inspect.currentframe().f_back.f_code
        # fname = os.path.split(func.co_filename)[1]
        # logger.debug(f"{func.co_name}({fname}:{func.co_firstlineno}) Deleting {key}")

        with StateManager.lock:
            # StateManager.lastSavedState = deep_clone(StateManager.state)
            deep_unset(StateManager.state, key)

            final_key = "root"
            for k in key.split("."):
                final_key += f"['{k}']"
            StateManager.changedKeys.append(final_key)

            if StateManager.saveBlocked == 0:
                StateManager.SaveState()
                # StateManager.ExportText(oldState)
            else:
                StateManager.CheckSaveBlockWatchdog()

    def Get(key: str, default=None):
        return deep_get(StateManager.state, key, default)

    def ExportText(oldState, diff):
        # logger.info("ExportState")
        # logger.info(diff)

        mergedDiffs = list(diff.get("values_changed", {}).items())
        mergedDiffs.extend(list(diff.get("type_changes", {}).items()))

        # logger.info(mergedDiffs)

        for changeKey, change in mergedDiffs:
            if any(changeKey.startswith(p) for p in StateManager.EXPORT_EXCLUDED_PREFIXES):
                continue

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
            if any(key.startswith(p) for p in StateManager.EXPORT_EXCLUDED_PREFIXES):
                continue

            item = extract(oldState, key)

            # Remove "root[" from start and separate keys
            filename = "/".join(key[5:].replace(
                "'", "").replace("]", "").replace("/", "_").split("["))

            # logger.info("Removed:", filename, item)

            StateManager.RemoveFilesDict(filename, item)

        addedKeys = diff.get("dictionary_item_added", {})

        for key in addedKeys:
            if any(key.startswith(p) for p in StateManager.EXPORT_EXCLUDED_PREFIXES):
                continue

            try:
                item = extract(StateManager.state, key)

                # Remove "root[" from start and separate keys
                path = "/".join(key[5:].replace(
                    "'", "").replace("]", "").replace("/", "_").split("["))
                # Remove "root[" from start and separate keys
                path = "/".join(key[5:].replace(
                    "'", "").replace("]", "").replace("/", "_").split("["))

                # logger.info("Added:", path, item)
                # logger.info("Added:", path, item)

                StateManager.CreateFilesDict(path, item)
            except Exception as e:
                logger.error(traceback.format_exc())

    def CreateFilesDict(path, di):
        parts = [p for p in path.split("/") if p]
        state_key = "root" + "".join(f"['{p}']" for p in parts)
        if any(state_key.startswith(p) for p in StateManager.EXPORT_EXCLUDED_PREFIXES):
            return

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
                        shutil.copyfile(
                            os.path.abspath(di),
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
        parts = [p for p in path.split("/") if p]
        state_key = "root" + "".join(f"['{p}']" for p in parts)
        if any(state_key.startswith(p) for p in StateManager.EXPORT_EXCLUDED_PREFIXES):
            return

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
