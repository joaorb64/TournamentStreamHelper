import json
import math
import textwrap
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *

def add_alt_text_tooltip_to_button(push_button: QPushButton):
    altTextTooltip = QApplication.translate(
            "tips", "Descriptive text (also known as Alt text) describes images for blind and low-vision users, and helps give context around images to everyone. As such, we highly recommend adding it to your image uploads on your websites and social media posts.")
    push_button.setToolTip('\n'.join(textwrap.wrap(altTextTooltip, 40)))
    return(push_button)


def load_program_state():
    data_path = "./out/program_state.json"
    with open(data_path, "rt", encoding="utf-8") as data_file:
        data_json = json.loads(data_file.read())
    return (data_json)


def generate_youtube(scoreboard_id=1, use_phase_name=True):
    title_length_limit = 100    # Character limit for video titles
    data = load_program_state()
    tournament_name = data.get("tournamentInfo").get("tournamentName")
    event_name = data.get("tournamentInfo").get("eventName")
    event_date = data.get("tournamentInfo").get("startAt")
    game_name = data.get("game").get("name")
    match_data = data.get("score").get(str(scoreboard_id))
    if not match_data:
        raise ValueError(f"Scoreboard #{scoreboard_id} could not be found")
    phase_data = match_data.get("phase")
    round_data = match_data.get("match")
    team_data = match_data.get("team")
    title_long = f"[{tournament_name.upper()}] - "
    title_short = f"[{tournament_name.upper()}] - "
    game_localisation = QApplication.translate("altText", "Game:")
    description = f"""
{tournament_name.upper()}
{event_name} - {event_date}
{game_localisation} {game_name}

"""
    if phase_data and use_phase_name:
        title_long = f"[{tournament_name}] {phase_data} - "
        title_short = f"[{tournament_name}] {phase_data} - "
    else:
        title_long = f"[{tournament_name}] {round_data} - "
        title_short = f"[{tournament_name}] {round_data} - "
    if phase_data:
        description = description + f"{phase_data} - {round_data}\n"
    else:
        description = description + f"{round_data}\n"
    for team_id in team_data.keys():
        current_team_data = team_data.get(team_id)
        team_name = current_team_data.get("teamName")
        player_names = []
        player_names_with_characters = []
        if team_name:
            title_long = f'{title_long}' + team_name
            title_short = f'{title_short}' + team_name
            description = description + team_name
        else:
            player_data = current_team_data.get("player")
            for player_id in player_data.keys():
                character_names = []
                current_player_data = player_data.get(player_id)
                player_name = current_player_data.get("mergedName")
                character_data = current_player_data.get("character")
                for character_id in character_data.keys():
                    current_character_data = character_data.get(character_id)
                    if current_character_data.get("name"):
                        character_names.append(current_character_data.get("name"))
                if player_name:
                    if player_name.replace(' [L]', ''):
                        player_names.append(player_name.replace(" [L]", ""))
                        if character_names:
                            player_names_with_characters.append(
                                f"{player_name.replace(' [L]', '')} ({', '.join(character_names)})")
                        else:
                            player_names_with_characters.append(
                                player_name.replace(" [L]", ""))
            title_long = f'{title_long}' + \
                " / ".join(player_names_with_characters)
            title_short = f'{title_short}' + " / ".join(player_names)
            description = description + \
                " / ".join(player_names_with_characters)

        if team_id == "1":
            title_long = f'{title_long} ' + \
                QApplication.translate("altText", "VS") + ' '
            title_short = f'{title_short} ' + \
                QApplication.translate("altText", "VS") + ' '
            description = f'{description} ' + \
                QApplication.translate("altText", "VS") + ' '

    description = f"{description}\n\n"
    commentator_data = data.get("commentary")
    commentator_names = []
    for commentator_id in commentator_data.keys():
        current_commentator_data = commentator_data.get(commentator_id)
        if current_commentator_data.get("mergedName"):
            commentator_names.append(
                current_commentator_data.get("mergedName"))
    if commentator_names:
        description = description + QApplication.translate(
            "altText", "Commentators:") + " " + " / ".join(commentator_names) + "\n"

    description = description + QApplication.translate("altText", "Stream powered by TournamentStreamHelper:") + \
        " " + "https://github.com/joaorb64/TournamentStreamHelper/releases"
    description = description.strip()

    if len(title_long) <= title_length_limit:
        return (title_long, description)
    else:
        if len(title_short) > title_length_limit:
            while len(title_short) > title_length_limit - 1:
                title_short = title_short[:-1]
            return (f"{title_short}…", description)
        else:
            return (title_short, description)


def generate_top_n_alt_text(bracket_type="DOUBLE_ELIMINATION"):
    def CalculatePlacementMath(x, bracket_type="DOUBLE_ELIMINATION"):
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

    def CalculatePlacement(x, bracket_type="DOUBLE_ELIMINATION"):
        if x in [1, 2, 3, 4]:
            return x
        placement_math = CalculatePlacementMath(x, bracket_type)
        change = x
        while CalculatePlacementMath(change, bracket_type) == placement_math:
            change = change - 1
        return (change+1)

    data = load_program_state()
    tournament_name = data.get("tournamentInfo").get("tournamentName")
    event_name = data.get("tournamentInfo").get("eventName")
    event_date = data.get("tournamentInfo").get("startAt")
    game_name = data.get("game").get("name")
    game_localisation = QApplication.translate("altText", "Game:")
    alt_text = f"""
{tournament_name.upper()}
{event_name} - {event_date}
{game_localisation} {game_name}

""" + QApplication.translate("altText", "Standings:").upper() + "\n"

    team_list = data.get("player_list").get("slot")
    for team_id in team_list.keys():
        current_team_data = team_list.get(team_id)
        team_name = current_team_data.get("teamName")
        players_text = []
        player_data = current_team_data.get("player")
        for player_id in player_data.keys():
            character_names = []
            current_player_data = player_data.get(player_id)
            player_name = current_player_data.get("mergedName")
            character_data = current_player_data.get("character")
            if current_player_data.get("country"):
                country_code = current_player_data.get("country").get("code")
            else:
                country_code = ""
            for character_id in character_data.keys():
                current_character_data = character_data.get(character_id)
                if current_character_data.get("name"):
                    character_names.append(current_character_data.get("name"))
            player_text = f"{player_name}"
            characters_text = ' / '.join(character_names)
            if country_code:
                if characters_text:
                    characters_text = country_code + ", " + characters_text
                else:
                    characters_text = country_code
            if characters_text:
                player_text = player_text + f" ({characters_text})"
            if player_name:
                players_text.append(player_text)
        placement = CalculatePlacement(int(team_id), bracket_type)
        players_text = " / ".join(players_text)
        if team_name:
            alt_text = alt_text + \
                f"{placement}/ {team_name} [{players_text}]\n"
        else:
            alt_text = alt_text + f"{placement}/ {players_text}\n"

    alt_text = f"{alt_text}\n\n"
    commentator_data = data.get("commentary")
    commentator_names = []
    for commentator_id in commentator_data.keys():
        current_commentator_data = commentator_data.get(commentator_id)
        if current_commentator_data.get("mergedName"):
            commentator_names.append(
                current_commentator_data.get("mergedName"))
    if commentator_names:
        alt_text = alt_text + QApplication.translate(
            "altText", "Commentators:") + " " + " / ".join(commentator_names) + "\n"

    alt_text = alt_text + \
        QApplication.translate(
            "altText", "Stream powered by TournamentStreamHelper")

    alt_text.strip()
    return (alt_text)


if __name__ == "__main__":
    from termcolor import colored
    print(colored("TEST MODE - TSHAltTextHelper.py", "red"))
    print("====")
    title, description = generate_youtube(1)
    print(colored("YouTube title: ", "yellow") + f"{title}")
    print(colored(f"\nDescription: \n", "yellow") + f"{description}")
    print(colored(f"\nTop 8 alt text: \n", "yellow")+f"{generate_top_n_alt_text()}")
