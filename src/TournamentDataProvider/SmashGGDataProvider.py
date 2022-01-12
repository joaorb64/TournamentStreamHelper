from collections import Counter
from typing import final
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel
import requests
import os
import traceback
from Helpers.TSHCountryHelper import TSHCountryHelper
from Helpers.TSHDictHelper import deep_get
from TSHGameAssetManager import TSHGameAssetManager
from TSHPlayerDB import TSHPlayerDB
from TournamentDataProvider import TournamentDataProvider
import json
import TSHTournamentDataProvider

from Workers import Worker


class SmashGGDataProvider(TournamentDataProvider.TournamentDataProvider):
    SetsQuery = None
    EntrantsQuery = None

    def __init__(self, url) -> None:
        super().__init__(url)

    def GetTournamentData(self):
        pass

    def GetMatch(self):
        pass

    def GetMatches(self):
        try:
            data = requests.post(
                "https://smash.gg/api/-/gql",
                headers={
                    "client-version": "19",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "EventMatchListQuery",
                    "variables": {
                        "filters": {
                            "state": [
                                1,
                                6,
                                2,
                                3
                            ],
                            "hideEmpty": True
                        },
                        "eventSlug": self.url.split("smash.gg/")[1]
                    },
                    "query": SmashGGDataProvider.SetsQuery
                }

            )
            print(data)

            data = json.loads(data.text)

            sets = deep_get(data, "data.event.sets.nodes", [])
            final_data = []

            for _set in sets:
                setData = {
                    "round_name": _set.get("fullRoundText"),
                    "tournament_phase": deep_get(_set, "phaseGroup.phase.name"),
                    "p1_name": deep_get(_set, "paginatedSlots.nodes", [])[0].get("entrant", {}).get("name", ""),
                    "p2_name": deep_get(_set, "paginatedSlots.nodes", [])[1].get("entrant", {}).get("name", ""),
                }

                players = [[], []]

                entrants = [
                    deep_get(_set, "paginatedSlots.nodes", [])[0].get(
                        "entrant", {}).get("participants", []),
                    deep_get(_set, "paginatedSlots.nodes", [])[1].get(
                        "entrant", {}).get("participants", [])
                ]

                for i, team in enumerate(entrants):
                    for j, entrant in enumerate(team):
                        player = entrant.get("player")
                        user = entrant.get("user")

                        playerData = {}

                        if player:
                            playerData["prefix"] = player.get("prefix")
                            playerData["gamerTag"] = player.get("gamerTag")
                            playerData["name"] = player.get("name")

                            # Main character
                            playerSelections = Counter()

                            sets = deep_get(player, "sets.nodes", [])
                            playerId = player.get("id")
                            if len(sets) > 0:
                                games = sets[0].get("games", [])
                                if games and len(games) > 0:
                                    for game in games:
                                        selections = game.get("selections", [])
                                        if selections:
                                            for selection in selections:
                                                participants = selection.get(
                                                    "entrant", {}).get("participants", [])
                                                if len(participants) > 0:
                                                    participantId = participants[0].get(
                                                        "player", {}).get("id", None)
                                                    if participantId and participantId == playerId:
                                                        playerSelections[selection.get(
                                                            "selectionValue")] += 1

                            main = playerSelections.most_common(1)

                            if len(main) > 0:
                                playerData["smashggMain"] = main[0][0]

                        if user:
                            if len(user.get("authorizations", [])) > 0:
                                playerData["twitter"] = user.get("authorizations", [])[
                                    0].get("externalUsername")

                            if len(user.get("images")) > 0:
                                playerData["picture"] = user.get("images")[
                                    0].get("url")

                            if user.get("location"):
                                # Country to country code
                                if user.get("location").get("country"):
                                    for country in TSHCountryHelper.countries.values():
                                        if user.get("location").get("country") == country.get("name"):
                                            playerData["country_code"] = country.get(
                                                "code")
                                            break

                                # State -- direct
                                if user.get("location").get("state"):
                                    stateCode = user.get(
                                        "location").get("state")
                                    if stateCode:
                                        playerData["state_code"] = user.get(
                                            "location").get("state")
                                # State -- from city
                                elif user.get("location").get("city"):
                                    stateCode = TSHCountryHelper.FindState(
                                        playerData["country_code"], user.get("location").get("city"))
                                    if stateCode:
                                        playerData["state_code"] = stateCode

                            if playerData.get("smashggMain"):
                                main = TSHGameAssetManager.instance.GetCharacterFromSmashGGId(
                                    playerData.get("smashggMain"))
                                if main:
                                    playerData["mains"] = main[0]

                        players[i].append(playerData)

                setData["entrants"] = players

                final_data.append(setData)

            return(final_data)
        except Exception as e:
            traceback.print_exc()

    def GetEntrants(self):
        self.threadpool = QThreadPool()
        worker = Worker(self.GetEntrantsWorker)
        self.threadpool.start(worker)

    def GetEntrantsWorker(self, progress_callback):
        try:
            page = 1
            totalPages = 1
            #final_data = QStandardItemModel()
            players = []

            while page <= totalPages:
                print(page, "/", totalPages)
                data = requests.post(
                    "https://smash.gg/api/-/gql",
                    headers={
                        "client-version": "19",
                        'Content-Type': 'application/json'
                    },
                    json={
                        "operationName": "EventEntrantsListQuery",
                        "variables": {
                            "eventSlug": self.url.split("smash.gg/")[1],
                            "page": page
                        },
                        "query": SmashGGDataProvider.EntrantsQuery
                    }

                )

                data = json.loads(data.text)

                totalPages = deep_get(
                    data, "data.event.entrants.pageInfo.totalPages", [])

                entrants = deep_get(data, "data.event.entrants.nodes", [])
                print("Entrants: ", len(entrants))

                for i, team in enumerate(entrants):
                    for j, entrant in enumerate(team.get("participants", [])):
                        player = entrant.get("player")
                        user = entrant.get("user")

                        playerData = {}

                        if player:
                            playerData["prefix"] = player.get("prefix")
                            playerData["gamerTag"] = player.get("gamerTag")
                            playerData["name"] = player.get("name")

                            # Main character
                            playerSelections = Counter()

                            sets = deep_get(player, "sets.nodes", [])
                            playerId = player.get("id")
                            if len(sets) > 0:
                                games = sets[0].get("games", [])
                                if games and len(games) > 0:
                                    for game in games:
                                        selections = game.get("selections", [])
                                        if selections:
                                            for selection in selections:
                                                participants = selection.get(
                                                    "entrant", {}).get("participants", [])
                                                if len(participants) > 0:
                                                    participantId = participants[0].get(
                                                        "player", {}).get("id", None)
                                                    if participantId and participantId == playerId:
                                                        playerSelections[selection.get(
                                                            "selectionValue")] += 1

                            main = playerSelections.most_common(1)

                            if len(main) > 0:
                                playerData["smashggMain"] = main[0][0]

                        if user:
                            if len(user.get("authorizations", [])) > 0:
                                playerData["twitter"] = user.get("authorizations", [])[
                                    0].get("externalUsername")

                            if len(user.get("images")) > 0:
                                playerData["picture"] = user.get("images")[
                                    0].get("url")

                            if user.get("location"):
                                # Country to country code
                                if user.get("location").get("country"):
                                    for country in TSHCountryHelper.countries.values():
                                        if user.get("location").get("country") == country.get("name"):
                                            playerData["country_code"] = country.get(
                                                "code")
                                            break

                                # State -- direct
                                if user.get("location").get("state"):
                                    stateCode = user.get(
                                        "location").get("state")
                                    if stateCode:
                                        playerData["state_code"] = user.get(
                                            "location").get("state")
                                # State -- from city
                                elif user.get("location").get("city"):
                                    stateCode = TSHCountryHelper.FindState(
                                        playerData["country_code"], user.get("location").get("city"))
                                    if stateCode:
                                        playerData["state_code"] = stateCode

                            if playerData.get("smashggMain"):
                                main = TSHGameAssetManager.instance.GetCharacterFromSmashGGId(
                                    playerData.get("smashggMain"))
                                if main:
                                    playerData["mains"] = main[0]

                        players.append(playerData)

                TSHPlayerDB.AddPlayers(players)
                players = []

                page += 1
        except Exception as e:
            traceback.print_exc()


f = open(os.path.dirname(os.path.realpath(__file__)) + "/" +
         "SmashGGSetsQuery.txt", 'r')
SmashGGDataProvider.SetsQuery = f.read()

f = open(os.path.dirname(os.path.realpath(__file__)) + "/" +
         "SmashGGEntrantsQuery.txt", 'r')
SmashGGDataProvider.EntrantsQuery = f.read()
