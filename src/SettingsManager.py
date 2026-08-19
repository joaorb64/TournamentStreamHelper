import os
import orjson
from .Helpers.TSHDictHelper import *


class SettingsManager:
    settings = {}

    def SaveSettings():
        with open("./user_data/settings.json", 'wb') as file:
            file.write(orjson.dumps(SettingsManager.settings, option=orjson.OPT_NON_STR_KEYS))

    def LoadSettings():
        try:
            with open("./user_data/settings.json", 'rb') as file:
                SettingsManager.settings = orjson.loads(file.read())
        except:
            SettingsManager.settings = {}

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
