import chinese_converter
import xml.etree.ElementTree as ET
import json
from copy import deepcopy

zh_cn_parse = ET.parse("src/i18n/TSH_zh-CN.ts")
root = zh_cn_parse.getroot()
for child in root:
    if child.tag == "context":
        for context_child in child:
            if context_child.tag == "message":
                for message_child in context_child:
                    if message_child.tag == "translation" and message_child.text:
                        traditional = chinese_converter.to_traditional(message_child.text)
                        message_child.text = traditional

zh_cn_parse.write("src/i18n/TSH_zh-TW.ts")

with open("src/i18n/TSH_zh-TW.ts", "rt", encoding="utf-8") as traditional_file:
    traditional_text = traditional_file.read()

with open("src/i18n/TSH_zh-TW.ts", "wt", encoding="utf-8") as traditional_file:
    header = '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n'
    traditional_text = traditional_text.replace('language="zh_CN"', 'language="zh_TW"')
    traditional_file.write(header+traditional_text)

for path in ["src/i18n/tournament_term", "stage_strike_app/src/i18n/locales"]:
    with open(f"{path}/zh-CN.json", "rt", encoding="utf-8") as simplified_file:
        simplified_json = json.loads(simplified_file.read())
    
    traditional_json = deepcopy(simplified_json)
    if "tournament_term" in path:
        for key in simplified_json.keys():
            for key_2 in simplified_json[key].keys():
                traditional_json[key][key_2] = chinese_converter.to_traditional(simplified_json[key][key_2])
    else:
        for key in simplified_json.keys():
            traditional_json[key] = chinese_converter.to_traditional(simplified_json[key])

    with open(f"{path}/zh-TW.json", "wt", encoding="utf-8") as traditional_file:
        traditional_file.write(json.dumps(traditional_json, indent=4))

print("Done")