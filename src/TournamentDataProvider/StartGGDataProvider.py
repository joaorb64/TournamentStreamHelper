from collections import Counter
import re
from time import sleep
from qtpy.QtCore import *
from qtpy.QtGui import QStandardItem, QStandardItemModel
import requests
import os
import traceback
from loguru import logger
from ..Helpers.TSHCountryHelper import TSHCountryHelper
from ..Helpers.TSHDictHelper import deep_get
from ..Helpers.TSHDirHelper import TSHResolve
from ..TSHGameAssetManager import TSHGameAssetManager
from ..TSHPlayerDB import TSHPlayerDB
from .TournamentDataProvider import TournamentDataProvider
import orjson
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
    StationsQuery = None
    StationSetsQuery = None
    # request for a single set with only info relevant for a set that is yet to be played
    FutureSetQuery = None

    player_seeds = {}

    def __init__(self, url, threadpool, parent) -> None:
        super().__init__(url, threadpool, parent)
        self.name = "StartGG"
        self.getMatchThreadPool = QThreadPool()
        self.getRecentSetsThreadPool = QThreadPool()
        self.getStationMatchesThreadPool = QThreadPool()

    # Queries the provided URL until a proper 200 status code has been provided back
    #
    # This should work fine in theory unless an API restriction is added
    def QueryRequests(self, url=None, type=None, headers={}, jsonParams=None, params=None):
        try:
            requestCode = 0
            data = None
            headers.update({
                "client-version": "20",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
            })
            retries = 0
            while requestCode != 200 and retries < 5:
                data = type(
                    url,
                    headers=headers,
                    json=jsonParams,
                    params=params
                )
                requestCode = data.status_code
                retries += 1
            data = orjson.loads(data.text)
            return data
        except Exception as e:
            logger.error(traceback.format_exc())
            return {}

    def GetTournamentData(self, progress_callback=None, cancel_event=None):
        finalData = {}

        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "TournamentDataQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.TournamentDataQuery
                }
            )

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
            finalData["endAt"] = deep_get(
                data, "data.event.tournament.endAt", "")
            finalData["eventStartAt"] = deep_get(
                data, "data.event.startAt", "")
            finalData["eventEndAt"] = deep_get(
                data, "data.event.endAt", "")
        except:
            logger.error(traceback.format_exc())

        return finalData

    def GetIconURL(self):
        url = None

        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
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

            images = deep_get(data, "data.event.tournament.images", [])

            if len(images) > 0:
                url = images[0]["url"]
        except:
            logger.error(traceback.format_exc())

        return url

    def GetTournamentPhases(self, progress_callback=None, cancel_event=None):
        phases = []

        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "TournamentPhasesQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.TournamentPhasesQuery
                }
            )

            logger.info(data)

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
            logger.error(traceback.format_exc())

        return phases

    def GetTournamentPhaseGroup(self, id, progress_callback=None, cancel_event=None):
        finalData = {}

        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "TournamentPhaseGroupQuery",
                    "variables": {
                        "id": id,
                        "videogameId": TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id")
                    },
                    "query": StartGGDataProvider.TournamentPhaseGroupQuery
                }
            )

            oldData = self.QueryRequests(
                f"https://api.smash.gg/phase_group/{id}",
                type=requests.get
            )

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
                # logger.info(s)

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
            logger.error(traceback.format_exc())

        return finalData

    def GetMatch(self, setId, progress_callback, cancel_event):
        finalResult = None

        try:
            pool = self.getMatchThreadPool

            result = {}

            fetchOld = Worker(self._GetMatchTasks, **{
                "progress_callback": None,
                "cancel_event": None,
                "setId": setId
            })
            fetchOld.signals.result.connect(
                lambda value: result.update({"old": value}))
            pool.start(fetchOld)

            fetchNew = Worker(self._GetMatchNewApi, **{
                "progress_callback": None,
                "cancel_event": None,
                "setId": setId
            })
            fetchNew.signals.result.connect(
                lambda value: result.update({"new": value}))
            pool.start(fetchNew)

            pool.waitForDone(5000)
            QCoreApplication.processEvents()

            logger.debug(result)

            finalResult = {}
            finalResult.update(result.get("new", {}))
            finalResult.update(result.get("old", {}))

            winnerProgression = result.get("old", {}).get("winnerProgression")
            if winnerProgression:
                indicator = "qualifier_winners_indicator"

                if int(finalResult.get("round") or 0) < 0:
                    indicator = "qualifier_losers_indicator"

                indicator = TSHLocaleHelper.matchNames.get(indicator)

                winnerProgression = re.sub(
                    r"\s*[\(\{\[].*?[\)\}\]]", "", winnerProgression).strip()
                finalResult["round_name"] = TSHLocaleHelper.matchNames.get(
                    "qualifier").format(winnerProgression, indicator)

            if result.get("new", {}).get("isOnline") == False:
                finalResult["bestOf"] = None

            finalResult["entrants"] = result.get("new", {}).get("entrants", [])

            if result.get("old", {}).get("entrants", []) is not None:
                for t, team in enumerate(result.get("old", {}).get("entrants", [])):
                    for p, player in enumerate(team):
                        if player["mains"]:
                            try:
                                finalResult["entrants"][t][p]["mains"] = player["mains"]
                                finalResult["has_selection_data"] = True
                            except:
                                logger.debug(traceback.format_exc())

            logger.debug(f"Final result: {finalResult}")

        except Exception as e:
            logger.error(traceback.format_exc())
        return finalResult

    def _GetMatchTasks(self, setId, progress_callback, cancel_event):
        if "preview" in str(setId):
            return self.ParseMatchDataOldApi({})

        try:
            data = self.QueryRequests(
                f'https://www.start.gg/api/-/gg_api./set/{setId};bustCache=true;expand=["setTask"];fetchMostRecentCached=true',
                type=requests.get,
                params={
                    "extensions": {"cacheControl": {"version": 1, "noCache": True}},
                    "cacheControl": {"version": 1, "noCache": True},
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
            )
            return self.ParseMatchDataOldApi(data)
        except Exception as e:
            logger.error(traceback.format_exc())
            return {}

    def _GetMatchNewApi(self, setId, progress_callback, cancel_event):
        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "SetQuery",
                    "variables": {
                        "id": setId
                    },
                    "query": StartGGDataProvider.SetQuery
                }
            )
            logger.debug(data.get("data", {}).get("set", {}))
            return self.ParseMatchDataNewApi(data.get("data", {}).get("set", {}))
        except Exception as e:
            logger.error(traceback.format_exc())
            return {}

    def GetMatches(self, getFinished=False, progress_callback=None, cancel_event=None):
        try:
            logger.info("Get matches", getFinished)
            states = [1, 6, 2]

            if getFinished:
                states.append(3)

            final_data = []

            page = 1
            totalPages = 1

            logger.info("Fetching sets")

            while page <= totalPages and (cancel_event is None or not cancel_event.is_set()):
                data = self.QueryRequests(
                    "https://www.start.gg/api/-/gql",
                    type=requests.post,
                    jsonParams={
                        "operationName": "EventMatchListQuery",
                        "variables": {
                            "filters": {
                                "state": states,
                                "hideEmpty": True
                            },
                            "eventSlug": self.url.split("start.gg/")[1],
                            "page": page,
                            "perPage": 64
                        },
                        "query": StartGGDataProvider.SetsQuery
                    }
                )

                totalPages = deep_get(
                    data, "data.event.sets.pageInfo.totalPages", 0)

                sets = deep_get(data, "data.event.sets.nodes", [])
                newSets = []

                for _set in sets:
                    parsed = self.ParseMatchDataNewApi(_set)
                    final_data.append(parsed)
                    newSets.append(parsed)

                if progress_callback:
                    progress_callback.emit({
                        "progress": page,
                        "totalPages": totalPages,
                        "sets": newSets
                    })

                page += 1
                logger.info(f"Fetching sets... {page}/{totalPages}")
            return (final_data)
        except Exception as e:
            logger.error(traceback.format_exc())
            return (final_data)
        return ([])

    def GetStations(self, progress_callback=None, cancel_event=None):
        try:
            logger.info("Get stations")

            final_data = []

            logger.info("Fetching stations")

            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "Stations",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1],
                    },
                    "query": StartGGDataProvider.StationsQuery
                }
            )

            stations = deep_get(data, "data.event.stations.nodes", [])
            queues = deep_get(data, "data.event.tournament.streamQueue", [])

            if stations is not None:
                for station in stations:
                    stream = ""

                    if queues is not None:
                        stream = next((deep_get(s, "stream.streamName", None) for s in queues if str(
                            deep_get(s, "stream.id", None)) == str(station.get("streamId"))), "")

                    final_data.append({
                        "id": station.get("id"),
                        "identifier": station.get("number"),
                        "type": "station",
                        "stream": stream
                    })

            if queues is not None:
                for queue in queues:
                    if queue.get("stream") is not None:
                        stream = queue.get("stream")
                        final_data.append({
                            "id": stream.get("id"),
                            "identifier": stream.get("streamName"),
                            "type": "stream"
                        })

            return (final_data)
        except Exception as e:
            logger.error(traceback.format_exc())
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
            logger.error(traceback.format_exc())

        return name

    def ParseMatchDataNewApi(self, _set):
        try:
            slots = deep_get(_set, "slots", [])
            p1 = slots[0] if len(slots) > 0 else {}
            p2 = slots[1] if len(slots) > 1 else {}

            # Add Pool identifier if phase has multiple Pools
            phase_name = deep_get(_set, "phaseGroup.phase.name")

            bracket_type = deep_get(_set, "phaseGroup.phase.bracketType", "")

            isPools = deep_get(_set, "phaseGroup.phase.groupCount", 0) > 1
            if isPools:
                phase_name += " - " + TSHLocaleHelper.phaseNames.get(
                    "group").format(deep_get(_set, "phaseGroup.displayIdentifier"))
            
            streamUrl = deep_get(_set, "stream.streamName")
            streamSource = deep_get(_set, "stream.streamSource")

            if streamSource == "TWITCH":
                streamUrl = "https://twitch.tv/" + streamUrl
            if streamSource == "YOUTUBE":
                streamUrl = "https://youtube.com/" + streamUrl

            setData = {
                "id": _set.get("id"),
                "team1score": _set.get("entrant1Score"),
                "team2score": _set.get("entrant2Score"),
                "round_name": StartGGDataProvider.TranslateRoundName(_set.get("fullRoundText")),
                "tournament_phase": phase_name,
                "bracket_type": bracket_type,
                "p1_name": p1.get("entrant", {}).get("name", "") if p1 and p1.get("entrant") != None else "",
                "p2_name": p2.get("entrant", {}).get("name", "") if p2 and p2.get("entrant") != None else "",
                "p1_seed": p1.get("entrant", {}).get("initialSeedNum", None) if p1 and p1.get("entrant") else None,
                "p2_seed": p2.get("entrant", {}).get("initialSeedNum", None) if p2 and p2.get("entrant") else None,
                "stream": streamUrl,
                "station": _set.get("station", {}).get("number", "") if _set.get("station", {}) != None else "",
                "isOnline": deep_get(_set, "event.isOnline"),
                "isPools": isPools,
                "round": _set.get("round")
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

                    if setData.get(f"p{i+1}_seed"):
                        playerData["seed"] = setData.get(f"p{i+1}_seed")

                    players[i].append(playerData)

            setData["entrants"] = players

            return setData
        except Exception as e:
            logger.error(traceback.format_exc())
            return {}

    def ParseMatchDataOldApi(self, respTasks):
        entities = respTasks.get("entities", {})
        sets = entities.get("sets", {})
        tasks = entities.get("setTask", [])

        selectedCharMap = {}
        entrant1Id = str(sets.get("entrant1Id"))
        entrant2Id = str(sets.get("entrant2Id"))

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

        logger.debug(f"selectedCharMap: {selectedCharMap}")
        selectedChars = [[], []]

        for char in selectedCharMap.items():
            if str(char[0]) == entrant1Id:
                selectedChars[0] = char[1]
            if str(char[0]) == entrant2Id:
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
            if str(latestWinner) == entrant1Id:
                lastWinnerSlot = 0
            if str(latestWinner) == entrant2Id:
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

                        if str(entrantId) == entrant1Id:
                            stageWins[0] = stages
                        if str(entrantId) == entrant2Id:
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

                            if str(entrant) == entrant1Id:
                                strikedBy[0].append(codename)
                            if str(entrant) == entrant2Id:
                                strikedBy[1].append(codename)
                else:
                    banPlayer = 0

                    if str(latestWinner) == entrant1Id:
                        banPlayer = 0
                    if str(latestWinner) == entrant2Id:
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

                    if str(latestWinner) == entrant1Id:
                        lastLoserSlot = 1
                    if str(latestWinner) == entrant2Id:
                        lastLoserSlot = 0

                    currPlayer = lastLoserSlot
                elif base.get("turn"):
                    for entrant, value in base.get("turn").items():
                        if str(entrant) == entrant1Id and value == True:
                            currPlayer = 1
                        if str(entrant) == entrant2Id and value == True:
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
                "currGame": sets.get("entrant1Score", 0) + sets.get("entrant2Score", 0)
            }

            rulesetState = {
                "neutralStages": allStagesFinal,
                "useDSR": dsr,
                "useMDSR": mdsr,
            }
        except:
            logger.info("No Stage Strike Info Found")
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

        # If we don't have mains from the selection data, fallback to the characterIds attribute
        for i in [0, 1]:
            if len(entrants[i]) == 0:
                characterIds = deep_get(
                    sets, f"entrant{i+1}CharacterIds", []) or []

                for char in characterIds:
                    try:
                        entrants[i] = [{
                            "mains": [TSHGameAssetManager.instance.GetCharacterFromStartGGId(char)[0], 0]
                        }]
                    except:
                        logger.error(traceback.format_exc())

        team1losers = False
        team2losers = False

        if sets.get("isGF", False):
            if "Reset" not in sets.get("fullRoundText", ""):
                team1losers = False
                team2losers = True
            else:
                team1losers = True
                team2losers = True

        logger.info("Team 1 Score - OLD API: " + str(sets.get("entrant1Score", None)))
        logger.info("Team 2 Score - OLD API: " + str(sets.get("entrant2Score", None)))

        return ({
            "stage_strike": stageStrikeState,
            "ruleset": rulesetState,
            "strikedBy": strikedBy,
            "entrants": entrants,
            "team1score": sets.get("entrant1Score", None),
            "team2score": sets.get("entrant2Score", None),
            "bestOf": sets.get("bestOf", None),
            "roundDivision": sets.get("roundDivision", None),
            "team1losers": team1losers,
            "team2losers": team2losers,
            "currPlayer": currPlayer,
            "winnerProgression": sets.get("wProgressingName", None),
            "loserProgression": sets.get("lProgressingName", None)
        })

    def ProcessFutureSet(self, _set, eventSlug):
        phase_name = deep_get(_set, "phaseGroup.phase.name")
        if deep_get(_set, "phaseGroup.phase.groupCount") > 1:
            phase_name += " - " + TSHLocaleHelper.phaseNames.get(
                "group").format(deep_get(_set, "phaseGroup.displayIdentifier"))

        frt = _set.get("fullRoundText", "")
        total_games = _set.get("totalGames", 0)
        seteventSlug = deep_get(_set, "event.slug", "")

        setData = {
            "id": _set.get("id"),
            "match": StartGGDataProvider.TranslateRoundName(frt),
            "phase": phase_name,
            "best_of": total_games,
            "best_of_text": TSHLocaleHelper.matchNames.get("best_of").format(total_games) if total_games > 0 else "",
            "state": _set.get("state"),
            "team": {},
            "station": deep_get(_set, "station.number", -1),
            "event": seteventSlug,
            "isCurrentEvent": seteventSlug == eventSlug
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
                    "seed": entrant.get("initialSeed", 889977666),
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
                    stateData = {}
                    if countryData:
                        states = countryData.get("states")
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
        return setData

    def GetStreamQueue(self, progress_callback=None, cancel_event=None):
        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "StreamQueueQuery",
                    "variables": {
                        "slug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.StreamQueueQuery
                }
            )
            logger.info("Stream queue loaded from StartGG")

            eventSlug = deep_get(data, "data.event.slug", "")
            queues = deep_get(data, "data.event.tournament.streamQueue", [])

            finalData = {}

            if not queues:
                logger.info("(No stream queue was found)")
                return finalData

            for q in queues:
                streamName = q.get("stream", {}).get("streamName", "")
                queueData = {}
                for setIndex, _set in enumerate(q.get("sets", [])):

                    setData = self.ProcessFutureSet(_set, eventSlug)

                    queueData[str(setIndex + 1)] = setData

                finalData[streamName] = queueData

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
            logger.error(traceback.format_exc())

        return {}

    def GetStreamMatchId(self, streamName):
        streamSet = None

        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "StreamSetsQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.StreamSetsQuery
                }
            )

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
            logger.error(traceback.format_exc())

        return streamSet

    def GetStationMatchsId(self, stationId):
        sets = None

        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "StationSetsQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1],
                        "filters": {
                            "state": [1, 2, 4, 5, 6],
                            "hideEmpty": True
                        }
                    },
                    "query": StartGGDataProvider.StationSetsQuery
                }
            )

            sets = deep_get(data, "data.event.sets.nodes", [])

            sets = [s for s in sets if str(deep_get(
                s, "station.id", "-1")) == str(stationId)]

        except Exception as e:
            logger.error(traceback.format_exc())

        return sets

    def GetStationMatchId(self, stationId):
        sets = self.GetStationMatchsId(self, stationId)

        return sets[0] if len(sets) > 0 else None

    def GetUserMatchId(self, user):
        matches = re.match(
            r".*start.gg/(user/[^/]*)", user)
        logger.info(matches)
        if matches:
            user = matches.groups()[0]

        userSet = None

        try:
            logger.info(user)
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
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

            logger.info(data)

            sets = deep_get(data, "data.user.player.sets.nodes")

            # If there's no active set, get last finished set instead
            if sets is not None and len(sets) == 0:
                data = self.QueryRequests(
                    "https://www.start.gg/api/-/gql",
                    type=requests.post,
                    jsonParams={
                        "operationName": "UserSetQuery",
                        "variables": {
                            "userSlug": user,
                            "filters": {
                            }
                        },
                        "query": StartGGDataProvider.UserSetQuery
                    }
                )

                logger.info(data)

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

                logger.info(userSet)
        except Exception as e:
            logger.error(traceback.format_exc())

        return userSet

    def GetEntrants(self):
        worker = Worker(self.GetEntrantsWorker, **{
            "gameId": TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id"),
            "eventSlug": self.url.split("start.gg/")[1]
        })
        self.threadpool.start(worker)

    def GetLastSets(self, playerID, playerNumber, callback, progress_callback, cancel_event):
        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "PlayerLastSetsQuery",
                    "variables": {
                        "eventSlug": self.url.split("start.gg/")[1],
                        "playerID": playerID
                    },
                    "query": StartGGDataProvider.LastSetsQuery
                }
            )

            sets = deep_get(
                data, "data.event.sets.nodes", [])

            set_data = []

            for set in sets:
                if not set:
                    continue
                if not set.get("winnerId"):
                    continue
                if len(set.get("slots", [])) < 2:
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
                player1Seed = set.get(
                    "slots", [{}])[0].get("initialSeedNum", 0)

                player2Info = set.get("slots", [{}, {}])[1].get("entrant", {}).get(
                    "participants", [{}])[0].get("player", {})
                player2Seed = set.get(
                    "slots", [{}])[1].get("initialSeedNum", 0)

                players = ["1", "2"]

                if player1Info.get("id") != playerID:
                    players.reverse()

                player_set = {
                    "phase_id": phaseIdentifier,
                    "phase_name": phaseName,
                    "round_name": StartGGDataProvider.TranslateRoundName(set.get("fullRoundText")),
                    f"player{players[0]}_score": set.get("entrant1Score") if set.get("entrant1Score") is not None else "0",
                    f"player{players[0]}_seed": player1Seed,
                    f"player{players[0]}_team": player1Info.get("prefix"),
                    f"player{players[0]}_name": player1Info.get("gamerTag"),
                    f"player{players[1]}_score": set.get("entrant2Score") if set.get("entrant2Score") is not None else "0",
                    f"player{players[1]}_seed": player2Seed,
                    f"player{players[1]}_team": player2Info.get("prefix"),
                    f"player{players[1]}_name": player2Info.get("gamerTag")
                }

                set_data.append(player_set)

            callback.emit(
                {"playerNumber": playerNumber, "last_sets": set_data})
        except Exception as e:
            logger.error(traceback.format_exc())
            callback.emit({"playerNumber": playerNumber, "last_sets": []})

    def GetPlayerHistoryStandings(self, playerID, playerNumber, gameType, callback, progress_callback, cancel_event):
        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "TournamentHistoryDataQuery",
                    "variables": {
                        "playerID": playerID,
                        "gameID": gameType
                    },
                    "query": StartGGDataProvider.HistorySetsQuery
                }
            )

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
                    logger.error("Failed to get Event Logo for: " +
                                 tournament.get("name") + " - " + event.get("name"))

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

    def GetRecentSets(self, id1, id2, videogame, callback, requestTime, progress_callback, cancel_event):
        try:
            id1 = [str(id1[0]), str(id1[1])]
            id2 = [str(id2[0]), str(id2[1])]

            pool = self.getRecentSetsThreadPool

            recentSets = []

            pool.clear()

            logger.info("Get recent sets start")

            for _id1, _id2, inverted in [[id1, id2, False], [id2, id1, True]]:
                for i in range(5):
                    worker = Worker(self.GetRecentSetsWorker, **{
                        "id1": _id1,
                        "id2": _id2,
                        "page": (i+1),
                        "inverted": inverted,
                        "videogame": videogame
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
            logger.info("Recent sets size: " + str(len(recentSets)))
            callback.emit({"sets": recentSets, "request_time": requestTime})
        except Exception as e:
            logger.error(traceback.format_exc())
            callback.emit({"sets": [], "request_time": requestTime})

    def GetRecentSetsWorker(self, id1, id2, page, videogame, inverted, progress_callback, cancel_event):
        try:
            recentSets = []

            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    # "operationName": "RecentSetsQuery",
                    "variables": {
                        "pid1": id1[0],
                        "uid1": id1[1],
                        "pid2": id2[0],
                        "uid2": id2[1],
                        "page": page,
                        "videogameId": videogame
                    },
                    "query": StartGGDataProvider.RecentSetsQuery
                }
            )

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

                    p1id = _set.get("slots", [{}, {}])[0].get("entrant", {}).get(
                        "participants", [{}])[0].get("player", {}).get("id")
                    p2id = _set.get("slots", [{}, {}])[1].get("entrant", {}).get(
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
                            score = [_set.get("entrant1Score") if _set.get("entrant1Score") is not None else "0",
                                     _set.get("entrant2Score") if _set.get("entrant2Score") is not None else "0"]
                        else:
                            score = [_set.get("entrant2Score") if _set.get("entrant2Score") is not None else "0",
                                     _set.get("entrant1Score") if _set.get("entrant1Score") is not None else "0"]
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
            logger.error(traceback.format_exc())
            return []

    def GetEntrantsWorker(self, eventSlug, gameId, progress_callback, cancel_event):
        try:
            page = 1
            totalPages = 1
            # final_data = QStandardItemModel()
            players = []

            while page <= totalPages:
                logger.info(str(page) + "/" + str(totalPages))
                data = self.QueryRequests(
                    "https://www.start.gg/api/-/gql",
                    type=requests.post,
                    jsonParams={
                        "operationName": "EventEntrantsListQuery",
                        "variables": {
                            "eventSlug": eventSlug,
                            "videogameId": gameId,
                            "page": page,
                        },
                        "query": StartGGDataProvider.EntrantsQuery
                    }
                )

                totalPages = deep_get(
                    data, "data.event.entrants.pageInfo.totalPages", 0)

                entrants = deep_get(data, "data.event.entrants.nodes", [])
                logger.info("Entrants: " + str(len(entrants)))

                for i, team in enumerate(entrants):
                    for j, entrant in enumerate(team.get("participants", [])):
                        playerData = StartGGDataProvider.ProcessEntrantData(
                            entrant)
                        playerData["seed"] = team.get("initialSeedNum", 0)
                        self.player_seeds[playerData["id"]
                                          [0]] = playerData["seed"]
                        players.append(playerData)

                TSHPlayerDB.AddPlayers(players)
                players = []

                page += 1
        except Exception as e:
            logger.error(traceback.format_exc())

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

    def GetStandings(self, playerNumber, progress_callback, cancel_event):
        try:
            data = self.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "TournamentStandingsQuery",
                    "variables": {
                        "playerNumber": playerNumber,
                        "eventSlug": self.url.split("start.gg/")[1]
                    },
                    "query": StartGGDataProvider.TournamentStandingsQuery
                }

            )

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
            logger.error(traceback.format_exc())

    def GetFutureMatch(self, matchId, progress_callback, cancel_event):
        data = self.QueryRequests(
            "https://www.start.gg/api/-/gql",
            type=requests.post,
            jsonParams={
                "operationName": "FutureSetQuery",
                "variables": {
                    "id": matchId
                },
                "query": StartGGDataProvider.FutureSetQuery
            }
        )

        data = deep_get(data, "data.set", None)

        if not data:
            return {}

        data = self.ProcessFutureSet(data, self.url.split("start.gg/")[1])

        return data

    def GetMatchAndInsertInListBecauseFuckPython(self, setId, list, i, progress_callback, cancel_event):
        set = self.GetFutureMatch(setId, None)

        if set:
            list[i] = set

    def GetFutureMatchesList(self, setsId, progress_callback, cancel_event):
        sets = []
        pool = self.getStationMatchesThreadPool
        i = 0
        for set in setsId:
            sets.append(None)
            worker = Worker(self.GetMatchAndInsertInListBecauseFuckPython, **{
                "setId": set.get("id"),
                "list": sets,
                "i": i
            })

            pool.start(worker)

            i += 1

        pool.waitForDone(5000)
        QCoreApplication.processEvents()

        sets_ = {}
        for index, set in enumerate(sets):
            sets_[str(index + 1)] = set

        return sets_

sggTdpDir = TSHResolve('src/TournamentDataProvider')

def readQueryFile(tdpdir, filename):
    with open(f"{tdpdir}/StartGG{filename}Query.txt", "r") as f:
        return f.read()

StartGGDataProvider.SetsQuery = readQueryFile(sggTdpDir, "Sets")
StartGGDataProvider.SetQuery = readQueryFile(sggTdpDir, "Set")
StartGGDataProvider.UserSetQuery = readQueryFile(sggTdpDir, "UserSet")
StartGGDataProvider.StreamSetsQuery = readQueryFile(sggTdpDir, "StreamSets")
StartGGDataProvider.EntrantsQuery = readQueryFile(sggTdpDir, "Entrants")
StartGGDataProvider.FutureSetQuery = readQueryFile(sggTdpDir, "FutureSet")
StartGGDataProvider.TournamentDataQuery = readQueryFile(sggTdpDir, "TournamentData")
StartGGDataProvider.RecentSetsQuery = readQueryFile(sggTdpDir, "RecentSets")
StartGGDataProvider.LastSetsQuery = readQueryFile(sggTdpDir, "PlayerLastSets")
StartGGDataProvider.HistorySetsQuery = readQueryFile(sggTdpDir, "PlayerTournamentHistory")
StartGGDataProvider.TournamentStandingsQuery = readQueryFile(sggTdpDir, "TournamentStandings")
StartGGDataProvider.TournamentPhasesQuery = readQueryFile(sggTdpDir, "TournamentPhases")
StartGGDataProvider.TournamentPhaseGroupQuery = readQueryFile(sggTdpDir, "TournamentPhaseGroup")
StartGGDataProvider.StationsQuery = readQueryFile(sggTdpDir, "Stations")
StartGGDataProvider.StationSetsQuery = readQueryFile(sggTdpDir, "StationSets")
StartGGDataProvider.StreamQueueQuery = readQueryFile(sggTdpDir, "StreamQueue")
