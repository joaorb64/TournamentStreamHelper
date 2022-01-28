from typing import final
import requests
import os
import traceback
import re
import json
from Helpers.TSHDictHelper import deep_get
from TSHGameAssetManager import TSHGameAssetManager
from TSHPlayerDB import TSHPlayerDB
from TournamentDataProvider import TournamentDataProvider
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from Workers import Worker
import TSHTournamentDataProvider


class ChallongeDataProvider(TournamentDataProvider.TournamentDataProvider):

    def __init__(self, url) -> None:
        super().__init__(url)

    def GetTournamentData(self):
        finalData = {}

        try:
            slug = re.findall(r"challonge\.com\/.*\/([^/]+)", self.url)
            if len(slug) > 0:
                slug = slug[0]

                data = requests.get(
                    f"https://challonge.com/en/search/tournaments.json?filters%5B&page=1&per=1&q={slug}",
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                        "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                        "Accept-Encoding": "gzip, deflate, br"
                    }
                )

                data = json.loads(data.text)

                collection = deep_get(data, "collection", [{}])[0]

                videogame = collection.get("filter", {}).get("id", None)
                if videogame:
                    TSHGameAssetManager.instance.SetGameFromChallongeId(
                        videogame)

                finalData["tournamentName"] = deep_get(collection, "name")

                details = collection.get("details", [])
                participantsElement = next(
                    (d for d in details if d.get("icon") == "fa fa-users"), None)
                if participantsElement:
                    participants = int(
                        participantsElement.get("text").split(" ")[0])
                    finalData["numEntrants"] = participants
                # finalData["address"] = deep_get(
                #     data, "data.event.tournament.venueAddress", "")
        except:
            traceback.print_exc()

        return finalData

    def GetMatch(self, id):
        finalData = {}

        try:
            data = requests.get(
                f"https://challonge.com/en/matches/{id}/details.json",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    "Accept-Encoding": "gzip, deflate, br"
                }
            )
            data = json.loads(data.text)

            finalData["team1score"] = deep_get(
                data, "participants.player1.scores", [None])[0]
            finalData["team2score"] = deep_get(
                data, "participants.player2.scores", [None])[0]
            finalData["clear"] = False
        except:
            traceback.print_exc()

        return finalData

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
                p1_split = deep_get(
                    match, "player1.display_name").rsplit("|", 1)

                p1_gamerTag = p1_split[-1].strip()
                p1_prefix = p1_split[0].strip() if len(p1_split) > 1 else None

                p2_split = deep_get(
                    match, "player2.display_name").rsplit("|", 1)

                p2_gamerTag = p2_split[-1].strip()
                p2_prefix = p2_split[0].strip() if len(p2_split) > 1 else None

                stream = deep_get(match, "station.stream_url", None)

                if not stream:
                    stream = deep_get(
                        match, "queued_for_station.stream_url", None)

                if stream:
                    stream = stream.split("twitch.tv/")[1].replace("/", "")

                final_data.append({
                    "id": deep_get(match, "id"),
                    "round_name": deep_get(match, "round_name"),
                    "tournament_phase": "Bracket",
                    "p1_name": deep_get(match, "player1.display_name"),
                    "p2_name": deep_get(match, "player2.display_name"),
                    "entrants": [
                        [{
                            "gamerTag": p1_gamerTag,
                            "prefix": p1_prefix
                        }],
                        [{
                            "gamerTag": p2_gamerTag,
                            "prefix": p2_prefix
                        }],
                    ],
                    "stream": stream,
                    "is_current_stream_game": True if deep_get(match, "station.stream_url", None) else False
                })

            print(final_data)
        except Exception as e:
            traceback.print_exc()

        return final_data

    def GetEntrants(self):
        self.threadpool = QThreadPool()
        worker = Worker(self.GetEntrantsWorker)
        self.threadpool.start(worker)

    def GetEntrantsWorker(self, progress_callback):
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

            all_entrants = {}

            for match in all_matches:
                for player in [match.get("player1"), match.get("player2")]:
                    if player:
                        if not player.get("id") in all_entrants:
                            playerData = {}

                            split = player.get("display_name").rsplit("|", 1)

                            gamerTag = split[-1].strip()
                            prefix = split[0].strip() if len(
                                split) > 1 else None

                            playerData["gamerTag"] = gamerTag
                            playerData["prefix"] = prefix

                            playerData["picture"] = player.get("portrait_url")

                            all_entrants[player.get("id")] = playerData

            TSHPlayerDB.AddPlayers(all_entrants.values())
        except Exception as e:
            traceback.print_exc()
