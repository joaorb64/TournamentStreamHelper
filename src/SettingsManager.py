import os
import json


class SettingsManager:
    settings = {}

    def SaveSettings():
        with open("./user_data/settings.json", 'w') as file:
            json.dump(SettingsManager.settings, file, indent=4)

    def LoadSettings():
        with open("./user_data/settings.json", 'r') as file:
            SettingsManager.settings = json.load(file)

    def Set(key: str, value):
        SettingsManager.settings[key] = value
        SettingsManager.SaveSettings()

    def Get(key: str, default=None):
        return SettingsManager.settings.get(key, default)


if not os.path.isfile("./user_data/settings.json"):
    SettingsManager.SaveSettings()

SettingsManager.LoadSettings()
