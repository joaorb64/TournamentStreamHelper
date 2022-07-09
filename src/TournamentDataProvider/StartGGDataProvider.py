from collections import Counter
import re
from time import sleep
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel
import requests
import os
import traceback
from ..Helpers.TSHCountryHelper import TSHCountryHelper
from ..Helpers.TSHDictHelper import deep_get
from ..TSHGameAssetManager import TSHGameAssetManager
from ..TSHPlayerDB import TSHPlayerDB
from .TournamentDataProvider import TournamentDataProvider
import json

from ..Workers import Worker


class StartGGDataProvider(TournamentDataProvider):
    SetsQuery = None
    SetQuery = None
    UserSetQuery = None
    StreamSetsQuery = None
    EntrantsQuery = None
    TournamentDataQuery = None
    RecentSetsQuery = None

    def __init__(self, url, threadpool, parent) -> None:
        super().__init__(url, threadpool, parent)
        self.name = "StartGG"
        self.getMatchThreadPool = QThreadPool()
        self.getRecentSetsThreadPool = QThreadPool()

    def GetTournamentData(self):
        finalData = {}

        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "TournamentDataQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.TournamentDataQuery
                }

            )

            data = json.loads(data.text)

            videogame = deep_get(data, "data.event.videogame.id", None)
            if videogame:
                TSHGameAssetManager.instance.SetGameFromStartGGId(
                    videogame)
                self.videogame = videogame

            finalData["tournamentName"] = deep_get(
                data, "data.event.tournament.name", "")
            finalData["eventName"] = deep_get(
                data, "data.event.name", "")
            finalData["numEntrants"] = deep_get(
                data, "data.event.numEntrants", 0)
            finalData["address"] = deep_get(
                data, "data.event.tournament.venueAddress", "")
        except:
            traceback.print_exc()

        return finalData

    def GetMatch(self, setId):
        try:
            r = requests.get(
                f'https://www.start.gg/api/-/gg_api./set/{setId};bustCache=true;expand=["setTask"];fetchMostRecentCached=true',
                {
                    "extensions": {"cacheControl": {"version": 1, "noCache": True}},
                    "cacheControl": {"version": 1, "noCache": True},
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
            )

        except Exception as e:
            traceback.print_exc()
        return {}

    def GetMatch(self, setId, progress_callback):
        finalResult = {}

        try:
            pool = self.getMatchThreadPool

            result = {}

            fetchOld = Worker(self._GetMatchTasks, **{
                "progress_callback": None,
                "setId": setId
            })
            fetchOld.signals.result.connect(
                lambda value: result.update({"old": value}))
            pool.start(fetchOld)

            fetchNew = Worker(self._GetMatchNewApi, **{
                "progress_callback": None,
                "setId": setId
            })
            fetchNew.signals.result.connect(
                lambda value: result.update({"new": value}))
            pool.start(fetchNew)

            pool.waitForDone(5000)
            QCoreApplication.processEvents()

            finalResult = {}
            finalResult.update(result["new"])
            finalResult.update(result["old"])

            if result["new"].get("isOnline") == False:
                finalResult["bestOf"] = None

            finalResult["entrants"] = result["new"]["entrants"]

            if result["old"].get("entrants", []) is not None:
                for t, team in enumerate(result["old"].get("entrants", [])):
                    for p, player in enumerate(team):
                        if player["mains"]:
                            finalResult["entrants"][t][p]["mains"] = player["mains"]
                            finalResult["has_selection_data"] = True

        except Exception as e:
            traceback.print_exc()
        return finalResult

    def _GetMatchTasks(self, setId, progress_callback):
        r = requests.get(
            f'https://www.start.gg/api/-/gg_api./set/{setId};bustCache=true;expand=["setTask"];fetchMostRecentCached=true',
            {
                "extensions": {"cacheControl": {"version": 1, "noCache": True}},
                "cacheControl": {"version": 1, "noCache": True},
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
        )
        data = json.loads(r.text)
        return self.ParseMatchDataOldApi(data)

    def _GetMatchNewApi(self, setId, progress_callback):
        data = requests.post(
            "https://www.start.gg/api/-/gql",
            headers={
                "client-version": "20",
                'Content-Type': 'application/json'
            },
            json={
                "operationName": "SetQuery",
                "variables": {
                    "id": setId
                },
                "query": StartGGDataProvider.SetQuery
            }
        )
        data = json.loads(data.text)
        return self.ParseMatchDataNewApi(data.get("data", {}).get("set", {}))

    def GetMatches(self):
        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
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
                                # 3
                            ],
                            "hideEmpty": True
                        },
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.SetsQuery
                }

            )

            data = json.loads(data.text)

            sets = deep_get(data, "data.event.sets.nodes", [])
            final_data = []

            for _set in sets:
                final_data.append(self.ParseMatchDataNewApi(_set))

            return(final_data)
        except Exception as e:
            traceback.print_exc()

    def ParseMatchDataNewApi(self, _set):
        p1 = deep_get(_set, "slots", [])[0]
        p2 = deep_get(_set, "slots", [])[1]

        # Add Pool identifier if phase has multiple Pools
        phase_name = deep_get(_set, "phaseGroup.phase.name")

        if deep_get(_set, "phaseGroup.phase.groupCount") > 1:
            phase_name += " - Pool " + \
                deep_get(_set, "phaseGroup.displayIdentifier")

        setData = {
            "id": _set.get("id"),
            "round_name": _set.get("fullRoundText"),
            "tournament_phase": phase_name,
            "p1_name": p1.get("entrant", {}).get("name", "") if p1 and p1.get("entrant", {}) != None else "",
            "p2_name": p2.get("entrant", {}).get("name", "") if p2 and p2.get("entrant", {}) != None else "",
            "stream": _set.get("stream", {}).get("streamName", "") if _set.get("stream", {}) != None else "",
            "isOnline": deep_get(_set, "event.isOnline"),
        }

        players = [[], []]

        entrants = [
            deep_get(_set, "slots", [])[0].get(
                "entrant", {}).get("participants", []) if deep_get(_set, "slots", [])[0].get(
                "entrant", {}) is not None else [],
            deep_get(_set, "slots", [])[1].get(
                "entrant", {}).get("participants", []) if deep_get(_set, "slots", [])[1].get(
                "entrant", {}) is not None else [],
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
                        playerData["startggMain"] = main[0][0]

                if user:
                    if len(user.get("authorizations", [])) > 0:
                        playerData["twitter"] = user.get("authorizations", [])[
                            0].get("externalUsername")

                    if user.get("genderPronoun"):
                        playerData["pronoun"] = user.get(
                            "genderPronoun")

                    if len(user.get("images")) > 0:
                        playerData["avatar"] = user.get("images")[
                            0].get("url")

                    if user.get("id"):
                        playerData["id"] = [
                            player.get("id"),
                            user.get("id")
                        ]

                    if user.get("location"):
                        # Country to country code
                        if user.get("location").get("country"):
                            for country in TSHCountryHelper.countries.values():
                                if user.get("location").get("country") == country.get("en_name"):
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
                        elif user.get("location").get("city") and playerData.get("country_code"):
                            stateCode = TSHCountryHelper.FindState(
                                playerData["country_code"], user.get("location").get("city"))
                            if stateCode:
                                playerData["state_code"] = stateCode

                    if playerData.get("startggMain"):
                        main = TSHGameAssetManager.instance.GetCharacterFromStartGGId(
                            playerData.get("startggMain"))
                        if main:
                            playerData["mains"] = main[0]

                players[i].append(playerData)

        setData["entrants"] = players

        return setData

    def ParseMatchDataOldApi(self, respTasks):
        tasks = respTasks.get("entities", {}).get("setTask", [])

        selectedCharMap = {}

        for task in reversed(tasks):
            if task.get("action") == "setup_character" or task.get("action") == "setup_strike":
                selectedCharMap = task.get(
                    "metadata", {}).get("charSelections", {})
                break

        selectedChars = [[], []]

        for char in selectedCharMap.items():
            if str(char[0]) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")):
                selectedChars[0] = char[1]
            if str(char[0]) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")):
                selectedChars[1] = char[1]

        latestWinner = None

        for task in reversed(tasks):
            if len(task.get("metadata", [])) == 0:
                continue
            if task.get("active"):
                continue
            if task.get("metadata", {}).get("report", {}).get("winnerId", None) is not None:
                latestWinner = int(task.get("metadata", {}).get(
                    "report", {}).get("winnerId"))
                break

        allStages = None
        strikedStages = None
        strikedBy = [[], []]
        selectedStage = None
        dsrStages = None
        currPlayer = 0

        for task in reversed(tasks):
            if task.get("action") in ["setup_strike", "setup_stage", "setup_character", "setup_ban", "report"]:
                if len(task.get("metadata", [])) == 0:
                    continue

                base = task.get("metadata", {})

                if task.get("action") == "report":
                    base = base.get("report", {})

                if base.get("strikeStages", None) is not None:
                    allStages = base.get("strikeStages")
                elif base.get("banStages", None) is not None:
                    allStages = base.get("banStages")

                if base.get("strikeList", None) is not None:
                    strikedStages = base.get("strikeList")
                elif base.get("banList", None) is not None:
                    strikedStages = base.get("banList")

                if base.get("stageSelection", None) is not None:
                    selectedStage = base.get("stageSelection")
                elif base.get("stageId", None) is not None:
                    selectedStage = base.get("stageId")

                # cannot repeat stages in the set
                if base.get("useDSR") and base.get("stageWins"):
                    dsrStages = []

                    for stage_array in base.get("stageWins").values():
                        for stage in stage_array:
                            dsrStages.append(int(stage))
                # cannot pick stage where you won
                elif base.get("useMDSR") and base.get("stageWins"):
                    loser = next(
                        (p for p in base.get("stageWins").keys()
                            if int(p) != int(latestWinner)),
                        None
                    )

                    if loser is not None:
                        dsrStages = []
                        dsrStages = [int(s) for s in base.get(
                            "stageWins")[loser]]

                if base.get("strikeList"):
                    for stage_code, entrant in base.get("strikeList").items():
                        stage = TSHGameAssetManager.instance.GetStageFromStartGGId(
                            int(stage_code))

                        if stage:
                            codename = stage[1].get("codename")

                            if str(entrant) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")):
                                strikedBy[0].append(codename)
                            if str(entrant) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")):
                                strikedBy[1].append(codename)
                else:
                    banPlayer = 0

                    if str(latestWinner) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")):
                        banPlayer = 0
                    if str(latestWinner) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")):
                        banPlayer = 1

                    if base.get("banList", None) is not None:
                        for stage_code in base.get("banList"):
                            if stage_code == None:
                                continue
                            stage = TSHGameAssetManager.instance.GetStageFromStartGGId(
                                int(stage_code))
                            if stage:
                                codename = stage[1].get("codename")
                                strikedBy[banPlayer].append(codename)

                if latestWinner:
                    lastLoserSlot = 0

                    if str(latestWinner) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")):
                        lastLoserSlot = 1
                    if str(latestWinner) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")):
                        lastLoserSlot = 0

                    currPlayer = lastLoserSlot
                elif base.get("turn"):
                    for entrant, value in base.get("turn").items():
                        if str(entrant) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")) and value == True:
                            currPlayer = 1
                        if str(entrant) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")) and value == True:
                            currPlayer = 0

                if allStages == None and strikedStages == None and selectedStage == None:
                    continue

                if allStages == None:
                    continue

                break

        try:
            allStagesFinal = {}
            for st in allStages:
                stage = TSHGameAssetManager.instance.GetStageFromStartGGId(
                    st)
                if stage:
                    allStagesFinal[stage[1].get("codename")] = stage[1]

            striked = []
            if strikedStages is not None:
                for stage in strikedStages:
                    stage = TSHGameAssetManager.instance.GetStageFromStartGGId(
                        stage)
                    if stage:
                        striked.append(stage[1].get("codename"))

            selected = ""
            if selectedStage is not None:
                selectedStage = TSHGameAssetManager.instance.GetStageFromStartGGId(
                    selectedStage)
                if selectedStage:
                    selected = selectedStage[1]

            dsr = []
            if dsrStages:
                for stage in dsrStages:
                    stage = TSHGameAssetManager.instance.GetStageFromStartGGId(
                        stage)
                    if stage:
                        dsr.append(stage[1].get("codename"))

            stageStrikeState = {
                "stages": allStagesFinal,
                "strikedBy": strikedBy,
                "striked": striked,
                "selected": selected,
                "dsr": dsr,
                "currPlayer": currPlayer
            }
        except:
            print(traceback.format_exc())
            allStages = None
            strikedStages = None
            strikedBy = [[], []]
            selectedStage = None
            dsrStages = None
            currPlayer = 0
            stageStrikeState = {}

        entrants = [[], []]

        for i, entrantChars in enumerate(selectedChars):
            for char in entrantChars:
                entrants[i].append({
                    "mains": [TSHGameAssetManager.instance.GetCharacterFromStartGGId(char)[0], 0]
                })

        team1losers = False
        team2losers = False

        if respTasks.get("entities", {}).get("sets", {}).get("isGF", False):
            if "Reset" not in respTasks.get("entities", {}).get("sets", {}).get("fullRoundText", ""):
                team1losers = False
                team2losers = True
            else:
                team1losers = True
                team2losers = True

        return({
            "stage_strike": stageStrikeState,
            "strikedBy": strikedBy,
            "entrants": entrants if len(entrants[0]) > 0 and len(entrants[1]) > 0 else None,
            "team1score": respTasks.get("entities", {}).get("sets", {}).get("entrant1Score", None),
            "team2score": respTasks.get("entities", {}).get("sets", {}).get("entrant2Score", None),
            "bestOf": respTasks.get("entities", {}).get("sets", {}).get("bestOf", None),
            "team1losers": team1losers,
            "team2losers": team2losers,
            "currPlayer": currPlayer
        })

    def GetStreamMatchId(self, streamName):
        streamSet = None

        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "StreamSetsQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.StreamSetsQuery
                }
            )
            data = json.loads(data.text)

            eventId = deep_get(data, "data.event.id", None)

            queues = deep_get(data, "data.event.tournament.streamQueue", [])

            if queues:
                queue = next(
                    (q for q in queues if q and q.get(
                        "stream", {}).get("streamName", "").lower() == streamName.lower()),
                    None
                )

                if queue and len(queue.get("sets")) > 0:
                    queueSets = [s for s in queue.get("sets") if deep_get(
                        s, "event.id") == eventId]
                    if len(queueSets) > 0:
                        streamSet = queueSets[0]
        except Exception as e:
            traceback.print_exc()

        return streamSet

    def GetUserMatchId(self, user):
        matches = re.match(
            r".*start.gg/(user/[^/]*)", user)
        print(matches)
        if matches:
            user = matches.groups()[0]

        userSet = None

        try:
            print(user)
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "UserSetQuery",
                    "variables": {
                        "userSlug": user
                    },
                    "query": StartGGDataProvider.UserSetQuery
                }
            )
            data = json.loads(data.text)

            print(data)

            sets = deep_get(data, "data.user.player.sets.nodes")
            if sets and len(sets) > 0:
                userSet = sets[0]

                videogame = deep_get(userSet, "event.videogame.id", None)
                if videogame:
                    TSHGameAssetManager.instance.SetGameFromStartGGId(
                        videogame)
                    self.videogame = videogame

                self.parent.SetTournament(
                    "https://start.gg/"+deep_get(userSet, "event.slug"))

                playerId = deep_get(data, "data.user.player.id")
                slots = userSet.get("slots", [])

                # Check if player is in slot 2
                if len(slots) >= 2:
                    participants = deep_get(
                        slots[1], "entrant.participants", [])
                    for participant in participants:
                        p = participant.get("player", {}).get("id", None)
                        if p == playerId:
                            userSet["reverse"] = True
                            break

                print(userSet)
        except Exception as e:
            traceback.print_exc()

        return userSet

    def GetEntrants(self):
        worker = Worker(self.GetEntrantsWorker, **{
            "gameId": TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id"),
            "eventSlug": self.url.split("start.gg/")[1]
        })
        self.threadpool.start(worker)

    def GetRecentSets(self, id1, id2, callback, requestTime, progress_callback):
        try:
            id1 = [str(id1[0]), str(id1[1])]
            id2 = [str(id2[0]), str(id2[1])]

            pool = self.getRecentSetsThreadPool

            recentSets = []

            pool.clear()

            print("Get recent sets start")

            for _id1, _id2, inverted in [[id1, id2, False], [id2, id1, True]]:
                for i in range(5):
                    worker = Worker(self.GetRecentSetsWorker, **{
                        "id1": _id1,
                        "id2": _id2,
                        "page": (i+1),
                        "inverted": inverted
                    })
                    worker.signals.result.connect(lambda result: [
                        recentSets.extend(result)
                    ])
                    pool.start(worker)

            pool.waitForDone(20000)
            QCoreApplication.processEvents()
            byId = {_set.get("id"): _set for _set in recentSets}
            recentSets = list(byId.values())
            recentSets.sort(key=lambda s: s.get("timestamp"), reverse=True)
            print("Recent sets size:", len(recentSets))
            callback.emit({"sets": recentSets, "request_time": requestTime})
        except Exception as e:
            traceback.print_exc()
            callback.emit({"sets": [], "request_time": requestTime})

    def GetRecentSetsWorker(self, id1, id2, page, inverted, progress_callback):
        try:
            recentSets = []

            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "RecentSetsQuery",
                    "variables": {
                        "pid1": id1[0],
                        "uid1": id1[1],
                        "pid2": id2[0],
                        "uid2": id2[1],
                        "page": page,
                        "videogameId": TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id")
                    },
                    "query": StartGGDataProvider.RecentSetsQuery
                }
            )
            data = json.loads(data.text)

            events = deep_get(data, "data.user.events.nodes", [])

            for event in events:
                if not event:
                    continue
                if not event.get("sets"):
                    continue

                sets = deep_get(event, "sets.nodes")

                for _set in sets:
                    phaseName = ""
                    phaseIdentifier = ""

                    # This is because a display identifier at a major (Ex. Pools C12) will return C12,
                    # otherwise startgg will just return a string containing "1"
                    if deep_get(_set, "phaseGroup.displayIdentifier") != "1":
                        phaseIdentifier = deep_get(
                            _set, "phaseGroup.displayIdentifier")
                    phaseName = deep_get(_set, "phaseGroup.phase.name")

                    p1id = _set.get("slots", [{}])[0].get("entrant", {}).get(
                        "participants", [{}])[0].get("player", {}).get("id")
                    p2id = _set.get("slots", [{}])[1].get("entrant", {}).get(
                        "participants", [{}])[0].get("player", {}).get("id")

                    p1id = str(p1id)
                    p2id = str(p2id)

                    if not p1id in [id1[0], id2[0]] or not p2id in [id1[0], id2[0]]:
                        continue

                    if _set.get("entrant1Score") == -1 or _set.get("entrant2Score") == -1:
                        continue

                    playerToEntrant = {}

                    playerToEntrant[id1[0]] = str(_set.get("slots", [{}])[
                        0].get("entrant", {}).get("id"))
                    playerToEntrant[id2[0]] = str(_set.get("slots", [{}])[
                        1].get("entrant", {}).get("id"))

                    winner = 0

                    winner = 0 if str(_set.get("winnerId")
                                      ) == playerToEntrant[p1id] else 1

                    score = [0, 0]

                    if _set.get("entrant1Score") != None and _set.get("entrant2Score") != None:
                        if p1id == id1[0]:
                            score = [_set.get("entrant1Score"),
                                     _set.get("entrant2Score")]
                        else:
                            score = [_set.get("entrant2Score"),
                                     _set.get("entrant1Score")]
                    else:
                        if (p1id == id1[0] and winner == 0) or (p1id == id1[1] and winner == 1):
                            score = ["W", "L"]
                        else:
                            score = ["L", "W"]

                    if inverted:
                        score.reverse()
                        if winner == 1:
                            winner = 0
                        elif winner == 0:
                            winner = 1

                    entry = {
                        "id": _set.get("id"),
                        "tournament": deep_get(event, "tournament.name"),
                        "event": event.get("name"),
                        "online": event.get("isOnline"),
                        "score": score,
                        "timestamp": event.get("startAt"),
                        "winner": winner,
                        "round": _set.get("fullRoundText"),
                        "phase_name": phaseName,
                        "phase_id": phaseIdentifier
                    }
                    recentSets.append(entry)
            return recentSets
        except Exception as e:
            traceback.print_exc()
            return []

    def GetEntrantsWorker(self, eventSlug, gameId, progress_callback):
        try:
            page = 1
            totalPages = 1
            # final_data = QStandardItemModel()
            players = []

            while page <= totalPages:
                print(page, "/", totalPages)
                data = requests.post(
                    "https://www.start.gg/api/-/gql",
                    headers={
                        "client-version": "20",
                        'Content-Type': 'application/json'
                    },
                    json={
                        "operationName": "EventEntrantsListQuery",
                        "variables": {
                            "eventSlug": eventSlug,
                            "videogameId": gameId,
                            "page": page,
                        },
                        "query": StartGGDataProvider.EntrantsQuery
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

                            mains = playerSelections.most_common()

                            if len(mains) > 0:
                                playerData["startggMains"] = mains

                        if user:
                            playerData["id"] = [
                                player.get("id"),
                                user.get("id")
                            ]

                            if len(user.get("authorizations", [])) > 0:
                                playerData["twitter"] = user.get("authorizations", [])[
                                    0].get("externalUsername")

                            if user.get("genderPronoun"):
                                playerData["pronoun"] = user.get(
                                    "genderPronoun")

                            if len(user.get("images")) > 0:
                                playerData["avatar"] = user.get("images")[
                                    0].get("url")

                            if user.get("location"):
                                # Country to country code
                                if user.get("location").get("country"):
                                    for country in TSHCountryHelper.countries.values():
                                        if user.get("location").get("country") == country.get("en_name"):
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
                                        playerData.get("country_code", None), user.get("location", {}).get("city", None))
                                    if stateCode:
                                        playerData["state_code"] = stateCode

                            if playerData.get("startggMains"):
                                if TSHGameAssetManager.instance.selectedGame:
                                    gameCodename = TSHGameAssetManager.instance.selectedGame.get(
                                        "codename")

                                    mains = []

                                    for sggmain in playerData.get("startggMains"):
                                        main = TSHGameAssetManager.instance.GetCharacterFromStartGGId(
                                            sggmain[0])
                                        if main:
                                            mains.append([main[0]])

                                    playerData["mains"] = {
                                        gameCodename: mains
                                    }
                                else:
                                    playerData["mains"] = {}

                        players.append(playerData)

                TSHPlayerDB.AddPlayers(players)
                players = []

                page += 1
        except Exception as e:
            traceback.print_exc()


f = open("src/TournamentDataProvider/StartGGSetsQuery.txt", 'r')
StartGGDataProvider.SetsQuery = f.read()

f = open("src/TournamentDataProvider/StartGGSetQuery.txt", 'r')
StartGGDataProvider.SetQuery = f.read()

f = open("src/TournamentDataProvider/StartGGUserSetQuery.txt", 'r')
StartGGDataProvider.UserSetQuery = f.read()

f = open("src/TournamentDataProvider/StartGGStreamSetsQuery.txt", 'r')
StartGGDataProvider.StreamSetsQuery = f.read()

f = open("src/TournamentDataProvider/StartGGEntrantsQuery.txt", 'r')
StartGGDataProvider.EntrantsQuery = f.read()

f = open("src/TournamentDataProvider/StartGGTournamentDataQuery.txt", 'r')
StartGGDataProvider.TournamentDataQuery = f.read()

f = open("src/TournamentDataProvider/StartGGRecentSetsQuery.txt", 'r')
StartGGDataProvider.RecentSetsQuery = f.read()
