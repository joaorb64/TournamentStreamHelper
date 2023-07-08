from collections import Counter
import re
from time import sleep
from qtpy.QtCore import *
from qtpy.QtGui import QStandardItem, QStandardItemModel
import requests
import os
import traceback
from ..Helpers.TSHCountryHelper import TSHCountryHelper
from ..Helpers.TSHDictHelper import deep_get
from ..TSHGameAssetManager import TSHGameAssetManager
from ..TSHPlayerDB import TSHPlayerDB
from .TournamentDataProvider import TournamentDataProvider
import json
from ..Helpers.TSHLocaleHelper import TSHLocaleHelper
from ..TSHBracket import is_power_of_two

from ..Workers import Worker
import sys


class StartGGDataProvider(TournamentDataProvider):
    SetsQuery = None
    SetQuery = None
    UserSetQuery = None
    StreamSetsQuery = None
    EntrantsQuery = None
    TournamentDataQuery = None
    RecentSetsQuery = None
    LastSetsQuery = None
    HistorySetsQuery = None
    TournamentStandingsQuery = None
    TournamentPhasesQuery = None
    TournamentPhaseGroupQuery = None
    StreamQueueQuery = None

    player_seeds = {}

    def __init__(self, url, threadpool, parent) -> None:
        super().__init__(url, threadpool, parent)
        self.name = "StartGG"
        self.getMatchThreadPool = QThreadPool()
        self.getRecentSetsThreadPool = QThreadPool()

    def GetTournamentData(self, progress_callback=None):
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
                self.videogame = videogame
                self.parent.signals.game_changed.emit(videogame)

            finalData["tournamentName"] = deep_get(
                data, "data.event.tournament.name", "")
            finalData["eventName"] = deep_get(
                data, "data.event.name", "")
            finalData["numEntrants"] = deep_get(
                data, "data.event.numEntrants", 0)
            finalData["address"] = deep_get(
                data, "data.event.tournament.venueAddress", "")
            finalData["shortLink"] = deep_get(
                data, "data.event.tournament.shortSlug", "")
            finalData["startAt"] = deep_get(
                data, "data.event.tournament.startAt", "")
        except:
            traceback.print_exc()

        return finalData

    def GetIconURL(self):
        url = None

        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "TournamentIconQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": '''
                        query TournamentIconQuery($eventSlug: String!) {
                            event(slug: $eventSlug) {
                                tournament{
                                    images(type: "profile") {
                                        type
                                        url
                                    }
                                }
                            }
                        }
                    '''
                }
            )
            data = json.loads(data.text)

            images = deep_get(data, "data.event.tournament.images", [])

            if len(images) > 0:
                url = images[0]["url"]
        except:
            traceback.print_exc()

        return url

    def GetTournamentPhases(self, progress_callback=None):
        phases = []

        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "TournamentPhasesQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.TournamentPhasesQuery
                }

            )

            data = json.loads(data.text)
            print(data)

            for phase in deep_get(data, "data.event.phases", []):
                phaseObj = {
                    "id": phase.get("id"),
                    "name": phase.get("name"),
                    "groups": []
                }

                for phaseGroup in deep_get(phase, "phaseGroups.nodes", []):
                    phaseObj["groups"].append({
                        "id": phaseGroup.get("id"),
                        "name": TSHLocaleHelper.phaseNames.get("group").format(phaseGroup.get('displayIdentifier')),
                        "bracketType": phaseGroup.get("bracketType")
                    })

                phases.append(phaseObj)
        except:
            traceback.print_exc()

        return phases

    def GetTournamentPhaseGroup(self, id, progress_callback=None):
        finalData = {}

        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "TournamentPhaseGroupQuery",
                    "variables": {
                        "id": id,
                        "videogameId": TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id")
                    },
                    "query": StartGGDataProvider.TournamentPhaseGroupQuery
                }
            )
            data = json.loads(data.text)

            oldData = requests.get(
                f"https://api.smash.gg/phase_group/{id}",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                }
            )
            oldData = json.loads(oldData.text)

            seeds = deep_get(data, "data.phaseGroup.seeds.nodes", [])
            seeds.sort(key=lambda s: s.get("seedNum"))

            seedMap: list = deep_get(data, "data.phaseGroup.seedMap.1")

            if seedMap:
                seedMap = [s if s != "bye" else -1 for s in seedMap]
                finalData["seedMap"] = seedMap

            teams = []

            for seed in seeds:
                team = {}
                participants = deep_get(seed, "entrant.participants")

                if participants is not None:
                    if len(participants) > 1:
                        team["name"] = deep_get(seed, "entrant.name")

                    team["players"] = []

                    for entrant in participants:
                        team["players"].append(StartGGDataProvider.ProcessEntrantData(
                            entrant, deep_get(seed, "entrant.paginatedSets.nodes")))

                teams.append(team)

            finalData["entrants"] = teams

            sets = deep_get(data, "data.phaseGroup.sets.nodes", [])

            # Preview IDs cannot be sorted normally
            # They follow the format: preview_2004442_1_5
            # Where ( preview_2004442_1_1 < preview_2004442_1_11 < preview_2004442_1_2 )
            isPreview = any("preview" in str(s.get("id")) for s in sets)

            if not isPreview:
                sets.sort(key=lambda s: (
                    abs(int(s.get("round"))), s.get("id")))
            else:
                sets.sort(key=lambda s: (abs(int(s.get("round"))),
                          int(s.get("id").split("_")[-1])))

            finalSets = {}

            for s in sets:
                print(s)

                round = int(s.get("round"))

                if not str(round) in finalSets:
                    finalSets[str(round)] = []

                finalSets[str(round)].append({
                    "score": [s.get("entrant1Score"), s.get("entrant2Score")],
                    "finished": s.get("state", 0) == 3
                })

            finalData["sets"] = finalSets

            finalData["progressionsIn"] = []

            for s in seeds:
                originPhaseId = deep_get(
                    s, "progressionSource.originPhaseGroup.id")
                if originPhaseId:
                    finalData["progressionsIn"].append(originPhaseId)

            finalData["winnersOnlyProgressions"] = deep_get(
                oldData, "entities.groups.hasCustomWinnerByes")

            for s in sets:
                if s.get("slots", []) and int(s.get("round")) == -2:
                    for slot in s.get("slots", []):
                        if slot.get("prereqType") == "seed":
                            finalData["winnersOnlyProgressions"] = False

                if finalData["winnersOnlyProgressions"] == False:
                    break

            finalData["customSeeding"] = deep_get(
                oldData, "entities.groups.hasCustomWinnerByes")

            if len(finalData["progressionsIn"]) > 0 and not finalData["winnersOnlyProgressions"]:
                originalKeys = list(finalData["sets"].keys())
                originalKeys.reverse()

                # If we have a non-power2 number of progressions in, we shift 2 rounds
                shift = 1 if is_power_of_two(
                    len(finalData["progressionsIn"])) else 2

                if deep_get(oldData, "entities.groups.hasCustomWinnerByes"):
                    shift = 1

                for roundKey in originalKeys:
                    round = int(roundKey)

                    # If we have progressions in, shift winners scores to the right
                    if round > 0:
                        finalData["sets"][str(
                            round+shift)] = finalData["sets"].pop(roundKey)

            finalData["progressionsOut"] = deep_get(
                data, "data.phaseGroup.progressionsOut")

            # StartGG gives us 2 sets for GFs, we want that divided into 2 rounds
            if finalData["progressionsOut"] == None or len(finalData["progressionsOut"]) == 0:
                lastRound = max([int(r) for r in finalData["sets"].keys()])
                if len(finalData["sets"][str(lastRound)]) > 1:
                    gfsReset = finalData["sets"][str(lastRound)].pop()
                    finalData["sets"][str(lastRound+1)] = [gfsReset]
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
            finalResult.update(result.get("new", {}))
            finalResult.update(result.get("old", {}))

            if result.get("new", {}).get("isOnline") == False:
                finalResult["bestOf"] = None

            finalResult["entrants"] = result.get("new", {}).get("entrants", [])

            if result.get("old", {}).get("entrants", []) is not None:
                for t, team in enumerate(result.get("old", {}).get("entrants", [])):
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

    def GetMatches(self, getFinished=False, progress_callback=None):
        try:
            print("Get matches", getFinished)
            states = [1, 6, 2]

            if getFinished:
                states.append(3)

            final_data = []

            page = 1
            totalPages = 1

            print("Fetching sets")

            while page <= totalPages:
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
                                "state": states,
                                "hideEmpty": True
                            },
                            "eventSlug": self.url.split("start.gg/")[1],
                            "page": page,
                            "perPage": 512
                        },
                        "query": StartGGDataProvider.SetsQuery
                    }
                )
                data = json.loads(data.text)

                totalPages = deep_get(
                    data, "data.event.sets.pageInfo.totalPages", 0)

                sets = deep_get(data, "data.event.sets.nodes", [])

                for _set in sets:
                    final_data.append(self.ParseMatchDataNewApi(_set))

                page += 1

                print(f"Fetching sets... {page}/{totalPages}")

            return (final_data)
        except Exception as e:
            traceback.print_exc()
            return (final_data)
        return ([])

    def TranslateRoundName(name: str):
        if name == None:
            return ""

        roundMapping = {
            "Grand Final Reset": "grand_final_reset",
            "Grand Final": "grand_final",
            "Winners Final": "winners_final",
            "Winners Semi-Final": "winners_semi_final",
            "Winners Quarter-Final": "winners_quarter_final",
            "Losers Final": "losers_final",
            "Losers Semi-Final": "losers_semi_final",
            "Losers Quarter-Final": "losers_quarter_final"
        }

        if name in roundMapping:
            return TSHLocaleHelper.matchNames.get(roundMapping.get(name))

        try:
            roundNumber = name.rsplit(" ")[-1]

            if "Winners" in name:
                return TSHLocaleHelper.matchNames.get("winners_round").format(roundNumber)
            elif "Losers" in name:
                return TSHLocaleHelper.matchNames.get("losers_round").format(roundNumber)
            elif name.startswith("Round "):
                return TSHLocaleHelper.matchNames.get("round").format(roundNumber)
        except:
            print(traceback.format_exc())

        return name

    def ParseMatchDataNewApi(self, _set):
        slots = deep_get(_set, "slots", [])
        p1 = slots[0] if len(slots) > 0 else {}
        p2 = slots[1] if len(slots) > 1 else {}

        # Add Pool identifier if phase has multiple Pools
        phase_name = deep_get(_set, "phaseGroup.phase.name")

        bracket_type = deep_get(_set, "phaseGroup.phase.bracketType", "")

        if deep_get(_set, "phaseGroup.phase.groupCount", 0) > 1:
            phase_name += " - " + TSHLocaleHelper.phaseNames.get(
                "group").format(deep_get(_set, "phaseGroup.displayIdentifier"))

        setData = {
            "id": _set.get("id"),
            "round_name": StartGGDataProvider.TranslateRoundName(_set.get("fullRoundText")),
            "tournament_phase": phase_name,
            "bracket_type": bracket_type,
            "p1_name": p1.get("entrant", {}).get("name", "") if p1 and p1.get("entrant", {}) != None else "",
            "p2_name": p2.get("entrant", {}).get("name", "") if p2 and p2.get("entrant", {}) != None else "",
            "stream": _set.get("stream", {}).get("streamName", "") if _set.get("stream", {}) != None else "",
            "isOnline": deep_get(_set, "event.isOnline"),
        }

        players = [[], []]

        entrants = [
            p1.get(
                "entrant", {}).get("participants", []) if p1.get(
                "entrant", {}) is not None else [],
            p2.get(
                "entrant", {}).get("participants", []) if p2.get(
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
                    if user.get("authorizations"):
                        if len(user.get("authorizations", [])) > 0:
                            playerData["twitter"] = user.get("authorizations", [])[
                                0].get("externalUsername")

                    if user.get("genderPronoun"):
                        playerData["pronoun"] = user.get(
                            "genderPronoun")

                    if user.get("images") and len(user.get("images")) > 0:
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

                if "id" not in playerData:
                    playerData["id"] = [
                        player.get("id"),
                        0
                    ]
                if playerData.get("id") and len(playerData.get("id")) > 0:
                    if playerData["id"][0] is not None:
                        playerData["seed"] = self.player_seeds.get(
                            playerData["id"][0])

                players[i].append(playerData)

        setData["entrants"] = players

        return setData

    def ParseMatchDataOldApi(self, respTasks):
        tasks = respTasks.get("entities", {}).get("setTask", [])

        selectedCharMap = {}

        for task in reversed(tasks):
            if task.get("action") in ["setup_character", "setup_strike", "setup_ban"]:
                selectedCharMap = task.get(
                    "metadata", {}).get("charSelections", {})
                if len(selectedCharMap) > 0:
                    break
            elif task.get("action") in ["report"]:
                allSelections = task.get("metadata", {}).get(
                    "report", {}).get("selections", [])

                if isinstance(allSelections, list):
                    for selection in allSelections:
                        if selection.get("selectionType") == "character":
                            selectedCharMap[str(selection.get("entrantId"))] = [
                                selection.get("selectionValue")]
                    if len(selectedCharMap) > 0:
                        break

        print(selectedCharMap)
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

        lastWinnerSlot = None

        if latestWinner:
            if str(latestWinner) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")):
                lastWinnerSlot = 0
            if str(latestWinner) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")):
                lastWinnerSlot = 1

        allStages = None
        strikedStages = None
        strikedBy = [[], []]
        selectedStage = None
        dsrStages = None
        currPlayer = 0
        dsr = False
        mdsr = False

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

                # Stages previously won in
                stageWins = [[], []]
                if base.get("stageWins"):

                    for entrantId, stageCodes in base.get("stageWins").items():
                        stages = []

                        for stageCode in stageCodes:
                            stages.append(TSHGameAssetManager.instance.GetStageFromStartGGId(
                                int(stageCode))[1].get("codename"))

                        if str(entrantId) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")):
                            stageWins[0] = stages
                        if str(entrantId) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")):
                            stageWins[1] = stages

                if base.get("useMDSR"):
                    mdsr = True
                if base.get("useDSR"):
                    dsr = True

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
            allStagesFinal = []
            for st in allStages:
                stage = TSHGameAssetManager.instance.GetStageFromStartGGId(
                    st)
                if stage:
                    allStagesFinal.append(stage[1])

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
                    int(selectedStage))
                if selectedStage:
                    selected = selectedStage[1].get("codename")

            stageStrikeState = {
                "strikedBy": strikedBy,
                "strikedStages": [striked],
                "stagesWon": stageWins,
                "selectedStage": selected,
                "currPlayer": currPlayer,
                "lastWinner": lastWinnerSlot,
                "currGame": respTasks.get("sets", {}).get("entrant1Score", 0) + respTasks.get("sets", {}).get("entrant2Score", 0)
            }

            rulesetState = {
                "neutralStages": allStagesFinal,
                "useDSR": dsr,
                "useMDSR": mdsr,
            }
        except:
            print("No Stage Strike Info Found")
            allStages = None
            strikedStages = None
            strikedBy = [[], []]
            selectedStage = None
            dsrStages = None
            currPlayer = 0
            stageStrikeState = {}
            rulesetState = {}

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

        return ({
            "stage_strike": stageStrikeState,
            "ruleset": rulesetState,
            "strikedBy": strikedBy,
            "entrants": entrants,
            "team1score": respTasks.get("entities", {}).get("sets", {}).get("entrant1Score", None),
            "team2score": respTasks.get("entities", {}).get("sets", {}).get("entrant2Score", None),
            "bestOf": respTasks.get("entities", {}).get("sets", {}).get("bestOf", None),
            "team1losers": team1losers,
            "team2losers": team2losers,
            "currPlayer": currPlayer
        })

    def GetStreamQueue(self, progress_callback=None):
        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "StreamQueueQuery",
                    "variables": {
                        "slug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.StreamQueueQuery
                }
            )
            data = json.loads(data.text)
            print("Stream queue loaded from StartGG")

            queues = deep_get(data, "data.event.tournament.streamQueue", [])

            finalData = {}

            if not queues:
                print("(No stream queue was found)")
                return finalData

            for q in queues:
                streamName = q.get("stream", {}).get("streamName", "")
                queueData = {}
                for setIndex, _set in enumerate(q.get("sets", [])):
                    phase_name = deep_get(_set, "phaseGroup.phase.name")
                    if deep_get(_set, "phaseGroup.phase.groupCount") > 1:
                        phase_name += " - " + TSHLocaleHelper.phaseNames.get(
                            "group").format(deep_get(_set, "phaseGroup.displayIdentifier"))

                    frt = _set.get("fullRoundText", "")
                    total_games = _set.get("totalGames", 0)

                    setData = {
                        "id": _set.get("id"),
                        "match": StartGGDataProvider.TranslateRoundName(frt),
                        "phase": phase_name,
                        "best_of": total_games,
                        "best_of_text": TSHLocaleHelper.matchNames.get("best_of").format(total_games) if total_games > 0 else "",
                        "state": _set.get("state"),
                        "team": {},
                        "station": deep_get(_set, "station.number", -1)
                    }

                    for teamIndex, slot in enumerate(_set.get("slots", [])):
                        entrant = slot.get("entrant", None)
                        if entrant:

                            losers = False
                            if "Gran" in frt:
                                if teamIndex == 1 or "Reset" in frt:
                                    losers = True

                            teamData = {
                                "teamName": entrant.get("name", ""),
                                "losers": losers,
                                "seed": entrant.get("seeds", [])[0].get("seedNum", 889977666),
                                "player": {}
                            }

                            # TODO : pull the state data

                            for playerIndex, participant in enumerate(entrant.get("participants", [])):
                                playerData = StartGGDataProvider.ProcessEntrantData(
                                    participant)
                                playerName = playerData.get("gamerTag", "")
                                team = playerData.get("prefix", "")

                                countryCode = playerData.get(
                                    "country_code", "")
                                stateCode = playerData.get("state_code", "")
                                countryData = TSHCountryHelper.countries.get(
                                    countryCode)
                                states = countryData.get("states")
                                stateData = {}
                                if stateCode:
                                    stateData = states[stateCode]

                                    path = f'./assets/state_flag/{countryCode}/{"_CON" if stateCode == "CON" else stateCode}.png'
                                    if not os.path.exists(path):
                                        path = None

                                    stateData.update({
                                        "asset": path
                                    })

                                playerData = {
                                    "country": TSHCountryHelper.GetBasicCountryInfo(countryCode),
                                    "state": stateData,
                                    "name": playerName,
                                    "team": team,
                                    "mergedName": team + "|" + playerName if isinstance(team, str) and team != "" else playerName,
                                    "pronoun": playerData.get("pronoun", ""),
                                    "real_name": playerData.get("name", ""),
                                    "online_avatar": playerData.get("avatar", ""),
                                    "twitter":  playerData.get("twitter", "")
                                }

                                teamData["player"][str(
                                    playerIndex + 1)] = playerData

                            setData["team"][str(teamIndex + 1)] = teamData

                    queueData[str(setIndex + 1)] = setData

                finalData[streamName] = queueData

            print(finalData)

            return finalData

            """
            if queues:
                lStreamName = streamName.lower()
                queue = next(
                    (q for q in queues if q and q.get("stream", {}).get("streamName", "").lower() == lStreamName),
                    {}
                )

                return queue
            """

        except Exception as e:
            traceback.print_exc()

        return {}

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
                lStreamName = streamName.lower()  # """performance"""
                queue = next(
                    (q for q in queues if q and q.get("stream", {}).get(
                        "streamName", "").lower() == lStreamName),
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
                        "userSlug": user,
                        "filters": {
                            "state": [1, 2, 4, 5, 6]
                        }
                    },
                    "query": StartGGDataProvider.UserSetQuery
                }
            )
            data = json.loads(data.text)

            print(data)

            sets = deep_get(data, "data.user.player.sets.nodes")

            # If there's no active set, get last finished set instead
            if sets is not None and len(sets) == 0:
                data = requests.post(
                    "https://www.start.gg/api/-/gql",
                    headers={
                        "client-version": "20",
                        'Content-Type': 'application/json'
                    },
                    json={
                        "operationName": "UserSetQuery",
                        "variables": {
                            "userSlug": user,
                            "filters": {
                            }
                        },
                        "query": StartGGDataProvider.UserSetQuery
                    }
                )
                data = json.loads(data.text)

                print(data)

                sets = deep_get(data, "data.user.player.sets.nodes")

            if sets and len(sets) > 0:
                userSet = sets[0]

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

    def GetLastSets(self, playerID, playerNumber, callback, progress_callback):
        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "PlayerLastSetsQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1],
                        "playerID": playerID
                    },
                    "query": StartGGDataProvider.LastSetsQuery
                }

            )

            data = json.loads(data.text)

            sets = deep_get(
                data, "data.event.sets.nodes", [])

            set_data = []

            for set in sets:
                if not set:
                    continue
                if not set.get("winnerId"):
                    continue

                phaseName = ""
                phaseIdentifier = ""

                # This is because a display identifier at a major (Ex. Pools C12) will return C12,
                # otherwise startgg will just return a string containing "1"
                if deep_get(set, "phaseGroup.displayIdentifier") != "1":
                    phaseIdentifier = deep_get(
                        set, "phaseGroup.displayIdentifier")
                phaseName = deep_get(set, "phaseGroup.phase.name")

                player1Info = set.get("slots", [{}])[0].get("entrant", {}).get(
                    "participants", [{}])[0].get("player", {})

                player2Info = set.get("slots", [{}])[1].get("entrant", {}).get(
                    "participants", [{}])[0].get("player", {})

                players = ["1", "2"]

                if player1Info.get("id") != playerID:
                    players.reverse()

                player_set = {
                    "phase_id": phaseIdentifier,
                    "phase_name": phaseName,
                    "round_name": StartGGDataProvider.TranslateRoundName(set.get("fullRoundText")),
                    f"player{players[0]}_score": set.get("entrant1Score"),
                    f"player{players[0]}_team": player1Info.get("prefix"),
                    f"player{players[0]}_name": player1Info.get("gamerTag"),
                    f"player{players[1]}_score": set.get("entrant2Score"),
                    f"player{players[1]}_team": player2Info.get("prefix"),
                    f"player{players[1]}_name": player2Info.get("gamerTag")
                }

                set_data.append(player_set)

            callback.emit(
                {"playerNumber": playerNumber, "last_sets": set_data})
        except Exception as e:
            traceback.print_exc()
            callback.emit({"playerNumber": playerNumber, "last_sets": []})

    def GetPlayerHistoryStandings(self, playerID, playerNumber, gameType, callback, progress_callback):
        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "TournamentHistoryDataQuery",
                    "variables": {
                        "playerID": playerID,
                        "gameID": gameType
                    },
                    "query": StartGGDataProvider.HistorySetsQuery
                }

            )

            data = json.loads(data.text)

            sets = deep_get(
                data, "data.player.recentStandings", [])

            set_data = []

            for set in sets:
                if not set:
                    continue
                if not set.get("placement"):
                    continue

                event = deep_get(set, "entrant.event", [])
                tournament = deep_get(event, "tournament", [])

                try:
                    tournamentPicture = tournament.get("images")[0].get("url")
                except:
                    tournamentPicture = None
                    print(traceback.format_exc())

                player_history = {
                    "placement": set.get("placement"),
                    "event_name": event.get("name"),
                    "tournament_name": tournament.get("name"),
                    "tournament_picture": tournamentPicture,
                    "entrants": event.get("numEntrants"),
                    "event_date": event.get("startAt")
                }

                set_data.append(player_history)

            callback.emit({"playerNumber": playerNumber,
                          "history_sets": set_data})
        except Exception as e:
            callback.emit({"playerNumber": playerNumber, "history_sets": []})

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
                        "round": StartGGDataProvider.TranslateRoundName(_set.get("fullRoundText")),
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
                    data, "data.event.entrants.pageInfo.totalPages", 0)

                entrants = deep_get(data, "data.event.entrants.nodes", [])
                print("Entrants: ", len(entrants))

                for i, team in enumerate(entrants):
                    for j, entrant in enumerate(team.get("participants", [])):
                        playerData = StartGGDataProvider.ProcessEntrantData(
                            entrant)
                        if deep_get(team, "seeds", []) is not None and len(deep_get(team, "seeds", [])) > 0:
                            playerData["seed"] = deep_get(team, "seeds", [])[
                                0].get("seedNum", 0)
                            self.player_seeds[playerData["id"]
                                              [0]] = playerData["seed"]
                        players.append(playerData)

                TSHPlayerDB.AddPlayers(players)
                players = []

                page += 1
        except Exception as e:
            traceback.print_exc()

    def ProcessEntrantData(entrant, setData=[]):
        player = entrant.get("player")
        user = entrant.get("user")

        playerData = {}

        if player:
            playerData["prefix"] = player.get("prefix")
            playerData["gamerTag"] = player.get("gamerTag")
            playerData["name"] = player.get("name")

            # Main character
            playerSelections = Counter()

            sets = []

            if not setData:
                sets = deep_get(player, "sets.nodes", [])
            else:
                sets = setData

            playerId = player.get("id")

            if len(sets) > 0:
                for _set in sets:
                    games = _set.get("games", [])
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

            if user.get("authorizations"):
                if len(user.get("authorizations", [])) > 0:
                    playerData["twitter"] = user.get("authorizations", [])[
                        0].get("externalUsername")

            if user.get("genderPronoun"):
                playerData["pronoun"] = user.get(
                    "genderPronoun")

            if len(user.get("images", [])) > 0:
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
        if "id" not in playerData:
            playerData["id"] = [
                player.get("id"),
                0
            ]

        return (playerData)

    def GetStandings(self, playerNumber, progress_callback):
        try:
            data = requests.post(
                "https://www.start.gg/api/-/gql",
                headers={
                    "client-version": "20",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "TournamentStandingsQuery",
                    "variables": {
                        "playerNumber": playerNumber,
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.TournamentStandingsQuery
                }

            )

            data = json.loads(data.text)

            standings = deep_get(data, "data.event.standings.nodes", [])

            teams = []

            for standing in standings:
                team = {}

                participants = deep_get(standing, "entrant.participants")

                if len(participants) > 1:
                    team["name"] = deep_get(standing, "entrant.name")

                team["players"] = []

                for entrant in participants:
                    team["players"].append(StartGGDataProvider.ProcessEntrantData(
                        entrant, deep_get(standing, "entrant.paginatedSets.nodes")))

                teams.append(team)
            return (teams)
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

f = open("src/TournamentDataProvider/StartGGPlayerLastSetsQuery.txt", 'r')
StartGGDataProvider.LastSetsQuery = f.read()

f = open("src/TournamentDataProvider/StartGGPlayerTournamentHistoryQuery.txt", 'r')
StartGGDataProvider.HistorySetsQuery = f.read()

f = open("src/TournamentDataProvider/StartGGTournamentStandingsQuery.txt", 'r')
StartGGDataProvider.TournamentStandingsQuery = f.read()

f = open("src/TournamentDataProvider/StartGGTournamentPhasesQuery.txt", 'r')
StartGGDataProvider.TournamentPhasesQuery = f.read()

f = open("src/TournamentDataProvider/StartGGTournamentPhaseGroupQuery.txt", 'r')
StartGGDataProvider.TournamentPhaseGroupQuery = f.read()

f = open("src/TournamentDataProvider/StartGGStreamQueueQuery.txt", 'r')
StartGGDataProvider.StreamQueueQuery = f.read()
