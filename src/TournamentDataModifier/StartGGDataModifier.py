from .TournamentDataModifier import TournamentDataModifier
import requests
from loguru import logger

def SendQuery_(token, query, variables, operationName):
    return requests.post(
        "https://www.start.gg/gql/alpha",
        headers = {
            "Authorization": "Bearer " + token
        },
        json = {
            "operationName": operationName,
            "query": query,
            "variables": variables
        }
    )

class StartGGDataModifier(TournamentDataModifier):
    SetGamesMutation = None

    def __init__(self, url, threadpool, parent):
        super().__init__(url, threadpool, parent)
        self.name = "StartGG"
        self.token = ""

    def SendQuery(self, query, variables, operationName):
        if not self.token:
            logger.error("Tried to use a startgg mutation without setting a token. Operation : " + operationName)
            return False 
        return SendQuery_(self.token, query, variables, operationName)

    def SetMatchGames(self, id, winnerId, gameData):
        data = self.SendQuery(StartGGDataModifier.SetGamesMutation, {
            "setId": id,
            "winnerId": winnerId,
            "gameData": gameData
        })
        
        logger.info("SET REPORTING REQUEST CAME BACK ===========")
        logger.info(data)


f = open("src/TournamentDataModifier/StartGGSetGamesMutation.txt", 'r')
StartGGDataModifier.SetGamesMutation = f.read()