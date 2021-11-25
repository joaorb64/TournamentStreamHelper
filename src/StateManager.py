import os
import json

from Helpers import deep_get, deep_set, deep_unset


class StateManager:
    state = {}

    def SaveState():
        with open("./out/program_state.json", 'w') as file:
            json.dump(StateManager.state, file, indent=4, sort_keys=True)

    def LoadState():
        with open("./out/program_state.json", 'r') as file:
            StateManager.state = json.load(file)

    def Set(key: str, value):
        deep_set(StateManager.state, key, value)
        StateManager.SaveState()

    def Unset(key: str):
        deep_unset(StateManager.state, key)
        StateManager.SaveState()

    def Get(key: str):
        return deep_get(StateManager.state, key)


if not os.path.isfile("./out/program_state.json"):
    StateManager.SaveState()

StateManager.LoadState()
