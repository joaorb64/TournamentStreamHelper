import os
import json

header_old = "org,name,full_name,country_code,state,twitter,main,color (0-7)"
header_new = "prefix,gamerTag,name,twitter,country_code,state_code,mains"

game_dir = "../user_data/games"
list_dir = os.listdir(game_dir)


class OldLine:
    org = ''
    name = ''
    full_name = ''
    twitter = ''
    country_code = ''
    state_code = ''
    main = ''
    color = ''

    def __init__(self, line: str) -> None:
        line = line.strip()
        self.org, self.name, self.full_name, self.country_code, self.state_code, self.twitter, self.main, self.color = line.split(
            ',')
        self.color = str(self.color)

    def get_game_id_from_main(self):
        for dir_name in list_dir:
            config_path = f"{game_dir}/{dir_name}/base_files/config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                game_config = json.loads(f.read())
            list_characters = game_config.get("character_to_codename")
            if self.main in list_characters.keys():
                return(dir_name)
        return(None)


def convert_database_3_to_4(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        old_database_csv = f.readlines()

    new_database = header_new + "\n"

    for line in old_database_csv:
        if header_old not in line:
            old_data = OldLine(line)
            print(old_data.name)
            game_id = old_data.get_game_id_from_main()
            if game_id:
                new_main_data_dict = {
                    game_id: [
                        [old_data.main, old_data.color]
                    ]
                }
                new_main_data = f"'{json.dumps(new_main_data_dict)}'"
            else:
                new_main_data = ''
            new_line = f"{old_data.org},{old_data.name},{old_data.full_name},{old_data.twitter},{old_data.country_code},{old_data.state_code},{new_main_data}"
            new_database = new_database + new_line + '\n'

    return(new_database)


if __name__ == '__main__':
    new_database_text = convert_database_3_to_4("../local_players_old.csv")
    with open('../user_data/local_players.csv', 'w', encoding='utf-8') as f:
        f.write(new_database_text)
