import os
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
import json
from .StateManager import StateManager
from .TSHStatsUtil import TSHStatsUtil
from .SettingsManager import SettingsManager
from loguru import logger
from .TSHGameAssetManager import TSHGameAssetManager

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class WebServerActions(QThread):
    def __init__(self, parent=None, scoreboard=None, stageWidget=None) -> None:
        super().__init__(parent)
        self.scoreboard = scoreboard
        self.stageWidget = stageWidget
        self.host_name = "0.0.0.0"
        self.port = 5000

    def program_state(self):
        return StateManager.state

    def ruleset(self):
        data = {}

        data["ruleset"] = StateManager.Get(f"score.ruleset", {})

        # Add webserver base path
        data.update({
            "basedir": os.path.abspath(".")
        })

        # Add player names
        teams = [1, 2]
        if self.scoreboard.teamsSwapped:
            teams.reverse()

        for i, t in enumerate(teams):
            if StateManager.Get(f"score.team.{i+1}.teamName"):
                data.update({
                    f"p{t}": StateManager.Get(f"score.team.{i+1}.teamName")
                })
            else:
                names = [p.get("name") for p in StateManager.Get(
                    f"score.team.{i+1}.player", {}).values() if p.get("name")]

                data.update({
                    f"p{t}": " / ".join(names)
                })

        # Add set data
        data.update({
            "best_of": StateManager.Get(f"score.best_of"),
            "match": StateManager.Get(f"score.match"),
            "phase": StateManager.Get(f"score.phase"),
            "state": StateManager.Get(f"score.stage_strike", {})
        })

        return data

    def stage_clicked(self, data):
        self.stageWidget.stageStrikeLogic.StageClicked(
            json.loads(data))
        return "OK"

    def confirm_clicked(self):
        self.stageWidget.stageStrikeLogic.ConfirmClicked()
        return "OK"

    def rps_win(self, winner):
        self.stageWidget.stageStrikeLogic.RpsResult(
            int(winner))
        return "OK"

    def match_win(self, winner):
        self.stageWidget.stageStrikeLogic.MatchWinner(
            int(winner))
        # Web server updating score here
        self.UpdateScore()
        return "OK"

    def set_gentlemans(self, value):
        self.stageWidget.stageStrikeLogic.SetGentlemans(
            value)
        return "OK"

    def stage_strike_undo(self):
        self.stageWidget.stageStrikeLogic.Undo()
        self.UpdateScore()
        return "OK"

    def stage_strike_redo(self):
        self.stageWidget.stageStrikeLogic.Redo()
        self.UpdateScore()
        return "OK"

    def reset(self):
        self.stageWidget.stageStrikeLogic.Initialize()
        self.UpdateScore()
        return "OK"

    def UpdateScore(self):
        logger.info("================UPDATE SCORE !============")
        logger.info(SettingsManager.Get(
            "general.control_score_from_stage_strike"))

        if not SettingsManager.Get("general.control_score_from_stage_strike", True):
            return

        score = [
            len(self.stageWidget.stageStrikeLogic.CurrentState(
            ).stagesWon[0]),
            len(self.stageWidget.stageStrikeLogic.CurrentState(
            ).stagesWon[1]),
        ]

        logger.info(f"We're supposed to update the score {score}")

        self.scoreboard.signals.ChangeSetData.emit({
            "team1score": score[0],
            "team2score": score[1],
            "reset_score": True
        })

    def post_score(self, data):
        score = json.loads(data)
        score.update({"reset_score": True})
        self.scoreboard.signals.ChangeSetData.emit(score)
        return "OK"

    def team_scoreup(self, team):
        if team == "1":
            self.scoreboard.signals.CommandScoreChange.emit(0, 1)
        else:
            self.scoreboard.signals.CommandScoreChange.emit(1, 1)
        return "OK"

    def team_scoredown(self, team):
        if team == "1":
            self.scoreboard.signals.CommandScoreChange.emit(0, -1)
        else:
            self.scoreboard.signals.CommandScoreChange.emit(1, -1)
        return "OK"

    def set_route(self, bestOf=None, phase=None, match=None, players=None, characters=None, losers=None, team=None):
        # Best Of argument
        # best-of=<Best Of Amount>
        if bestOf is not None:
            if not isinstance(bestOf, int):
                bestOf = 0

            self.scoreboard.signals.ChangeSetData.emit(
                json.loads(
                    json.dumps({'bestOf': bestOf})
                )
            )

        # Phase argument
        # phase=<Phase Name>
        if phase is not None:
            if not isinstance(phase, str):
                phase = 'Pools'

            self.scoreboard.signals.ChangeSetData.emit(
                json.loads(
                    json.dumps({'tournament_phase': phase})
                )
            )

        # Match argument
        # match=<Match Name>
        if match is not None:
            if not isinstance(match, str):
                match = 'Pools'

            self.scoreboard.signals.ChangeSetData.emit(
                json.loads(
                    json.dumps({'round_name': match})
                )
            )

        # Players argument
        # players=<Amount of Players>
        if players is not None:
            if not isinstance(players, int):
                players = 1

            self.scoreboard.playerNumber.setValue(players)

        # Characters argument
        # characters=<Amount of Characters>
        if characters is not None:
            if not isinstance(characters, int):
                characters = 1

            self.scoreboard.charNumber.setValue(characters)

        # Losers argument
        # losers=<True/False>&team=<Team Number>
        if losers is not None:
            losers = bool(losers)
            if not isinstance(team, str):
                team = '1'

            self.scoreboard.signals.ChangeSetData.emit(
                json.loads(
                    json.dumps({'team' + team + 'losers': losers})
                )
            )
        return "OK"

    def set_team_data(self, team, player, data):
        self.scoreboard.signals.ChangeSetData.emit({
            "team": team,
            "player": player,
            "data": data
        })
        return "OK"

    def get_characters(self):
        data = {}
        for row in range(TSHGameAssetManager.instance.characterModel.rowCount()):
            item: QStandardItem = TSHGameAssetManager.instance.characterModel.index(
                row, 0)
            item_data = item.data(Qt.ItemDataRole.UserRole)

            if item_data is not None:
                data[item_data.get("name")] = item_data
        return data

    def swap_teams(self):
        self.scoreboard.signals.SwapTeams.emit()
        return "OK"

    def open_sets(self):
        self.scoreboard.signals.SetSelection.emit()
        return "OK"

    def pull_stream_set(self):
        self.scoreboard.signals.StreamSetSelection.emit()
        return "OK"

    def pull_user_set(self):
        self.scoreboard.signals.UserSetSelection.emit()
        return "OK"

    def stats_recent_sets(self):
        TSHStatsUtil.instance.signals.RecentSetsSignal.emit()
        return "OK"

    def stats_upset_factor(self):
        TSHStatsUtil.instance.signals.UpsetFactorCalculation.emit()
        return "OK"

    def stats_last_sets(self, player):
        if player == "1":
            TSHStatsUtil.instance.signals.LastSetsP1Signal.emit()
        elif player == "2":
            TSHStatsUtil.instance.signals.LastSetsP2Signal.emit()
        elif player == "both":
            TSHStatsUtil.instance.signals.LastSetsP1Signal.emit()
            TSHStatsUtil.instance.signals.LastSetsP2Signal.emit()
        else:
            logger.error(
                "[Last Sets] Unable to find player defined. Allowed values are: 1, 2, or both")
        return "OK"

    def stats_history_sets(self, player):
        if player == "1":
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP1Signal.emit()
        elif player == "2":
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP2Signal.emit()
        elif player == "both":
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP1Signal.emit()
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP2Signal.emit()
        else:
            logger.error(
                "[History Standings] Unable to find player defined. Allowed values are: 1, 2, or both")
        return "OK"

    def reset_scores(self):
        self.scoreboard.ResetScore()
        return "OK"

    def reset_match(self):
        self.scoreboard.ClearScore()
        self.scoreboard.scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        return "OK"

    def reset_players(self):
        self.scoreboard.CommandClearAll()
        return "OK"

    def clear_all(self):
        self.scoreboard.ClearScore()
        self.scoreboard.scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        self.scoreboard.playerNumber.setValue(1)
        self.scoreboard.charNumber.setValue(1)
        self.scoreboard.CommandClearAll()
        return "OK"

    def load_set(self, set=None):
        if set is not None:
            if not isinstance(set, str):
                set = '0'
            self.scoreboard.signals.NewSetSelected.emit(
                json.loads(
                    json.dumps({
                        'id': set,
                        'auto_update': "set"
                    })
                )
            )
        return "OK"
