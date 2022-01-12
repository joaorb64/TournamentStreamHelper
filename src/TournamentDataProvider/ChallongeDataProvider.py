from typing import final
import requests
import os
import traceback
import re
import json
from Helpers.TSHDictHelper import deep_get
from TournamentDataProvider import TournamentDataProvider
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from Workers import Worker
import TSHTournamentDataProvider


class ChallongeDataProvider(TournamentDataProvider.TournamentDataProvider):

    def __init__(self, url) -> None:
        super().__init__(url)

    def GetTournamentData(self):
        pass

    def GetMatch(self):
        pass

    def GetMatches(self):
        final_data = []

        try:
            data = requests.get(
                self.url+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )
            print(data)

            data = json.loads(data.text)

            rounds = deep_get(data, "rounds", {})
            matches = deep_get(data, "matches_by_round", {})

            all_matches = []

            for round in matches.values():
                for match in round:
                    match["round_name"] = next(
                        r["title"] for r in rounds if r["number"] == match.get("round"))
                    all_matches.append(match)

            all_matches = [
                match for match in all_matches if match.get("state") == "open"]

            for match in all_matches:
                final_data.append({
                    "round_name": deep_get(match, "round_name"),
                    "p1_name": deep_get(match, "player1.display_name"),
                    "p2_name": deep_get(match, "player2.display_name")
                })

            print(final_data)
        except Exception as e:
            traceback.print_exc()

        return final_data

    def GetEntrants(self):
        self.threadpool = QThreadPool()
        worker = Worker(self.GetEntrantsWorker)
        worker.signals.progress.connect(self.GetEntrantsProgress)
        self.threadpool.start(worker)

    def GetEntrantsWorker(self, progress_callback):
        try:
            final_data = QStandardItemModel()

            data = requests.get(
                self.url+".json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )
            print(data)

            data = json.loads(data.text)

            rounds = deep_get(data, "rounds", {})
            matches = deep_get(data, "matches_by_round", {})

            all_matches = []

            for round in matches.values():
                for match in round:
                    match["round_name"] = next(
                        r["title"] for r in rounds if r["number"] == match.get("round"))
                    all_matches.append(match)

            all_entrants = {}

            for match in all_matches:
                for player in [match.get("player1"), match.get("player2")]:
                    if player:
                        if not player.get("id") in all_entrants:
                            playerData = {}
                            playerData["gamerTag"] = player.get("display_name")
                            playerData["picture"] = player.get("portrait_url")
                            item = QStandardItem(playerData["gamerTag"])
                            item.setData(playerData, Qt.ItemDataRole.UserRole)

                            final_data.appendRow(item)
                            all_entrants[player.get("id")] = playerData

            progress_callback.emit(final_data)

            print(final_data)
        except Exception as e:
            traceback.print_exc()

    def GetEntrantsProgress(self, progress):
        TSHTournamentDataProvider.TSHTournamentDataProvider.entrantsModel = progress
        TSHTournamentDataProvider.TSHTournamentDataProvider.signals.entrants_updated.emit()
