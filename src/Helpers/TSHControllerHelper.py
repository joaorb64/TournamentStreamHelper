from tempfile import TemporaryDirectory

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import requests
import os
import pathlib
import shutil
import time
import traceback
import zipfile
import json
from loguru import logger
import glob

from .TSHDownloadHelper import DownloadDialog, download_file
from ..SettingsManager import SettingsManager
from pathlib import Path


class TSHControllerHelperSignals(QObject):
    controllersUpdated = Signal()


class TSHControllerHelper(QObject):
    instance: "TSHControllerHelper" = None

    signals = TSHControllerHelperSignals()

    def __init__(self) -> None:
        super().__init__()
        self.controller_list = {}
        self.controllerModel = QStandardItemModel()

    def init(self):
        if SettingsManager.Get("general.disable_controller_file_downloading", False):
            logger.debug("Skipping controller file download (SETTING ENABLED)")
        else:
            self.UpdateControllerFile()
        self.BuildControllerTree()
        self.UpdateControllerModel()

    def UpdateControllerFile(self):
        try:
            out_dir = pathlib.Path('./assets/controller')

            if out_dir.exists():
                modtime = out_dir.stat().st_mtime
                if time.time() - modtime <= (12 * 60 * 60):
                    logger.debug("Skipping controller db download.")
                    return

            url = 'https://github.com/Wolfy76700/ControllerDatabase/archive/refs/heads/main.zip'

            def extract_file(filename):
                with TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
                    try:
                        with zipfile.ZipFile(filename, 'r') as zip_file:
                            zip_file.extractall(tmp_dir)

                        # Move directory
                        if os.path.exists("./assets/controller"):
                            shutil.rmtree("./assets/controller")

                        shutil.move(tmp_dir, "./assets/controller")

                        logger.info("Controller files updated")
                        return True
                    except Exception:
                        logger.opt(exception=True).error("Failed to extract Controller files")
                return False

            DownloadDialog(
                url,
                filename=None,
                desc="Controller files",
                validator=extract_file,
                assume_size=(1024*1024*95) # ~95MB
            ).exec()

        except Exception as e:
            logger.opt(exception=True).error(
                "Could not update /assets/controller: ")

    def BuildControllerTree(self):
        controller_list = {}
        list_controller_directories = glob.glob("./assets/controller/ControllerDatabase-main/*/*/*/")
        if os.name == "nt":
            for i in range(len(list_controller_directories)):
                list_controller_directories[i] = list_controller_directories[i].replace("\\\\", "/")
                list_controller_directories[i] = list_controller_directories[i].replace("\\", "/")
        for controller_directory in list_controller_directories:
            if os.path.exists(f"{controller_directory}/config.json"):
                split = controller_directory.split("/")
                controller_id = f"{split[-4]}/{split[-3]}/{split[-2]}"
                # print(f"Loading: {controller_id}")
                with open(f"{controller_directory}/config.json", "rt", encoding="utf-8") as config_file:
                    config_json = json.loads(config_file.read())
                    if os.path.exists(f'{"/".join(split[:-2])}/config.json'):
                        with open(f'{"/".join(split[:-2])}/config.json', "rt", encoding="utf-8") as manufacturer_file:
                            manufacturer = json.loads(manufacturer_file.read()).get("name")
                            # print(f"Manufacturer: {manufacturer}")
                    else:
                        manufacturer = None

                    if os.path.exists(f'{"/".join(split[:-3])}/config.json'):
                        with open(f'{"/".join(split[:-3])}/config.json', "rt", encoding="utf-8") as controller_type_file:
                            controller_type = json.loads(controller_type_file.read()).get("name")
                            # print(f"Type: {controller_type}")
                    else:
                        controller_type = None

                    if os.path.exists(f"{controller_directory}/image.png"):
                        icon_path = f"{controller_directory}/image.png"
                    else:
                        icon_path = None
                        
                    if os.path.exists(f"{controller_directory}/icon.png"):
                        simple_icon_path = f"{controller_directory}/icon.png"
                    else:
                        simple_icon_path = None

                    # Get category icon
                    category_path = Path(controller_directory).parent.parent.relative_to("./")
                    if os.path.exists(f"./{category_path}/icon.png"):
                        category_icon_path = f"./{category_path}/icon.png"
                    else:
                        category_icon_path = None

                    controller_json = {
                        "name": config_json.get("name"),
                        "manufacturer": manufacturer,
                        "type": controller_type,
                        "icon_path": icon_path,
                        "config_path": f"{controller_directory}/config.json",
                        "simple_icon_path": simple_icon_path,
                        "category_icon_path": category_icon_path
                    }

                    if config_json.get("short_name"):
                        controller_json["short_name"] = config_json.get("short_name")
                    else:
                        controller_json["short_name"] = config_json.get("name")

                    controller_list[controller_id] = controller_json
        self.controller_list = controller_list


    def UpdateControllerModel(self):
        try:
            self.controllerModel = QStandardItemModel()

            # Add one empty
            item = QStandardItem("")
            self.controllerModel.appendRow(item)

            for c in self.controller_list.keys():
                item = QStandardItem()
                item.setData(c, Qt.ItemDataRole.EditRole)
                data = {
                    "name": self.controller_list[c].get("name"),
                    "short_name": self.controller_list[c].get("short_name"),
                    "manufacturer": self.controller_list[c].get("manufacturer"),
                    "type": self.controller_list[c].get("type"),
                    "codename": c
                }

                
                data["icon_path"] = self.controller_list[c].get("icon_path")
                data["simple_icon_path"] = self.controller_list[c].get("simple_icon_path")
                data["category_icon_path"] = self.controller_list[c].get("category_icon_path")
                if data["icon_path"]:
                    item.setIcon(QIcon(QPixmap.fromImage(QImage(data["icon_path"])))
                    )
                    width, height = QImage(data["icon_path"]).width(), QImage(data["icon_path"]).height()
                    data["icon_dimensions"] = {
                        "x": int(width),
                        "y": int(height)
                    }
                else:
                    item.setIcon(QIcon(QPixmap.fromImage(QImage('./assets/icons/cancel.svg')))
                    )
                
                if data["simple_icon_path"]:
                    width, height = QImage(data["simple_icon_path"]).width(), QImage(data["simple_icon_path"]).height()
                    data["simple_icon_dimensions"] = {
                        "x": int(width),
                        "y": int(height)
                    }

                if data["category_icon_path"]:
                    width, height = QImage(data["category_icon_path"]).width(), QImage(data["category_icon_path"]).height()
                    data["category_icon_dimensions"] = {
                        "x": int(width),
                        "y": int(height)
                    }

                if self.controller_list[c].get("name") != c:
                    item.setData(
                        f'{self.controller_list[c].get("name")}', Qt.ItemDataRole.EditRole)

                item.setData(data, Qt.ItemDataRole.UserRole)
                self.controllerModel.appendRow(item)

            self.controllerModel.sort(0)
        except:
            logger.error(traceback.format_exc())

TSHControllerHelper.instance = TSHControllerHelper()
