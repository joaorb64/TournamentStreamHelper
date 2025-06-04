from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import requests
import os
import shutil
import traceback
import zipfile
import json
from loguru import logger
import glob


class TSHControllerHelperSignals(QObject):
    controllersUpdated = Signal()


class TSHControllerHelper(QObject):
    instance: "TSHControllerHelper" = None

    signals = TSHControllerHelperSignals()

    def __init__(self) -> None:
        super().__init__()
        self.controller_list = {}
        self.controllerModel = QStandardItemModel()

        self.UpdateControllerFile()
        self.BuildControllerTree()
        self.UpdateControllerModel()
    

    def UpdateControllerFile(self):
        try:
            url = 'https://github.com/Wolfy76700/ControllerDatabase/archive/refs/heads/main.zip'
            r = requests.get(url, allow_redirects=True)

            with open('./assets/controller.zip.tmp', 'wb') as zip_file:
                zip_file.write(r.content)

            try:
                # Extract ZIP
                if os.path.exists("./assets/controller_tmp"):
                    shutil.rmtree("./assets/controller_tmp")
                with zipfile.ZipFile('./assets/controller.zip.tmp', 'r') as zip_file:
                    os.mkdir('./assets/controller_tmp')
                    zip_file.extractall('./assets/controller_tmp')

                # Remove ZIP
                os.remove('./assets/controller.zip.tmp')

                # Move directory
                if os.path.exists("./assets/controller"):
                    shutil.rmtree("./assets/controller")
                os.rename(
                    './assets/controller_tmp',
                    './assets/controller'
                )

                logger.info("Controller files updated")
            except:
                logger.error("Controller files download failed")
        except Exception as e:
            logger.error(
                "Could not update /assets/controller: "+str(e))

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

                    controller_json = {
                        "name": config_json.get("name"),
                        "manufacturer": manufacturer,
                        "type": controller_type,
                        "icon_path": icon_path,
                        "config_path": f"{controller_directory}/config.json"
                    }
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
                    "manufacturer": self.controller_list[c].get("manufacturer"),
                    "type": self.controller_list[c].get("type"),
                    "codename": c
                }

                
                data["icon_path"] = self.controller_list[c].get("icon_path")
                if data["icon_path"]:
                    item.setIcon(QIcon(QPixmap.fromImage(QImage(data["icon_path"])))
                    )
                else:
                    item.setIcon(QIcon(QPixmap.fromImage(QImage('./assets/icons/cancel.svg')))
                    )
                
                if self.controller_list[c].get("name") != c:
                    item.setData(
                        f'{self.controller_list[c].get("name")}', Qt.ItemDataRole.EditRole)

                item.setData(data, Qt.ItemDataRole.UserRole)
                self.controllerModel.appendRow(item)

            self.controllerModel.sort(0)
        except:
            logger.error(traceback.format_exc())

TSHControllerHelper.instance = TSHControllerHelper()
