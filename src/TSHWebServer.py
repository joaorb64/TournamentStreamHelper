import os
import traceback
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from flask import Flask, send_from_directory, request
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
import json
from loguru import logger
from .TSHWebServerActions import WebServerActions
from .TSHScoreboardManager import TSHScoreboardManager
import traceback

import logging
log = logging.getLogger('socketio.server')
log.setLevel(logging.ERROR)


class WebServer(QThread):
    app = Flask(__name__, static_folder=os.path.curdir)
    cors = CORS(app)
    socketio = SocketIO(
        app,
        cors_allowed_origins='*',
        #Uncomment to enable SocketIO logging (As logging is unuseful, we'll make this a dev flag)
        #logger=logger,
        async_mode='threading'
    )
    app.config['CORS_HEADERS'] = 'Content-Type'
    actions = None

    def __init__(self, parent=None, stageWidget=None) -> None:
        super().__init__(parent)
        WebServer.actions = WebServerActions(
            parent=parent,
            scoreboard=TSHScoreboardManager.instance,
            stageWidget=stageWidget
        )
        self.host_name = "0.0.0.0"
        self.port = 5000

    @socketio.on('connect')
    def ws_connect(message):
        emit('program_state', WebServer.actions.program_state(), json=True)

    @socketio.on_error_default
    def ws_on_error(e):
        logger.error(traceback.format_exc()) 

    def emit(self, event, *args, **kwargs):
        WebServer.socketio.emit(event, *args, **kwargs)

    @app.route('/ruleset')
    def ruleset():
        return WebServer.actions.ruleset()

    @socketio.on('ruleset')
    def ws_ruleset(message):
        emit('ruleset', WebServer.actions.ruleset(), json=True)

    @app.route('/stage_strike_stage_clicked', methods=['POST'])
    def stage_clicked():
        return WebServer.actions.stage_clicked(request.get_data())

    @socketio.on('stage_strike_stage_clicked')
    def ws_stage_clicked(message):
        emit('stage_strike_stage_clicked', WebServer.actions.stage_clicked(message))

    @app.route('/stage_strike_confirm_clicked', methods=['POST'])
    def confirm_clicked():
        return WebServer.actions.confirm_clicked()

    @socketio.on('stage_strike_confirm_clicked')
    def ws_confirm_clicked(message):
        emit('stage_strike_confirm_clicked', WebServer.actions.confirm_clicked())

    @app.route('/stage_strike_rps_win', methods=['POST'])
    def rps_win():
        return WebServer.actions.rps_win(json.loads(request.get_data()).get("winner"))

    @socketio.on('stage_strike_rps_win')
    def ws_rps_win(message):
        emit('stage_strike_rps_win', WebServer.actions.rps_win(json.loads(message).get("winner")))

    @app.route('/stage_strike_match_win', methods=['POST'])
    def match_win():
        return WebServer.actions.match_win(json.loads(request.get_data()).get("winner"))

    @socketio.on('stage_strike_match_win')
    def ws_match_win(message):
        emit('stage_strike_match_win', WebServer.actions.match_win(json.loads(message).get("winner")))

    @app.route('/stage_strike_set_gentlemans', methods=['POST'])
    def set_gentlemans():
        return WebServer.actions.set_gentlemans(json.loads(request.get_data()).get("value"))

    @socketio.on('stage_strike_set_gentlemans')
    def ws_set_gentlemans(message):
        emit('stage_strike_set_gentlemans', WebServer.actions.set_gentlemans(json.loads(message).get("value")))

    @app.route('/stage_strike_undo', methods=['POST'])
    def stage_strike_undo():
        return WebServer.actions.stage_strike_undo()

    @socketio.on('stage_strike_undo')
    def ws_stage_strike_undo(message):
        emit('stage_strike_undo', WebServer.actions.stage_strike_undo())

    @app.route('/stage_strike_redo', methods=['POST'])
    def stage_strike_redo():
        return WebServer.actions.stage_strike_redo()

    @socketio.on('stage_strike_redo')
    def ws_stage_strike_redo(message):
        emit('stage_strike_redo', WebServer.actions.stage_strike_redo())

    @app.route('/stage_strike_reset', methods=['POST'])
    def reset():
        return WebServer.actions.reset()

    @socketio.on('stage_strike_reset')
    def ws_reset(message):
        emit('stage_strike_reset', WebServer.actions.reset())

    @app.route('/score', methods=['POST'])
    def post_score():
        return WebServer.actions.post_score(request.get_data())

    @socketio.on('score')
    def ws_post_score(message):
        emit('score', WebServer.actions.post_score(message))

    # Ticks score of Team specified up by 1 point
    @app.route('/scoreboard<scoreboardNumber>-team<team>-scoreup')
    def team_scoreup(scoreboardNumber, team):
        return WebServer.actions.team_scoreup(scoreboardNumber, team)

    @socketio.on('team_scoreup')
    def ws_team_scoreup(message):
        info = json.loads(message)
        emit('team_scoreup',
            WebServer.actions.team_scoreup(info.get("scoreboardNumber"), info.get("team")))

    # Ticks score of Team specified down by 1 point
    @app.route('/scoreboard<scoreboardNumber>-team<team>-scoredown')
    def team_scoredown(scoreboardNumber, team):
        return WebServer.actions.team_scoredown(team)

    @socketio.on('team_scoredown')
    def ws_team_scoredown(message):
        info = json.loads(message)
        emit('team_scoredown',
            WebServer.actions.team_scoredown(info.get("scoreboardNumber"), info.get("team")))

    # Dynamic endpoint to allow flexible sets of information
    # Ex. http://192.168.1.2:5000/set?best-of=5
    #
    # Test Scenario that was used
    # Ex. http://192.168.4.34:5000/set?best-of=5&phase=Top 32&match=Winners Finals
    @app.route('/scoreboard<scoreboardNumber>-set')
    def set_route(scoreboardNumber):
        return WebServer.actions.set_route(
            scoreboardNumber,
            bestOf=request.args.get('best-of'),
            phase=request.args.get('phase'),
            match=request.args.get('match'),
            players=request.args.get('players'),
            characters=request.args.get('characters'),
            losers=request.args.get('losers'),
            team=request.args.get('team')
        )

    @socketio.on('set')
    def ws_set_route(message):
        parsed = json.loads(message)
        emit('set', WebServer.actions.set_route(
            parsed.get("scoreboardNumber"),
            bestOf=parsed.get('best_of'),
            phase=parsed.get('phase'),
            match=parsed.get('match'),
            players=parsed.get('players'),
            characters=parsed.get('characters'),
            losers=parsed.get('losers'),
            team=parsed.get('team')
        ))

    # Set player data
    @app.post('/scoreboard<scoreboardNumber>-update-team-<team>-<player>')
    def set_team_data(scoreboardNumber, team, player):
        data = request.get_json()
        return WebServer.actions.set_team_data(scoreboardNumber, team, player, data)
    
    @socketio.on('update_team')
    def ws_set_team_data(message):
        data = json.loads(message)
        emit('update_team',
            WebServer.actions.set_team_data(
                data.get("scoreboardNumber"),
                data.get("team"),
                data.get("player"),
                data
            ))

    # Get characters
    @app.route('/characters')
    def get_characters():
        return WebServer.actions.get_characters()
    
    @socketio.on('characters')
    def ws_get_characters(message):
        emit('characters', WebServer.actions.get_characters(), json=True)

    # Swaps teams
    @app.route('/scoreboard<scoreboardNumber>-swap-teams')
    def swap_teams(scoreboardNumber):
        return WebServer.actions.swap_teams(scoreboardNumber)
    
    @socketio.on('swap_teams')
    def ws_swap_teams(message):
        info = json.loads(message)
        emit('swap_teams', WebServer.actions.swap_teams(info.get("scoreboardNumber")))

    # Opens Set Selector Window
    @app.route('/scoreboard<scoreboardNumber>-open-set')
    def open_sets(scoreboardNumber):
        return WebServer.actions.open_sets(scoreboardNumber)
    
    @socketio.on('open_set')
    def ws_open_sets(message):
        info = json.loads(message)
        emit('open_set', WebServer.actions.open_sets(info.get("scoreboardNumber")))

    # Pulls Current Stream Set
    @app.route('/scoreboard<scoreboardNumber>-pull-stream')
    def pull_stream_set(scoreboardNumber):
        return WebServer.actions.pull_stream_set(scoreboardNumber)
    
    @socketio.on('pull_stream')
    def ws_pull_stream_set(message):
        info = json.loads(message)
        emit('pull_stream', WebServer.actions.pull_stream_set(info.get("scoreboardNumber")))

    # Pulls Current User Set
    @app.route('/pull-user')
    def pull_user_set():
        return WebServer.actions.pull_user_set()
    
    @socketio.on('pull_user')
    def ws_pull_user_set(message):
        info = json.loads(message)
        emit('pull_user', WebServer.actions.pull_user_set(info.get("scoreboardNumber")))

    # Resubmits Call for Recent Sets
    @app.route('/scoreboard<scoreboardNumber>-stats-recent-sets')
    def stats_recent_sets(scoreboardNumber):
        return WebServer.actions.stats_recent_sets(scoreboardNumber)
    
    @socketio.on('stats_recent_sets')
    def ws_stats_recent_sets(message):
        info = json.loads(message)
        emit('stats_recent_sets',
            WebServer.actions.stats_recent_sets(info.get("scoreboardNumber"), info.get("player")))

    # Resubmits Call for Upset Factor
    @app.route('/scoreboard<scoreboardNumber>-stats-upset-factor')
    def stats_upset_factor(scoreboardNumber):
        return WebServer.actions.stats_upset_factor(scoreboardNumber)
    
    @socketio.on('stats_upset_factor')
    def ws_stats_upset_factor(message):
        info = json.loads(message)
        emit('stats_upset_factor',
            WebServer.actions.stats_upset_factor(info.get("scoreboardNumber"), info.get("player")))

    # Resubmits Call for Last Sets
    @app.route('/scoreboard<scoreboardNumber>-stats-last-sets-<player>')
    def stats_last_sets(scoreboardNumber, player):
        return WebServer.actions.stats_last_sets(scoreboardNumber, player)
    
    @socketio.on('stats_last_sets')
    def ws_stats_last_sets(message):
        info = json.loads(message)
        emit('stats_last_sets',
            WebServer.actions.stats_last_sets(info.get("scoreboardNumber"), info.get("player")))

   # Resubmits Call for History Sets
    @app.route('/scoreboard<scoreboardNumber>-stats-history-sets-<player>')
    def stats_history_sets(scoreboardNumber, player):
        return WebServer.actions.stats_history_sets(scoreboardNumber, player)
    
    @socketio.on('stats_history_sets')
    def ws_stats_history_sets(message):
        info = json.loads(message)
        emit('stats_history_sets',
            WebServer.actions.stats_history_sets(info.get("scoreboardNumber"), info.get("player")))

    # Resets scores
    @app.route('/scoreboard<scoreboardNumber>-reset-scores')
    def reset_scores(scoreboardNumber):
        return WebServer.actions.reset_scores(scoreboardNumber)
    
    @socketio.on('reset_scores')
    def ws_reset_scores(message):
        info = json.loads(message)
        emit('reset_scores',
            WebServer.actions.reset_scores(info.get("scoreboardNumber")))

    # Resets scores, match, phase, and losers status
    @app.route('/scoreboard<scoreboardNumber>-reset-match')
    def reset_match(scoreboardNumber):
        return WebServer.actions.reset_match(scoreboardNumber)
    
    @socketio.on('reset_match')
    def ws_reset_match(message):
        info = json.loads(message)
        emit('reset_match',
            WebServer.actions.reset_match(info.get("scoreboardNumber")))

    # Resets scores, match, phase, and losers status
    @app.route('/scoreboard<scoreboardNumber>-reset-players')
    def reset_players(scoreboardNumber):
        return WebServer.actions.reset_players(scoreboardNumber)
    
    @socketio.on('reset_players')
    def ws_reset_players(message):
        info = json.loads(message)
        emit('reset_players',
            WebServer.actions.reset_players(info.get("scoreboardNumber")))

    # Resets all values
    @app.route('/scoreboard<scoreboardNumber>-clear-all')
    def clear_all(scoreboardNumber):
        return WebServer.actions.clear_all(scoreboardNumber)
    
    @socketio.on('clear_all')
    def ws_clear_all(message):
        info = json.loads(message)
        emit('clear_all',
            WebServer.actions.clear_all(info.get("scoreboardNumber")))

    # Loads a set remotely by providing a set ID to pull from the data provider
    @app.route('/scoreboard<scoreboardNumber>-load-set')
    def load_set(scoreboardNumber):
        return WebServer.actions.load_set(scoreboardNumber, request.args.get("set"))

    @socketio.on('load_set')
    def ws_load_set(message):
        info = json.loads(message)
        emit('load_set',
            WebServer.actions.load_set(info.get("scoreboardNumber"), info.get("set")))

    @app.route('/', defaults=dict(filename=None))
    @app.route('/<path:filename>', methods=['GET', 'POST'])
    @cross_origin()
    def test(filename):
        filename = filename or 'stage_strike_app/build/index.html'
        return send_from_directory(os.path.abspath("."), filename, as_attachment=filename.endswith(".gz"))

    def run(self):
        try:
            self.socketio.run(app=self.app, host=self.host_name, port=self.port,
                          debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
        except Exception as e:
            logger.error(traceback.format_exc())

