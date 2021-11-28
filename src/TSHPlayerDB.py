import os
import json
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re


class TSHPlayerDBSignals(QObject):
    db_updated = pyqtSignal()


class TSHPlayerDB:
    instance: "TSHPlayerDB" = None

    def __init__(self) -> None:
        self.signals = TSHPlayerDBSignals()

    def LoadGames(self):
        pass


if TSHPlayerDB.instance == None:
    TSHPlayerDB.instance = TSHPlayerDB()
