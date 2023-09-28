from PIL import Image, ImageDraw
from pathlib import Path
import json
import os
import re
from copy import deepcopy

tested_assets = {
    "abaa": ["full"],
    "arms": ["full"],
    "en1a": ["full"],
    "jackie": ["full"],
    "sdbz": ["full"],
    "sf6": ["base_files/icon", "full"],
    "idols": ["base_files/icon", "full"],
    "jojoasbr": ["full"],
    "roa": ["base_files/icon", "full"],
    "avg2": ["full"]
}

main_out_path = "../out/test"


def draw_eyesight(game, asset_pack):
    print(game)
    print(asset_pack)
    game_folder = f"../user_data/games/{game}"
    asset_folder = f"{game_folder}/{asset_pack}"
    asset_pack_config_path = f"{asset_folder}/config.json"
    with open(asset_pack_config_path, 'rt', encoding='utf-8') as f:
        asset_pack_config = json.loads(f.read())
        eyesight_data = asset_pack_config.get("eyesights")
        prefix = asset_pack_config.get("prefix")
        postfix = asset_pack_config.get("postfix")

    sub_out_path = f"{main_out_path}/{game}/{asset_pack}"
    out_path = f"{sub_out_path}/draw"
    Path(out_path).mkdir(parents=True, exist_ok=True)

    for codename in eyesight_data.keys():

        image_regexp = f"{prefix}{codename}{postfix}([0-9]+)\.png"
        list_png = [f for f in os.listdir(
            asset_folder) if re.search(image_regexp, f)]
        for png_filename in list_png:
            try:
                skin_index = re.search(image_regexp, png_filename).group(1)
                png_path = f"{asset_folder}/{png_filename}"
                new_png_path = f"{out_path}/{png_filename}"

                eyesight_coordinates_dict = eyesight_data.get(
                    codename).get(str(int(skin_index)))
                if not eyesight_coordinates_dict:
                    eyesight_coordinates_dict = eyesight_data.get(
                        codename).get('0')

                if eyesight_coordinates_dict:
                    eyesight_coordinates = (eyesight_coordinates_dict.get(
                        "x"), eyesight_coordinates_dict.get("y"))

                    png_image = Image.open(png_path).convert("RGBA")
                    png_size = png_image.size
                    new_png_image = deepcopy(png_image)
                    draw = ImageDraw.Draw(new_png_image)
                    draw.line([(eyesight_coordinates[0], 0), (eyesight_coordinates[0], png_size[1])], fill=(
                        255, 0, 0), width=5)
                    draw.line([(0, eyesight_coordinates[1]), (png_size[0],
                            eyesight_coordinates[1])], fill=(255, 0, 0), width=5)
                    new_png_image.save(new_png_path)
            except Exception as e:
                print(f"Error in file {png_filename}")
                print(">> "+str(e))


for game in tested_assets.keys():
    for asset_pack in tested_assets[game]:
        draw_eyesight(game, asset_pack)
