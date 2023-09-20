import os
import json
import collections

file_list = []

for root, dirs, files in os.walk("src"):
    path = root.split(os.sep)
    print((len(path) - 1) * '---', os.path.basename(root))
    for file in files:
        if file.endswith((".py", ".ui")):
            print(len(path) * '---', file)
            file_list.append(f"{root}/{file}")

print(file_list)

languages = [
    "en",
    "pt-BR",
    "fr",
    "ja",
    "es",
    "de",
    "it",
    "zh-CN",
    "zh-TW"
]

output = [f'src/i18n/TSH_{lang}.ts' for lang in languages]

os.system(
    f"lupdate {' '.join(file_list)} -ts {' '.join(output)}")

# Force vanished strings to be included
for out_path in output:
    with open(out_path, "rt", encoding='utf-8') as out_file:
        out = out_file.read()
    with open(out_path, "wt", encoding='utf-8') as out_file:
        out_file.write(out.replace(' type="vanished"', ""))

with open("src/i18n/mapping.json", 'rt', encoding='utf-8') as mapping_file:
    mapping_data = json.loads(mapping_file.read())

supported_languages = mapping_data["languages"]
ordered_languages = collections.OrderedDict(sorted(supported_languages.items()))
mapping_data["languages"] = ordered_languages

with open("src/i18n/mapping.json", 'wt', encoding='utf-8') as mapping_file:
    mapping_file.write(json.dumps(mapping_data, indent=2))