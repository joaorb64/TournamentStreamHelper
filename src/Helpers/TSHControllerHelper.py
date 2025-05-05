import re
import unicodedata
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import requests
import os
import shutil
import traceback
import zipfile
from .TSHDictHelper import deep_get
from ..TournamentDataProvider import TournamentDataProvider
from .TSHLocaleHelper import TSHLocaleHelper
import json
from loguru import logger


class TSHControllerHelperSignals(QObject):
    countriesUpdated = Signal()


class TSHControllerHelper(QObject):
    instance: "TSHControllerHelper" = None

    def __init__(self) -> None:
        super().__init__()
        self.UpdateControllerFile()

    def UpdateControllerFile(self):
        class DownloaderThread(QThread):
            def run(self):
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
                        TSHControllerHelper.LoadControllers()
                    except:
                        logger.error("Controller files download failed")
                except Exception as e:
                    logger.error(
                        "Could not update /assets/controller: "+str(e))
        downloaderThread = DownloaderThread(self)
        downloaderThread.start()


TSHControllerHelper.instance = TSHControllerHelper()
