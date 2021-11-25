import os
import json


class SettingsManager:
    settings = {}

    def SaveSettings():
        with open("./settings.json", 'w') as file:
            json.dump(SettingsManager.settings, file, indent=4)

    def LoadSettings():
        with open("./settings.json", 'r') as file:
            SettingsManager.settings = json.load(file)

    def Set(key: str, value):
        SettingsManager.settings[key] = value
        SettingsManager.SaveSettings()

    def Get(key: str):
        return SettingsManager.settings.get(key)


if not os.path.isfile("./settings.json"):
    SettingsManager.SaveSettings()

SettingsManager.LoadSettings()
