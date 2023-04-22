import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from flask import Flask, send_from_directory, request
from flask_cors import CORS, cross_origin
import json
from .StateManager import StateManager
from .TSHStatsUtil import TSHStatsUtil


class WebServer(QThread):
    app = Flask(__name__, static_folder=os.path.curdir)
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    scoreboard = None

    def __init__(self, parent=None, scoreboard=None, stageWidget=None) -> None:
        super().__init__(parent)
        WebServer.scoreboard = scoreboard
        WebServer.stageWidget = stageWidget
        self.host_name = "0.0.0.0"
        self.port = 5000

    @app.route("/ruleset")
    def main():
        data = {}

        data["ruleset"] = StateManager.Get(f"score.ruleset", {})

        # Add webserver base path
        data.update({
            "basedir": os.path.abspath(".")
        })

        # Add player names
        teams = [1, 2]
        if WebServer.scoreboard.teamsSwapped:
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

    @app.route('/stage_strike_stage_clicked', methods=['POST'])
    def stage_clicked():
        WebServer.stageWidget.stageStrikeLogic.StageClicked(json.loads(request.get_data()))
        return "OK"
    
    @app.route('/stage_strike_confirm_clicked', methods=['POST'])
    def confirm_clicked():
        WebServer.stageWidget.stageStrikeLogic.ConfirmClicked()
        return "OK"
    
    @app.route('/stage_strike_rps_win', methods=['POST'])
    def rps_win():
        WebServer.stageWidget.stageStrikeLogic.RpsResult(int(json.loads(request.get_data()).get("winner")))
        return "OK"
    
    @app.route('/stage_strike_match_win', methods=['POST'])
    def match_win():
        WebServer.stageWidget.stageStrikeLogic.MatchWinner(int(json.loads(request.get_data()).get("winner")))
        WebServer.UpdateScore()
        return "OK"

    @app.route('/stage_strike_set_gentlemans', methods=['POST'])
    def set_gentlemans():
        WebServer.stageWidget.stageStrikeLogic.SetGentlemans(json.loads(request.get_data()).get("value"))
        return "OK"

    @app.route('/stage_strike_undo', methods=['POST'])
    def stage_strike_undo():
        WebServer.stageWidget.stageStrikeLogic.Undo()
        WebServer.UpdateScore()
        return "OK"

    @app.route('/stage_strike_redo', methods=['POST'])
    def stage_strike_redo():
        WebServer.stageWidget.stageStrikeLogic.Redo()
        WebServer.UpdateScore()
        return "OK"
    
    @app.route('/stage_strike_reset', methods=['POST'])
    def reset():
        WebServer.stageWidget.stageStrikeLogic.Initialize()
        WebServer.UpdateScore()
        return "OK"

    def UpdateScore():
        score = [
            len(WebServer.stageWidget.stageStrikeLogic.CurrentState().stagesWon[0]),
            len(WebServer.stageWidget.stageStrikeLogic.CurrentState().stagesWon[1]),
        ]
        
        WebServer.scoreboard.signals.UpdateSetData.emit({
            "team1score": score[0],
            "team2score": score[1],
            "reset_score": True
        })

    @app.route('/score', methods=['POST'])
    def post_score():
        score = json.loads(request.get_data())
        score.update({"reset_score": True})
        WebServer.scoreboard.signals.UpdateSetData.emit(score)
        return "OK"

    # Ticks score of Team specified up by 1 point
    @app.route('/team<team>-scoreup')
    def team_scoreup(team):
        if team == "1":
            WebServer.scoreboard.signals.CommandScoreChange.emit(0, 1)
        else:
            WebServer.scoreboard.signals.CommandScoreChange.emit(1, 1)
        return "OK"

    # Ticks score of Team specified down by 1 point
    @app.route('/team<team>-scoredown')
    def team_scoredown(team):
        if team == "1":
            WebServer.scoreboard.signals.CommandScoreChange.emit(0, -1)
        else:
            WebServer.scoreboard.signals.CommandScoreChange.emit(1, -1)
        return "OK"

    # Dynamic endpoint to allow flexible sets of information
    # Ex. http://192.168.1.2:5000/set?best-of=5
    #
    # Test Scenario that was used
    # Ex. http://192.168.4.34:5000/set?best-of=5&phase=Top 32&match=Winners Finals
    @app.route('/set')
    def set_route():
        # Best Of argument
        # best-of=<Best Of Amount>
        if request.args.get('best-of') is not None:
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'bestOf': request.args.get(
                        'best-of', default='0', type=int)})
                )
            )

        # Phase argument
        # phase=<Phase Name>
        if request.args.get('phase') is not None:
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'tournament_phase': request.args.get(
                        'phase', default='Pools', type=str)})
                )
            )

        # Match argument
        # match=<Match Name>
        if request.args.get('match') is not None:
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'round_name': request.args.get(
                        'match', default='Pools', type=str)})
                )
            )

        # Players argument
        # players=<Amount of Players>
        if request.args.get('players') is not None:
            WebServer.scoreboard.playerNumber.setValue(
                request.args.get('players', default=1, type=int))

        # Characters argument
        # characters=<Amount of Characters>
        if request.args.get('characters') is not None:
            WebServer.scoreboard.charNumber.setValue(
                request.args.get('characters', default=1, type=int))

        # Losers argument
        # losers=<True/False>&team=<Team Number>
        if request.args.get('losers') is not None:
            losers = request.args.get('losers', default=False, type=bool)
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'team' + request.args.get('team',
                               default='1', type=str) + 'losers': bool(losers)})
                )
            )
        return "OK"

    # Swaps teams
    @app.route('/swap-teams')
    def swap_teams():
        WebServer.scoreboard.signals.SwapTeams.emit()
        return "OK"

    # Opens Set Selector Window
    @app.route('/open-set')
    def open_sets():
        WebServer.scoreboard.signals.SetSelection.emit()
        return "OK"

    # Pulls Current Stream Set
    @app.route('/pull-stream')
    def pull_stream_set():
        WebServer.scoreboard.signals.StreamSetSelection.emit()
        return "OK"

    # Pulls Current User Set
    @app.route('/pull-user')
    def pull_user_set():
        WebServer.scoreboard.signals.UserSetSelection.emit()
        return "OK"

    # Resubmits Call for Recent Sets
    @app.route('/stats-recent-sets')
    def stats_recent_sets():
        TSHStatsUtil.instance.signals.RecentSetsSignal.emit()
        return "OK"

    # Resubmits Call for Last Sets
    @app.route('/stats-last-sets-<player>')
    def stats_last_sets(player):
        if player == "1":
            TSHStatsUtil.instance.signals.LastSetsP1Signal.emit()
        elif player == "2":
            TSHStatsUtil.instance.signals.LastSetsP2Signal.emit()
        elif player == "both":
            TSHStatsUtil.instance.signals.LastSetsP1Signal.emit()
            TSHStatsUtil.instance.signals.LastSetsP2Signal.emit()
        else:
            print("[Last Sets] Unable to find player defined. Allowed values are: 1, 2, or both")
        return "OK"

   # Resubmits Call for History Sets
    @app.route('/stats-history-sets-<player>')
    def stats_history_sets(player):
        if player == "1":
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP1Signal.emit()
        elif player == "2":
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP2Signal.emit()
        elif player == "both":
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP1Signal.emit()
            TSHStatsUtil.instance.signals.PlayerHistoryStandingsP2Signal.emit()
        else:
            print("[History Standings] Unable to find player defined. Allowed values are: 1, 2, or both")
        return "OK"

    # Resets scores
    @app.route('/reset-scores')
    def reset_scores():
        WebServer.scoreboard.signals.UpdateSetData.emit({
            "team1score": 0,
            "team2score": 0
        })
        return "OK"

    # Resets scores, match, phase, and losers status
    @app.route('/reset-match')
    def reset_match():
        WebServer.scoreboard.ClearScore()
        WebServer.scoreboard.scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        return "OK"

    # Resets all values
    @app.route('/clear-all')
    def clear_all():
        WebServer.scoreboard.ClearScore()
        WebServer.scoreboard.scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        WebServer.scoreboard.playerNumber.setValue(1)
        WebServer.scoreboard.charNumber.setValue(1)
        return "OK"

    @app.route('/', defaults=dict(filename=None))
    @app.route('/<path:filename>', methods=['GET', 'POST'])
    @cross_origin()
    def test(filename):
        filename = filename or 'stage_strike_app/build/index.html'
        return send_from_directory(os.path.abspath("."), filename, as_attachment=filename.endswith(".gz"))

    def run(self):
        self.app.run(host=self.host_name, port=self.port,
                     debug=False, use_reloader=False)
