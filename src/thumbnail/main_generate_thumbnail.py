# This script can be used to generate thumbnails using ./out/program_state.json and ./thumbnail_base
# Run as python ./src/generate_thumbnail in order to test it

from math import cos, radians, sin
from numbers import Rational
import random
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from cgitb import text
from textwrap import fill
from pathlib import Path
import json
from click import style
import requests
import shutil
import string
from copy import deepcopy
import datetime
import os
import re

from src.TSHGameAssetManager import TSHGameAssetManager
from src.Helpers.TSHLocaleHelper import TSHLocaleHelper

is_preview = False

display_phase = True
use_team_names = False
use_sponsors = True
all_eyesight = False
no_separator = 0

crop_borders = [] # left, right, top, bottom
scale_fill_x = 0
scale_fill_y = 0

proportional_zoom = 1

def color_code_to_tuple(color_code):
    raw_color_code = color_code.lstrip("#")
    red = int(raw_color_code[0:2], base=16)
    green = int(raw_color_code[2:4], base=16)
    blue = int(raw_color_code[4:6], base=16)
    color = (red, green, blue)
    return color


def generate_separator_images(thumbnail, color_code="#888888", width=3):
    x_size, y_size = round(thumbnail.width()/2), int(thumbnail.height())
    x_separator = QPixmap(x_size, y_size)
    x_separator.fill(QColor(0, 0, 0, 0))
    y_separator = x_separator.copy(x_separator.rect())

    actual_width_y = round(width*ratio[0])
    actual_width_x = round(width*ratio[1])

    painter = QPainter(x_separator)

    painter.setPen(
        QPen(QColor(color_code), actual_width_x))

    painter.drawLine(0, int(y_size/2), x_size, int(y_size/2))

    painter.end()

    painter = QPainter(y_separator)

    painter.setPen(
        QPen(QColor(color_code), actual_width_y))

    painter.drawLine(int(x_size/2), 0, int(x_size/2), y_size)

    painter.end()

    return(x_separator, y_separator)


def find(element, json):
    keys = element.split('.')
    rv = json
    for key in keys:
        rv = rv[key]
    return rv


def calculate_new_dimensions(current_size, max_size):
    # Use -1 if you do not want to constrain in that dimension
    x_ratio = max_size[0]/current_size.width()
    y_ratio = max_size[1]/current_size.height()

    if max_size[0] < 0 and max_size[1] < 0:
        raise ValueError(
            msg=f"Size cannot be negative, given max size is {max_size}")

    if (x_ratio*current_size.height() > max_size[1]) or x_ratio < 0:
        new_x = y_ratio*current_size.width()
        new_y = max_size[1]
    else:
        new_x = max_size[0]
        new_y = x_ratio*current_size.height()
    return((round(new_x), round(new_y)))


def resize_image_to_max_size(image: QPixmap, max_size, eyesight_coordinates=None, fill_x=True, fill_y=True, zoom=1):
    current_size = image.size()
    x_ratio = max_size[0]/current_size.width()
    y_ratio = max_size[1]/current_size.height()

    if max_size[0] < 0 or max_size[1] < 0:
        raise ValueError(
            msg=f"Size cannot be negative, given max size is {max_size}")

    resized_eyesight = None
    effective_zoom = zoom
    zoom_step = 0.01
    zoom_flag = False
    while not zoom_flag:
        if (x_ratio < y_ratio):
            new_x = y_ratio*current_size.width()*effective_zoom
            new_y = max_size[1]*effective_zoom
            if eyesight_coordinates:
                resized_eyesight = (
                    round(eyesight_coordinates[0]*y_ratio*effective_zoom), round(eyesight_coordinates[1]*y_ratio*effective_zoom))
        else:
            new_x = max_size[0]*effective_zoom
            new_y = x_ratio*current_size.height()*effective_zoom
            if eyesight_coordinates:
                resized_eyesight = (
                    round(eyesight_coordinates[0]*x_ratio*effective_zoom), round(eyesight_coordinates[1]*x_ratio*effective_zoom))
        if not(new_x < max_size[0] and ("left" in crop_borders) and ("right" in crop_borders)):
            if not(new_y < max_size[1] and ("top" in crop_borders) and ("bottom" in crop_borders)):
                zoom_flag = True
        if not zoom_flag:
            effective_zoom += zoom_step

    new_size = (round(new_x), round(new_y))
    new_image = image.scaled(
        new_size[0], new_size[1], transformMode=Qt.TransformationMode.SmoothTransformation)

    # crop
    if not resized_eyesight:
        left = round(-(max_size[0] - new_x)/2)
        top = round(-(max_size[1] - new_y)/2)
        right = round((max_size[0] + new_x)/2)
        bottom = round((max_size[1] + new_y)/2)
    else:
        left = round(resized_eyesight[0]-(max_size[0]/2))
        top = round(resized_eyesight[1]-(max_size[1]/2))
        right = round(resized_eyesight[0]+(max_size[0]/2))
        bottom = round(resized_eyesight[1]+(max_size[1]/2))
        if left < 0:
            left = 0
            right = max_size[0]
        if top < 0:
            top = 0
            bottom = max_size[1]
        if right > new_x:
            right = new_x
            left = new_x - max_size[0]
        if bottom > new_y:
            bottom = new_y
            top = new_y - max_size[1]
    if max_size[0] > new_x:
        left = round(-(max_size[0] - new_x)/2)
        right = round((max_size[0] + new_x)/2)
        if ("left" in crop_borders):
            left = 0
            right = max_size[0]
        if ("right" in crop_borders):
            right = max_size[0]
            left = new_x - max_size[0]
    if max_size[1] > new_y:
        top = round(-(max_size[1] - new_y)/2)
        bottom = round((max_size[1] + new_y)/2)
        if ("top" in crop_borders):
            top = 0
            bottom = max_size[1]
        if ("bottom" in crop_borders):
            bottom = max_size[1]
            top = new_y - max_size[1]

    new_image = create_composite_image(new_image, QSize(max_size[0], max_size[1]), (-left, -top))

    return(new_image)


def create_composite_image(image, size, coordinates):
    background = QPixmap(size)
    background.fill(QColor(0, 0, 0, 0))
    painter = QPainter(background)
    painter.drawPixmap(int(coordinates[0]), int(coordinates[1]), image)
    painter.end()
    return(background)

def generate_multicharacter_positions(character_number, center=[0.5, 0.5], radius=0.3):
    positions = []

    # For 1 character, just center it
    if character_number == 1:
        radius = 0
    
    angle_rad = radians(270)

    if character_number == 2:
        angle_rad = 45

    for i in range(character_number):
        angle = angle_rad + radians(360/character_number) * i
        pos = [
            center[0] + cos(angle) * radius,
            center[1] + sin(angle) * radius
        ]
        positions.append(pos)

    return positions

def paste_image_matrix(thumbnail, path_matrix, max_size, paste_coordinates, eyesight_matrix, player_index=0, flip_p1=False, flip_p2=False, fill_x=True, fill_y=True, customZoom=1, horizontalAlign=50, verticalAlign=50, uncropped_edges=[]):
    separator_h_image, separator_v_image = generate_separator_images(
        thumbnail, separator_color_code, separator_width)
    num_line = len(path_matrix)

    global proportional_zoom, no_separator, is_preview

    # if (player_index == 1 and flip_p2) or (player_index == 0 and flip_p1):
    #     paste_coordinates = (
    #         round(thumbnail.width()-paste_coordinates[0]-max_size[0]), paste_coordinates[1])
        # thumbnail = thumbnail.transformed(QTransform().scale(-1, 1))

    for line_index in range(0, len(path_matrix)):
        line = path_matrix[line_index]

        eyesight_line = []

        if eyesight_matrix and len(eyesight_matrix) >= line_index:
            eyesight_line = eyesight_matrix[line_index]

        num_col = len(line)

        for col_index in reversed(range(0, len(line))):
            individual_max_size = (
                round(max_size[0]/num_col), round(max_size[1]/num_line))
            image_path = line[col_index]

            individual_paste_x = round(
                paste_coordinates[0] + col_index*individual_max_size[0])
            individual_paste_y = round(
                paste_coordinates[1] + line_index*individual_max_size[1])
            
            if no_separator != 0:
                individual_max_size = (max_size[0], round(max_size[1]/num_line))
                individual_paste_x = paste_coordinates[0]

            print(f"Processing asset: {image_path}")

            pix = QPixmap(image_path, "RGBA")
            painter = QPainter(thumbnail)

            eyesight_coordinates = (pix.width()/2, pix.height()/2)

            if len(eyesight_line) >= col_index:
                if eyesight_line[col_index] != None:
                    eyesight_coordinates = eyesight_line[col_index]
            
            uncropped_edge = []

            if len(uncropped_edges) >= line_index:
                if len(uncropped_edges[line_index]) >= col_index:
                    uncropped_edge = uncropped_edges[line_index][col_index]
            
            # For cropped assets, zoom to fill
            # Calculate max zoom
            zoom_x = max_size[0] / pix.width()
            zoom_y = max_size[1] / pix.height()

            min_zoom = 1

            print(uncropped_edge)

            if not uncropped_edge:
                if zoom_x > zoom_y:
                    min_zoom = zoom_x
                else:
                    min_zoom = zoom_y
            else:
                if 'u' in uncropped_edge and 'd' in uncropped_edge and 'l' in uncropped_edge and 'r' in uncropped_edge:
                    min_zoom = customZoom * proportional_zoom
                elif 'l' in uncropped_edge or 'r' in uncropped_edge:
                    min_zoom = zoom_y
                elif 'u' in uncropped_edge or 'd' in uncropped_edge:
                    min_zoom = zoom_x
                else:
                    min_zoom = customZoom * proportional_zoom

            global scale_fill_x, scale_fill_y
            if scale_fill_x and not scale_fill_y:
                min_zoom = zoom_x
            elif scale_fill_y and not scale_fill_x:
                min_zoom = zoom_y
            elif scale_fill_x and scale_fill_y:
                min_zoom = max(zoom_x, zoom_y)

            zoom = max(min_zoom, customZoom * min_zoom)

            xx = 0
            yy = 0

            customCenter = [horizontalAlign/100.0, verticalAlign/100.0]

            if player_index == 1:
                customCenter[0] = 1 - customCenter[0]

            if (player_index == 1 and flip_p2) or (player_index == 0 and flip_p1):
                customCenter[0] = 1 - customCenter[0]

            if not customCenter:
                customCenter = [0.5, 0.5]
            
            if no_separator != 0:
                customCenter = generate_multicharacter_positions(num_col)[col_index]

            xx = -eyesight_coordinates[0] * zoom + individual_max_size[0] * customCenter[0]
            yy = -eyesight_coordinates[1] * zoom + individual_max_size[1] * customCenter[1]

            original_xx = xx
            original_yy = yy
            
            # Max move X
            maxMoveX = individual_max_size[0] - pix.width() * zoom

            if not 'l' in uncropped_edge:
                if xx > 0: xx = 0
            
            if not 'r' in uncropped_edge:
                if xx < maxMoveX: xx = maxMoveX

            # Max move Y
            maxMoveY = individual_max_size[1] - pix.height() * zoom

            if not 'u' in uncropped_edge:
                if yy > 0: yy = 0
            
            if not 'd' in uncropped_edge:
                if yy < maxMoveY: yy = maxMoveY

            flip = False

            if (player_index == 1 and flip_p2) or (player_index == 0 and flip_p1):
                flip = True
            
            area = QPixmap(int(individual_max_size[0]), int(individual_max_size[1]))
            area.fill(QColor(0, 0, 0, 0))
            
            areaPaint = QPainter(area)

            areaPaint.drawPixmap(
                int(xx), int(yy),
                pix
                .scaled(int(zoom*pix.width()), int(zoom*pix.height()), transformMode=Qt.TransformationMode.SmoothTransformation)
            )

            areaPaint.end()

            if flip:
                area = area.transformed(QTransform().scale(-1, 1))

            painter.drawPixmap(
                int(individual_paste_x),
                int(individual_paste_y),
                area
            )
            painter.end()

            if is_preview:
                global font_1
                draw_text(
                    thumbnail,
                    "Scale: {0:.2f}".format(zoom) + '%'+"\n",
                    font_1, 20, (0, 0, 0),
                    (round(paste_coordinates[0] + col_index*round(max_size[0]/num_col)), individual_paste_y),
                    (round(max_size[0]/num_col), 20),
                    True,
                    (255,255,255),
                    (4, 2)
                )

                draw_text(
                    thumbnail,
                    f'Eyesight offset: ({int(original_xx - xx)}, {int(original_yy - yy)})',
                    font_1, 20, (0, 0, 0),
                    (round(paste_coordinates[0] + col_index*round(max_size[0]/num_col)), individual_paste_y+20),
                    (round(max_size[0]/num_col), 20),
                    True,
                    (255,255,255),
                    (4, 2)
                )
            
            # Vertical separator line
            if no_separator == 0:
                left = round(0)
                top = round(0)
                right = round(separator_v_image.width())
                bottom = round(individual_max_size[1])
                separator_v_image = separator_v_image.copy(
                    left, top, right-left, bottom-top)
                separator_v_offset = max_size[0]/num_col
                for i in range(1, num_col):
                    separator_paste_x = round(
                        paste_coordinates[0]-(separator_v_image.width()/2)+i*separator_v_offset)
                    separator_paste_y = individual_paste_y
                    separator_paste_coordinates = (
                        separator_paste_x, separator_paste_y)
                    composite_image = create_composite_image(
                        separator_v_image, thumbnail.size(), separator_paste_coordinates)
                    painter = QPainter(thumbnail)
                    painter.drawPixmap(0, 0, composite_image)
                    painter.end()

        # Horizontal separator line
        left = round(0)
        top = round(0)
        right = round(max_size[0])
        bottom = round(separator_h_image.height())
        separator_h_image = separator_h_image.copy(
            left, top, right-left, bottom-top)
        separator_h_offset = max_size[1]/num_line
        for i in range(1, num_line):
            separator_paste_x = paste_coordinates[0]
            separator_paste_y = round(
                paste_coordinates[1]-(separator_h_image.height()/2)+i*separator_h_offset)
            separator_paste_coordinates = (
                separator_paste_x, separator_paste_y)
            composite_image = create_composite_image(
                separator_h_image, thumbnail.size(), separator_paste_coordinates)
            painter = QPainter(thumbnail)
            painter.drawPixmap(0, 0, composite_image)
            painter.end()

    # if (player_index == 1 and flip_p2) or (player_index == 0 and flip_p1):
    #     thumbnail = thumbnail.transformed(QTransform().scale(-1, 1))

    return(thumbnail)


def paste_characters(thumbnail, data, all_eyesight, used_assets, flip_p1=False, flip_p2=False, fill_x=True, fill_y=True, zoom=1, horizontalAlign=50, verticalAlign=50):
    max_x_size = round(
        template_data["character_images"]["dimensions"]["x"]*ratio[0]/2)
    max_y_size = round(
        template_data["character_images"]["dimensions"]["y"]*ratio[1])
    max_size = (max_x_size, max_y_size)
    origin_x_coordinates = [round(template_data["character_images"]["position"]["x"]*ratio[0]), round(
        template_data["character_images"]["position"]["x"]*ratio[0])+max_x_size]
    origin_y_coordinates = [
        round(template_data["character_images"]["position"]["y"]*ratio[1]),
        round(template_data["character_images"]["position"]["y"]*ratio[1])
    ]

    path_matrices = []
    eyesight_matrices = []
    uncropped_edge_matrices = []

    for i in [0, 1]:
        team_index = i+1

        path_matrix = []
        eyesight_matrix = []
        uncropped_edge_matrix = []

        current_team = find(f"score.team.{team_index}.player", data)
        for player_key in current_team.keys():
            character_list = []
            eyesight_list = []
            uncropped_edge_list = []
            characters = find(f"{player_key}.character", current_team)
            for character_key in characters.keys():
                try:
                    image_path = find(
                        f"{character_key}.assets.{used_assets}.asset", characters)
                    eyesight_coordinates = None

                    character_path = find(
                        f"{character_key}.assets.{used_assets}", characters)

                    if character_path.get("eyesight"):
                        eyesight_coordinates = (
                            character_path.get("eyesight")["x"], character_path.get("eyesight")["y"])
                    
                    uncropped_edges = None

                    if character_path.get("uncropped_edge"):
                        uncropped_edges = character_path.get("uncropped_edge")
                    else:
                        uncropped_edges = []

                    if image_path:
                        character_list.append(image_path)
                        eyesight_list.append(eyesight_coordinates)
                        uncropped_edge_list.append(uncropped_edges)
                except KeyError:
                    None
            if character_list:
                # For team 1, characters must come from the center
                # so we have to reverse the array
                if i == 0:
                    character_list.reverse()
                    eyesight_list.reverse()
                    uncropped_edge_list.reverse()
                path_matrix.append(character_list)
                eyesight_matrix.append(eyesight_list)
                uncropped_edge_matrix.append(uncropped_edge_list)
        
        path_matrices.append(path_matrix)
        eyesight_matrices.append(eyesight_matrix)
        uncropped_edge_matrices.append(uncropped_edge_matrix)

    # Calculate proportional scaling
    global proportional_zoom
    proportional_zoom = 1

    max_width = 0
    max_height = 0

    for path_matrix in path_matrices:
        for player_pathes in path_matrix:
            for path in player_pathes:
                pix = QPixmap(path)
                max_width = max(max_width, pix.width())
                max_height = max(max_height, pix.height())
    
    proportional_zoom = min(proportional_zoom, max_size[0] / max_width * 2)
    proportional_zoom = min(proportional_zoom, max_size[1] / max_height * 2)

    for i in [0, 1]:
        team_index = i+1

        path_matrix = path_matrices[i]
        eyesight_matrix = eyesight_matrices[i]
        uncropped_edge_matrix = uncropped_edge_matrices[i]
        
        paste_x = origin_x_coordinates[i]
        paste_y = origin_y_coordinates[i]
        paste_coordinates = (paste_x, paste_y)
        
        thumbnail = paste_image_matrix(
            thumbnail, path_matrix, max_size, paste_coordinates, eyesight_matrix, i, flip_p1, flip_p2,
            fill_x, fill_y, zoom, horizontalAlign=horizontalAlign, verticalAlign=verticalAlign, uncropped_edges=uncropped_edge_matrix)

    return(thumbnail)


def draw_text(thumbnail, text, font_data, max_font_size, color, pos, container_size, outline, outline_color, padding=(32, 16)):
    painter = QPainter(thumbnail)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    font = QFont()
    family = font_data["name"]
    font.setFamily(family)
    font.setPixelSize(int(max_font_size))
    type = font_data["fontPath"]
    if "bold" in type.lower():
        font.setBold(True)
    if "italic" in type.lower():
        font.setItalic(True)

    fontMetrics = QFontMetricsF(font)

    while(fontMetrics.height()+2*padding[1] > int(container_size[1])):
        max_font_size -= 1
        if max_font_size <= 0:
            raise ValueError("Text too small, size cannot be negative")
        font.setPixelSize(int(max_font_size))
        fontMetrics = QFontMetricsF(font)

    stretch = 100

    while(fontMetrics.width(text)+2*padding[0] > int(container_size[0])):
        if stretch <= template_data["lower_text_stretch_limit"]:
            max_font_size -= 1
            if max_font_size <= 0:
                raise ValueError("Text too small, size cannot be negative")
            font.setPixelSize(int(max_font_size))
        else:
            stretch -= 1
            font.setStretch(stretch)
        fontMetrics = QFontMetricsF(font)

    text_x = round((pos[0]+padding[0]))
    text_y = round((pos[1]+padding[1]))
    text_coordinates = (text_x, text_y)
    print(text_coordinates)

    if outline:
        stroke_width = round(8*ratio[1])
    else:
        stroke_width = 0

    path = QPainterPath()

    painter.setFont(font)

    pen = QPen()

    if isinstance(color, tuple):
        color = [color] * len(text)
    
    pos_x = int(text_coordinates[0]) + (container_size[0] - padding[0]*2) / 2 - fontMetrics.width(text)/2

    for i, char in enumerate(text):
        path.clear()
        
        pen.setWidth(stroke_width)
        pen.setColor(QColor(
            outline_color[0],
            outline_color[1],
            outline_color[2]
        ))
        painter.setPen(pen)

        painter.setBrush(QColor(
            color[i][0],
            color[i][1],
            color[i][2]
        ))

        path.addText(
            pos_x,
            int(text_coordinates[1]) + fontMetrics.height()/4 +
            (container_size[1]-padding[1]*2)/2,
            font,
            char
        )

        painter.drawPath(path)

        pen.setWidth(0)
        pen.setColor(QColor(0, 0, 0, 0))
        painter.setPen(pen)
        painter.drawPath(path)

        pos_x += fontMetrics.width(char)

    painter.end()


def paste_player_text(thumbnail, data, use_team_names=False, use_sponsors=True):
    text_player_max_dimensions = (round(template_data["character_images"]["dimensions"]["x"]*ratio[0]/2.0), round(
        template_data["player_text"]["dimensions"]["y"]*ratio[1]))
    text_player_coordinates = [
        (round((template_data["character_images"]["position"]["x"])*ratio[0]), round(
            (template_data["player_text"]["height_center"]-(template_data["player_text"]["dimensions"]["y"]/2.0))*ratio[1])),
        (round((template_data["character_images"]["position"]["x"]+(2*template_data["character_images"]["dimensions"]["x"]/4.0))*ratio[0]),
         round((template_data["player_text"]["height_center"]-(template_data["player_text"]["dimensions"]["y"]/2.0))*ratio[1]))
    ]

    font_path = font_1
    # get_text_size_for_height(thumbnail, font_path, pixel_height)
    text_size = template_data["initial_font_size"]*ratio[1]
    player_text_color = text_color[0]


    for i in [0, 1]:
        team_index = i+1
        player_list = []
        color_mask = []
        if use_team_names:
            player_name = find(f"score.team.{team_index}.teamName", data)
        else:
            current_team = find(f"score.team.{team_index}.player", data)
            for key in current_team.keys():
                current_data = ""
                individual_color_mask = []

                team = current_team[key].get("team", "")
                if team:
                    current_data += team+" "
                    individual_color_mask += [sponsor_color[i]] * len(team+" ")

                current_data += current_team[key].get("name", "")
                individual_color_mask += [player_text_color["font_color"]] * len(current_team[key].get("name", ""))
                
                if current_data:
                    current_data = current_data.rstrip("[L]").strip()
                if (not use_sponsors) or (not current_data):
                    current_data = current_team[key].get("name")
                    individual_color_mask += [player_text_color["font_color"]] * len(current_data)
                    if current_data:
                        current_data = current_data.strip()
                if current_data:
                    player_list.append(current_data)
                    color_mask.append(individual_color_mask)

            player_name = " / ".join(player_list)
            
            final_color_mask = color_mask[0]

            if len(color_mask) > 0:
                for mask in color_mask[1:]:
                    final_color_mask += [player_text_color["font_color"]] * 3
                    final_color_mask += mask

        if use_team_names or len(player_list) > 1:
            player_type = "team"
        else:
            player_type = "player"

        print(f"Processing {player_type}: {player_name}")

        draw_text(
            thumbnail,
            player_name,
            font_path,
            text_size,
            final_color_mask,
            text_player_coordinates[i],
            text_player_max_dimensions,
            player_text_color["has_outline"],
            player_text_color["outline_color"],
            (round(template_data["player_text"]["x_offset"]*ratio[0]),
             round(template_data["player_text"]["y_padding"]*ratio[1]))
        )


def paste_round_text(thumbnail, data, display_phase=True):
    if display_phase:
        if template_data["info_text"]["horizontal"]:
            round_text_pos = (round(template_data["info_text"]["x_position"]*ratio[0]), round((template_data["info_text"]["height_center"]-(
                template_data["info_text"]["dimensions"]["y"]/2.0))*ratio[1]))
            phase_text_pos = (round(template_data["info_text"]["x_position"]*ratio[0])+round((template_data["info_text"]["dimensions"]["x"]/2.0)*ratio[0]), round(
                (template_data["info_text"]["height_center"]-(template_data["info_text"]["dimensions"]["y"]/2.0))*ratio[1]))

            text_max_dimensions = (round((template_data["info_text"]["dimensions"]["x"]/2.0)*ratio[0]), round(
                template_data["info_text"]["dimensions"]["y"]*ratio[1]))
        else:
            y_0 = template_data["info_text"]["height_center"] - \
                (template_data["info_text"]["dimensions"]["y"]/2.0)
            y_1 = template_data["info_text"]["height_center"]
            phase_text_pos = (
                round(template_data["info_text"]["x_position"]*ratio[0]), round(y_0*ratio[1]))
            round_text_pos = (
                round(template_data["info_text"]["x_position"]*ratio[0]), round(y_1*ratio[1]))

            text_max_dimensions = (round((template_data["info_text"]["dimensions"]["x"])*ratio[0]), round(
                (template_data["info_text"]["dimensions"]["y"]/2.0)*ratio[1]))

        text_size = template_data["initial_font_size"]*ratio[1]
        y_padding = round(template_data["info_text"]["y_padding"]*ratio[1])
        if not template_data["info_text"]["horizontal"]:
            y_padding = round(y_padding/2.0)

        draw_text(
            thumbnail,
            find(f"score.phase", data),
            font_2,
            text_size,
            text_color[1]["font_color"],
            phase_text_pos,
            text_max_dimensions,
            text_color[1]["has_outline"],
            text_color[1]["outline_color"],
            (round(template_data["info_text"]
             ["x_offset"]*ratio[0]/2.0), y_padding)
        )

        draw_text(
            thumbnail,
            find(f"score.match", data),
            font_2,
            text_size,
            text_color[1]["font_color"],
            round_text_pos,
            text_max_dimensions,
            text_color[1]["has_outline"],
            text_color[1]["outline_color"],
            (round(template_data["info_text"]
             ["x_offset"]*ratio[0]/2.0), y_padding)
        )
    else:
        round_text_pos = (round(template_data["info_text"]["x_position"]*ratio[0]), round((template_data["info_text"]["height_center"]-(
            template_data["info_text"]["dimensions"]["y"]/2.0))*ratio[1]))
        text_max_dimensions = (round((template_data["info_text"]["dimensions"]["x"])*ratio[0]), round(
            template_data["info_text"]["dimensions"]["y"]*ratio[1]))

        text_size = template_data["initial_font_size"]*ratio[1]

        draw_text(
            thumbnail,
            find(f"score.match", data),
            font_2,
            text_size,
            text_color[1]["font_color"],
            round_text_pos,
            text_max_dimensions,
            text_color[1]["has_outline"],
            text_color[1]["outline_color"],
            (round(template_data["info_text"]["x_offset"]*ratio[0]),
             round(template_data["info_text"]["y_padding"]*ratio[1]))
        )


def paste_main_icon(thumbnail, icon_path):
    if icon_path:
        max_x_size = round(
            template_data["icons_position"]["main"]["dimensions"]["x"]*ratio[0])
        max_y_size = round(
            template_data["icons_position"]["main"]["dimensions"]["y"]*ratio[1])
        max_size = (max_x_size, max_y_size)

        icon_image = QPixmap(icon_path, 'RGBA')
        icon_size = calculate_new_dimensions(icon_image.size(), max_size)
        icon_image = icon_image.transformed(
            QTransform().scale(
                icon_size[0]/icon_image.width(), icon_size[1]/icon_image.height()),
            Qt.TransformationMode.SmoothTransformation)

        x_offset = template_data["base_ratio"]["x"] / 2.0
        if template_data["icons_position"]["bind_to_character_images"]:
            x_offset = template_data["character_images"]["dimensions"]["x"] / \
                2.0 + template_data["character_images"]["position"]["x"]

        y_offset = template_data["icons_position"]["y_offset"]
        if template_data["icons_position"]["bind_to_character_images"]:
            y_offset = y_offset + \
                template_data["character_images"]["position"]["y"]
        if template_data["icons_position"]["align"].lower() == "bottom":
            y_offset = template_data["base_ratio"]["y"] - \
                template_data["icons_position"]["y_offset"] - \
                icon_image.height()/ratio[1]
            print(y_offset)
            if template_data["icons_position"]["bind_to_character_images"]:
                y_offset = template_data["character_images"]["position"]["y"] + template_data["character_images"]["dimensions"]["y"] - \
                    template_data["icons_position"]["y_offset"] - \
                    icon_image.height()/ratio[1]

        icon_x = round(x_offset*ratio[0] - icon_size[0]/2)
        icon_y = y_offset*ratio[1]
        icon_coordinates = (icon_x, icon_y)
        composite_image = create_composite_image(
            icon_image, thumbnail.size(), icon_coordinates)

        painter = QPainter(thumbnail)
        painter.drawPixmap(0, 0, composite_image)
        painter.end()
    return(thumbnail)


def paste_side_icon(thumbnail, icon_path_list):
    if len(icon_path_list) > 2:
        raise(ValueError(msg="Error: icon_path_list has 3 or more elements"))

    max_x_size = round(
        template_data["icons_position"]["side"]["dimensions"]["x"]*ratio[0])
    max_y_size = round(
        template_data["icons_position"]["side"]["dimensions"]["y"]*ratio[0])
    max_size = (max_x_size, max_y_size)

    for index in range(0, len(icon_path_list)):
        icon_path = icon_path_list[index]
        if icon_path:
            icon_image = QPixmap(icon_path, 'RGBA')
            icon_size = calculate_new_dimensions(icon_image.size(), max_size)
            icon_image = icon_image.transformed(
                QTransform().scale(
                    icon_size[0]/icon_image.width(), icon_size[1]/icon_image.height()),
                Qt.TransformationMode.SmoothTransformation)

            y_offset = template_data["icons_position"]["y_offset"]
            if template_data["icons_position"]["bind_to_character_images"]:
                y_offset = y_offset + \
                    template_data["character_images"]["position"]["y"]
            if template_data["icons_position"]["align"].lower() == "bottom":
                y_offset = template_data["base_ratio"]["y"] - \
                    template_data["icons_position"]["y_offset"] - \
                    icon_image.height()/ratio[1]
                print(y_offset)
                if template_data["icons_position"]["bind_to_character_images"]:
                    y_offset = template_data["character_images"]["position"]["y"] + template_data["character_images"]["dimensions"]["y"] - \
                        template_data["icons_position"]["y_offset"] - \
                        icon_image.height()/ratio[1]

            x_offset = index*template_data["base_ratio"]["x"]
            if template_data["icons_position"]["bind_to_character_images"]:
                x_offset = template_data["character_images"]["position"]["x"] + \
                    index*template_data["character_images"]["dimensions"]["x"]
            x_offset = x_offset - \
                round(template_data["icons_position"]
                      ["side"]["x_offset"]) * ((index*2)-1)
            icon_x = x_offset*ratio[0] - index*icon_size[0]
            icon_y = y_offset*ratio[1]

            icon_coordinates = (round(icon_x), round(icon_y))
            composite_image = create_composite_image(
                icon_image, thumbnail.size(), icon_coordinates)

            painter = QPainter(thumbnail)
            painter.drawPixmap(0, 0, composite_image)
            painter.end()
    return(thumbnail)


def createFalseData(gameAssetManager: TSHGameAssetManager = None, used_assets: str = None):
    # Array [{"name", "asset"}]
    chars = []

    if gameAssetManager and len(gameAssetManager.instance.characters.keys()) > 0:

        for i in range(4):
            asset = None
            while (not asset):
                key = list(gameAssetManager.instance.characters.keys())[
                    random.randint(0, len(gameAssetManager.instance.characters)-1)]

                character = gameAssetManager.instance.characters[key]
                skin = random.randint(0, len(gameAssetManager.instance.characters[key]))

                data = gameAssetManager.instance.GetCharacterAssets(
                    character.get("codename"), skin)

                asset = data.get(used_assets)

                if not asset:
                    asset = data.get("full")
                if not asset:
                    asset = data.get("portrait")

            name = key
            if character.get("locale"):
                locale = TSHLocaleHelper.programLocale
                if locale.replace("-", "_") in character["locale"]:
                    name = character["locale"][locale.replace("-", "_")]
                elif re.split("-|_", locale)[0] in character["locale"]:
                    name = character["locale"][re.split("-|_", locale)[0]]

            chars.append({
                "name": name,
                "team": gameAssetManager.instance.selectedGame.get("codename").upper(),
                "asset": {
                    "assets": {
                        "full": asset
                    },
                    "codename": character["codename"],
                    "name": key,
                    "skin": "0"
                }
            })
    else:
        for i in range(4):
            chars.append({
                "name": QApplication.translate("app","Player {0}").format(i+1),
                "team": QApplication.translate("app","Sponsor {0}").format(i+1),
                "asset": {
                    "assets": {
                        "full": {
                            "asset": f"./assets/mock_data/mock_asset/full_character_{i}.png",
                            "eyesight": {
                                "x": 540,
                                "y": 126
                            }
                        }
                    },
                    "codename": "character",
                    "name": "Character",
                    "skin": "0"
                },
            })

    print(chars)

    data = {
        "game": {
            "codename": "test",
            "name": "Test",
            "smashgg_id": 0
        },
        "score": {
            "best_of": 0,
            "match": QApplication.translate("app","Winners Finals"),
            "phase": QApplication.translate("app","Pool {0}").format("A"),
            "team": {
                "1": {
                    "losers": False,
                    "player": {
                        "1": {
                            "character": {
                                "1": chars[0]["asset"],
                                "2": chars[1]["asset"]
                            },
                            "country": {},
                            "mergedName": f"{chars[0]['team']} | {chars[0]['name']}",
                            "name": chars[0]["name"],
                            "state": {},
                            "team": chars[0]["team"]
                        }
                    },
                    "score": 0,
                    "teamName": QApplication.translate("app","Team {0}").format("A")
                },
                "2": {
                    "losers": False,
                    "player": {
                        "1": {
                            "character": {
                                "1": chars[2]["asset"]
                            },
                            "country": {},
                            "mergedName": f"{chars[2]['team']} | {chars[2]['name']}",
                            "name": chars[2]["name"],
                            "state": {},
                            "team": chars[2]["team"]
                        },
                        "2": {
                            "character": {
                                "1": chars[3]["asset"]
                            },
                            "country": {},
                            "mergedName": f"{chars[3]['team']} | {chars[3]['name']}",
                            "name": chars[3]["name"],
                            "state": {},
                            "team": chars[3]["team"]
                        }
                    },
                    "score": 0,
                    "teamName": QApplication.translate("app","Team {0}").format("B")
                }
            }
        }
    }
    return data


def generate(settingsManager, isPreview=False, gameAssetManager=None):
    # can't import SettingsManager (ImportError: attempted relative import beyond top-level package) so.. parameter ?
    settings = settingsManager.Get("thumbnail")

    global is_preview
    is_preview = isPreview

    data_path = "./out/program_state.json"
    out_path = "./out/thumbnails" if not isPreview else "./tmp/thumbnail"
    tmp_path = "./tmp"

    # IMG PATH
    foreground_path = settings["foreground_path"]
    if not os.path.isfile(foreground_path):
        raise Exception(f"Foreground {foreground_path} doesn't exist !")
    background_path = settings["background_path"]
    if not os.path.isfile(background_path):
        raise Exception(f"Background {background_path} doesn't exist !")
    main_icon_path = settings["main_icon_path"]
    if main_icon_path and not os.path.isfile(main_icon_path):
        raise Exception(f"Main Icon {main_icon_path} doesn't exist !")
    side_icon_list = settings["side_icon_list"]
    # not blocking so empty
    if side_icon_list[0] and not os.path.isfile(side_icon_list[0]):
        print(f"Top Left Icon {side_icon_list[0]} doesn't exist !")
        side_icon_list[0] = ''
    if side_icon_list[1] and not os.path.isfile(side_icon_list[1]):
        print(f"Top Right Icon {side_icon_list[1]} doesn't exist !")
        side_icon_list[1] = ''
    # BOOLEAN
    display_phase = settings["display_phase"]
    use_team_names = settings["use_team_names"]
    use_sponsors = settings["use_sponsors"]
    flip_p1 = settings["flip_p1"]
    flip_p2 = settings["flip_p2"]

    font_list = ["./assets/font/OpenSans/OpenSans-Bold.ttf",
                 "./assets/font/OpenSans/OpenSans-Semibold.ttf"]
    if settings["font_list"][0]:
        font_list[0] = settings["font_list"][0]
    if settings["font_list"][1]:
        font_list[1] = settings["font_list"][1]

    global text_color
    text_color = [
        {
            "font_color": color_code_to_tuple(settings["font_color"][0]),
            "has_outline": settings["font_outline_enabled"][0],
            "outline_color": color_code_to_tuple(settings["font_outline_color"][0])
        },
        {
            "font_color": color_code_to_tuple(settings["font_color"][1]),
            "has_outline": settings["font_outline_enabled"][1],
            "outline_color": color_code_to_tuple(settings["font_outline_color"][1])
        }
    ]

    global sponsor_color
    sponsor_color = [
        color_code_to_tuple(settings.get("sponsor_font_color_1", ["#FFFFFF"])[0]),
        color_code_to_tuple(settings.get("sponsor_font_color_2", ["#FFFFFF"])[0])
    ]

    zoom = 1

    try:
        with open(data_path, 'rt', encoding='utf-8') as f:
            data = json.loads(f.read())
        # if data missing
        if not data.get("game").get("codename"):
            raise Exception(QApplication.translate("thumb_app", "Please select a game first"))
        # - if more than one player (team of 2,3 etc), not necessary because test is made on paste_player_text
        for i in [1, 2]:
            if 'name' not in data.get("score").get("team").get(str(i)).get("player").get("1"):
                raise Exception(QApplication.translate("thumb_app", "Player {0} tag missing").format(i))

        game_codename = data.get("game").get("codename")
        used_assets = settings[f"asset/{game_codename}"]
        asset_data_path = f"./user_data/games/{game_codename}/{used_assets}/config.json"
        zoom = settings.get(f"zoom/{game_codename}", 100)/100
    except Exception as e:
        if isPreview:
            game_codename = data.get("game").get("codename")
            data = createFalseData(
                gameAssetManager, settings.get(f"asset/{game_codename}"))
            used_assets = "full"
            asset_data_path = f"./assets/mock_data/mock_asset/config.json"
            zoom = settings.get(f"zoom/{game_codename}", 100)/100
        else:
            raise e

    with open(asset_data_path, 'rt', encoding='utf-8') as f:
        all_eyesight = json.loads(f.read()).get("eyesights")

    Path(tmp_path).mkdir(parents=True, exist_ok=True)
    # for i in range(0, len(font_list)):
    #     if font_list[i]["fontPath"].startswith("http"):
    #         tmp_font_dir = f"{tmp_path}/fonts"
    #         filename, extension = os.path.splitext(font_list[i]["fontPath"])
    #         filename = f"font_{i}{extension}"
    #         Path(tmp_font_dir).mkdir(parents=True, exist_ok=True)
    #         local_font_path = f"{tmp_font_dir}/{filename}"
    #         with open(local_font_path, 'wb') as f:
    #             font_response = requests.get(font_list[i]["fontPath"])
    #             f.write(font_response.content)
    #             font_list[i]["fontPath"] = local_font_path

    global font_1
    global font_2
    font_1 = font_list[0]
    font_2 = font_list[1]

    global separator_color_code
    global separator_width
    separator_color_code = settings["separator"]["color"]
    separator_width = settings["separator"]["width"]

    Path(out_path).mkdir(parents=True, exist_ok=True)

    foreground = QPixmap(foreground_path, "RGBA")
    background = QPixmap(background_path, "RGBA")
    global template_data
    with open(settings["thumbnail_type"], 'rt') as template_data_file:
        template_data = template_data_file.read()
        template_data = json.loads(template_data)

    if isPreview:
        background = background.scaled(
            int(background.width()/2),
            int(background.height()/2),
            transformMode=Qt.TransformationMode.SmoothTransformation
        )

    global ratio
    ratio = (background.width()/template_data["base_ratio"]["x"],
             background.height()/template_data["base_ratio"]["y"])
    
    global scale_fill_x, scale_fill_y
    scale_fill_x = settings.get(f"scaleToFillX/{game_codename}", 0)
    scale_fill_y = settings.get(f"scaleToFillY/{game_codename}", 0)

    global no_separator
    no_separator = settings.get(f"hideSeparators/{game_codename}", 0)

    foreground = foreground.scaled(
        background.width(),
        background.height(),
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    thumbnail = QPixmap(background.width(), background.height())
    thumbnail.fill(QColor(0, 0, 0, 0))

    composite_image = create_composite_image(
        background, thumbnail.size(), (0, 0))

    painter = QPainter(thumbnail)
    painter.drawPixmap(0, 0, composite_image)
    painter.drawPixmap(0, 0, background)
    painter.end()

    horizontalAlign = settings.get(f"horizontalAlign/{game_codename}", 50)
    verticalAlign = settings.get(f"verticalAlign/{game_codename}", 50)

    thumbnail = paste_characters(
        thumbnail, data, all_eyesight, used_assets, flip_p1, flip_p2, fill_x=True, fill_y=True, zoom=zoom, horizontalAlign=horizontalAlign, verticalAlign=verticalAlign)
    composite_image = create_composite_image(
        foreground, thumbnail.size(), (0, 0))

    painter = QPainter(thumbnail)
    painter.drawPixmap(0, 0, composite_image)
    painter.end()

    paste_player_text(thumbnail, data, use_team_names, use_sponsors)
    paste_round_text(thumbnail, data, display_phase)
    thumbnail = paste_main_icon(thumbnail, main_icon_path)
    thumbnail = paste_side_icon(thumbnail, side_icon_list)

    # TODO get char name
    if not isPreview:
        tag_player1 = find("score.team.1.player.1.name", data)
        tag_player2 = find("score.team.2.player.1.name", data)
        thumbnail_filename = f"{tag_player1}-vs-{tag_player2}-{datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
        thumbnail.save(f"{out_path}/{thumbnail_filename}.png")
        thumbnail.save(f"{out_path}/{thumbnail_filename}.jpg")
        if os.path.isdir(tmp_path):
            shutil.rmtree(tmp_path)
        print(
            f"Thumbnail successfully saved as {out_path}/{thumbnail_filename}.png and {out_path}/{thumbnail_filename}.jpg")
        return f"{out_path}/{thumbnail_filename}.png"
    else:
        thumbnail_filename = f"template"
        thumbnail.save(f"{out_path}/{thumbnail_filename}.png")
        print(
            f"Thumbnail successfully saved as {out_path}/{thumbnail_filename}.png")
        return f"{out_path}/{thumbnail_filename}.png"
