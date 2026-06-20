import requests
import traceback
from loguru import logger
from .StateManager import StateManager
from .SettingsManager import SettingsManager
from .TSHGameAssetManager import TSHGameAssetManager

STARTGG_GQL_ENDPOINT = "https://api.start.gg/gql/alpha"

ASSIGN_STREAM_MUTATION = """
mutation AssignStream($setId: ID!, $streamId: ID!) {
  assignStream(setId: $setId, streamId: $streamId) {
    id
    state
  }
}
"""

REPORT_SET_MUTATION = """
mutation ReportBracketSet($setId: ID!, $winnerId: ID!, $isDQ: Boolean, $gameData: [BracketSetGameDataInput]) {
  reportBracketSet(setId: $setId, winnerId: $winnerId, isDQ: $isDQ, gameData: $gameData) {
    id
    state
  }
}
"""


def _gql_request(api_token: str, query: str, variables: dict) -> dict:
    response = requests.post(
        STARTGG_GQL_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def AssignStream(set_id: str, stream_id: str) -> dict:
    """
    Assign a Start.gg stream to the given set so it appears in the stream queue.
    Returns a dict with keys: success (bool), message (str), data (dict or None).
    """
    api_token = SettingsManager.Get("api_keys.startgg", "")
    if not api_token:
        return {
            "success": False,
            "message": "No Start.gg API token configured.\nGo to Settings → API Keys to add your token.",
            "data": None,
        }

    try:
        variables = {"setId": str(set_id), "streamId": str(stream_id)}
        logger.info(f"AssignStream GQL request: variables={variables}")
        data = _gql_request(api_token, ASSIGN_STREAM_MUTATION, variables)
        logger.info(f"AssignStream GQL response: {data}")

        errors = data.get("errors")
        if errors:
            messages = [e.get("message", str(e)) for e in errors]
            hint = ""
            if any("unknown" in m.lower() for m in messages):
                hint = "\n\nThis usually means the stream is not registered for this event on Start.gg, or your token lacks TO permissions."
            msg = "; ".join(messages)
            return {"success": False, "message": f"Start.gg error: {msg}{hint}", "data": data}

        result = data.get("data", {}).get("assignStream")
        if result:
            return {
                "success": True,
                "message": f"Set assigned to stream successfully!\nSet ID: {result.get('id')} — State: {result.get('state')}",
                "data": data,
            }

        logger.warning(f"AssignStream: unexpected response structure: {data}")
        return {"success": False, "message": "Unexpected response from Start.gg.", "data": data}

    except requests.exceptions.HTTPError as e:
        logger.error(f"AssignStream HTTP error: {e}")
        return {"success": False, "message": f"HTTP error: {e}", "data": None}
    except Exception:
        logger.error(f"AssignStream error:\n{traceback.format_exc()}")
        return {"success": False, "message": f"Error assigning stream:\n{traceback.format_exc()}", "data": None}


def _get_character_startgg_id(char_data: dict) -> int | None:
    # Prefer the ID baked in at model-build time (correct game-specific ID).
    stored_id = char_data.get("startgg_character_id")
    if stored_id:
        return int(stored_id)
    # Fallback for older state without the field.
    codename = char_data.get("en_name") or char_data.get("codename")
    if not codename:
        return None
    return TSHGameAssetManager.instance.GetStartGGIdFromCodename(codename)


def BuildGameData(scoreboard_number: int, team1_entrant_id: str, team2_entrant_id: str) -> list:
    """
    Build per-game data list for the reportBracketSet mutation.
    team1_entrant_id / team2_entrant_id are the START.GG entrant IDs for the
    UI left (team-1) and right (team-2) sides respectively, with any team-swap
    already resolved by the caller.
    """
    best_of = StateManager.Get(f"score.{scoreboard_number}.best_of", 0) or 0
    wins_needed = (best_of // 2) + 1 if best_of > 0 else None

    games = []
    t1_wins = 0
    t2_wins = 0
    game_idx = 1
    while True:
        if wins_needed and (t1_wins >= wins_needed or t2_wins >= wins_needed):
            break

        stage = StateManager.Get(f"score.{scoreboard_number}.stages.{game_idx}")
        if stage is None:
            break

        t1_win = StateManager.Get(f"score.{scoreboard_number}.stages.{game_idx}.t1_win", False)
        t2_win = StateManager.Get(f"score.{scoreboard_number}.stages.{game_idx}.t2_win", False)

        if t1_win:
            t1_wins += 1
        elif t2_win:
            t2_wins += 1

        if not t1_win and not t2_win:
            game_idx += 1
            continue

        winner_entrant_id = team1_entrant_id if t1_win else team2_entrant_id

        game_entry = {
            "gameNum": game_idx,
            "winnerId": winner_entrant_id,
        }

        # Stage ID
        if isinstance(stage, dict) and stage.get("smashgg_id"):
            game_entry["stageId"] = stage["smashgg_id"]

        # Character selections — iterate both UI teams
        selections = []
        for team_ui_idx, entrant_id in enumerate([team1_entrant_id, team2_entrant_id], start=1):
            if not entrant_id:
                continue
            player_idx = 1
            while True:
                char_slot_data = StateManager.Get(
                    f"score.{scoreboard_number}.stages.{game_idx}.team.{team_ui_idx}.player.{player_idx}.character"
                )
                if char_slot_data is None:
                    break
                for _, char_data in char_slot_data.items():
                    if not char_data:
                        continue
                    char_id = _get_character_startgg_id(char_data)
                    if not char_id:
                        continue
                    selections.append({"entrantId": entrant_id, "characterId": char_id})
                player_idx += 1

        if selections:
            game_entry["selections"] = selections

        games.append(game_entry)
        game_idx += 1

    return games


def ReportSet(
    scoreboard_number: int,
    is_dq: bool = False,
    set_id=None,
    entrant1_id: str = None,
    entrant2_id: str = None,
) -> dict:
    """
    Report the current set result to Start.gg.
    set_id / entrant1_id / entrant2_id can be passed directly (e.g. after name-based resolution);
    if omitted they are read from StateManager.
    Returns a dict with keys: success (bool), message (str), data (dict or None).
    """
    api_token = SettingsManager.Get("api_keys.startgg", "")
    if not api_token:
        return {
            "success": False,
            "message": "No Start.gg API token configured.\nGo to Settings → API Keys to add your token.",
            "data": None,
        }

    if set_id is None:
        set_id = StateManager.Get(f"score.{scoreboard_number}.set_id")
    if entrant1_id is None:
        entrant1_id = StateManager.Get(f"score.{scoreboard_number}.entrant1_id", "") or ""
    if entrant2_id is None:
        entrant2_id = StateManager.Get(f"score.{scoreboard_number}.entrant2_id", "") or ""

    teams_swapped = StateManager.Get(f"score.{scoreboard_number}.teamsSwapped", False)

    # Map UI positions to entrant IDs
    if not teams_swapped:
        ui_team1_entrant = entrant1_id
        ui_team2_entrant = entrant2_id
    else:
        ui_team1_entrant = entrant2_id
        ui_team2_entrant = entrant1_id

    team1_score = StateManager.Get(f"score.{scoreboard_number}.team.1.score", 0) or 0
    team2_score = StateManager.Get(f"score.{scoreboard_number}.team.2.score", 0) or 0

    if team1_score == team2_score and not is_dq:
        return {"success": False, "message": "Scores are tied. Cannot report without a winner.", "data": None}

    winner_entrant_id = ui_team1_entrant if team1_score > team2_score else ui_team2_entrant

    if not winner_entrant_id:
        return {
            "success": False,
            "message": "Could not determine winner entrant ID.\nMake sure the set was loaded from Start.gg.",
            "data": None,
        }

    game_data = BuildGameData(scoreboard_number, ui_team1_entrant, ui_team2_entrant)

    variables = {
        "setId": str(set_id),
        "winnerId": str(winner_entrant_id),
        "isDQ": is_dq,
    }
    if game_data:
        variables["gameData"] = game_data

    try:
        data = _gql_request(api_token, REPORT_SET_MUTATION, variables)

        errors = data.get("errors")
        if errors:
            msg = "; ".join(e.get("message", str(e)) for e in errors)
            return {"success": False, "message": f"Start.gg API error:\n{msg}", "data": data}

        result = data.get("data", {}).get("reportBracketSet")
        if result:
            reported = result[0] if isinstance(result, list) else result
            return {
                "success": True,
                "message": f"Set reported successfully!\nSet ID: {reported.get('id')} — State: {reported.get('state')}",
                "data": data,
            }

        return {"success": False, "message": "Unexpected response from Start.gg.", "data": data}

    except requests.exceptions.HTTPError as e:
        logger.error(f"TSHStartGGSetReporter HTTP error: {e}")
        return {"success": False, "message": f"HTTP error: {e}", "data": None}
    except Exception:
        logger.error(f"TSHStartGGSetReporter error:\n{traceback.format_exc()}")
        return {"success": False, "message": f"Error reporting set:\n{traceback.format_exc()}", "data": None}
