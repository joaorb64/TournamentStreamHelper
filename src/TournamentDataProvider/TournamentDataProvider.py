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

    def GetTournamentData(self, progress_callback=None):
        pass

    def GetMatch(self, setId, progress_callback=None):
        pass

    def GetMatches(self, getFinished=False, progress_callback=None):
        pass

    def GetStations(self, progress_callback=None):
        pass

    def GetStreamQueue(self, streamName, progress_callback=None):
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

    def GetPlayerHistoryStandings(self, playerId, playerNumber, gameType):
        pass

    def GetTournamentPhases(self, progress_callback=None):
        pass

    def GetTournamentPhaseGroup(self, id, progress_callback=None):
        pass

    def GetStandings(self, playerNumber):
        pass

    def GetFutureMatch(self, progrss_callback=None):
        pass

    #give me a list of objects that contain a "id" property
    def GetFutureMatchesList(self, sets: object, progress_callback=None):
        pass