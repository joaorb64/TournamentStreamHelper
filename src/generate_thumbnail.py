# This script can be used to generate thumbnails using ./out/program_state.json and ./thumbnail_base
# Run as python ./src/generate_thumbnail in order to test it

from turtle import back
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

foreground_path = "./thumbnail_base/foreground.png"
background_path = "./thumbnail_base/background.png"
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

def resize_image_to_max_size(image:Image, max_size):
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

    #crop
    left = round(-(max_size[0] - new_x)/2)
    top = round(-(max_size[1] - new_y)/2)
    right = round((max_size[0] + new_x)/2)
    bottom = round((max_size[1] + new_y)/2)
    image = image.crop((left, top, right, bottom))

    return(image)

def create_composite_image(image, size, coordinates):
    background = Image.new('RGBA', size, (0,0,0,0))
    background.paste(image, coordinates, image)
    return(background)

def paste_characters(thumbnail, data):
    used_assets = "full"

    max_x_size = round(thumbnail.size[0]/2)
    max_y_size = thumbnail.size[1]
    max_size = (max_x_size, max_y_size)
    origin_x_coordinates = [0, max_x_size]
    origin_y_coordinates = [0, 0]

    for i in [0, 1]:
        team_index = i+1
        current_image_path = find(
            f"score.team.{team_index}.players.1.character.1.assets.{used_assets}.asset", data)
        character_image = Image.open(current_image_path).convert('RGBA')
        character_image = resize_image_to_max_size(character_image, max_size)
        paste_x = origin_x_coordinates[i]
        paste_y = origin_y_coordinates[i]
        paste_coordinates = (paste_x, paste_y)
        composite_image = create_composite_image(character_image, thumbnail.size, paste_coordinates)
        thumbnail = Image.alpha_composite(thumbnail, composite_image)

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

    if (calculated_height <= pixel_height+tolerance and calculated_height >= pixel_height-tolerance) or recursion_level>100:
        return(current_size)
    elif calculated_height < pixel_height:
        result = get_text_size_for_height(
            thumbnail, font_path, pixel_height, [current_size, search_interval[1]], recursion_level+1)
        return(result)
    else:
        result = get_text_size_for_height(
            thumbnail, font_path, pixel_height, [search_interval[0], current_size], recursion_level+1)
        return(result)


def paste_player_text(thumbnail, data):
    text_player_coordinates_center = [
        (480.0/1920.0, 904.0/1080.0), (1440./1920.0, 904.0/1080.0)]
    text_player_max_dimensions = (-1, 100.0/1080.0)
    pixel_height = round(text_player_max_dimensions[1]*thumbnail.size[1])
    font_path = f"{opensans_path}/OpenSans-Bold.ttf"
    text_size = get_text_size_for_height(thumbnail, font_path, pixel_height)

    draw = ImageDraw.Draw(thumbnail)

    for i in [0, 1]:
        team_index = i+1
        current_player = find(f"score.team.{team_index}.players.1", data)
        player_name = current_player.get("mergedName")

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
    max_x_size = round(thumbnail.size[0]*(200.0/1920.0))
    max_y_size = round(thumbnail.size[1]*(200.0/1080.0))
    max_size = (max_x_size, max_y_size)

    icon_image = Image.open(icon_path).convert('RGBA')
    icon_size = calculate_new_dimensions(icon_image.size, max_size)
    icon_image = icon_image.resize(icon_size, resample=Image.BICUBIC)

    icon_x = round(thumbnail.size[0]/2 - icon_size[0]/2)
    icon_y = round(thumbnail.size[1]*(6.0/1080.0))
    icon_coordinates = (icon_x, icon_y)
    composite_image = create_composite_image(icon_image, thumbnail.size, icon_coordinates)
    thumbnail = Image.alpha_composite(thumbnail, composite_image)
    return(thumbnail)


Path(out_path).mkdir(parents=True, exist_ok=True)

foreground = Image.open(foreground_path).convert('RGBA')
background = Image.open(background_path).convert('RGBA')
with open(data_path, 'rt', encoding='utf-8') as f:
    data = json.loads(f.read())

thumbnail = Image.new("RGBA", foreground.size, "PINK")
composite_image = create_composite_image(background, thumbnail.size, (0,0))
thumbnail = Image.alpha_composite(thumbnail, composite_image)
thumbnail.paste(background, (0, 0), mask=background)
thumbnail = paste_characters(thumbnail, data)
composite_image = create_composite_image(foreground, thumbnail.size, (0,0))
thumbnail = Image.alpha_composite(thumbnail, composite_image)
paste_player_text(thumbnail, data)
paste_round_text(thumbnail, data, display_phase)
thumbnail = paste_icon(thumbnail, icon_path)

thumbnail_filename = f"thumb-{datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
thumbnail.save(f"{out_path}/{thumbnail_filename}.png")
thumbnail.convert("RGB").save(f"{out_path}/{thumbnail_filename}.jpg")

shutil.rmtree(tmp_path)
