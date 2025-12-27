import os
import re
from flask import abort
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
import orjson

from .Helpers.TSHCountryHelper import TSHCountryHelper
from .Helpers.TSHQtHelper import gui_thread_async, gui_thread_sync
from .StateManager import StateManager
from .TSHStatsUtil import TSHStatsUtil
from .SettingsManager import SettingsManager
from loguru import logger
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHBracketView import TSHBracketView
from .TSHBracketWidget import TSHBracketWidget
from .TSHPlayerDB import TSHPlayerDB
from .TSHScoreboardWidget import TSHScoreboardWidget
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHCommentaryWidget import TSHCommentaryWidget
from .Helpers.TSHControllerHelper import TSHControllerHelper
from .Helpers.TSHLocaleHelper import TSHLocaleHelper
from .Workers import Worker
import os

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class WebServerActions(QThread):
    def __init__(self, parent=None, scoreboard=None, stageWidget=None, commentaryWidget: TSHCommentaryWidget=None) -> None:
        super().__init__(parent)
        self.scoreboard = scoreboard
        self.stageWidget = stageWidget
        self.commentaryWidget = commentaryWidget
        self.threadPool = QThreadPool()

    def program_state(self):
        return {'state': StateManager.state, 'delta_index': StateManager.deltaIndex}

    @gui_thread_sync
    def ruleset(self):
        data = {}

        data["ruleset"] = StateManager.Get(f"score.ruleset", {})

        # Add webserver base path
        data.update({
            "basedir": os.path.abspath(".")
        })

        if self.scoreboard.GetTabAmount() < 1:
            return data

        # Add player names
        teams = [1, 2]
        if self.scoreboard.GetScoreboard(1).teamsSwapped:
            teams.reverse()

        for i, t in enumerate(teams):
            if StateManager.Get(f"score.1.team.{i+1}.teamName"):
                data.update({
                    f"p{t}": StateManager.Get(f"score.1.team.{i+1}.teamName")
                })
            else:
                names = [p.get("name") for p in StateManager.Get(
                    f"score.1.team.{i+1}.player", {}).values() if p.get("name")]

                data.update({
                    f"p{t}": " / ".join(names)
                })

        # Add set data
        data.update({
            "best_of": StateManager.Get(f"score.1.best_of"),
            "match": StateManager.Get(f"score.1.match"),
            "phase": StateManager.Get(f"score.1.phase"),
            "state": StateManager.Get(f"score.1.stage_strike", {})
        })

        return data

    @gui_thread_sync
    def stage_clicked(self, data):
        self.stageWidget.stageStrikeLogic.StageClicked(
            orjson.loads(data))
        return "OK"

    @gui_thread_sync
    def confirm_clicked(self):
        self.stageWidget.stageStrikeLogic.ConfirmClicked()
        return "OK"

    @gui_thread_sync
    def rps_win(self, winner):
        self.stageWidget.stageStrikeLogic.RpsResult(
            int(winner))
        return "OK"

    @gui_thread_sync
    def match_win(self, winner):
        self.stageWidget.stageStrikeLogic.MatchWinner(
            int(winner))
        # Web server updating score here
        self.UpdateScore()
        return "OK"

    @gui_thread_sync
    def set_gentlemans(self, value):
        self.stageWidget.stageStrikeLogic.SetGentlemans(
            value)
        return "OK"

    @gui_thread_sync
    def stage_strike_undo(self):
        self.stageWidget.stageStrikeLogic.Undo()
        self.UpdateScore()
        return "OK"

    @gui_thread_sync
    def stage_strike_redo(self):
        self.stageWidget.stageStrikeLogic.Redo()
        self.UpdateScore()
        return "OK"

    @gui_thread_sync
    def reset(self):
        self.stageWidget.stageStrikeLogic.Initialize()
        self.UpdateScore()
        return "OK"

    @gui_thread_sync
    def UpdateScore(self):
        if not SettingsManager.Get("general.control_score_from_stage_strike", True):
            return

        score = [
            len(self.stageWidget.stageStrikeLogic.CurrentState(
            ).stagesWon[0]),
            len(self.stageWidget.stageStrikeLogic.CurrentState(
            ).stagesWon[1]),
        ]

        logger.info(f"We're supposed to update the score {score}")

        self.scoreboard.GetScoreboard(1).signals.ChangeSetData.emit({
            "team1score": score[0],
            "team2score": score[1],
            "reset_score": True
        })

    @gui_thread_sync
    def post_score(self, data):
        score = orjson.loads(data)
        scoreboard_number = 1

        if "scoreboard" in score:
            try:
                scoreboard_number = int(score["scoreboard"])
            except ValueError:
                logger.warning(f"Couldn't parse scoreboard [${score['scoreboard']}] from /post_data as int, falling back to scoreboard 1")
                scoreboard_number = 1

        score.update({"reset_score": True})
        self.scoreboard.GetScoreboard(scoreboard_number).signals.ChangeSetData.emit(score)
        return "OK"

    def team_scoreup(self, scoreboard, team):
        if str(team) == "1":
            self.scoreboard.GetScoreboard(scoreboard).signals.CommandScoreChange.emit(0, 1)
        else:
            self.scoreboard.GetScoreboard(scoreboard).signals.CommandScoreChange.emit(1, 1)
        return "OK"

    def team_scoredown(self, scoreboard, team):
        if str(team) == "1":
            self.scoreboard.GetScoreboard(scoreboard).signals.CommandScoreChange.emit(0, -1)
        else:
            self.scoreboard.GetScoreboard(scoreboard).signals.CommandScoreChange.emit(1, -1)
        return "OK"

    def team_color(self, scoreboard, team, color):
        if str(team) == "1":
            self.scoreboard.GetScoreboard(scoreboard).signals.CommandTeamColor.emit(0, color)
        else:
            self.scoreboard.GetScoreboard(scoreboard).signals.CommandTeamColor.emit(1, color)
        return "OK"

    def get_scoreboard(self, scoreboard):
        sb_widget: TSHScoreboardWidget = self.scoreboard.GetScoreboard(scoreboard)
        return StateManager.Get(f'score.{sb_widget.scoreboardNumber}')

    @gui_thread_sync
    def set_route(self,
                  scoreboard,
                  bestOf=None,
                  phase=None,
                  match=None,
                  players=None,
                  characters=None,
                  losers=None,
                  team=None):
        # Best Of argument
        # best-of=<Best Of Amount>
        if bestOf is not None:
            self.scoreboard.GetScoreboard(scoreboard).signals.ChangeSetData.emit(
                orjson.loads(
                    orjson.dumps({'bestOf': int(bestOf)})
                )
            )

        # Phase argument
        # phase=<Phase Name>
        if phase is not None:
            self.scoreboard.GetScoreboard(scoreboard).signals.ChangeSetData.emit(
                orjson.loads(
                    orjson.dumps({'tournament_phase': phase})
                )
            )

        # Match argument
        # match=<Match Name>
        if match is not None:
            self.scoreboard.GetScoreboard(scoreboard).signals.ChangeSetData.emit(
                orjson.loads(
                    orjson.dumps({'round_name': match})
                )
            )

        # Players argument
        # players=<Amount of Players>
        if players is not None:
            self.scoreboard.GetScoreboard(scoreboard).playerNumber.setValue(int(players))

        # Characters argument
        # characters=<Amount of Characters>
        if characters is not None:
            self.scoreboard.GetScoreboard(scoreboard).charNumber.setValue(int(characters))

        # Losers argument
        # losers=<True/False>&team=<Team Number>
        if losers is not None:
            self.scoreboard.GetScoreboard(scoreboard).signals.ChangeSetData.emit(
                orjson.loads(
                    orjson.dumps({'team' + str(team) + 'losers': False if losers.lower() == 'false' else True})
                )
            )
        return "OK"

    def set_team_data(self, scoreboard, team, player, data):
        self.scoreboard.GetScoreboard(scoreboard).signals.ChangeSetData.emit({
            "team": team,
            "player": player,
            "data": data
        })
        return "OK"

    def set_commentary_data(self, index, data):
        logger.info(self.commentaryWidget)
        index = int(index) - 1
        if index < 0:
            return "ERROR : index can't be lower than 1"
        self.commentaryWidget.ChangeCommDataSignal.emit(index, data)

        return "OK"

    @gui_thread_sync
    def set_game(self, data):
        # Not actually sure if this needs to be in the GUI thread but the asset manager is complex enough that it seems
        # worthwhile to dispatch it like this.
        set_codename = data.get("codename")
        found_game = False
        for i, codename in enumerate(TSHGameAssetManager.instance.games.keys()):
            if codename == set_codename:
                # TSHGameAssetManager.instance.selectedGame = TSHGameAssetManager.instance.games[codename]
                # self.parent().SetGame()
                TSHGameAssetManager.instance.LoadGameAssets(i+1, async_mode=False, mods_active=data.get("mods_active", False), mods_reload_mode=True)
                found_game = True
                break

        if not found_game:
            return f"Could not find game {set_codename}"

        return "OK"

    def get_games(self):
        data = {}
        for key in TSHGameAssetManager.instance.games.keys():
            data[key] = {
                "name": TSHGameAssetManager.instance.games[key].get("name"),
                "locale": TSHGameAssetManager.instance.games[key].get("locale"),
                "smashgg_game_id": TSHGameAssetManager.instance.games[key].get("smashgg_game_id"),
                "has_stages": bool(TSHGameAssetManager.instance.games[key].get("stage_to_codename")),
                "has_variants": bool(TSHGameAssetManager.instance.games[key].get("variant_to_codename")),
                "has_colors": bool(TSHGameAssetManager.instance.games[key].get("preset_colors"))
            }

        return data
    
    def get_current_game(self):
        return StateManager.Get("game")
    
    def get_match_names(self):
        response = {
            "match": TSHLocaleHelper.matchNames,
            "phase": TSHLocaleHelper.phaseNames
        }
        return response

    @gui_thread_sync
    def get_characters(self):
        data = {}
        for row in range(TSHGameAssetManager.instance.characterModel.rowCount()):
            item: QStandardItem = TSHGameAssetManager.instance.characterModel.index(
                row, 0)
            item_data = item.data(Qt.ItemDataRole.UserRole)

            if item_data is not None:
                skin_models = TSHGameAssetManager.instance.skinModels.get(item_data.get("en_name"))
                item_data["skins"] = []
                if skin_models is not None:
                    for skindex in range(skin_models.rowCount()):
                        item_data["skins"].append(skin_models.index(skindex, 0).data(Qt.ItemDataRole.UserRole))
                data[item_data.get("name")] = item_data

        return data

    @gui_thread_sync
    def get_variants(self):
        data = {}
        for row in range(TSHGameAssetManager.instance.variantModel.rowCount()):
            item: QStandardItem = TSHGameAssetManager.instance.variantModel.index(
                row, 0)
            item_data = item.data(Qt.ItemDataRole.UserRole)

            if item_data is not None:
                data[item_data.get("name")] = item_data
        return data

    def get_controllers(self):
        data = TSHControllerHelper.instance.controller_list
        for key in data.keys():
            data[key]["codename"] = key
        return data

    def swap_teams(self, scoreboard):
        self.scoreboard.GetScoreboard(scoreboard).signals.SwapTeams.emit()
        return "OK"
    
    def get_swap(self, scoreboard):
        return str(self.scoreboard.GetScoreboard(scoreboard).teamsSwapped)

    def open_sets(self, scoreboard):
        self.scoreboard.GetScoreboard(scoreboard).signals.SetSelection.emit()
        return "OK"

    def pull_stream_set(self, scoreboard):
        self.scoreboard.GetScoreboard(scoreboard).signals.StreamSetSelection.emit()
        return "OK"

    def pull_user_set(self):
        self.scoreboard.GetScoreboard(1).signals.UserSetSelection.emit()
        return "OK"

    def stats_recent_sets(self, scoreboard):
        TSHStatsUtil.instance.signals.RecentSetsSignal.emit()
        return "OK"

    def stats_upset_factor(self, scoreboard):
        TSHStatsUtil.instance.signals.UpsetFactorCalculation.emit()
        return "OK"

    def stats_last_sets(self, scoreboard, player):
        if str(player) == "1":
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.LastSetsP1Signal.emit()
        elif str(player) == "2":
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.LastSetsP2Signal.emit()
        elif player == "both":
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.LastSetsP1Signal.emit()
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.LastSetsP2Signal.emit()
        else:
            logger.error(
                "[Last Sets] Unable to find player defined. Allowed values are: 1, 2, or both")
        return "OK"

    @gui_thread_sync
    def stats_history_sets(self, scoreboard, player):
        if str(player) == "1":
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.PlayerHistoryStandingsP1Signal.emit()
        elif str(player) == "2":
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.PlayerHistoryStandingsP2Signal.emit()
        elif player == "both":
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.PlayerHistoryStandingsP1Signal.emit()
            self.scoreboard.GetScoreboard(
                scoreboard).stats.signals.PlayerHistoryStandingsP2Signal.emit()
        else:
            logger.error(
                "[History Standings] Unable to find player defined. Allowed values are: 1, 2, or both")
        return "OK"

    @gui_thread_sync
    def reset_scores(self, scoreboard):
        self.scoreboard.GetScoreboard(scoreboard).ResetScore()
        return "OK"

    @gui_thread_sync
    def reset_match(self, scoreboard):
        self.scoreboard.GetScoreboard(scoreboard).ClearScore()
        self.scoreboard.GetScoreboard(scoreboard).scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        return "OK"

    @gui_thread_sync
    def reset_players(self, scoreboard):
        self.scoreboard.GetScoreboard(scoreboard).CommandClearAll()
        return "OK"

    @gui_thread_sync
    def clear_all(self, scoreboard):
        self.scoreboard.GetScoreboard(scoreboard).ClearScore()
        self.scoreboard.GetScoreboard(scoreboard).scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        self.scoreboard.GetScoreboard(scoreboard).playerNumber.setValue(1)
        self.scoreboard.GetScoreboard(scoreboard).charNumber.setValue(1)
        self.scoreboard.GetScoreboard(scoreboard).CommandClearAll()
        return "OK"

    @gui_thread_sync
    def get_thumbnail(self, scoreboard, file_format):
        thumbnailPath = self.scoreboard.GetScoreboard(scoreboard).GenerateThumbnail(quiet_mode=True, disable_msgbox=True)
        if thumbnailPath:
            if file_format == "jpg":
                thumbnailPath = thumbnailPath.replace(".png", ".jpg")
            return os.path.abspath(thumbnailPath)
        else:
            return None

    @gui_thread_sync
    def update_bracket(self):
        id = TSHTournamentDataProvider.instance.provider.GetTournamentPhases()[0].get("groups")[0].get("id")
        data = TSHTournamentDataProvider.instance.provider.GetTournamentPhaseGroup(id)
        TSHTournamentDataProvider.instance.signals.tournament_phasegroup_updated.emit(data)
        return "OK"

    @gui_thread_sync
    def load_set(self, scoreboard, set=None, no_mains=False):
        if set is not None:
            if not isinstance(set, str):
                set = '0'
            self.scoreboard.GetScoreboard(scoreboard).signals.NewSetSelected.emit(
                orjson.loads(
                    orjson.dumps({
                        'id': set,
                        'auto_update': "set",
                        'no_mains': no_mains
                    })
                )
            )
        return "OK"

    def get_comms(self):
        return StateManager.Get("commentary")

    def get_set(self, scoreboard):
        if self.scoreboard.GetScoreboard(scoreboard).lastSetSelected is None:
            return "0"
        else:
            return str(self.scoreboard.GetScoreboard(scoreboard).lastSetSelected)

    def get_sets(self, args):
        provider = TSHTournamentDataProvider.instance.GetProvider()
        if provider is None:
            return []

        if args.get('getFinished') is not None:
            sets = provider.GetMatches(getFinished=True)
            return sets
        else:
            sets = provider.GetMatches(getFinished=False)
            return sets

    def get_playerdb(self):
        return TSHPlayerDB.database

    def get_match(self, setId=None):
        provider = TSHTournamentDataProvider.instance.GetProvider()
        return provider.GetMatch(setId=int(setId))

    @gui_thread_sync
    def load_player_from_tag(self, scoreboard, tag, team, player, no_mains=False):
        result = self.scoreboard.GetScoreboard(scoreboard).LoadPlayerFromTag(str(tag), int(team), int(player), no_mains)
        if result == True:
            return "OK"
        else:
            return "ERROR"

    def load_commentator_from_tag(self, index, tag, no_mains=False):
        index = int(index) - 1
        if index < 0:
            return "ERROR : index can't be lower than 1" 
        result = self.commentaryWidget.LoadCommFromTagSignal.emit(index, tag, no_mains)

    def load_tournament(self, url=None):
        logger.error(f"URL PROVIDED: {url}")
        if url is None or url == "":
            TSHTournamentDataProvider.instance.signals.tournament_url_update.emit(None)
            return "OK"
        else:
            validators = [
                QRegularExpression("start.gg/tournament/[^/]+/event[s]?/[^/]+")
            ]

            for validator in validators:
                    match = validator.match(url).capturedTexts()
                    if len(match) > 0:
                        continue
            
            if "start.gg" in url:
                matches = re.match(
                    "(.*start.gg/tournament/[^/]*/event[s]?/[^/]*)", url)
                if matches:
                    url = matches.group(0)

                    # Some URLs in startgg have eventS but the API doesn't work with that format
                    url = url.replace("/events/", "/event/")

            SettingsManager.Set("TOURNAMENT_URL", url)
            TSHTournamentDataProvider.instance.signals.tournament_url_update.emit(url)
            
            return "OK"

    @gui_thread_sync
    def get_states(self, countryCode: str):
        return TSHCountryHelper.GetStates(countryCode)
