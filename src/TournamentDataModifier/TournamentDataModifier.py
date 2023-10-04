class TournamentDataProvider:
    def __init__(self, url, threadpool, parent) -> None:
        self.name = ""
        self.url = url
        self.threadpool = threadpool
        self.parent = parent

    def SetMatchScoreFinal(self, id, p1score, p2score):
        pass

    def SetMatchGames(self, id, winnerId, gameData):
        pass