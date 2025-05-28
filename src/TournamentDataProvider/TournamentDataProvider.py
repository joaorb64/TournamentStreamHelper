import requests
import orjson
from loguru import logger
import random
from urllib.parse import quote as urlencode


class TournamentDataProvider:
    def __init__(self, url, threadpool, parent) -> None:
        self.name = ""
        self.url = url
        self.entrants = []
        self.tournamentData = {}
        self.threadpool = threadpool
        self.videogame = None
        self.parent = parent

    def GetIconURL(self):
        pass

    def GetEntrants(self):
        pass

    def GetTournamentData(self, progress_callback=None, cancel_event=None):
        pass

    def GetMatch(self, setId, progress_callback=None, cancel_event=None):
        pass

    def GetMatches(self, getFinished=False, progress_callback=None, cancel_event=None):
        pass

    def GetStations(self, progress_callback=None, cancel_event=None):
        pass

    def GetStreamQueue(self, streamName=None, progress_callback=None, cancel_event=None):
        pass

    def GetStreamMatchId(self, streamName):
        pass

    def GetStationMatchId(self, stationId):
        pass

    def GetStationMatchsId(self, stationId):
        pass

    def GetUserMatchId(self, user):
        pass

    def GetRecentSets(self, id1, id2, videogame, callback):
        pass

    def GetLastSets(self, playerId, playerNumber):
        pass

    def GetCompletedSets(self):
        pass

    def GetPlayerHistoryStandings(self, playerId, playerNumber, gameType):
        pass

    def GetTournamentPhases(self, progress_callback=None, cancel_event=None):
        pass

    def GetTournamentPhaseGroup(self, id, progress_callback=None, cancel_event=None):
        pass

    def GetStandings(self, playerNumber):
        pass

    def GetFutureMatch(self, progrss_callback=None):
        pass

    # give me a list of objects that contain a "id" property
    def GetFutureMatchesList(self, sets: object, progress_callback=None, cancel_event=None):
        pass

    def ConvertStreamUrl(self, stream):
        if "twitch.tv" in stream:
            stream = stream.split("twitch.tv/")[1].replace("/", "")
            stream = f"Twitch: {stream}"
        if "youtube.com" in stream or "youtu.be" in stream:
            if "youtu.be" in stream:  # Convert stream URL if shortened
                stream = stream.split("?")[0]
                stream = f"https://youtube.com/watch?v={stream.split('/')[-1]}"

            # Use 3rd Party Client to get YouTube info
            data_server_search = requests.get(
                "https://api.invidious.io/instances.json?pretty=1&sort_by=health")
            if int(data_server_search.status_code) == 200:
                # Filter data servers which are up and reliable
                possible_data_server_list = []
                for data_server_info in orjson.loads(data_server_search.text):
                    if data_server_info[1].get("api") \
                            and data_server_info[1].get("monitor") \
                            and not data_server_info[1].get("monitor").get("down") \
                            and data_server_info[1].get("monitor").get("uptime") == 100:
                        possible_data_server_list.append(
                            data_server_info[1].get("uri"))
                possible_data_server_list = sorted(
                    possible_data_server_list, key=lambda x: random.random())
                for data_server in possible_data_server_list:
                    logger.info(f"YouTube Data Info Server: {data_server}")
                    info = requests.get(
                        f"{data_server}/api/v1/resolveurl?url={urlencode(stream)}")
                    logger.info(f"Youtube Stream Info request: {info.text}")
                    if int(info.status_code) == 200:
                        if orjson.loads(info.text).get("videoId"):
                            info = requests.get(
                                f'{data_server}/api/v1/videos/{info.json().get("videoId")}')
                            logger.info(
                                f"Youtube Video Info request: {info.text}")
                            if int(info.status_code) == 200:
                                stream = f'"{orjson.loads(info.text).get("title")}"'
                                stream = f"YouTube: {stream}"
                                break
                        elif orjson.loads(info.text).get("ucid"):
                            info = requests.get(
                                f'{data_server}/api/v1/channels/{info.json().get("ucid")}')
                            logger.info(
                                f"Youtube Channel Info request: {info.text}")
                            if int(info.status_code) == 200:
                                stream = orjson.loads(info.text).get("author")
                                stream = f"YouTube: {stream}"
                                break
        return (stream)
