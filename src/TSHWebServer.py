import html
import os
import traceback
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from flask import Flask, send_from_directory, request, send_file
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
import orjson
from loguru import logger
from .TSHWebServerActions import WebServerActions
from .TSHScoreboardManager import TSHScoreboardManager
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHCommentaryWidget import TSHCommentaryWidget
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
        # Uncomment to enable SocketIO logging (As logging is unuseful, we'll make this a dev flag)
        # logger=logger,
        async_mode='threading'
    )
    app.config['CORS_HEADERS'] = 'Content-Type'
    actions = None

    def __init__(self, parent=None, stageWidget=None, commentaryWidget: TSHCommentaryWidget=None) -> None:
        super().__init__(parent)
        WebServer.actions = WebServerActions(
            parent=parent,
            scoreboard=TSHScoreboardManager.instance,
            stageWidget=stageWidget,
            commentaryWidget=commentaryWidget
        )
        self.host_name = "0.0.0.0"
        self.port = 5000
        
    @app.route('/program-state')
    def program_state():
        return WebServer.actions.program_state()

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
        emit('stage_strike_stage_clicked',
             WebServer.actions.stage_clicked(message))

    @app.route('/stage_strike_confirm_clicked', methods=['POST'])
    def confirm_clicked():
        return WebServer.actions.confirm_clicked()

    @socketio.on('stage_strike_confirm_clicked')
    def ws_confirm_clicked(message):
        emit('stage_strike_confirm_clicked',
             WebServer.actions.confirm_clicked())

    @app.route('/stage_strike_rps_win', methods=['POST'])
    def rps_win():
        return WebServer.actions.rps_win(orjson.loads(request.get_data()).get("winner"))

    @socketio.on('stage_strike_rps_win')
    def ws_rps_win(message):
        emit('stage_strike_rps_win', WebServer.actions.rps_win(
            orjson.loads(message).get("winner")))

    @app.route('/stage_strike_match_win', methods=['POST'])
    def match_win():
        return WebServer.actions.match_win(orjson.loads(request.get_data()).get("winner"))

    @socketio.on('stage_strike_match_win')
    def ws_match_win(message):
        emit('stage_strike_match_win', WebServer.actions.match_win(
            orjson.loads(message).get("winner")))

    @app.route('/stage_strike_set_gentlemans', methods=['POST'])
    def set_gentlemans():
        return WebServer.actions.set_gentlemans(orjson.loads(request.get_data()).get("value"))

    @socketio.on('stage_strike_set_gentlemans')
    def ws_set_gentlemans(message):
        emit('stage_strike_set_gentlemans', WebServer.actions.set_gentlemans(
            orjson.loads(message).get("value")))

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
        info = orjson.loads(message)
        emit('team_scoreup',
             WebServer.actions.team_scoreup(info.get("scoreboardNumber", "1"), info.get("team")))

    # Ticks score of Team specified down by 1 point
    @app.route('/scoreboard<scoreboardNumber>-team<team>-scoredown')
    def team_scoredown(scoreboardNumber, team):
        return WebServer.actions.team_scoredown(scoreboardNumber, team)

    @socketio.on('team_scoredown')
    def ws_team_scoredown(message):
        info = orjson.loads(message)
        emit('team_scoredown',
             WebServer.actions.team_scoredown(info.get("scoreboardNumber", "1"), info.get("team")))

    # Set color of team
    @app.route('/scoreboard<scoreboardNumber>-team<team>-color-<color>')
    def team_color(scoreboardNumber, team, color):
        return WebServer.actions.team_color(scoreboardNumber, team, "#" + color)

    @socketio.on('team_color')
    def ws_team_color(message):
        info = orjson.loads(message)
        emit('team_scoredown',
             WebServer.actions.team_color(info.get("scoreboardNumber", "1"), info.get("team"), "#" + info.get("color")))

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
        parsed = orjson.loads(message)
        emit('set', WebServer.actions.set_route(
            parsed.get("scoreboardNumber", "1"),
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
        data = orjson.loads(message)
        emit('update_team',
             WebServer.actions.set_team_data(
                 data.get("scoreboardNumber", "1"),
                 data.get("team"),
                 data.get("player"),
                 data
            ))

    @app.post('/update-commentary-<caster>')
    def set_commentary_data(caster):
        data = request.get_json()
        return WebServer.actions.set_commentary_data(caster, data)
    
    @socketio.on('update_commentary')
    def ws_set_commentary_data(message):
        data = orjson.loads(message)
        emit('update_commentary', 
            WebServer.actions.set_commentary_data(
                data.get("commentator"),
                data
            ))

    # Get characters
    @app.route('/characters')
    def get_characters():
        return WebServer.actions.get_characters()

    @socketio.on('characters')
    def ws_get_characters(message):
        emit('characters', WebServer.actions.get_characters(), json=True)

    # Get variants
    @app.route('/variants')
    def get_variants():
        return WebServer.actions.get_variants()

    @socketio.on('variants')
    def ws_get_variants(message):
        emit('variants', WebServer.actions.get_variants(), json=True)

    # Get controllers
    @app.route('/controllers')
    def get_controllers():
        return WebServer.actions.get_controllers()

    @socketio.on('controllers')
    def ws_get_controllers(message):
        emit('controllers', WebServer.actions.get_controllers(), json=True)

    # Swaps teams
    @app.route('/scoreboard<scoreboardNumber>-swap-teams')
    def swap_teams(scoreboardNumber):
        return WebServer.actions.swap_teams(scoreboardNumber)

    @socketio.on('swap_teams')
    def ws_swap_teams(message):
        info = orjson.loads(message)
        emit('swap_teams', WebServer.actions.swap_teams(
            info.get("scoreboardNumber", "1")))

    # Are the teams currently swapped?
    @app.route('/scoreboard<scoreboardNumber>-get-swap')
    def get_swap(scoreboardNumber):
        return WebServer.actions.get_swap(scoreboardNumber)

    @socketio.on('get_swap')
    def ws_get_swap(message):
        info = orjson.loads(message)
        emit('get_swap', WebServer.actions.get_swap(
            info.get("scoreboardNumber", "1")))

    # Opens Set Selector Window
    @app.route('/scoreboard<scoreboardNumber>-open-set')
    def open_sets(scoreboardNumber):
        return WebServer.actions.open_sets(scoreboardNumber)

    @socketio.on('open_set')
    def ws_open_sets(message):
        info = orjson.loads(message)
        emit('open_set', WebServer.actions.open_sets(
            info.get("scoreboardNumber", "1")))

    # Pulls Current Stream Set
    @app.route('/scoreboard<scoreboardNumber>-pull-stream')
    def pull_stream_set(scoreboardNumber):
        return WebServer.actions.pull_stream_set(scoreboardNumber)

    @socketio.on('pull_stream')
    def ws_pull_stream_set(message):
        info = orjson.loads(message)
        emit('pull_stream', WebServer.actions.pull_stream_set(
            info.get("scoreboardNumber", "1")))

    # Pulls Current User Set
    @app.route('/pull-user')
    def pull_user_set():
        return WebServer.actions.pull_user_set()

    @socketio.on('pull_user')
    def ws_pull_user_set(message):
        info = orjson.loads(message)
        emit('pull_user', WebServer.actions.pull_user_set(
            info.get("scoreboardNumber", "1")))

    # Resubmits Call for Recent Sets
    @app.route('/scoreboard<scoreboardNumber>-stats-recent-sets')
    def stats_recent_sets(scoreboardNumber):
        return WebServer.actions.stats_recent_sets(scoreboardNumber)

    @socketio.on('stats_recent_sets')
    def ws_stats_recent_sets(message):
        info = orjson.loads(message)
        emit('stats_recent_sets',
             WebServer.actions.stats_recent_sets(info.get("scoreboardNumber", "1"), info.get("player")))

    # Resubmits Call for Upset Factor
    @app.route('/scoreboard<scoreboardNumber>-stats-upset-factor')
    def stats_upset_factor(scoreboardNumber):
        return WebServer.actions.stats_upset_factor(scoreboardNumber)

    @socketio.on('stats_upset_factor')
    def ws_stats_upset_factor(message):
        info = orjson.loads(message)
        emit('stats_upset_factor',
             WebServer.actions.stats_upset_factor(info.get("scoreboardNumber", "1"), info.get("player")))

    # Resubmits Call for Last Sets
    @app.route('/scoreboard<scoreboardNumber>-stats-last-sets-<player>')
    def stats_last_sets(scoreboardNumber, player):
        return WebServer.actions.stats_last_sets(scoreboardNumber, player)

    @socketio.on('stats_last_sets')
    def ws_stats_last_sets(message):
        info = orjson.loads(message)
        emit('stats_last_sets',
             WebServer.actions.stats_last_sets(info.get("scoreboardNumber", "1"), info.get("player")))

   # Resubmits Call for History Sets
    @app.route('/scoreboard<scoreboardNumber>-stats-history-sets-<player>')
    def stats_history_sets(scoreboardNumber, player):
        return WebServer.actions.stats_history_sets(scoreboardNumber, player)

    @socketio.on('stats_history_sets')
    def ws_stats_history_sets(message):
        info = orjson.loads(message)
        emit('stats_history_sets',
             WebServer.actions.stats_history_sets(info.get("scoreboardNumber", "1"), info.get("player")))

    # Resets scores
    @app.route('/scoreboard<scoreboardNumber>-reset-scores')
    def reset_scores(scoreboardNumber):
        return WebServer.actions.reset_scores(scoreboardNumber)

    @socketio.on('reset_scores')
    def ws_reset_scores(message):
        info = orjson.loads(message)
        emit('reset_scores',
             WebServer.actions.reset_scores(info.get("scoreboardNumber", "1")))

    # Resets scores, match, phase, and losers status
    @app.route('/scoreboard<scoreboardNumber>-reset-match')
    def reset_match(scoreboardNumber):
        return WebServer.actions.reset_match(scoreboardNumber)

    @socketio.on('reset_match')
    def ws_reset_match(message):
        info = orjson.loads(message)
        emit('reset_match',
             WebServer.actions.reset_match(info.get("scoreboardNumber", "1")))

    # Resets scores, match, phase, and losers status
    @app.route('/scoreboard<scoreboardNumber>-reset-players')
    def reset_players(scoreboardNumber):
        return WebServer.actions.reset_players(scoreboardNumber)

    @socketio.on('reset_players')
    def ws_reset_players(message):
        info = orjson.loads(message)
        emit('reset_players',
             WebServer.actions.reset_players(info.get("scoreboardNumber", "1")))

    # Resets all values
    @app.route('/scoreboard<scoreboardNumber>-clear-all')
    def clear_all(scoreboardNumber):
        return WebServer.actions.clear_all(scoreboardNumber)

    @socketio.on('clear_all')
    def ws_clear_all(message):
        info = orjson.loads(message)
        emit('clear_all',
             WebServer.actions.clear_all(info.get("scoreboardNumber", "1")))
        
    # Get thumbnail
    @app.route('/scoreboard<scoreboardNumber>-get-thumbnail-<fileFormat>')
    def get_thumbnail(scoreboardNumber, fileFormat):
        if fileFormat.lower() in ["png", "jpg"]:
            result = WebServer.actions.get_thumbnail(scoreboardNumber, fileFormat.lower())
            if result:
                return send_file(result, mimetype=f"image/{fileFormat.lower()}")
            else:
                return "An error has occured, please check TSH logs for more information"
        else:
            return f"File format {fileFormat} not recognized"

    # Get the sets to be played
    @app.route('/get-sets')
    def get_sets():
        return WebServer.actions.get_sets(request.args)

    @socketio.on('get_sets')
    def ws_get_sets(message):
        emit('get_sets', WebServer.actions.get_sets(orjson.loads(message)))
        
    # Loads info on a match
    @app.route('/get-match-<setId>')
    def get_match(setId):
        return WebServer.actions.get_match(setId)

    @socketio.on('get_match')
    def ws_get_match(message):
        info = orjson.loads(message)
        emit('get_match', WebServer.actions.get_match(info.get("setId")))

    # Get the commentators
    @app.route('/get-comms')
    def get_comms():
        return WebServer.actions.get_comms()

    @socketio.on('get_comms')
    def ws_get_comms():
        emit('get_comms', WebServer.actions.get_comms())

    # Loads a set remotely by providing a set ID to pull from the data provider
    @app.route('/scoreboard<scoreboardNumber>-load-set')
    def load_set(scoreboardNumber):
        if request.args.get('no-mains') is not None:
            return WebServer.actions.load_set(scoreboardNumber, request.args.get("set"), no_mains=True)
        else:
            return WebServer.actions.load_set(scoreboardNumber, request.args.get("set"))

    @socketio.on('load_set')
    def ws_load_set(message):
        info = orjson.loads(message)
        if info.get('no-mains') is not None:
            emit('load_set', WebServer.actions.load_set(
                info.get("scoreboardNumber", "1"), info.get("set"), no_mains=True))
        else:
            emit('load_set', WebServer.actions.load_set(
                info.get("scoreboardNumber", "1"), info.get("set")))

    # Loads a set remotely by providing a set ID to pull from the data provider
    @app.route('/scoreboard<scoreboardNumber>-get-set')
    def get_set(scoreboardNumber):
        return WebServer.actions.get_set(scoreboardNumber)

    @socketio.on('get_set')
    def ws_get_set(message):
        emit('get_set', WebServer.actions.get_set(
            orjson.loads(message).get('scoreboardNumber', '1')))

    # Update bracket
    @app.route('/update-bracket')
    def update_bracket():
        return WebServer.actions.update_bracket()

    @socketio.on('update_bracket')
    def ws_update_bracket(message):
        emit('update_bracket', WebServer.actions.update_bracket())

    # Load player from tag
    @app.route('/scoreboard<scoreboardNumber>-load-player-from-tag-<team>-<player>')
    def load_player_from_tag(scoreboardNumber, team, player):
        if request.args.get('tag') is None:
            return "No tag provided"
        no_mains = request.args.get('no-mains') is not None
        return WebServer.actions.load_player_from_tag(scoreboardNumber, html.unescape(request.args.get('tag')), team, player, no_mains)

    @socketio.on('load_player_from_tag')
    def ws_load_player_from_tag(message):
        args = orjson.loads(message)
        if args.get('tag') is None:
            emit('load_player_from_tag', 'No tag provided')
            return
        no_mains = args.get('no-mains') is not None
        team = args.get('team')
        player = args.get('player')
        scoreboardNumber = args.get('scoreboardNumber', '1')
        emit('load_player_from_tag', WebServer.actions.load_player_from_tag(
            scoreboardNumber, html.unescape(args.get('tag')), team, player, no_mains))

    @app.route('/load-commentator-from-tag-<caster>')
    def load_commentator_from_tag(caster):
        if request.args.get('tag') is None:
            return "No tag provided"
        no_mains = request.args.get('no-mains') is not None
        return WebServer.actions.load_commentator_from_tag(caster, html.unescape(request.args.get('tag')), no_mains)

    @socketio.on('load_commentator_from_tag')
    def ws_load_commentator_from_tag(message):
        args = orjson.loads(message)
        if args.get('tag') is None:
            emit('load_commentator_from_tag', 'No tag provided')
            return
        no_mains = args.get('no-mains') is not None
        caster = args.get('commentator')
        emit('load_commentator_from_tag', WebServer.actions.load_commentator_from_tag(caster, html.unescape(args.get('tag')), no_mains))

    # Update bracket
    @app.route('/set-tournament')
    def set_tournament():
        return WebServer.actions.load_tournament(request.args.get('url'))

    @socketio.on('set_tournament')
    def ws_set_tournament(message):
        emit('set_tournament', WebServer.actions.load_tournament(request.args.get('url')))

    @app.route('/', defaults=dict(filename=None))
    @app.route('/<path:filename>', methods=['GET', 'POST'])
    @cross_origin()
    def test(filename):
        try:
            filename = filename or 'stage_strike_app/build/index.html'
            return send_from_directory(os.path.abspath('.'), filename, as_attachment=filename.endswith('.gz'))
        except Exception as e:
            logger.error(f"File not found: {e}")

    def run(self):
        try:
            self.socketio.run(app=self.app, host=self.host_name, port=self.port,
                              debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
        except Exception as e:
            logger.error(traceback.format_exc())
