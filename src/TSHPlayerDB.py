import os
import json
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re
import csv
import traceback


class TSHPlayerDBSignals(QObject):
    db_updated = pyqtSignal()


class TSHPlayerDB:
    signals = TSHPlayerDBSignals()
    database = {}
    model: QStandardItemModel = None
    fieldnames = ["prefix", "gamerTag", "name", "twitter",
                  "country_code", "state_code", "mains", "colors"]

    def LoadDB():
        try:
            if os.path.exists("./local_players.csv") == False:
                with open('./local_players.csv', 'w', encoding='utf-8') as outfile:
                    spamwriter = csv.writer(outfile)
                    spamwriter.writerow(TSHPlayerDB.fieldnames)

            with open('./local_players.csv', 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for player in reader:
                    tag = player.get(
                        "prefix")+" "+player.get("gamerTag") if player.get("prefix") else player.get("gamerTag")
                    if tag not in TSHPlayerDB.database:
                        TSHPlayerDB.database[tag] = player

            TSHPlayerDB.SetupModel()
        except Exception as e:
            print(traceback.format_exc())

    def AddPlayers(players, overwrite=False):
        for player in players:
            if player is not None:
                tag = player.get(
                    "prefix")+" "+player.get("gamerTag") if player.get("prefix") else player.get("gamerTag")

                if not overwrite:
                    if tag not in TSHPlayerDB.database:
                        TSHPlayerDB.database[tag] = player
                    else:
                        TSHPlayerDB.database[tag].update(player)
                else:
                    TSHPlayerDB.database[tag] = player

        TSHPlayerDB.SaveDB()
        TSHPlayerDB.SetupModel()

    def DeletePlayer(tag):
        if tag in TSHPlayerDB.database:
            del TSHPlayerDB.database[tag]

        TSHPlayerDB.SaveDB()
        TSHPlayerDB.SetupModel()

    def SetupModel():
        TSHPlayerDB.model = QStandardItemModel()

        for player in TSHPlayerDB.database.values():
            if player is not None:
                tag = player.get(
                    "prefix")+" "+player.get("gamerTag") if player.get("prefix") else player.get("gamerTag")

                item = QStandardItem(tag)
                item.setData(player, Qt.ItemDataRole.UserRole)

                TSHPlayerDB.model.appendRow(item)

        TSHPlayerDB.signals.db_updated.emit()

    def SaveDB():
        try:
            with open('./local_players.csv', 'w', encoding="utf-8", newline='') as outfile:
                spamwriter = csv.DictWriter(
                    outfile, fieldnames=TSHPlayerDB.fieldnames, extrasaction="ignore")
                spamwriter.writeheader()

                for player in TSHPlayerDB.database.values():
                    if player is not None:
                        spamwriter.writerow(player)
        except Exception as e:
            print(traceback.format_exc())


TSHPlayerDB.LoadDB()
