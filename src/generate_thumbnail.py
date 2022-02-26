# This script can be used to generate thumbnails using ./out/program_state.json and ./thumbnail_base
# Run as python ./src/generate_thumbnail in order to test it

from PIL import Image, ImageFont, ImageDraw
from pathlib import Path
import json
import requests
import zipfile
import shutil
import string
from copy import deepcopy
import datetime

display_phase = True
use_team_names = False
use_sponsors = True

foreground_path = "./thumbnail_base/foreground.png"
background_path = "./thumbnail_base/background.png"
separator_h_path = "./thumbnail_base/separator_h.png"
separator_v_path = "./thumbnail_base/separator_v.png"
data_path = "./out/program_state.json"
out_path = "./out/thumbnails"
tmp_path = "./tmp"
icon_path = "./icons/icon.png"

Path(tmp_path).mkdir(parents=True, exist_ok=True)


def download_opensans():
    http_path = "https://www.fontsquirrel.com/fonts/download/open-sans"
    local_path = f"{tmp_path}/opensans"
    response = requests.get(http_path)
    with open(f"{local_path}.zip", 'wb') as f:
        f.write(response.content)
    with zipfile.ZipFile(f"{local_path}.zip", 'r') as zip_ref:
        Path(local_path).mkdir(parents=True, exist_ok=True)
        zip_ref.extractall(local_path)
    return(local_path)


opensans_path = download_opensans()


def find(element, json):
    keys = element.split('.')
    rv = json
    for key in keys:
        rv = rv[key]
    return rv


def calculate_new_dimensions(current_size, max_size):
    # Use -1 if you do not want to constrain in that dimension
    x_ratio = max_size[0]/current_size[0]
    y_ratio = max_size[1]/current_size[1]

    if max_size[0] < 0 and max_size[1] < 0:
        raise ValueError(
            msg=f"Size cannot be negative, given max size is {max_size}")

    if (x_ratio*current_size[1] > max_size[1]) or x_ratio < 0:
        new_x = y_ratio*current_size[0]
        new_y = max_size[1]
    else:
        new_x = max_size[0]
        new_y = x_ratio*current_size[1]
    return((round(new_x), round(new_y)))


def resize_image_to_max_size(image: Image, max_size):
    current_size = image.size
    x_ratio = max_size[0]/current_size[0]
    y_ratio = max_size[1]/current_size[1]

    if max_size[0] < 0 or max_size[1] < 0:
        raise ValueError(
            msg=f"Size cannot be negative, given max size is {max_size}")

    if (x_ratio < y_ratio):
        new_x = y_ratio*current_size[0]
        new_y = max_size[1]
    else:
        new_x = max_size[0]
        new_y = x_ratio*current_size[1]

    new_size = (round(new_x), round(new_y))
    image = image.resize(new_size, resample=Image.BICUBIC)

    # crop
    left = round(-(max_size[0] - new_x)/2)
    top = round(-(max_size[1] - new_y)/2)
    right = round((max_size[0] + new_x)/2)
    bottom = round((max_size[1] + new_y)/2)
    image = image.crop((left, top, right, bottom))

    return(image)


def create_composite_image(image, size, coordinates):
    background = Image.new('RGBA', size, (0, 0, 0, 0))
    background.paste(image, coordinates, image)
    return(background)


def paste_image_matrix(thumbnail, path_matrix, max_size, paste_coordinates):
    num_line = len(path_matrix)

    for line_index in range(0, len(path_matrix)):
        line = path_matrix[line_index]
        num_col = len(line)
        for col_index in range(0, len(line)):
            individual_max_size = (
                round(max_size[0]/num_col), round(max_size[1]/num_line))
            image_path = line[col_index]
            print(f"Processing asset: {image_path}")
            individual_paste_x = round(
                paste_coordinates[0] + col_index*individual_max_size[0])
            individual_paste_y = round(
                paste_coordinates[1] + line_index*individual_max_size[1])
            individual_paste_coordinates = (
                individual_paste_x, individual_paste_y)
            character_image = Image.open(image_path).convert('RGBA')
            character_image = resize_image_to_max_size(
                character_image, individual_max_size)
            composite_image = create_composite_image(
                character_image, thumbnail.size, individual_paste_coordinates)
            thumbnail = Image.alpha_composite(thumbnail, composite_image)

            separator_v_image = Image.open(separator_v_path).convert('RGBA')
            # crop
            left = round(0)
            top = round(0)
            right = round(separator_v_image.size[0])
            bottom = round(individual_max_size[1])
            separator_v_image = separator_v_image.crop(
                ((left, top, right, bottom)))
            separator_v_offset = max_size[0]/num_col
            for i in range(1, num_col):
                separator_paste_x = round(
                    paste_coordinates[0]-(separator_v_image.size[0]/2)+i*separator_v_offset)
                separator_paste_y = individual_paste_y
                separator_paste_coordinates = (
                    separator_paste_x, separator_paste_y)
                composite_image = create_composite_image(
                    separator_v_image, thumbnail.size, separator_paste_coordinates)
                thumbnail = Image.alpha_composite(thumbnail, composite_image)

        separator_h_image = Image.open(separator_h_path).convert('RGBA')
        # crop
        left = round(0)
        top = round(0)
        right = round(max_size[0])
        bottom = round(separator_h_image.size[1])
        separator_h_image = separator_h_image.crop(
            ((left, top, right, bottom)))
        separator_h_offset = max_size[1]/num_line
        for i in range(1, num_line):
            separator_paste_x = paste_coordinates[0]
            separator_paste_y = round(
                paste_coordinates[1]-(separator_h_image.size[1]/2)+i*separator_h_offset)
            separator_paste_coordinates = (
                separator_paste_x, separator_paste_y)
            composite_image = create_composite_image(
                separator_h_image, thumbnail.size, separator_paste_coordinates)
            thumbnail = Image.alpha_composite(thumbnail, composite_image)

    return(thumbnail)


def paste_characters(thumbnail, data):
    used_assets = "full"

    max_x_size = round(thumbnail.size[0]/2)
    max_y_size = thumbnail.size[1]
    max_size = (max_x_size, max_y_size)
    origin_x_coordinates = [0, max_x_size]
    origin_y_coordinates = [0, 0]

    for i in [0, 1]:
        team_index = i+1
        path_matrix = []
        current_team = find(f"score.team.{team_index}.players", data)
        for player_key in current_team.keys():
            character_list = []
            characters = find(f"{player_key}.character", current_team)
            for character_key in characters.keys():
                try:
                    image_path = find(
                        f"{character_key}.assets.{used_assets}.asset", characters)
                    if image_path:
                        character_list.append(image_path)
                except KeyError:
                    None
            if character_list:
                path_matrix.append(character_list)

        paste_x = origin_x_coordinates[i]
        paste_y = origin_y_coordinates[i]
        paste_coordinates = (paste_x, paste_y)
        thumbnail = paste_image_matrix(
            thumbnail, path_matrix, max_size, paste_coordinates)

    return(thumbnail)


def get_text_size_for_height(thumbnail, font_path, pixel_height, search_interval=None, recursion_level=0):
    if pixel_height <= 1:
        raise ValueError("pixel_height too small")

    tolerance = 0
    thumbnail_copy = deepcopy(thumbnail)
    draw = ImageDraw.Draw(thumbnail_copy)
    if not search_interval:
        search_interval = [0, pixel_height*2]
    current_size = round((search_interval[0] + search_interval[1])/2)
    font = ImageFont.truetype(font_path, current_size)
    bbox = draw.textbbox((0, 0), string.ascii_letters, font=font)
    calculated_height = bbox[-1]

    if (calculated_height <= pixel_height+tolerance and calculated_height >= pixel_height-tolerance) or recursion_level > 100:
        return(current_size)
    elif calculated_height < pixel_height:
        result = get_text_size_for_height(
            thumbnail, font_path, pixel_height, [current_size, search_interval[1]], recursion_level+1)
        return(result)
    else:
        result = get_text_size_for_height(
            thumbnail, font_path, pixel_height, [search_interval[0], current_size], recursion_level+1)
        return(result)


def paste_player_text(thumbnail, data, use_team_names=False, use_sponsors=True):
    text_player_coordinates_center = [
        (480.0/1920.0, 904.0/1080.0), (1440./1920.0, 904.0/1080.0)]
    text_player_max_dimensions = (-1, 100.0/1080.0)
    pixel_height = round(text_player_max_dimensions[1]*thumbnail.size[1])
    font_path = f"{opensans_path}/OpenSans-Bold.ttf"
    text_size = get_text_size_for_height(thumbnail, font_path, pixel_height)

    draw = ImageDraw.Draw(thumbnail)

    for i in [0, 1]:
        team_index = i+1
        player_list = []
        if use_team_names:
            player_name = find(f"score.team.{team_index}.teamName", data)
        else:
            current_team = find(f"score.team.{team_index}.players", data)
            for key in current_team.keys():
                current_data = current_team[key].get("mergedName")
                if (not use_sponsors) or (not current_data):
                    current_data = current_team[key].get("name")
                if current_data:
                    player_list.append(current_data)
            player_name = " / ".join(player_list)

        if use_team_names or len(player_list) > 1:
            player_type = "team"
        else:
            player_type = "player"

        print(f"Processing {player_type}: {player_name}")

        font = ImageFont.truetype(font_path, text_size)
        text_x = round(text_player_coordinates_center[i][0]*thumbnail.size[0])
        text_y = round(text_player_coordinates_center[i][1]*thumbnail.size[1])
        text_coordinates = (text_x, text_y)

        draw.text(text_coordinates, player_name,
                  (255, 255, 255), font=font, anchor="mm")


def paste_round_text(thumbnail, data, display_phase=True):
    phase_text_coordinates_center = (960.0/1920.0, 1008.0/1080.0)
    round_text_coordinates_center = (960.0/1920.0, 1052.0/1080.0)
    text_max_dimensions = (-1, 40.0/1080.0)

    if not display_phase:
        round_text_coordinates_center = (round_text_coordinates_center[0], (
            round_text_coordinates_center[1] + phase_text_coordinates_center[1])/2)
        text_max_dimensions = (-1, text_max_dimensions[1]*2)

    pixel_height = round(text_max_dimensions[1]*thumbnail.size[1])
    font_path = f"{opensans_path}/OpenSans-Semibold.ttf"
    text_size = get_text_size_for_height(thumbnail, font_path, pixel_height)

    draw = ImageDraw.Draw(thumbnail)

    if display_phase:
        current_phase = find(f"score.phase", data)

        font = ImageFont.truetype(font_path, text_size)
        text_x = round(phase_text_coordinates_center[0]*thumbnail.size[0])
        text_y = round(phase_text_coordinates_center[1]*thumbnail.size[1])
        text_coordinates = (text_x, text_y)
        draw.text(text_coordinates, current_phase,
                  (255, 255, 255), font=font, anchor="mm")

    current_round = find(f"score.match", data)

    font = ImageFont.truetype(font_path, text_size)
    text_x = round(round_text_coordinates_center[0]*thumbnail.size[0])
    text_y = round(round_text_coordinates_center[1]*thumbnail.size[1])
    text_coordinates = (text_x, text_y)
    draw.text(text_coordinates, current_round,
              (255, 255, 255), font=font, anchor="mm")


def paste_icon(thumbnail, icon_path):
    max_x_size = round(thumbnail.size[0]*(150.0/1920.0))
    max_y_size = round(thumbnail.size[1]*(150.0/1080.0))
    max_size = (max_x_size, max_y_size)

    icon_image = Image.open(icon_path).convert('RGBA')
    icon_size = calculate_new_dimensions(icon_image.size, max_size)
    icon_image = icon_image.resize(icon_size, resample=Image.BICUBIC)

    icon_x = round(thumbnail.size[0]/2 - icon_size[0]/2)
    icon_y = round(thumbnail.size[1]*(6.0/1080.0))
    icon_coordinates = (icon_x, icon_y)
    composite_image = create_composite_image(
        icon_image, thumbnail.size, icon_coordinates)
    thumbnail = Image.alpha_composite(thumbnail, composite_image)
    return(thumbnail)


Path(out_path).mkdir(parents=True, exist_ok=True)

foreground = Image.open(foreground_path).convert('RGBA')
background = Image.open(background_path).convert('RGBA')
with open(data_path, 'rt', encoding='utf-8') as f:
    data = json.loads(f.read())

thumbnail = Image.new("RGBA", foreground.size, "PINK")
composite_image = create_composite_image(background, thumbnail.size, (0, 0))
thumbnail = Image.alpha_composite(thumbnail, composite_image)
thumbnail.paste(background, (0, 0), mask=background)
thumbnail = paste_characters(thumbnail, data)
composite_image = create_composite_image(foreground, thumbnail.size, (0, 0))
thumbnail = Image.alpha_composite(thumbnail, composite_image)
paste_player_text(thumbnail, data, use_team_names, use_sponsors)
paste_round_text(thumbnail, data, display_phase)
thumbnail = paste_icon(thumbnail, icon_path)

thumbnail_filename = f"thumb-{datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
thumbnail.save(f"{out_path}/{thumbnail_filename}.png")
thumbnail.convert("RGB").save(f"{out_path}/{thumbnail_filename}.jpg")

shutil.rmtree(tmp_path)

print(
    f"Thumbnail successfully saved as {out_path}/{thumbnail_filename}.png and {out_path}/{thumbnail_filename}.jpg")
