from qtpy.QtWidgets import *
from enum import Enum

# Enum for Selecting Widget Mode (Mainly for dropdown and switch/if statements)
class TSHTeamBattleModeEnum(Enum):
    # STOCK POOL
    # Each player will have an active checkbox, a "dead" checkbox, a spinner with X number of stocks
    # remaining (automatically controlled by dynamic spinner in the top bar).
    # As each stock decreases, the system will export the total pool of stocks remaining and total "score".
    # When a player hits 0 remaining stocks, the system will automatically declare them as "dead" (toggleable).
    STOCK_POOL = QApplication.translate("app", "Stock Pool (Smash)")

    # FIRST TO
    # Each player will have an active checkbox, a "dead" checkbox, a spinner with X current score of a player to the "First To" amount.
    # When increasing player score, if the "First To" amount is reached, the system will reset the player's points
    # and declare the other player "dead" (toggleable).
    # [Easiest way to do it without needing to handle for other cases, and can be handled through signal calls]
    FIRST_TO = QApplication.translate("app", "First To (First To X Team Individuals)")

    # Allows matching the current spinbox value to the enum to allow easier matching in code.
    # Also works across the language barrier thanks to using the translations for values :D
    # Ex. "Stock Pool (Smash)" will match to STOCK_POOL
    def MatchToMode(battleMode: str):
        for mode in TSHTeamBattleModeEnum:
            if mode.value == battleMode:
                return mode
        return TSHTeamBattleModeEnum.STOCK_POOL