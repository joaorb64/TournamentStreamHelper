import requests
import os
import traceback
import re
import json
from ..Helpers.TSHDictHelper import deep_get
from ..TSHGameAssetManager import TSHGameAssetManager
from ..TSHPlayerDB import TSHPlayerDB
from .TournamentDataProvider import TournamentDataProvider
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from ..Workers import Worker


class ChallongeDataProvider(TournamentDataProvider):

    def __init__(self, url, threadpool, parent) -> None:
        super().__init__(url, threadpool, parent)
        self.name = "Challonge"

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
                    self.videogame = videogame

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

    def GetMatch(self, setId, progress_callback):
        finalData = {}

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
            data = json.loads(data.text)

            all_matches = self.GetAllMatchesFromData(data)

            match = next((m for m in all_matches if str(
                m.get("id")) == str(setId)), None)

            if match:
                finalData = self.ParseMatchData(match)
        except:
            traceback.print_exc()

        print(finalData)

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

            data = json.loads(data.text)

            all_matches = self.GetAllMatchesFromData(data)

            all_matches = [
                match for match in all_matches if match.get("state") in ["open", "pending"] and match.get("player1") and match.get("player2")]

            for match in all_matches:
                final_data.append(self.ParseMatchData(match))

            final_data.reverse()
        except Exception as e:
            traceback.print_exc()

        return final_data

    def GetAllMatchesFromData(self, data):
        rounds = deep_get(data, "rounds", {})
        matches = deep_get(data, "matches_by_round", {})

        all_matches = []

        for r, round in enumerate(matches.values()):
            for m, match in enumerate(round):
                match["round_name"] = next(
                    r["title"] for r in rounds if r["number"] == match.get("round"))
                if data.get("tournament", {}).get("tournament_type") == "round robin":
                    match["phase"] = "Round Robin"
                else:
                    match["phase"] = "Bracket"
                if r == len(matches.values()) - 1:
                    if m == 0:
                        match["isGF"] = True
                    elif m == 1:
                        match["isGFR"] = True
                all_matches.append(match)

        for group in deep_get(data, "groups", []):
            rounds = deep_get(group, "rounds", {})
            matches = deep_get(group, "matches_by_round", {})

            for round in matches.values():
                for match in round:
                    match["round_name"] = next(
                        r["title"] for r in rounds if r["number"] == match.get("round"))
                    match["phase"] = group.get("name")
                    all_matches.append(match)

        return all_matches

    def GetStreamMatchId(self, streamName):
        sets = self.GetMatches()

        streamSet = next(
            (s for s in sets if s.get("stream", None) ==
             streamName and s.get("is_current_stream_game")),
            None
        )

        return streamSet

    def GetUserMatchId(self, user):
        sets = self.GetMatches()

        userSet = next(
            (s for s in sets if s.get("p1_name")
             == user or s.get("p2_name") == user),
            None
        )

        if userSet and user == userSet.get("p2_name"):
            userSet["reverse"] = True

        return userSet

    def ParseMatchData(self, match):
        p1_split = deep_get(
            match, "player1.display_name").rsplit("|", 1)

        p1_gamerTag = p1_split[-1].strip()
        p1_prefix = p1_split[0].strip() if len(p1_split) > 1 else None
        p1_avatar = deep_get(match, "player1.portrait_url")

        p2_split = deep_get(
            match, "player2.display_name").rsplit("|", 1)

        p2_gamerTag = p2_split[-1].strip()
        p2_prefix = p2_split[0].strip() if len(p2_split) > 1 else None
        p2_avatar = deep_get(match, "player2.portrait_url")

        stream = deep_get(match, "station.stream_url", None)

        if not stream:
            stream = deep_get(
                match, "queued_for_station.stream_url", None)

        if stream:
            stream = stream.split("twitch.tv/")[1].replace("/", "")

        team1losers = False
        team2losers = False

        if match.get("isGF"):
            team1losers = False
            team2losers = True
        elif match.get("isGFR"):
            team1losers = True
            team2losers = True

        scores = match.get("scores")
        if len(match.get("scores")) < 2:
            scores = [None, None]

        return({
            "id": deep_get(match, "id"),
            "round_name": deep_get(match, "round_name"),
            "tournament_phase": match.get("phase"),
            "p1_name": deep_get(match, "player1.display_name"),
            "p2_name": deep_get(match, "player2.display_name"),
            "entrants": [
                [{
                    "gamerTag": p1_gamerTag,
                    "prefix": p1_prefix,
                    "avatar": p1_avatar
                }],
                [{
                    "gamerTag": p2_gamerTag,
                    "prefix": p2_prefix,
                    "avatar": p2_avatar
                }],
            ],
            "stream": stream,
            "is_current_stream_game": True if deep_get(match, "station.stream_url", None) else False,
            "team1score": scores[0],
            "team2score": scores[1],
            "team1losers": team1losers,
            "team2losers": team2losers,
        })

    def GetEntrants(self):
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

            all_matches = self.GetAllMatchesFromData(data)

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

                            playerData["avatar"] = player.get("portrait_url")

                            all_entrants[player.get("id")] = playerData

            TSHPlayerDB.AddPlayers(all_entrants.values())
        except Exception as e:
            traceback.print_exc()
