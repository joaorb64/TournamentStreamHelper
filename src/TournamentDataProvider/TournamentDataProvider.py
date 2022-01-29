class TournamentDataProvider:
    def __init__(self, url) -> None:
        self.url = url
        self.entrants = []
        self.tournamentData = {}

    def GetEntrants(self):
        pass

    def GetTournamentData(self):
        pass

    def GetMatch(self, setId):
        pass

    def GetMatches(self):
        pass

    def GetStreamMatchId(self, streamName):
        pass
