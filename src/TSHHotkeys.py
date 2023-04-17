import re
import unicodedata
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import requests
import os
import traceback
import json
import copy
from .SettingsManager import SettingsManager

class TSHHotkeysSignals(QObject):
    team1_score_up = pyqtSignal()
    team1_score_down = pyqtSignal()
    team2_score_up = pyqtSignal()
    team2_score_down = pyqtSignal()
    reset_scores = pyqtSignal()
    load_set = pyqtSignal()
    swap_teams = pyqtSignal()

class TSHHotkeys(QObject):
    instance: "TSHHotkeys" = None
    signals = TSHHotkeysSignals()
    parent: QWidget = None
    shortcuts = {}

    keys = {
        "load_set": "Ctrl+O",
        "team1_score_up": "F1",
        "team1_score_down": "F2",
        "team2_score_up": "F3",
        "team2_score_down": "F4",
        "reset_scores": "Ctrl+R",
        "swap_teams": "Ctrl+S"
    }

    loaded_keys = {}

    def __init__(self) -> None:
        super().__init__()
        self.LoadUserHotkeys()

    def UiMounted(self, parent):
        self.parent = parent
        self.SetupHotkeys()

    def ReloadHotkeys(self):
        self.LoadUserHotkeys()
        self.SetupHotkeys()
    
    def SetupHotkeys(self):
        for k, v in self.loaded_keys.items():
            if getattr(self.signals, k):
                try:
                    if k not in self.shortcuts:
                        shortcut = QShortcut(QKeySequence(v), self.parent)
                        shortcut.setContext(Qt.ApplicationShortcut)
                        self.shortcuts[k] = shortcut
                        shortcut.activated.connect(lambda k=k,v=v: self.HotkeyTriggered(k, v))
                    else:
                        self.shortcuts[k].setKey(v)
                except:
                    print(traceback.format_exc())
            else:
                print(f"TSHHotkeys: Command {k} not found")
    
    def HotkeyTriggered(self, k, v):
        if not SettingsManager.Get("hotkeys.hotkeys_enabled", True) == False:
            print(f"Activated {k} by pressing {v}")
            getattr(self.signals, k).emit()
    
    def LoadUserHotkeys(self):
        user_keys = SettingsManager.Get("hotkeys")
        self.loaded_keys = copy.copy(self.keys)

        # Update keys
        self.loaded_keys.update((k,v) for k,v in user_keys.items() if k in self.keys)

        print("User hotkeys loaded")

TSHHotkeys.instance = TSHHotkeys()