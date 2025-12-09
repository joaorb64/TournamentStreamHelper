import grpc
import os
import traceback

from dotenv import load_dotenv 
load_dotenv()
PARRYGG_API_KEY = os.getenv('PARRYGG_API_KEY')

from google.protobuf.json_format import MessageToJson
from loguru import logger

# ParryGG Imports
# TODO: Probably won't use all of these.
from parrygg.services.tournament_service_pb2_grpc import TournamentServiceStub
from parrygg.services.event_service_pb2_grpc import EventServiceStub
from parrygg.services.phase_service_pb2_grpc import PhaseServiceStub
from parrygg.services.bracket_service_pb2_grpc import BracketServiceStub
from parrygg.services.match_service_pb2_grpc import MatchServiceStub
from parrygg.services.match_game_service_pb2_grpc import MatchGameServiceStub
from parrygg.services.entrant_service_pb2_grpc import EntrantServiceStub
from parrygg.services.user_service_pb2_grpc import UserServiceStub
from parrygg.services.game_service_pb2_grpc import GameServiceStub

# TODO: This is poor practice, will change later.
from parrygg.services.tournament_service_pb2 import *
from parrygg.services.event_service_pb2 import *
from parrygg.services.phase_service_pb2 import *
from parrygg.services.bracket_service_pb2 import *
from parrygg.services.match_service_pb2 import *
from parrygg.services.match_game_service_pb2 import *
from parrygg.services.entrant_service_pb2 import *
from parrygg.services.user_service_pb2 import *
from parrygg.services.game_service_pb2 import *

from .TournamentDataProvider import TournamentDataProvider

# Other Imports used by StartGGDataProvider
# TODO: May or may not be required.
from ..Helpers.TSHCountryHelper import TSHCountryHelper
from ..Helpers.TSHDictHelper import deep_get
from ..Helpers.TSHDirHelper import TSHResolve
from ..Helpers.TSHQtHelper import invokeSlot
from ..TSHGameAssetManager import TSHGameAssetManager
from ..TSHPlayerDB import TSHPlayerDB
import orjson
from ..Helpers.TSHLocaleHelper import TSHLocaleHelper
from ..TSHBracket import is_power_of_two
from ..Workers import Worker

class ParryGGDataProvider(TournamentDataProvider):
    metadata = None
    channel = None
    # Services will be created as they're required.
    tournament_service = None
    event_service = None

    def __init__(self, url, threadpool, tshTdp) -> None:
        super().__init__(url, threadpool, tshTdp)
        self.name = "ParryGG"
        
        # Initialize gRPC channel
        self._initialize_grpc_connection()
    
    def _initialize_grpc_connection(self):
        """Initialize gRPC connection to ParryGG API"""
        try:
            # Create gRPC channel
            self.channel = grpc.secure_channel("api.parry.gg:443", grpc.ssl_channel_credentials())
            
            # Set up metadata for authentication
            if PARRYGG_API_KEY:
                self.metadata = [("x-api-key", PARRYGG_API_KEY)]
            else:
                logger.warning("PARRYGG_API_KEY not found in environment variables")
                self.metadata = []
                
        except Exception as e:
            logger.error(f"Failed to initialize ParryGG gRPC connection: {e}")
    
    def GetIconURL(self):
        # TODO: Accessed early
        pass
    
    def GetEntrants(self):
        # TODO: Accessed early
        pass
    
    def GetTournamentData(self, progress_callback=None, cancel_event=None):
        # TODO: Accessed early
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
        # TODO: Accessed early
        pass
    
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
