from qtpy.QtCore import *

from datetime import datetime
import math

from .StateManager import *
from .SettingsManager import *
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from loguru import logger


class TSHStatsSignals(QObject):
    RecentSetsSignal = Signal()
    LastSetsP1Signal = Signal()
    LastSetsP2Signal = Signal()
    PlayerHistoryStandingsP1Signal = Signal()
    PlayerHistoryStandingsP2Signal = Signal()
    UpsetFactorCalculation = Signal()


class TSHStatsUtil:
    instance: "TSHStatsUtil" = None

    def __init__(self):
        self.signals: TSHStatsSignals = TSHStatsSignals()

        self.signals.PlayerHistoryStandingsP1Signal.connect(
            self.GetPlayerHistoryStandingsP1)
        self.signals.PlayerHistoryStandingsP2Signal.connect(
            self.GetPlayerHistoryStandingsP2)
        self.signals.LastSetsP1Signal.connect(self.GetLastSetsP1)
        self.signals.LastSetsP2Signal.connect(self.GetLastSetsP2)
        self.signals.RecentSetsSignal.connect(self.GetRecentSets)
        self.signals.UpsetFactorCalculation.connect(self.GetSetUpsetFactor)

        TSHTournamentDataProvider.instance.signals.history_sets_updated.connect(
            self.UpdateHistorySets)
        TSHTournamentDataProvider.instance.signals.last_sets_updated.connect(
            self.UpdateLastSets)
        TSHTournamentDataProvider.instance.signals.recent_sets_updated.connect(
            self.UpdateRecentSets)
        TSHTournamentDataProvider.instance.signals.stream_queue_loaded.connect(
            self.UpdateStreamQueue)

    def GetRecentSets(self):
        updated = False
        # Only if 1 player on each side
        if len(self.scoreboard.team1playerWidgets) == 1 and TSHTournamentDataProvider.instance and TSHTournamentDataProvider.instance.provider.name == "StartGG":
            p1id = StateManager.Get(f"score.team.1.player.1.id")
            p2id = StateManager.Get(f"score.team.2.player.1.id")
            if p1id and p2id and json.dumps(p1id) != json.dumps(p2id):
                StateManager.Set(f"score.recent_sets", {
                    "state": "loading",
                    "sets": []
                })
                TSHTournamentDataProvider.instance.GetRecentSets(p1id, p2id)
                updated = True

        if not updated:
            StateManager.Set(f"score.recent_sets", {
                "state": "done",
                "sets": []
            })

    def UpdateRecentSets(self, data):
        lastUpdateTime = StateManager.Get(f"score.recent_sets.request_time", 0)

        if data.get("request_time", 0) > lastUpdateTime:
            StateManager.Set(f"score.recent_sets", {
                "state": "done",
                "sets": data.get("sets"),
                "request_time": data.get("request_time")
            })

    def GetLastSetsP1(self):
        # Only if 1 player on each side
        if len(self.scoreboard.team1playerWidgets) == 1 and TSHTournamentDataProvider.instance:
            p1id = StateManager.Get(f"score.team.1.player.1.id")
            if p1id:
                TSHTournamentDataProvider.instance.GetLastSets(p1id, "1")
            else:
                StateManager.Set(f"score.last_sets.1", {})

    def GetLastSetsP2(self):
        # Only if 1 player on each side
        if len(self.scoreboard.team1playerWidgets) == 1 and TSHTournamentDataProvider.instance:
            p2id = StateManager.Get(f"score.team.2.player.1.id")
            if p2id:
                TSHTournamentDataProvider.instance.GetLastSets(p2id, "2")
            else:
                StateManager.Set(f"score.last_sets.2", {})

    def UpdateLastSets(self, data):
        StateManager.BlockSaving()
        i = 1
        for set in data.get("last_sets", []):
            StateManager.Set(f"score.last_sets." + data.get("playerNumber") + "." + str(i), {
                "phase_id": set.get("phase_id"),
                "phase_name": set.get("phase_name"),
                "round_name": set.get("round_name"),
                "player_score": set.get("player1_score"),
                "player_team": set.get("player1_team"),
                "player_name": set.get("player1_name"),
                "oponent_score": set.get("player2_score"),
                "oponent_team": set.get("player2_team"),
                "oponent_name": set.get("player2_name")
            })
            i += 1
        StateManager.ReleaseSaving()

    def GetPlayerHistoryStandingsP1(self):
        # Only if 1 player on each side
        if len(self.scoreboard.team1playerWidgets) == 1 and TSHTournamentDataProvider.instance and TSHTournamentDataProvider.instance.provider.name == "StartGG":
            p1id = StateManager.Get(f"score.team.1.player.1.id")
            if p1id:
                TSHTournamentDataProvider.instance.GetPlayerHistoryStandings(
                    p1id, "1", StateManager.Get(f"game.smashgg_id"))
            else:
                StateManager.Set(f"score.history_sets.1", {})

    def GetPlayerHistoryStandingsP2(self):
        # Only if 1 player on each side
        if len(self.scoreboard.team1playerWidgets) == 1 and TSHTournamentDataProvider.instance and TSHTournamentDataProvider.instance.provider.name == "StartGG":
            p2id = StateManager.Get(f"score.team.2.player.1.id")
            if p2id:
                TSHTournamentDataProvider.instance.GetPlayerHistoryStandings(
                    p2id, "2", StateManager.Get(f"game.smashgg_id"))
            else:
                StateManager.Set(f"score.history_sets.2", {})

    def UpdateHistorySets(self, data):
        StateManager.BlockSaving()
        i = 1
        for set in data.get("history_sets", []):
            StateManager.Set(f"score.history_sets." + data.get("playerNumber") + "." + str(i), {
                "placement": set.get("placement"),
                "event_name": set.get("event_name"),
                "tournament_name": set.get("tournament_name"),
                "tournament_picture": set.get("tournament_picture"),
                "entrants": set.get("entrants"),
                "event_date_month": datetime.fromtimestamp(set.get("event_date")).strftime("%B"),
                "event_date_day": datetime.fromtimestamp(set.get("event_date")).strftime("%d"),
                "event_date_year": datetime.fromtimestamp(set.get("event_date")).strftime("%Y")
            })
            i += 1
        StateManager.ReleaseSaving()

    def GetSetUpsetFactor(self):
        if len(self.scoreboard.team1playerWidgets) == 1 and TSHTournamentDataProvider.instance and TSHTournamentDataProvider.instance.provider.name == "StartGG":
            bracket_type = StateManager.Get(f"score.bracket_type", "")
            p1id = StateManager.Get(f"score.team.1.player.1.id")
            p2id = StateManager.Get(f"score.team.2.player.1.id")

            if p1id and p2id and json.dumps(p1id) != json.dumps(p2id):
                p1 = StateManager.Get(f"score.team.1.player.1.seed")
                p2 = StateManager.Get(f"score.team.2.player.1.seed")
                if p1 and p2:
                    logger.info("P1 Seed: " + str(p1))
                    p1_upset = self.CalculatePlacementMath(bracket_type, p1)

                    logger.info("P2 Seed: " + str(p2))
                    p2_upset = self.CalculatePlacementMath(bracket_type, p2)

                    StateManager.Set(f"score.upset_factor",
                                     abs(p1_upset - p2_upset))
        else:
            StateManager.Set(f"score.upset_factor", 0)

    def _setWithDifferentKey(source, sKey, target, tKey):
        value = source.deep_get(sKey)
        if value:
            target.deep_set(tKey, value)

    def formatStreamQueueData(self, data):
        pass

    def UpdateStreamQueue(self, data):
        StateManager.BlockSaving()

        StateManager.Set(f"streamQueue", data)
        StateManager.Set(f"currentStream",
                         SettingsManager.Get("twitch_username"))

        StateManager.ReleaseSaving()

    # Calculation of Seeding/Placement to determine
    # Upset Factor or Seeding Performance Rating
    #
    # bracket_type [STRING] = The bracket type returned from Start.GG
    #
    # x [INTEGER] = The seeding/placement value being used to determine
    # the end product (Ex. Seeding for UF or Seeding/Placement for SPR)
    def CalculatePlacementMath(self, bracket_type, x):
        # Due to how the logs works, if the player is first seed,
        # the value will always be 0 and no math needs to be done.
        if x <= 1:
            return 0

        single_elim_calc = math.floor(math.log2(x - 1))
        double_elim_calc = math.ceil(math.log2((2 * x) / 3))

        # Double Elimination Sum of Values
        if bracket_type == "DOUBLE_ELIMINATION":
            return single_elim_calc + double_elim_calc
        # Single Elimination Sum of Values
        elif bracket_type == "SINGLE_ELIMINATION":
            return single_elim_calc
        else:
            return 0


TSHStatsUtil.instance = TSHStatsUtil()
