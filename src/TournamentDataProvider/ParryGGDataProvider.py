import grpc
import traceback
import requests
from loguru import logger

# ParryGG Imports
from parrygg.services.tournament_service_pb2_grpc import TournamentServiceStub
from parrygg.services.event_service_pb2_grpc import EventServiceStub
from parrygg.services.phase_service_pb2_grpc import PhaseServiceStub
from parrygg.services.bracket_service_pb2_grpc import BracketServiceStub
from parrygg.services.match_service_pb2_grpc import MatchServiceStub
from parrygg.services.match_game_service_pb2_grpc import MatchGameServiceStub
from parrygg.services.entrant_service_pb2_grpc import EntrantServiceStub
from parrygg.services.user_service_pb2_grpc import UserServiceStub
from parrygg.services.game_service_pb2_grpc import GameServiceStub
from parrygg.services.stream_service_pb2_grpc import StreamServiceStub

from parrygg.services.tournament_service_pb2 import *
from parrygg.services.event_service_pb2 import *
from parrygg.services.phase_service_pb2 import *
from parrygg.services.bracket_service_pb2 import *
from parrygg.services.match_service_pb2 import *
from parrygg.services.entrant_service_pb2 import *
from parrygg.services.user_service_pb2 import *
from parrygg.services.game_service_pb2 import *
from parrygg.services.stream_service_pb2 import *

from parrygg.models.slug_pb2 import SlugType
from parrygg.models.bracket_pb2 import BracketType, MatchState, SlotState
from parrygg.models.image_pb2 import ImageType
from parrygg.models.event_pb2 import LocationType
from parrygg.models.hierarchy_pb2 import PathType
from parrygg.models.stream_pb2 import StreamPlatform, StreamQueueEntryStatus
from parrygg.models.user_pb2 import LinkedAccountProvider

from .TournamentDataProvider import TournamentDataProvider
from .StartGGDataProvider import StartGGDataProvider
from ..TSHPlayerDB import TSHPlayerDB
from ..TSHGameAssetManager import TSHGameAssetManager
from ..Helpers.TSHCountryHelper import TSHCountryHelper
from ..Helpers.TSHQtHelper import invokeSlot

# URL path tokens used for parsing/splitting tournament URLs.
PARRY_HOST_PATH = "parry.gg/"
PARRY_MANAGE_PATH = "/_manage/"

# URL format templates — keep all URL construction declarative at one place.
# Stream URL formats match parrygg-web/app/lib/routes.ts streamUrl().
PARRY_TOURNAMENT_URL_FORMAT = "https://parry.gg/{}"
TWITCH_STREAM_URL_FORMAT = "https://www.twitch.tv/{}"
YOUTUBE_STREAM_URL_FORMAT = "https://www.youtube.com/@{}/live"

# gRPC endpoint for the parry backend.
PARRY_GRPC_TARGET = "api.parry.gg:443"

# Fallback tournament icon when a tournament has no banner image.
PARRY_FAVICON_URL = "https://parry.gg/assets/favicon-BgItT2B4.png"

# Parry profile URL prefix (used to identify a user-lookup placeholder URL
# when a provider is constructed without a tournament context).
PARRY_PROFILE_PATH = "parry.gg/profile/"

# Map parry's BracketType enum to the bare-string values TSH consumers
# (e.g. TSHBracketWidget's bracketType gate) compare against. Explicit map
# rather than prefix-stripping so a future parry enum rename or new bracket
# type fails loudly rather than silently producing a wrong string.
_BRACKET_TYPE_NAMES = {
    BracketType.BRACKET_TYPE_SINGLE_ELIMINATION: "SINGLE_ELIMINATION",
    BracketType.BRACKET_TYPE_DOUBLE_ELIMINATION: "DOUBLE_ELIMINATION",
    BracketType.BRACKET_TYPE_ROUND_ROBIN: "ROUND_ROBIN",
}


def _bracket_type_name(value):
    return _BRACKET_TYPE_NAMES.get(value, "")


class _CapturingCallback:
    # Synchronous adapter for StartGGDataProvider methods that emit results
    # via a Qt-style callback. The StartGG calls we delegate to are
    # synchronous from the caller's POV (Worker.wait_for_all + emit before
    # return), so capturing the value inline is safe.
    def __init__(self):
        self.result = None

    def emit(self, value):
        self.result = value


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
    stream_service = None

    tournament_slug = None
    event_slug = None
    tournament_id = None
    event_id = None

    _timeout = 10
    metadata = None

    # Caches populated lazily; cleared on tournament change via cleanup()
    _tournament_cache = None  # parrygg.models.Tournament
    _phases_cache = None  # dict[phase_id -> Phase]
    _streams_cache = None  # dict[stream_id -> {"channel": str, "platform": int, "display_name": str}]
    _linked_startgg_cache = None  # dict[parry_user_id -> {"slug", "user_id"} or None]
    _startgg_pid_cache = None  # dict[startgg_user_slug -> startgg_player_id_str or None]
    _startgg_mains_cache = None  # dict[parry_user_id -> mains dict or {}]
    _startgg_subquery = None  # lazy StartGGDataProvider for cross-platform fallback queries

    def __init__(self, url, threadpool, tshTdp, api_key=None) -> None:
        super().__init__(url, threadpool, tshTdp)
        self.name = "ParryGG"
        self._initialized = False

        if api_key:
            self.metadata = [("x-api-key", api_key)]
        else:
            logger.warning("No API key provided for ParryGG")
            self.metadata = []
        
        self._get_slugs_and_ids()
    
    def _get_slugs_and_ids(self):
        if self._initialized:
            return

        # Skip slug parsing entirely for profile URLs (used when this provider
        # is constructed standalone for the "Load tournament from user" flow —
        # there's no tournament/event to bind to yet).
        if PARRY_PROFILE_PATH in self.url:
            self._initialized = True
            return

        # Strip the admin "/_manage" path segment so manage URLs like
        # parry.gg/<tournament>/_manage/<event>/main/bracket parse the same as
        # canonical parry.gg/<tournament>/<event>. The dialog/web validators
        # also strip this, but parsing here keeps the provider resilient.
        path = self.url.split(PARRY_HOST_PATH, 1)[1].replace(PARRY_MANAGE_PATH, "/", 1)
        segments = path.split("/")
        self.tournament_slug = segments[0]
        self.event_slug = segments[1] if len(segments) > 1 else ""

        self._setup_service("Tournament")

        try:
            get_tournament_request = GetTournamentRequest()
            get_tournament_request.tournament_slug = self.tournament_slug
            get_tournament_response = self.tournament_service.GetTournament(get_tournament_request, metadata=self.metadata, timeout=self._timeout)

            self._tournament_cache = get_tournament_response.tournament
            self.tournament_id = get_tournament_response.tournament.id

            for event in get_tournament_response.tournament.events:
                if event.slug == self.event_slug:
                    self.event_id = event.id
                    break

            self._initialized = True

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
            self.channel = grpc.secure_channel(PARRY_GRPC_TARGET, grpc.ssl_channel_credentials())

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
            case "Stream":
                if self.stream_service is None:
                    self.stream_service = StreamServiceStub(self.channel)
            case _:
                logger.error(f"Service {service_name} not recognized")
    
    def _get_phases(self):
        """Lazy-load and cache event phases keyed by phase ID."""
        if self._phases_cache is not None:
            return self._phases_cache
        self._setup_service("Event")
        try:
            req = GetEventRequest()
            req.id = self.event_id
            resp = self.event_service.GetEvent(req, metadata=self.metadata, timeout=self._timeout)
            self._phases_cache = {phase.id: phase for phase in resp.event.phases}
        except Exception as e:
            logger.error(f"Error loading phases: {e}")
            self._phases_cache = {}
        return self._phases_cache

    def _get_streams(self):
        """Lazy-load and cache tournament streams keyed by stream ID, with resolved URL."""
        if self._streams_cache is not None:
            return self._streams_cache
        self._setup_service("Stream")
        cache = {}
        try:
            req = GetTournamentStreamsRequest()
            req.tournament_identifier.tournament_slug = self.tournament_slug
            resp = self.stream_service.GetTournamentStreams(req, metadata=self.metadata, timeout=self._timeout)
            logger.info(f"GetTournamentStreams returned {len(resp.streams)} streams for tournament_slug={self.tournament_slug}")
            for stream in resp.streams:
                # Strip a leading "@" so users typing the YouTube handle with or
                # without the @ both render the same URL (parrygg-web does the
                # same in routes.ts streamUrl()).
                channel = stream.channel.lstrip("@")
                if stream.platform == StreamPlatform.STREAM_PLATFORM_TWITCH:
                    url = TWITCH_STREAM_URL_FORMAT.format(channel)
                elif stream.platform == StreamPlatform.STREAM_PLATFORM_YOUTUBE:
                    url = YOUTUBE_STREAM_URL_FORMAT.format(channel)
                else:
                    url = stream.channel
                cache[stream.id] = {
                    "url": url,
                    "channel": stream.channel,
                    "platform": stream.platform,
                    "display_name": stream.display_name or stream.channel,
                    "capacity": max(1, stream.capacity),
                }
                logger.info(f"  stream id={stream.id} platform={StreamPlatform.Name(stream.platform)} channel={stream.channel!r} -> {url}")
        except Exception as e:
            logger.error(f"Error loading streams: {traceback.format_exc()}")
        self._streams_cache = cache
        return cache

    def _is_online(self):
        """True if the tournament's location_type is ONLINE."""
        if self._tournament_cache is None:
            return False
        return self._tournament_cache.location_type == LocationType.LOCATION_TYPE_ONLINE

    @staticmethod
    def _phase_id_from_hierarchy(hierarchy):
        for path in hierarchy.paths:
            if path.type == PathType.PATH_TYPE_PHASE:
                return path.id
        return None

    @staticmethod
    def _phase_name_from_hierarchy(hierarchy):
        for path in hierarchy.paths:
            if path.type == PathType.PATH_TYPE_PHASE:
                return path.name
        return ""

    @staticmethod
    def _bracket_name_from_hierarchy(hierarchy):
        for path in hierarchy.paths:
            if path.type == PathType.PATH_TYPE_BRACKET:
                return path.name
        return ""

    @staticmethod
    def _seed_entrant(seed):
        # Prefer the resolved entrant; fall back to the projected one when a
        # seed's occupant hasn't been determined yet (e.g. progression-fed
        # bracket positions). Mirrors start.gg's preview/projected behavior.
        if seed.HasField("event_entrant") and seed.event_entrant.HasField("entrant"):
            return seed.event_entrant
        if seed.HasField("projected_event_entrant") and seed.projected_event_entrant.HasField("entrant"):
            return seed.projected_event_entrant
        return None

    @classmethod
    def _team_display_name(cls, seed):
        # parry's EventEntrant carries an optional team display name; when it's
        # blank (most cases today) join gamer tags, matching the layouts'
        # fallback (TSHBracketView.py:138 and e.g. layout/scoreboard_pandastic
        # /index.js:177).
        ee = cls._seed_entrant(seed)
        if ee is None:
            return ""
        if ee.name:
            return ee.name
        return " / ".join(u.gamer_tag for u in ee.entrant.users)

    @staticmethod
    def _translate_round_name(label):
        # parry's Round.label is a server-computed English string (e.g.
        # "Winners Final", "Grand Final"), same shape as start.gg's
        # fullRoundText. Route through the shared StartGG translator so users
        # get locale-translated output. If parry's exact strings ever diverge
        # from start.gg's roundMapping keys, extend that table or add a parry
        # normalization step here.
        return StartGGDataProvider.TranslateRoundName(label or "")

    def _resolve_stream(self, match):
        """Return a stream URL string for a match, or '' if not queued."""
        if not match.HasField("stream_queue_entry"):
            return ""
        sid = match.stream_queue_entry.stream_id
        if not sid:
            logger.info(f"Match {match.id} has stream_queue_entry but stream_id is empty")
            return ""
        url = self._get_streams().get(sid, {}).get("url", "")
        if not url:
            logger.info(f"Stream {sid!r} not found in cache for match {match.id}; cache has {list(self._get_streams().keys())}")
        else:
            logger.info(f"Match {match.id} resolved to stream {url}")
        return url

    def _get_startgg_subquery(self):
        """Lazy-init a StartGGDataProvider used to run cross-platform fallback
        queries (H2H, character lookup) when a parry user has a linked
        start.gg account. URL is a placeholder — sub-queries we run don't
        depend on the active tournament URL.
        """
        if self._startgg_subquery is None:
            self._startgg_subquery = StartGGDataProvider(
                "start.gg/", self.threadpool, self.tshTdp,
            )
        return self._startgg_subquery

    def _get_linked_startgg_account(self, parry_user_id):
        """Return {'slug', 'user_id'} for a parry user's linked start.gg
        account, or None if not linked. Cached per provider lifetime.
        """
        if self._linked_startgg_cache is None:
            self._linked_startgg_cache = {}
        if parry_user_id in self._linked_startgg_cache:
            return self._linked_startgg_cache[parry_user_id]

        result = None
        self._setup_service("User")
        try:
            req = GetUserRequest()
            req.id = parry_user_id
            resp = self.user_service.GetUser(req, metadata=self.metadata, timeout=self._timeout)
            for acct in resp.user.linked_accounts:
                if (acct.provider == LinkedAccountProvider.LINKED_ACCOUNT_PROVIDER_STARTGG
                        and acct.slug):
                    result = {"slug": acct.slug, "user_id": acct.user_id}
                    break
        except Exception:
            logger.error(f"Error fetching linked accounts for parry user {parry_user_id}: {traceback.format_exc()}")

        self._linked_startgg_cache[parry_user_id] = result
        return result

    def _resolve_startgg_player_id(self, startgg_slug):
        """Resolve a start.gg user slug to its player.id by running UserSetQuery.
        StartGG's RecentSetsQuery requires both player_id and user_id; user_id
        comes from the LinkedAccount, but player_id is per-game and only
        accessible via UserSetQuery.
        """
        if self._startgg_pid_cache is None:
            self._startgg_pid_cache = {}
        if startgg_slug in self._startgg_pid_cache:
            return self._startgg_pid_cache[startgg_slug]

        sgg = self._get_startgg_subquery()
        result = None
        try:
            data = sgg.QueryRequests(
                "https://www.start.gg/api/-/gql",
                type=requests.post,
                jsonParams={
                    "operationName": "UserSetQuery",
                    "variables": {"userSlug": startgg_slug, "filters": {}},
                    "query": StartGGDataProvider.UserSetQuery,
                },
            )
            pid = (data.get("data", {}) or {}).get("user", {}).get("player", {}).get("id") if data else None
            if pid:
                result = str(pid)
        except Exception:
            logger.error(f"Error resolving start.gg player_id for slug {startgg_slug}: {traceback.format_exc()}")

        self._startgg_pid_cache[startgg_slug] = result
        return result

    def _fetch_bracket(self, bracket_id):
        """Fetch a single bracket (with matches/seeds/rounds populated)."""
        self._setup_service("Bracket")
        try:
            req = GetBracketRequest()
            req.id = bracket_id
            resp = self.bracket_service.GetBracket(req, metadata=self.metadata, timeout=self._timeout)
            return resp.bracket
        except Exception as e:
            logger.error(f"Error fetching bracket {bracket_id}: {traceback.format_exc()}")
            return None

    @staticmethod
    def _seeds_for_match(match, seeds_by_id):
        """Return list of Seed protos in slot order, matching match.slots."""
        out = []
        for slot in match.slots:
            seed = seeds_by_id.get(slot.seed_id)
            if seed:
                out.append(seed)
        return out

    @staticmethod
    def _round_label_for_match(match, rounds_by_key):
        """Look up a Round.label string for a match within a bracket. Joins on (number, winners_side)."""
        round_msg = rounds_by_key.get((match.round, match.winners_side))
        return round_msg.label if round_msg else ""

    def _build_match_info(self, match, seeds, phase, bracket, round_label):
        """Build the TSH match dict from raw parry pieces.

        Args:
            match: Match proto.
            seeds: list of Seed protos in slot order.
            phase: Phase proto (or None).
            bracket: Bracket proto (or None).
            round_label: server-supplied English round label (will be locale-translated).
        """
        is_pools = bool(phase and len(phase.brackets) > 1)
        phase_name = phase.name if phase else ""
        if is_pools and bracket:
            phase_name = f"{phase_name} - {bracket.name}"

        bracket_type = _bracket_type_name(phase.bracket_type) if phase else ""

        # Build entrants list (team support: iterate all users)
        entrants = []
        for seed in seeds:
            team = []
            ee = self._seed_entrant(seed)
            if ee is not None:
                for user in ee.entrant.users:
                    team.append({
                        "prefix": user.sponsor_name,
                        "gamerTag": user.gamer_tag,
                        "name": (user.first_name + " " + user.last_name).strip(),
                        # id = [lookup_id, global_user_id]. Parry has no
                        # per-game concept like start.gg's player_id, so
                        # both elements are user_id; format-aligned with
                        # start.gg's [player_id, user_id] convention.
                        "id": [user.id, user.id],
                    })
            entrants.append(team)

        return {
            "id": match.id,
            "team1score": int(match.slots[0].score) if len(match.slots) > 0 else 0,
            "team2score": int(match.slots[1].score) if len(match.slots) > 1 else 0,
            "round_name": self._translate_round_name(round_label),
            "tournament_phase": phase_name,
            "bracket_type": bracket_type,
            "p1_name": self._team_display_name(seeds[0]) if len(seeds) > 0 else "",
            "p2_name": self._team_display_name(seeds[1]) if len(seeds) > 1 else "",
            "p1_seed": seeds[0].seed if len(seeds) > 0 else "",
            "p2_seed": seeds[1].seed if len(seeds) > 1 else "",
            "stream": self._resolve_stream(match),
            "station": "",
            "isOnline": self._is_online(),
            "isPools": is_pools,
            "round": match.round,
            "entrants": entrants if entrants else [[]],
        }

    def _fetch_future_set(self, match_id):
        """Fetch a single match by ID and convert to TSH future-set format."""
        try:
            req = GetMatchRequest()
            req.id = match_id
            resp = self.match_service.GetMatch(req, metadata=self.metadata, timeout=self._timeout)
            return self._process_future_set(resp.match)
        except Exception as e:
            logger.error(f"Error fetching match {match_id} for stream queue: {traceback.format_exc()}")
            return None

    def _process_future_set(self, ctx):
        """Convert a parry MatchContext to TSH future-set format.

        Mirrors the shape produced by StartGGDataProvider.ProcessFutureSet so
        downstream consumers (templates, scoreboard widgets) can render parry
        and start.gg stream queues identically.
        """
        match = ctx.match
        seeds = ctx.seeds
        hierarchy = ctx.hierarchy

        phase_id = self._phase_id_from_hierarchy(hierarchy)
        phase_name = self._phase_name_from_hierarchy(hierarchy)
        phase = self._get_phases().get(phase_id) if phase_id else None
        is_pools = bool(phase and len(phase.brackets) > 1)
        if is_pools:
            bracket_name = self._bracket_name_from_hierarchy(hierarchy)
            if bracket_name:
                phase_name = f"{phase_name} - {bracket_name}"

        teams = {}
        for team_index, seed in enumerate(seeds):
            team = {
                "teamName": self._team_display_name(seed),
                "losers": False,
                "seed": seed.seed,
                "player": {},
            }
            ee = self._seed_entrant(seed)
            if ee is not None:
                for player_index, user in enumerate(ee.entrant.users):
                    country_data = TSHCountryHelper.countries.get(user.location_country) or {}
                    state_data = {}
                    if user.location_state:
                        state_data = (country_data.get("states") or {}).get(user.location_state, {})

                    avatar_url = next(
                        (img.url for img in user.images if img.type == ImageType.IMAGE_TYPE_AVATAR),
                        "",
                    )
                    name = user.gamer_tag
                    sponsor = user.sponsor_name
                    team["player"][str(player_index + 1)] = {
                        "country": TSHCountryHelper.GetBasicCountryInfo(user.location_country),
                        "state": state_data,
                        "name": name,
                        "team": sponsor,
                        "mergedName": f"{sponsor}|{name}" if sponsor else name,
                        "pronoun": user.pronouns,
                        "real_name": (user.first_name + " " + user.last_name).strip(),
                        "online_avatar": avatar_url,
                        "twitter": "",
                    }
            teams[str(team_index + 1)] = team

        return {
            "id": match.id,
            "match": self._translate_round_name(ctx.round.label),
            "phase": phase_name,
            "best_of": 0,
            "best_of_text": "",
            "state": match.state,
            "team": teams,
            "station": "",
            "event": self.event_slug,
            "isCurrentEvent": True,
        }

    def GetIconURL(self):
        self._setup_service("Tournament")
        
        get_tournament_request = GetTournamentRequest()
        get_tournament_request.tournament_slug = self.tournament_slug
        get_tournament_response = self.tournament_service.GetTournament(get_tournament_request, metadata=self.metadata, timeout=self._timeout)

        for image in get_tournament_response.tournament.images:
            # Look for banner image, can be replaced in future if icons are added.
            if image.type == ImageType.IMAGE_TYPE_BANNER:
                return image.url + "?aspect_ratio=1:1"
        
        # Fallback to the ParryGG favicon if no suitable image is found.
        logger.warning("No banner image found.")
        return PARRY_FAVICON_URL

    def GetEntrants(self):
        self._setup_service("Event")

        players = []

        try:
            get_event_entrants_request = GetEventEntrantsRequest()
            get_event_entrants_request.event_identifier.event_slug_path.tournament_slug = self.tournament_slug
            get_event_entrants_request.event_identifier.event_slug_path.event_slug = self.event_slug
            get_event_entrants_response = self.event_service.GetEventEntrants(get_event_entrants_request, metadata=self.metadata, timeout=self._timeout)

            logger.info(f"GetEntrants: parry returned {len(get_event_entrants_response.event_entrants)} entrants")

            for entrant in get_event_entrants_response.event_entrants:
                # Emit one player per user; team members share the same
                # entrant.id and seed.
                for user in entrant.entrant.users:
                    formatted_entrant = {
                        "prefix": user.sponsor_name,
                        "gamerTag": user.gamer_tag,
                        "name": f"{user.first_name} {user.last_name}".strip(),
                        # id = [lookup_id, global_user_id]; parry has no
                        # per-game scope so both are user.id.
                        "id": [user.id, user.id],
                        "pronoun": user.pronouns,
                        "avatar": "",
                        "country_code": user.location_country,
                        "state_code": user.location_state,
                        "seed": entrant.seed
                    }

                    for image in user.images:
                        if image.type == ImageType.IMAGE_TYPE_AVATAR:
                            formatted_entrant["avatar"] = image.url
                            break

                    players.append(formatted_entrant)
        except Exception as e:
            logger.error(f"Error processing entrants: {traceback.format_exc()}")

        logger.info(f"GetEntrants: adding {len(players)} players to TSHPlayerDB")
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

            # Prefer custom slug, fall back to primary; emit as a full URL.
            custom_slug = next((s.slug for s in tournament_data.slugs if s.type == SlugType.SLUG_TYPE_CUSTOM), None)
            primary_slug = next((s.slug for s in tournament_data.slugs if s.type == SlugType.SLUG_TYPE_PRIMARY), None)
            chosen_slug = custom_slug or primary_slug
            if chosen_slug:
                tournament_info["shortLink"] = PARRY_TOURNAMENT_URL_FORMAT.format(chosen_slug)
            
            videogame = event_data.game.slug
            if videogame:
                self.videogame = videogame
                self.tshTdp.signals.game_changed.emit(videogame)
                
        except Exception as e:
            logger.error(f"Error extracting tournament data: {e}")

        return tournament_info
    
    def GetMatch(self, setId, progress_callback=None, cancel_event=None):
        self._setup_service("Match")
        try:
            req = GetMatchRequest()
            req.id = setId
            resp = self.match_service.GetMatch(req, metadata=self.metadata, timeout=self._timeout)
            ctx = resp.match
            phase_id = self._phase_id_from_hierarchy(ctx.hierarchy)
            phase = self._get_phases().get(phase_id) if phase_id else None
            # MatchContext doesn't carry the bracket struct directly — phase.brackets[i]
            # references match the bracket id from the hierarchy path.
            bracket_id = next(
                (p.id for p in ctx.hierarchy.paths if p.type == PathType.PATH_TYPE_BRACKET),
                None,
            )
            bracket = next(
                (b for b in (phase.brackets if phase else []) if b.id == bracket_id),
                None,
            )
            return self._build_match_info(ctx.match, list(ctx.seeds), phase, bracket, ctx.round.label)
        except Exception as e:
            logger.error(f"Error getting match: {traceback.format_exc()}")
            return {}

    def GetMatches(self, getFinished=False, progress_callback=None, cancel_event=None):
        """Traverse Event -> Phase -> Bracket and emit one TSH match dict per match.

        Bracket-traversal is preferred over MatchService.GetMatches because the
        Bracket-side Match protos populate stream_queue_entry, which the flat
        match list does not.
        """
        final_data = []
        with_queue_entry = 0
        phases = self._get_phases()
        total_brackets = sum(len(p.brackets) for p in phases.values())

        try:
            for phase in phases.values():
                for bracket_ref in phase.brackets:
                    bracket = self._fetch_bracket(bracket_ref.id)
                    if bracket is None:
                        continue
                    seeds_by_id = {s.id: s for s in bracket.seeds}
                    rounds_by_key = {(r.number, r.winners_side): r for r in bracket.rounds}

                    for match in bracket.matches:
                        if not getFinished and match.state == MatchState.MATCH_STATE_COMPLETED:
                            continue
                        seeds = self._seeds_for_match(match, seeds_by_id)
                        if len(seeds) == 0:
                            continue
                        if match.HasField("stream_queue_entry"):
                            with_queue_entry += 1
                        round_label = self._round_label_for_match(match, rounds_by_key)
                        final_data.append(
                            self._build_match_info(match, seeds, phase, bracket, round_label)
                        )

            logger.info(
                f"GetMatches (bracket traversal): kept {len(final_data)} matches across "
                f"{total_brackets} brackets (getFinished={getFinished}); "
                f"{with_queue_entry} have stream_queue_entry set"
            )

        except Exception as e:
            logger.error(f"Error processing matches: {traceback.format_exc()}")

        return final_data
    
    def GetStations(self, progress_callback=None, cancel_event=None):
        # parry.gg has no first-class "station" concept; emit each stream as a
        # TSH "stream" entry so the stream selector populates. The "stream"
        # field carries the resolved URL for the dialog's Stream column;
        # "identifier" is the human-friendly display name for the auto-update
        # banner ("Auto update (Stream [<identifier>])").
        #
        # parry streams have a "capacity" field for multi-up broadcasts (e.g.
        # capacity=4 = four matches on screen at once). Each capacity slot is
        # surfaced as its own row so a user can bind one TSH scoreboard per
        # slot. The provider's GetStreamMatchId reads the "slot" key to pick
        # the Nth STREAM_QUEUE_ENTRY_STATUS_ONSTREAM match for that stream.
        rows = []
        for stream_id, info in self._get_streams().items():
            capacity = info.get("capacity", 1)
            for slot in range(capacity):
                identifier = info["display_name"]
                if capacity > 1:
                    identifier = f"{identifier} (Slot {slot + 1}/{capacity})"
                rows.append({
                    "id": stream_id,
                    "identifier": identifier,
                    "type": "stream",
                    "stream": info["url"],
                    "slot": slot,
                })
        return rows

    def GetStreamQueue(self, progress_callback=None, cancel_event=None):
        """Return {stream_display_name: {position_str: future_set_data}} across all streams."""
        self._setup_service("Stream")
        self._setup_service("Match")
        final_data = {}
        try:
            for stream_id, info in self._get_streams().items():
                req = GetStreamQueueRequest()
                req.stream_id = stream_id
                resp = self.stream_service.GetStreamQueue(req, metadata=self.metadata, timeout=self._timeout)
                queue_data = {}
                for position, entry in enumerate(resp.entries, start=1):
                    if not entry.match_id:
                        continue
                    set_data = self._fetch_future_set(entry.match_id)
                    if set_data:
                        queue_data[str(position)] = set_data
                final_data[info["display_name"]] = queue_data
            logger.info(f"GetStreamQueue: returned queues for {len(final_data)} streams")
        except Exception as e:
            logger.error(f"Error processing stream queue: {traceback.format_exc()}")
        return final_data

    def GetStreamMatchId(self, station):
        """Return the future-set data for the match currently ON_STREAM on the station's slot.

        ``station`` is the dict produced by ``GetStations`` — uses
        ``station['id']`` (parry stream UUID) and ``station['slot']`` (0-indexed
        capacity slot) to select the Nth STREAM_QUEUE_ENTRY_STATUS_ONSTREAM
        match in queue order. For backward compatibility with callers passing
        a bare identifier string, falls back to a name-based lookup with slot 0.
        """
        self._setup_service("Stream")
        self._setup_service("Match")
        try:
            if isinstance(station, dict):
                stream_id = station.get("id")
                slot = station.get("slot", 0)
            else:
                target = (station or "").lower()
                stream_id = next(
                    (sid for sid, info in self._get_streams().items()
                     if info["display_name"].lower() == target or info["channel"].lower() == target),
                    None,
                )
                slot = 0
            if not stream_id:
                return None
            req = GetStreamQueueRequest()
            req.stream_id = stream_id
            resp = self.stream_service.GetStreamQueue(req, metadata=self.metadata, timeout=self._timeout)
            on_stream_entries = [
                e for e in resp.entries
                if e.status == StreamQueueEntryStatus.STREAM_QUEUE_ENTRY_STATUS_ONSTREAM and e.match_id
            ]
            if slot >= len(on_stream_entries):
                return None
            return self._fetch_future_set(on_stream_entries[slot].match_id)
        except Exception as e:
            logger.error(f"Error in GetStreamMatchId: {traceback.format_exc()}")
            return None

    def GetStationMatchId(self, stationId):
        # parry.gg has no station concept.
        return None

    def GetStationMatchsId(self, stationId):
        # parry has no station concept, but a parry stream has an ordered
        # queue of matches. Returning that queue here lets TSH's existing
        # station-queue plumbing (LoadStationSetsDo → GetFutureMatchesList →
        # station_queue StateManager key) populate an upcoming-matches
        # overlay for parry streams. ``stationId`` is the parry stream UUID
        # passed via lastStationSelected['id'].
        if not stationId or stationId not in self._get_streams():
            return []
        self._setup_service("Stream")
        try:
            req = GetStreamQueueRequest()
            req.stream_id = stationId
            resp = self.stream_service.GetStreamQueue(req, metadata=self.metadata, timeout=self._timeout)
            return [{"id": entry.match_id} for entry in resp.entries if entry.match_id]
        except Exception:
            logger.error(f"Error fetching parry stream queue for {stationId}: {traceback.format_exc()}")
            return []
    
    # Accepts a parry profile URL (https://parry.gg/profile/<uuid>) or a bare UUID.
    @staticmethod
    def _parse_user_id(user):
        if user and PARRY_PROFILE_PATH in user:
            return user.split(PARRY_PROFILE_PATH, 1)[1].split("/")[0].split("?")[0]
        return (user or "").strip()

    # Prefer a READY/IN_PROGRESS match; fall back to most-recent completed.
    # MatchesFilter.state is a singular enum, so fetch by user_id only and
    # post-filter on the response.
    def _find_active_or_recent_match(self, user_id):
        self._setup_service("Match")
        req = GetMatchesRequest()
        req.filter.user_id = user_id
        resp = self.match_service.GetMatches(req, metadata=self.metadata, timeout=self._timeout)
        active = [
            c for c in resp.matches
            if c.match.state in (MatchState.MATCH_STATE_READY, MatchState.MATCH_STATE_IN_PROGRESS)
        ]
        if active:
            return active[0]
        completed = [c for c in resp.matches if c.match.state == MatchState.MATCH_STATE_COMPLETED]
        if completed:
            return max(completed, key=lambda c: c.match.ended_at.seconds)
        return None

    @staticmethod
    def _tournament_url_from_hierarchy(hierarchy):
        tournament_slug = next(
            (p.slug for p in hierarchy.paths if p.type == PathType.PATH_TYPE_TOURNAMENT),
            None,
        )
        event_slug = next(
            (p.slug for p in hierarchy.paths if p.type == PathType.PATH_TYPE_EVENT),
            None,
        )
        if not tournament_slug or not event_slug:
            return None
        return PARRY_TOURNAMENT_URL_FORMAT.format(f"{tournament_slug}/{event_slug}")

    @staticmethod
    def _user_in_slot_2(seeds, user_id):
        if len(seeds) < 2 or not seeds[0].HasField("event_entrant") or not seeds[0].event_entrant.HasField("entrant"):
            return False
        return user_id not in (u.id for u in seeds[0].event_entrant.entrant.users)

    def GetUserMatchId(self, user):
        user_id = self._parse_user_id(user)
        if not user_id:
            return None
        ctx = self._find_active_or_recent_match(user_id)
        if ctx is None:
            return None
        url = self._tournament_url_from_hierarchy(ctx.hierarchy)
        if url:
            invokeSlot(self.tshTdp.SetTournament, url)
        set_data = self._process_future_set(ctx)
        if self._user_in_slot_2(ctx.seeds, user_id):
            set_data["reverse"] = True
        return set_data

    def _build_event_player_dict(self, user):
        """Build a StartGG-shaped player dict for set/standings consumers."""
        return {
            "prefix": user.sponsor_name,
            "gamerTag": user.gamer_tag,
            "name": (user.first_name + " " + user.last_name).strip(),
            "id": [user.id, user.id],
            "country_code": user.location_country,
            "state_code": user.location_state,
            "pronoun": user.pronouns,
        }

    def _set_player_pair_from_match(self, match, seeds_by_id):
        """Return (seed1, seed2, p1_user, p2_user) for a match, or None if missing data."""
        if len(match.slots) < 2:
            return None
        seed1 = seeds_by_id.get(match.slots[0].seed_id)
        seed2 = seeds_by_id.get(match.slots[1].seed_id)
        if not seed1 or not seed2:
            return None
        if not seed1.HasField("event_entrant") or not seed1.event_entrant.HasField("entrant"):
            return None
        if not seed2.HasField("event_entrant") or not seed2.event_entrant.HasField("entrant"):
            return None
        users1 = seed1.event_entrant.entrant.users
        users2 = seed2.event_entrant.entrant.users
        if not users1 or not users2:
            return None
        return seed1, seed2, users1[0], users2[0]

    def _build_completed_set(self, match, seeds_by_id, rounds_by_key, phase, bracket):
        """Build a StartGG-shaped completed-set dict (winner/loser oriented)."""
        pair = self._set_player_pair_from_match(match, seeds_by_id)
        if pair is None:
            return None
        seed1, seed2, u1, u2 = pair
        team1_player = self._build_event_player_dict(u1)
        team2_player = self._build_event_player_dict(u2)
        score1 = int(match.slots[0].score)
        score2 = int(match.slots[1].score)

        # winner/loser orientation — score wins (parry doesn't expose a winner_id).
        if score1 >= score2:
            keys = ["winner", "loser"]
        else:
            keys = ["loser", "winner"]

        round_msg = rounds_by_key.get((match.round, match.winners_side))
        round_label = self._translate_round_name(round_msg.label if round_msg else "")

        phase_name = phase.name if phase else ""
        phase_identifier = bracket.name if (bracket and phase and len(phase.brackets) > 1) else ""

        return {
            "phase_id": phase_identifier,
            "phase_name": phase_name,
            "round_name": round_label,
            f"{keys[0]}_score": score1,
            f"{keys[0]}_seed": seed1.seed,
            f"{keys[0]}_team": {1: {"sponsor": team1_player["prefix"], "gamertag": team1_player["gamerTag"]}},
            f"{keys[0]}_team_name": "",
            f"{keys[1]}_score": score2,
            f"{keys[1]}_seed": seed2.seed,
            f"{keys[1]}_team": {1: {"sponsor": team2_player["prefix"], "gamertag": team2_player["gamerTag"]}},
            f"{keys[1]}_team_name": "",
            "ended_at": match.ended_at.seconds,
        }

    def _build_last_set(self, match, seeds_by_id, rounds_by_key, phase, bracket, target_user_id):
        """Build a StartGG-shaped last-set dict (player1/player2 oriented; target as player1)."""
        pair = self._set_player_pair_from_match(match, seeds_by_id)
        if pair is None:
            return None
        seed1, seed2, u1, u2 = pair
        score1 = int(match.slots[0].score)
        score2 = int(match.slots[1].score)

        # Target user goes to player1
        if u1.id != target_user_id and u2.id == target_user_id:
            seed1, seed2 = seed2, seed1
            u1, u2 = u2, u1
            score1, score2 = score2, score1

        round_msg = rounds_by_key.get((match.round, match.winners_side))
        round_label = self._translate_round_name(round_msg.label if round_msg else "")
        phase_name = phase.name if phase else ""
        phase_identifier = bracket.name if (bracket and phase and len(phase.brackets) > 1) else ""

        return {
            "phase_id": phase_identifier,
            "phase_name": phase_name,
            "round_name": round_label,
            "player1_score": score1,
            "player1_seed": seed1.seed,
            "player1_team": u1.sponsor_name,
            "player1_name": u1.gamer_tag,
            "player2_score": score2,
            "player2_seed": seed2.seed,
            "player2_team": u2.sponsor_name,
            "player2_name": u2.gamer_tag,
            "ended_at": match.ended_at.seconds,
        }

    def _iter_completed_matches(self):
        """Yield (match, seeds_by_id, rounds_by_key, phase, bracket) for every completed match in the event."""
        for phase in self._get_phases().values():
            for bracket_ref in phase.brackets:
                bracket = self._fetch_bracket(bracket_ref.id)
                if bracket is None:
                    continue
                seeds_by_id = {s.id: s for s in bracket.seeds}
                rounds_by_key = {(r.number, r.winners_side): r for r in bracket.rounds}
                for match in bracket.matches:
                    if match.state != MatchState.MATCH_STATE_COMPLETED:
                        continue
                    yield match, seeds_by_id, rounds_by_key, phase, bracket

    def GetRecentSets(self, id1, id2, videogame, callback, requestTime, progress_callback=None, cancel_event=None):
        """Head-to-head: list of sets where both players faced each other.

        ``id1``/``id2`` are ``[lookup_id, user_id]`` lists from parry's
        player dicts (both elements are user_id since parry has no
        per-game scope). Uses parry user_ids to filter
        MatchService.GetMatches and intersect by opponent. Cross-platform
        merge with start.gg linked accounts is handled below.
        """
        try:
            user_id_1 = id1[1] if len(id1) > 1 else None
            user_id_2 = id2[1] if len(id2) > 1 else None
            if not user_id_1 or not user_id_2:
                callback.emit({"sets": [], "request_time": requestTime})
                return

            self._setup_service("Match")
            req = GetMatchesRequest()
            req.filter.user_id = user_id_1
            resp = self.match_service.GetMatches(req, metadata=self.metadata, timeout=self._timeout)

            recent = []
            for match_context in resp.matches:
                match = match_context.match
                seeds = list(match_context.seeds)
                if len(seeds) < 2 or match.state != MatchState.MATCH_STATE_COMPLETED:
                    continue
                set_data = self._build_h2h_set(match_context, user_id_1, user_id_2)
                if set_data is not None:
                    recent.append(set_data)

            # Cross-platform fallback: when both parry users have linked
            # start.gg accounts, fetch their start.gg H2H history too and
            # merge. Output shape matches parry-native sets, so dedupe by id
            # and re-sort works without remapping.
            startgg_sets = self._fetch_startgg_h2h(user_id_1, user_id_2)
            if startgg_sets:
                seen_ids = {s.get("id") for s in recent if s.get("id")}
                for s in startgg_sets:
                    if s.get("id") not in seen_ids:
                        recent.append(s)

            recent.sort(key=lambda s: s.get("timestamp", 0), reverse=True)
            logger.info(
                f"GetRecentSets: H2H {user_id_1} vs {user_id_2} -> {len(recent)} sets "
                f"(parry + {len(startgg_sets) if startgg_sets else 0} from linked start.gg)"
            )
            callback.emit({"sets": recent, "request_time": requestTime})
        except Exception as e:
            logger.error(f"Error in GetRecentSets: {traceback.format_exc()}")
            callback.emit({"sets": [], "request_time": requestTime})

    def _fetch_startgg_h2h(self, parry_user_id_1, parry_user_id_2):
        link_1 = self._get_linked_startgg_account(parry_user_id_1)
        link_2 = self._get_linked_startgg_account(parry_user_id_2)
        if not link_1 or not link_2:
            return []
        videogame_id = TSHGameAssetManager.instance.selectedGame.get("smashgg_game_id")
        if not videogame_id:
            return []
        pid_1 = self._resolve_startgg_player_id(link_1["slug"])
        pid_2 = self._resolve_startgg_player_id(link_2["slug"])
        if not pid_1 or not pid_2:
            return []

        # Delegate to StartGG's public GetRecentSets — it owns the
        # fan-out (5 pages × 2 directions), dedupe, and sort.
        cb = _CapturingCallback()
        self._get_startgg_subquery().GetRecentSets(
            [pid_1, str(link_1["user_id"])],
            [pid_2, str(link_2["user_id"])],
            videogame_id,
            cb,
            0,
            None,
            None,
        )
        return (cb.result or {}).get("sets", [])

    def EnrichPlayerData(self, playerData):
        # Lazy mains fill from a linked start.gg account. Fires once per
        # SetData; cached at every layer (linked-account, player-id,
        # mains) so repeated slot loads are free.
        if not playerData or playerData.get("mains"):
            return playerData
        ids = playerData.get("id") or []
        user_id = ids[1] if len(ids) > 1 else None
        if not user_id:
            return playerData
        mains = self._fetch_startgg_mains(user_id)
        if mains:
            playerData["mains"] = mains
        return playerData

    def _fetch_startgg_mains(self, parry_user_id):
        # Delegates to StartGG's GetUserMains. Returns the same `mains`
        # shape ProcessEntrantData produces ({gameCodename: [[char], ...]})
        # or {} when the user lacks a linked start.gg account or no
        # smashgg_game_id is mapped for the active game.
        if self._startgg_mains_cache is None:
            self._startgg_mains_cache = {}
        if parry_user_id in self._startgg_mains_cache:
            return self._startgg_mains_cache[parry_user_id]

        link = self._get_linked_startgg_account(parry_user_id)
        if not link:
            self._startgg_mains_cache[parry_user_id] = {}
            return {}
        selected = TSHGameAssetManager.instance.selectedGame or {}
        videogame_id = selected.get("smashgg_game_id")
        if not videogame_id:
            return {}  # don't cache — game may change
        mains = self._get_startgg_subquery().GetUserMains(link["slug"], videogame_id)
        self._startgg_mains_cache[parry_user_id] = mains
        return mains

    def _build_h2h_set(self, match_context, target_user_id, opponent_user_id):
        """Build a set dict in the shape `recent_sets` / `recent_sets_full` layouts expect:
        score=[target_score, opponent_score], winner=0/1 (0 if target won),
        plus tournament/event/online/timestamp/round/phase fields.
        Returns None if the match doesn't actually pair target vs opponent.
        """
        match = match_context.match
        seeds = list(match_context.seeds)
        if len(seeds) < 2 or len(match.slots) < 2:
            return None

        # Identify which slot belongs to which user
        def slot_user_ids(seed):
            if not seed.HasField("event_entrant") or not seed.event_entrant.HasField("entrant"):
                return ()
            return tuple(u.id for u in seed.event_entrant.entrant.users)

        slot0_users = frozenset(slot_user_ids(seeds[0]))
        slot1_users = frozenset(slot_user_ids(seeds[1]))
        # Set-equality (not membership) so a doubles match where the two
        # users happen to face each other across opposing teams isn't
        # counted as a 1v1 H2H. Using sets keeps the comparison
        # forward-compatible: lifting target/opponent to multi-user team
        # frozensets later would let the same check serve team-vs-team H2H
        # without further changes.
        target_team = frozenset([target_user_id])
        opponent_team = frozenset([opponent_user_id])
        if slot0_users == target_team and slot1_users == opponent_team:
            target_slot, opponent_slot = 0, 1
        elif slot1_users == target_team and slot0_users == opponent_team:
            target_slot, opponent_slot = 1, 0
        else:
            return None

        target_score = int(match.slots[target_slot].score)
        opponent_score = int(match.slots[opponent_slot].score)

        # Tournament/event names from MatchContext.hierarchy
        hierarchy = match_context.hierarchy
        tournament_name = next(
            (p.name for p in hierarchy.paths if p.type == PathType.PATH_TYPE_TOURNAMENT),
            "",
        )
        event_name = next(
            (p.name for p in hierarchy.paths if p.type == PathType.PATH_TYPE_EVENT),
            "",
        )

        return {
            "id": match.id,
            "tournament": tournament_name,
            "event": event_name,
            "online": self._is_online(),
            "score": [target_score, opponent_score],
            "timestamp": match.ended_at.seconds,
            "winner": 0 if target_score >= opponent_score else 1,
            "round": self._translate_round_name(match_context.round.label),
            "phase_name": self._phase_name_from_hierarchy(hierarchy),
            "phase_id": "",
        }

    def GetLastSets(self, playerID, playerNumber, callback, progress_callback=None, cancel_event=None):
        """Last 10 completed sets for the given player in the current event.
        playerID is the parry user_id (UUID) — populated as id[0] in the
        provider's player dicts; see id-shape note in _build_match_info.
        """
        try:
            user_id = playerID
            if not user_id:
                callback.emit({"playerNumber": playerNumber, "last_sets": []})
                return

            sets = []
            for match, seeds_by_id, rounds_by_key, phase, bracket in self._iter_completed_matches():
                # Check if target user participated
                participating = False
                for slot in match.slots:
                    seed = seeds_by_id.get(slot.seed_id)
                    if seed and seed.HasField("event_entrant") and seed.event_entrant.HasField("entrant"):
                        for user in seed.event_entrant.entrant.users:
                            if user.id == user_id:
                                participating = True
                                break
                    if participating:
                        break
                if not participating:
                    continue

                set_data = self._build_last_set(match, seeds_by_id, rounds_by_key, phase, bracket, user_id)
                if set_data:
                    sets.append(set_data)

            sets.sort(key=lambda s: s.get("ended_at", 0), reverse=True)
            sets = sets[:10]
            logger.info(f"GetLastSets: user {user_id} player{playerNumber} -> {len(sets)} sets")
            callback.emit({"playerNumber": playerNumber, "last_sets": sets})
        except Exception as e:
            logger.error(f"Error in GetLastSets: {traceback.format_exc()}")
            callback.emit({"playerNumber": playerNumber, "last_sets": []})

    def GetCompletedSets(self, progress_callback=None, cancel_event=None):
        """Last 10 completed sets in the current event, most recent first."""
        try:
            sets = []
            for match, seeds_by_id, rounds_by_key, phase, bracket in self._iter_completed_matches():
                set_data = self._build_completed_set(match, seeds_by_id, rounds_by_key, phase, bracket)
                if set_data:
                    sets.append(set_data)
            sets.sort(key=lambda s: s.get("ended_at", 0), reverse=True)
            sets = sets[:10]
            logger.info(f"GetCompletedSets: -> {len(sets)} sets")
            return sets
        except Exception as e:
            logger.error(f"Error in GetCompletedSets: {traceback.format_exc()}")
            return []

    def GetPlayerHistoryStandings(self, playerID, playerNumber, gameType, callback, progress_callback=None, cancel_event=None):
        """Recent tournament placements for a player, via UserService.GetUserPlacements.

        Filters out non-singles events (entrant_size != 1) since the consumer
        in TSHStatsUtil only requests this data when the scoreboard is in
        1v1 mode.

        To resolve event/tournament metadata we use the same trick as
        parrygg-web's RecentTournamentResults (parrygg-web/app/components/
        RecentTournamentResults.tsx + routes/_base-layout.profile.$userId.tsx):
        a single GetTournaments(filter={user_id}) returns every tournament
        the user is registered in with each tournament's events embedded,
        so we build an event_id -> (event, tournament) map in-memory and
        avoid per-placement RPCs.

        Pass-1 (parry-native): uses parry's placements only. Pass 2 will merge
        in start.gg history for users with linked accounts.
        """
        try:
            user_id = playerID
            if not user_id:
                callback.emit({"playerNumber": playerNumber, "history_sets": []})
                return

            self._setup_service("User")
            self._setup_service("Tournament")

            # One-shot: fetch every tournament the user is registered in
            # (with embedded events list).
            event_lookup = {}
            try:
                t_req = GetTournamentsRequest()
                t_req.filter.user_id = user_id
                t_resp = self.tournament_service.GetTournaments(t_req, metadata=self.metadata, timeout=self._timeout)
                for tournament in t_resp.tournaments:
                    for event in tournament.events:
                        event_lookup[event.id] = (event, tournament)
            except Exception as e:
                logger.warning(f"GetPlayerHistoryStandings: failed to fetch user's tournaments: {e}")

            req = GetUserPlacementsRequest()
            req.id = user_id
            # Page over ~50 to ensure we have enough singles results after
            # filtering out doubles/3v3 events.
            req.pagination_request.page_size = 50
            resp = self.user_service.GetUserPlacements(req, metadata=self.metadata, timeout=self._timeout)

            history = []
            for result in resp.results:
                if len(history) >= 10:
                    break
                if not result.HasField("placement"):
                    continue
                event_id = result.event_id
                lookup = event_lookup.get(event_id)
                if not lookup:
                    continue
                event, tournament = lookup

                if event.entrant_size != 1:
                    continue

                tournament_picture = next(
                    (img.url for img in tournament.images if img.type == ImageType.IMAGE_TYPE_BANNER),
                    None,
                )

                placement = result.placement
                history.append({
                    "placement": placement.placement,
                    "event_name": event.name,
                    "tournament_name": tournament.name,
                    "tournament_picture": tournament_picture,
                    "entrants": event.entrant_count,
                    "event_date": event.start_date.seconds,
                })

            logger.info(f"GetPlayerHistoryStandings: user {user_id} -> {len(history)} placements")
            callback.emit({"playerNumber": playerNumber, "history_sets": history})
        except Exception as e:
            logger.error(f"Error in GetPlayerHistoryStandings: {traceback.format_exc()}")
            callback.emit({"playerNumber": playerNumber, "history_sets": []})
    
    def GetTournamentPhases(self, progress_callback=None, cancel_event=None):
        self._setup_service("Event")

        phases = []

        try:
            get_event_request = GetEventRequest()
            get_event_request.id = self.event_id
            get_event_response = self.event_service.GetEvent(get_event_request, metadata=self.metadata, timeout=self._timeout)
            
            for phase in get_event_response.event.phases:
                logger.info(f"phase {phase.id[:8]}… ({phase.name!r}) has {len(phase.brackets)} bracket(s)")
                phase_info = {
                    "id": phase.id,
                    "name": phase.name,
                    "groups": []
                }

                for bracket in phase.brackets:
                    logger.info(f"  bracket {bracket.id[:8]}… name={bracket.name!r} index={bracket.index}")
                    # `bracketType` (camelCase) matches the field name TSHBracketWidget
                    # reads at line 240 to gate dropdown enablement; non-DOUBLE_ELIMINATION
                    # brackets are intentionally disabled for now.
                    bracket_info = {
                        "id": bracket.id,
                        "name": bracket.name,
                        "bracketType": _bracket_type_name(phase.bracket_type),
                    }

                    phase_info["groups"].append(bracket_info)

                phases.append(phase_info)
        
        except Exception as e:
            logger.error(f"Error getting tournament phases: {e}")
        
        return phases
    
    def GetTournamentPhaseGroup(self, id, progress_callback=None, cancel_event=None):
        """Build the bracket-detail dict TSH renders.

        StartGG calls this a "phase group" — for parry that's a single Bracket.
        Output shape matches StartGGDataProvider.GetTournamentPhaseGroup so the
        TSHBracket consumer treats both providers identically:
            {
                "entrants": [{"players": [...], "name": str?}, ...],   # ordered by seed
                "seedMap": [seed numbers in bracket position order],
                "sets": {"<signed round>": [{"score": [t1, t2], "finished": bool}]},
                "progressionsIn": [],
                "progressionsOut": [],
                "winnersOnlyProgressions": bool,
                "customSeeding": bool,
            }
        """
        final_data = {}
        try:
            bracket = self._fetch_bracket(id)
            if bracket is None:
                return {}

            # parry's BracketService.GetBracket returns the whole phase's seeds
            # on every bracket within the phase, so a multi-pool phase reports
            # all phase entrants for each pool. Filter to the seeds actually
            # referenced by this bracket's matches, then renumber pool-locally
            # so TSHBracket's seeding(playerNumber) produces the right layout
            # for the pool's real size.
            referenced_seed_ids = {
                slot.seed_id
                for match in bracket.matches
                for slot in match.slots
                if slot.seed_id
            }
            seeds_in_bracket = sorted(
                (s for s in bracket.seeds if s.id in referenced_seed_ids),
                key=lambda s: s.seed,
            )

            entrants = []
            for pool_local_seed, seed in enumerate(seeds_in_bracket, start=1):
                team = {"players": []}
                ee = self._seed_entrant(seed)
                if ee is not None:
                    entrant = ee.entrant
                    if len(entrant.users) > 1:
                        team["name"] = self._team_display_name(seed)
                    for user in entrant.users:
                        avatar = next(
                            (img.url for img in user.images if img.type == ImageType.IMAGE_TYPE_AVATAR),
                            "",
                        )
                        team["players"].append({
                            "prefix": user.sponsor_name,
                            "gamerTag": user.gamer_tag,
                            "name": (user.first_name + " " + user.last_name).strip(),
                            "id": [user.id, user.id],
                            "country_code": user.location_country,
                            "state_code": user.location_state,
                            "pronoun": user.pronouns,
                            "avatar": avatar,
                            "seed": pool_local_seed,
                        })
                entrants.append(team)
            final_data["entrants"] = entrants

            # No seedMap: parry's Seed.bracket_index isn't a reliable
            # bracket-position field today (sorting by it produces sequential
            # 1..N instead of standard bracket layout). Omitting the key lets
            # TSHBracket fall back to its own seeding(playerNumber) at
            # TSHBracket.py:71, which produces the correct power-of-2 bracket
            # layout with seeds beyond originalPlayerNumber rendered as byes.

            # Sets keyed by signed round number (positive=winners, negative=losers),
            # matching start.gg's convention.
            sets_by_round = {}
            
            # Offset of 2 for brackets with a power of 2 player count, 3 otherwise.
            n = len(bracket.seeds)
            losers_offset = 2 if n > 0 and (n & (n - 1)) == 0 else 3
            
            for match in bracket.matches:
                round_key = str(match.round if match.winners_side else -match.round - losers_offset)
                sets_by_round.setdefault(round_key, []).append({
                    "score": [
                        int(match.slots[0].score) if len(match.slots) > 0 and match.slots[0].state == SlotState.SLOT_STATE_NUMERIC else -1,
                        int(match.slots[1].score) if len(match.slots) > 1 and match.slots[1].state == SlotState.SLOT_STATE_NUMERIC else -1,
                    ],
                    "finished": match.state == MatchState.MATCH_STATE_COMPLETED,
                })
            final_data["sets"] = sets_by_round

            # Progressions: TSH consumers only read len() to drive the in/out
            # spinners (TSHBracketWidget.UpdatePhaseGroup).
            #
            # Outgoing: Bracket.progressions carries one entry per seed
            # advancing out. Filter to those originating from this bracket
            # to drop sibling-bracket noise in shared phases.
            progressions_out = [
                p for p in bracket.progressions
                if not p.origin_bracket_id or p.origin_bracket_id == bracket.id
            ]
            final_data["progressionsOut"] = [p.id for p in progressions_out]

            # Inbound: each Seed that arrived from a prior bracket has its
            # `progression` field populated. parrygg-shared's bracket renderer
            # uses the same signal (domain/bracket.ts:248-250).
            final_data["progressionsIn"] = [
                s.id for s in bracket.seeds if s.HasField("progression")
            ]
            final_data["winnersOnlyProgressions"] = False
            final_data["customSeeding"] = False

            logger.info(
                f"GetTournamentPhaseGroup: bracket {id} ({bracket.name}) -> "
                f"{len(entrants)} entrants, {len(bracket.matches)} matches across {len(sets_by_round)} rounds, "
                f"{len(final_data['progressionsIn'])} progressions in, {len(final_data['progressionsOut'])} progressions out"
            )

        except Exception as e:
            logger.error(f"Error processing phase group: {traceback.format_exc()}")

        return final_data
    
    def GetStandings(self, playerNumber, progress_callback=None, cancel_event=None):
        """Top N event placements via EventService.GetEventPlacements.

        Output mirrors StartGGDataProvider.GetStandings — a list of teams
        ordered by placement, each with a 'players' list of player dicts.
        """
        try:
            self._setup_service("Event")
            req = GetEventPlacementsRequest()
            req.id = self.event_id
            resp = self.event_service.GetEventPlacements(req, metadata=self.metadata, timeout=self._timeout)

            placements = sorted(
                [p for p in resp.placements if p.HasField("event_entrant")],
                key=lambda p: p.placement,
            )[:playerNumber]

            teams = []
            for placement in placements:
                entrant = placement.event_entrant.entrant
                team = {"players": []}
                if len(entrant.users) > 1:
                    team["name"] = ""
                for user in entrant.users:
                    avatar = next(
                        (img.url for img in user.images if img.type == ImageType.IMAGE_TYPE_AVATAR),
                        "",
                    )
                    team["players"].append({
                        "prefix": user.sponsor_name,
                        "gamerTag": user.gamer_tag,
                        "name": (user.first_name + " " + user.last_name).strip(),
                        "id": [user.id, user.id],
                        "country_code": user.location_country,
                        "state_code": user.location_state,
                        "pronoun": user.pronouns,
                        "avatar": avatar,
                        "seed": placement.seed,
                    })
                teams.append(team)

            logger.info(f"GetStandings: top {playerNumber} -> {len(teams)} teams")
            return teams
        except Exception as e:
            logger.error(f"Error in GetStandings: {traceback.format_exc()}")
            return []
    
    def GetFutureMatch(self, matchId, progress_callback, cancel_event):
        return self._fetch_future_set(matchId) or {}

    def GetFutureMatchesList(self, setsId, progress_callback, cancel_event):
        # Returns {position_str: future_set} keyed by 1-based position in
        # the queue, matching StartGGDataProvider.GetFutureMatchesList shape.
        result = {}
        for position, item in enumerate(setsId or [], start=1):
            match_id = item.get("id") if isinstance(item, dict) else item
            if not match_id:
                continue
            future_set = self._fetch_future_set(match_id)
            if future_set:
                result[str(position)] = future_set
        return result
    
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
