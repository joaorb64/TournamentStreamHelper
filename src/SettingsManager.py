import os
import json
from .Helpers.TSHDictHelper import *


class SettingsManager:
    settings = {}

    def SaveSettings():
        with open("./user_data/settings.json", 'w') as file:
            json.dump(SettingsManager.settings, file, indent=4, sort_keys=True)

    def LoadSettings():
        with open("./user_data/settings.json", 'r') as file:
            SettingsManager.settings = json.load(file)

    def Set(key: str, value):
        deep_set(SettingsManager.settings, key, value)
        SettingsManager.SaveSettings()
    
    def Unset(key: str):
        deep_unset(SettingsManager.settings, key)
        SettingsManager.SaveSettings()

    def Get(key: str, default=None):
        return deep_get(SettingsManager.settings, key, default)


if not os.path.isfile("./user_data/settings.json"):
    SettingsManager.SaveSettings()

SettingsManager.LoadSettings()
