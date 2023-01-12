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
path_to_asset = f"{dir_to_asset}/tournament_matches.txt"

for lang in lang_list:
    Path(dir_to_asset.replace("{lang}", lang)).mkdir(parents=True, exist_ok=True)
    try:
        with open(path_to_asset.replace("{lang}", lang), 'rt', encoding='utf-8') as locale_file:
            locale_lines = locale_file.readlines()
            for i in range(len(locale_lines)):
                locale_lines[i] = locale_lines[i].strip()
    except FileNotFoundError:
        locale_lines = []

    with open(path_to_json.replace("{lang}", lang), 'rt', encoding='utf-8') as json_file:
        dictionary = json.loads(json_file.read())

    with open(path_to_asset.replace("{lang}", lang), 'wt', encoding='utf-8') as locale_file:
        for line in locale_lines:
            locale_file.write(f"{line}\n")
        for key in dictionary:
            if dictionary[key] not in locale_lines:
                if "{0}" in dictionary[key]:
                    for i in range(1, 6):
                        if dictionary[key].replace("{0}", str(i)) not in locale_lines:
                            locale_file.write(f'{dictionary[key].replace("{0}", str(i))}\n')
                else:
                    locale_file.write(f"{dictionary[key]}\n")
