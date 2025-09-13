import os
import orjson
from .Helpers.TSHDictHelper import *


class LayoutOptionsManager:
    presets = {}
    currentPreset = ""
    settings = {}

    def SaveSettings():
        with open("./user_data/layout_options.json", 'wb') as file:
            file.write(orjson.dumps(LayoutOptionsManager.settings, option=orjson.OPT_NON_STR_KEYS))

    def LoadSettings():
        try:
            with open("./user_data/layout_options.json", 'rb') as file:
                LayoutOptionsManager.settings = orjson.loads(file.read())
        except:
            LayoutOptionsManager.settings = {}

    def Set(key: str, value):
        deep_set(LayoutOptionsManager.settings, key, value)
        LayoutOptionsManager.SaveSettings()
    
    def Unset(key: str):
        deep_unset(LayoutOptionsManager.settings, key)
        LayoutOptionsManager.SaveSettings()

    def Get(key: str, default=None):
        return deep_get(LayoutOptionsManager.settings, key, default)


if not os.path.isfile("./user_data/layout_options.json"):
    LayoutOptionsManager.SaveSettings()

LayoutOptionsManager.LoadSettings()
