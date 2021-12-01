import requests
import os
import traceback
from TournamentDataProvider import TournamentDataProvider


class SmashGGDataProvider(TournamentDataProvider.TournamentDataProvider):
    SetsQuery = None

    def __init__(self, url) -> None:
        super().__init__(url)

    def GetEntrants(self):
        pass

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
                        "eventSlug": "tournament/semanal-ultra-arcade-30/event/smash-top-da-contorno-28"
                    },
                    "query": SmashGGDataProvider.SetsQuery
                }

            )
            print(data)
            print(data.text)
        except Exception as e:
            traceback.print_exc()
