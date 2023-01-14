from pathlib import Path
import json
import glob
import os

path_to_json = "./src/i18n/round_names/{lang}.json"
json_files = glob.glob(path_to_json.replace("{lang}", "*"))
lang_list = []
for filename in json_files:
    lang_list.append(os.path.basename(filename).replace(".json", ""))
print(lang_list)

dir_to_asset = "./assets/locale/{lang}"
path_to_asset = f"{dir_to_asset}/[file].txt"
path_to_default = "./assets/[file].txt"

txt_file_list = ['tournament_matches', 'tournament_phases']
key_list = ["match", "phase"]

for lang in lang_list:
    for j in range(len(txt_file_list)):
        current_path_to_asset = path_to_asset.replace("{lang}", lang).replace("[file]", txt_file_list[j])
        Path(dir_to_asset.replace("{lang}", lang)).mkdir(parents=True, exist_ok=True)
        locale_lines = []
        with open(path_to_json.replace("{lang}", lang), 'rt', encoding='utf-8') as json_file:
            dictionary = json.loads(json_file.read())[key_list[j]]

        with open(current_path_to_asset, 'wt', encoding='utf-8') as locale_file:
            for line in locale_lines:
                locale_file.write(f"{line}\n")
            for key in dictionary:
                if dictionary[key] not in locale_lines:
                    if "{0}" in dictionary[key]:
                        for i in range(1, 6):
                            if dictionary[key].replace("{0}", str(i)) not in locale_lines:
                                if j == 0:
                                    locale_file.write(f'{dictionary[key].replace("{0}", str(i))}\n')
                                else:
                                    locale_file.write(f'{dictionary[key].replace("{0}", chr(i+64))}\n')
                    else:
                        locale_file.write(f"{dictionary[key]}\n")

for i in range(len(txt_file_list)):
    current_path_to_asset = path_to_asset.replace("{lang}", "en").replace("[file]", txt_file_list[i])
    try:
        with open(current_path_to_asset, 'rt', encoding='utf-8') as locale_file:
            with open(path_to_default.replace("[file]", txt_file_list[i]), 'wt', encoding='utf-8') as default_file:
                default_file.write(locale_file.read())
    except FileNotFoundError:
        None
