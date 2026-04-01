import grpc
from loguru import logger

# ParryGG Imports
# TODO: Probably won't use all of these.
from parrygg.services.tournament_service_pb2_grpc import TournamentServiceStub
from parrygg.services.event_service_pb2_grpc import EventServiceStub
from parrygg.services.phase_service_pb2_grpc import PhaseServiceStub
from parrygg.services.bracket_service_pb2_grpc import BracketServiceStub
from parrygg.services.match_service_pb2_grpc import MatchServiceStub
from parrygg.services.entrant_service_pb2_grpc import EntrantServiceStub
from parrygg.services.user_service_pb2_grpc import UserServiceStub
from parrygg.services.game_service_pb2_grpc import GameServiceStub

# TODO: This is poor practice, will change later.
from parrygg.services.tournament_service_pb2 import *
from parrygg.services.event_service_pb2 import *
from parrygg.services.phase_service_pb2 import *
from parrygg.services.bracket_service_pb2 import *
from parrygg.services.match_service_pb2 import *
from parrygg.services.entrant_service_pb2 import *
from parrygg.services.user_service_pb2 import *
from parrygg.services.game_service_pb2 import *

from parrygg.models.slug_pb2 import SlugType
from parrygg.models.bracket_pb2 import BracketType
from parrygg.models.image_pb2 import ImageType

# Other Imports used by StartGGDataProvider
# TODO: May or may not be required.
from .TournamentDataProvider import TournamentDataProvider
from ..TSHPlayerDB import TSHPlayerDB
# from ..Helpers.TSHCountryHelper import TSHCountryHelper
# from ..Helpers.TSHDictHelper import deep_get
# from ..Helpers.TSHDirHelper import TSHResolve
# from ..Helpers.TSHQtHelper import invokeSlot, gui_thread_sync
# from ..TSHGameAssetManager import TSHGameAssetManager
# import orjson
# from ..Helpers.TSHLocaleHelper import TSHLocaleHelper
# from ..TSHBracket import is_power_of_two
# from ..Workers import Worker

class ParryGGDataProvider(TournamentDataProvider):
    tournament_service = None
    event_service = None
    phase_service = None
    bracket_service = None
    match_service = None
    matchgame_service = None
    entrant_service = None
    user_service = None
    game_service = None

    _timeout = 10
    metadata = None

    def __init__(self, url, threadpool, tshTdp, api_key=None) -> None:
        super().__init__(url, threadpool, tshTdp)
        self.name = "ParryGG"

        if api_key:
            self.metadata = [("x-api-key", api_key)]
        else:
            logger.warning("No API key provided for ParryGG")
            self.metadata = []
        
        self._get_slugs_and_ids()
    
    def _get_slugs_and_ids(self):
        self.tournament_slug = self.url.split("parry.gg/")[1].split("/")[0]
        self.event_slug = self.url.split("parry.gg/")[1].split("/")[1]
        
        self._setup_service("Tournament")

        try:
            get_tournament_request = GetTournamentRequest()
            get_tournament_request.tournament_slug = self.tournament_slug
            get_tournament_response = self.tournament_service.GetTournament(get_tournament_request, metadata=self.metadata, timeout=self._timeout)

            self.tournament_id = get_tournament_response.tournament.id

            for event in get_tournament_response.tournament.events:
                if event.slug == self.event_slug:
                    self.event_id = event.id
                    break
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                # logger.error("ParryGG authentication failed - invalid API key")
                raise Exception("Invalid API key")
            elif e.code() == grpc.StatusCode.NOT_FOUND:
                raise Exception("Tournament or Event not found")
            else:
                logger.error(f"ParryGG gRPC error: {e}")
                
    def _setup_service(self, service_name):
        if not hasattr(self, 'channel') or self.channel is None:
            self.channel = grpc.secure_channel("api.parry.gg:443", grpc.ssl_channel_credentials())

        match service_name:
            case "Tournament":
                if self.tournament_service is None:
                    self.tournament_service = TournamentServiceStub(self.channel)
            case "Event":
                if self.event_service is None:
                    self.event_service = EventServiceStub(self.channel)
            case "Phase":
                if self.phase_service is None:
                    self.phase_service = PhaseServiceStub(self.channel)
            case "Bracket":
                if self.bracket_service is None:
                    self.bracket_service = BracketServiceStub(self.channel)
            case "Match":
                if self.match_service is None:
                    self.match_service = MatchServiceStub(self.channel)
            case "MatchGame":
                if self.matchgame_service is None:
                    self.matchgame_service = MatchGameServiceStub(self.channel)
            case "Entrant":
                if self.entrant_service is None:
                    self.entrant_service = EntrantServiceStub(self.channel)
            case "User":
                if self.user_service is None:
                    self.user_service = UserServiceStub(self.channel)
            case "Game":
                if self.game_service is None:
                    self.game_service = GameServiceStub(self.channel)
            case _:
                logger.error(f"Service {service_name} not recognized")
    
    def GetIconURL(self):
        self._setup_service("Tournament")
        
        get_tournament_request = GetTournamentRequest()
        get_tournament_request.tournament_slug = self.tournament_slug
        get_tournament_response = self.tournament_service.GetTournament(get_tournament_request, metadata=self.metadata, timeout=self._timeout)

        for image in get_tournament_response.tournament.images:
            # Look for banner image, can be replaced in future if icons are added.
            if image.type == ImageType.IMAGE_TYPE_BANNER:
                return image.url
        
        # Fallback to the ParryGG favicon if no suitable image is found.
        logger.warning("No banner image found.")
        return "https://parry.gg/assets/favicon-BgItT2B4.png"

    def GetEntrants(self):
        self._setup_service("Event")

        players = []
        
        try:
            get_event_entrants_request = GetEventEntrantsRequest()
            get_event_entrants_request.event_identifier.event_slug_path.tournament_slug = self.tournament_slug
            get_event_entrants_request.event_identifier.event_slug_path.event_slug = self.event_slug
            get_event_entrants_response = self.event_service.GetEventEntrants(get_event_entrants_request, metadata=self.metadata, timeout=self._timeout)

            for entrant in get_event_entrants_response.event_entrants:
                # Assuming single user for now, no teams.
                user = entrant.entrant.users[0]

                # Format the entrant correctly.
                formatted_entrant = {
                    "prefix": "",
                    "gamerTag": user.gamer_tag,
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "id": [entrant.entrant.id],
                    "pronoun": user.pronouns,
                    "avatar": "",
                    "country_code": user.location_country,
                    "state_code": user.location_state,
                    "seed": 0 #entrant.seed
                }
                
                # Extract avatar URL from images.
                for image in user.images:
                    if image.type == ImageType.IMAGE_TYPE_AVATAR:
                        formatted_entrant["avatar"] = image.url
                        break
                
                players.append(formatted_entrant)
        except Exception as e:
            logger.error(f"Error processing entrants: {e}")

        TSHPlayerDB.AddPlayers(players)
    
    def GetTournamentData(self, progress_callback=None, cancel_event=None):
        self._setup_service("Tournament")

        get_tournament_request = GetTournamentRequest()
        get_tournament_request.tournament_slug = self.tournament_slug
        get_tournament_response = self.tournament_service.GetTournament(get_tournament_request, metadata=self.metadata, timeout=self._timeout)

        tournament_data = get_tournament_response.tournament

        for event in tournament_data.events:
            if event.slug == self.event_slug:
                event_data = event
                break
        
        tournament_info = {}
        
        try:
            tournament_info["tournamentName"] = tournament_data.name
            tournament_info["eventName"] = event_data.name
            tournament_info["numEntrants"] = event_data.entrant_count
            tournament_info["address"] = tournament_data.venue_address
            tournament_info["startAt"] = tournament_data.start_date.seconds
            tournament_info["endAt"] = tournament_data.end_date.seconds
            tournament_info["eventStartAt"] = event_data.start_date.seconds
            tournament_info["eventEndAt"] = ""

            for slug in tournament_data.slugs:
                if slug.type == SlugType.SLUG_TYPE_CUSTOM:
                    tournament_info["shortLink"] = slug.slug
                    break
            
            videogame = event_data.game.slug
            if videogame:
                self.videogame = videogame
                self.tshTdp.signals.game_changed.emit(videogame)
                
        except Exception as e:
            logger.error(f"Error extracting tournament data: {e}")

        return tournament_info
    
    def GetMatch(self, setId, progress_callback=None, cancel_event=None):
        pass
    
    def GetMatches(self, getFinished=False, progress_callback=None, cancel_event=None):
        # TODO Get actual match data, returning an empty list avoids a crash for now.
        return []
    
    def GetStations(self, progress_callback=None, cancel_event=None):
        # TODO Get actual station/stream data, returning an empty list avoids a crash for now.
        # Stations are not a short-term priority for parry.gg, but streams are actively being worked on.   
        return []
    
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
        self._setup_service("Event")

        phases = []

        try:
            get_event_request = GetEventRequest()
            get_event_request.id = self.event_id
            get_event_response = self.event_service.GetEvent(get_event_request, metadata=self.metadata, timeout=self._timeout)
            
            for phase in get_event_response.event.phases:
                phase_info = {
                    "id": phase.id,
                    "name": phase.name,
                    "groups": []
                }

                for bracket in phase.brackets:
                    bracket_info = {
                        "id": bracket.id,
                        "name": bracket.name,
                        "type": BracketType.Name(phase.bracket_type)
                    }

                    phase_info["groups"].append(bracket_info)

                phases.append(phase_info)
        
        except Exception as e:
            logger.error(f"Error getting tournament phases: {e}")
        
        return phases
    
    def GetTournamentPhaseGroup(self, id, progress_callback=None, cancel_event=None):
        pass
    
    def GetStandings(self, playerNumber):
        pass
    
    def GetFutureMatch(self, progrss_callback=None):
        pass
    
    def GetFutureMatchesList(self, sets: object, progress_callback=None, cancel_event=None):
        pass
    
    def cleanup(self):
        """Properly cleanup gRPC channel and resources"""
        if hasattr(self, 'channel') and self.channel:
            try:
                self.channel.close()
                logger.info("gRPC channel closed successfully")
            except Exception as e:
                logger.error(f"Error closing gRPC channel: {e}")
    
    def __del__(self):
        """Ensure cleanup happens when destroyed"""
        self.cleanup()
