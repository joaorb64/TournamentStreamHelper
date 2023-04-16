import re
import unicodedata
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import requests
import os
import traceback
import json

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
    shortcuts = []

    keys = {
        "load_set": "Ctrl+O",
        "team1_score_up": "F1",
        "team1_score_down": "F2",
        "team2_score_up": "F3",
        "team2_score_down": "F4",
        "reset_scores": "Ctrl+R",
        "swap_teams": "Ctrl+S"
    }

    def __init__(self) -> None:
        super().__init__()

    def UiMounted(self, parent):
        self.parent = parent

        for k, v in self.keys.items():
            if getattr(self.signals, k):
                try:
                    self.shortcuts.append(QShortcut(v, self.parent).activated.connect(lambda k=k,v=v: [
                        print(f"Activated {k} by pressing {v}"),
                        getattr(self.signals, k).emit()
                    ]))
                except:
                    print(traceback.format_exc())
            else:
                print(f"TSHHotkeys: Command {k} not found")
    
    def LoadUserHotkeys(self):
        # If there's no hotkeys file, create one
        try:
            if not os.path.exists("user_data/hotkeys.json"):
                with open("./user_data/hotkeys.json", 'w') as file:
                    json.dump(self.keys, file, indent=4)
        except:
            print("Could not create default hotkeys file in user_data")
            print(traceback.format_exc())
        
        # Load hotkeys from file
        try:
            user_keys = {}

            if os.path.exists("user_data/hotkeys.json"):
                with open("./user_data/hotkeys.json", 'r') as file:
                    user_keys = json.load(file)

            self.keys.update(user_keys)

            print("User hotkeys loaded")
        except:
            print("Could load user hotkeys")
            print(traceback.format_exc())



TSHHotkeys.instance = TSHHotkeys()
TSHHotkeys.instance.LoadUserHotkeys()