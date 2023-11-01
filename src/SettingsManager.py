import os
import orjson
from .Helpers.TSHDictHelper import *


class SettingsManager:
    settings = {}

    def SaveSettings():
        with open("./user_data/settings.json", 'w') as file:
            file.write(orjson.dumps(SettingsManager.settings))

    def LoadSettings():
        with open("./user_data/settings.json", 'r') as file:
            SettingsManager.settings = orjson.loads(file.read())

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
