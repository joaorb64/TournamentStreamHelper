import math
from .Helpers.TSHLocaleHelper import TSHLocaleHelper
from loguru import logger

class BracketSet():
    BYE = -1
    PENDING = -2

    def __init__(self, bracket: "Bracket", pos) -> None:
        self.bracket: Bracket = bracket
        self.playerIds = [BracketSet.BYE, BracketSet.BYE]
        self.score = [0, 0]
        self.winNext: "BracketSet" = None
        self.winNextSlot: int = 0
        self.loseNext: "BracketSet" = None
        self.loseNextSlot: int = 0
        self.pos = pos
        self.finished = False

# Bracket always has a power of 2 number of players
# if there are less than that, we round up and add
# 'bye's as the lower seeded players
def next_power_of_2(x):
    return 1 if x == 0 else 2**math.ceil(math.log2(x))

# Seeding order logic
def seeding(numPlayers):
    rounds = math.log(numPlayers)/math.log(2)-1
    pls = [1,2]
    for i in range(int(rounds)):
        pls = nextLayer(pls)
    return pls

# Checks if a number is power of 2
def is_power_of_two(n):
    return (n != 0) and (n & (n-1) == 0)

def nextLayer(pls):
    out = []
    length = len(pls)*2+1
    
    for d in pls:
        out.append(d)
        out.append(length-d)
    return out

class Bracket():
    def __init__(self, playerNumber, progressionsIn, seedMap=None, winnersOnlyProgressions=False, customSeeding=False) -> None:
        self.originalPlayerNumber = playerNumber
        self.playerNumber = next_power_of_2(playerNumber)

        self.progressionsIn = progressionsIn

        if seedMap:
            if len(seedMap) < self.playerNumber:
                for i in range(len(seedMap)+1, self.playerNumber+1):
                    seedMap.append(-1)
            seeds = seedMap
        else:
            seeds = seeding(self.playerNumber)
        
        self.seedMap = seeds

        self.winnersOnlyProgressions = winnersOnlyProgressions

        self.customSeeding = customSeeding
        
        if progressionsIn > 0 and -1 in self.seedMap:
            self.winnersOnlyProgressions = True

        self.rounds = {}

        for i in range(len(seeds)):
            if seeds[i] > self.originalPlayerNumber:
                seeds[i] = -1

        # Create winners
        self.rounds["1"] = []
        for i in range(self.playerNumber):
            if i % 2 == 0:
                _set = BracketSet(self, [1, len(self.rounds["1"])])
                _set.playerIds[0] = seeds[i]
                _set.playerIds[1] = seeds[i+1]
                self.rounds["1"].append(_set)
        
        # Create losers
        self.rounds["-1"] = []
        self.rounds["-2"] = []
        for i in range(int(self.playerNumber/2)):
            self.rounds["-1"].append(BracketSet(self, [-1, int(len(self.rounds["-1"])/2)]))
            self.rounds["-2"].append(BracketSet(self, [-1, int(len(self.rounds["-2"])/2)]))
        
        # Fill with -1
        for round in ["-1", "-2"]:
            for _set in self.rounds[round]:
                _set.score = [-1, -1]
                _set.finished = True
        
        # Expand winners
        subBracket = []
        i = self.playerNumber/2

        while i > 1:
            i = math.floor(i/2)
            round = [BracketSet(self, [2+len(subBracket), i]) for i in range(int(i))]
            subBracket.append(round)
        subBracket.append([BracketSet(self, [2+len(subBracket), 0])])
        subBracket.append([BracketSet(self, [2+len(subBracket), 0])])

        for r, round in enumerate(subBracket):
            self.rounds[str(2+r)] = round
        
        # Expand losers
        subBracket = []
        i = self.playerNumber/2

        while i > 1:
            i = math.floor(i/2)
            for j in range(2):
                round = [BracketSet(self, [-1-len(subBracket), i]) for i in range(math.floor(i))]
                subBracket.append(round)

        for r, round in enumerate(subBracket):
            self.rounds[str(-3-r)] = round

        # Connect sets
        for k, round in self.rounds.items():
            roundNum = int(k)

            if roundNum > 0:
                for j, _set in enumerate(round):
                    try:
                        _set.winNext = self.rounds[str(roundNum+1)][math.floor(j/2)]
                        targetIdW = j%2
                        if int(k) < 0 and abs(int(k))%2 == 1: targetIdW = 1
                        _set.winNextSlot = targetIdW
                    except Exception as e:
                        logger.error(e)
                    try:
                        if abs(roundNum)%4 == 0:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][(int(len(round)/2)+j)%len(round)]
                        elif abs(roundNum)%4 == 1:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][j]
                        elif abs(roundNum)%4 == 2:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][(-1-j)%len(round)]
                        elif abs(roundNum)%4 == 3:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][(int(len(round)/2)-1-j)%len(round)]
                        
                        targetIdL = 0
                        
                        if roundNum == 1:
                            targetIdL = j % 2
                        
                        _set.loseNextSlot = targetIdL
                    except Exception as e:
                        logger.error(e)
            else:
                for j, _set in enumerate(round):
                    try:
                        if abs(roundNum)%2 == 0:
                            _set.winNext = self.rounds[str(roundNum-1)][math.floor(j/2)]
                        else:
                            _set.winNext = self.rounds[str(roundNum-1)][j]
                        targetIdW = j%2
                        if int(k) < 0 and abs(int(k))%2 == 1: targetIdW = 1
                        _set.winNextSlot = targetIdW
                    except Exception as e:
                        logger.error(e)
        
        # Connect losers to winners for grand finals
        lastLosers = min([int(r) for r in self.rounds.keys()])
        gfsRound = max([int(r) for r in self.rounds.keys()]) - 1
        self.rounds[str(lastLosers)][0].winNext = self.rounds[str(gfsRound)][0]

        # Connect grand finals to reset
        gfsResetRound = max([int(r) for r in self.rounds.keys()])
        gfsRound = gfsResetRound - 1
        self.rounds[str(gfsRound)][0].winNext = self.rounds[str(gfsResetRound)][0]
        self.rounds[str(gfsRound)][0].loseNext = self.rounds[str(gfsResetRound)][0]
    
    def IsBye(self, playerId):
        if playerId == -1 or playerId > self.originalPlayerNumber: return True
        return False
    
    def UpdateBracket(self):
        for roundKey, round in sorted(self.rounds.items(), key=lambda x: (int(x[0]) < 0, abs(int(x[0])))):
            for j, _set in enumerate(round):
                targetIdW = j%2
                targetIdL = 0
                if int(roundKey) < 0 and abs(int(roundKey))%2 == 1: targetIdW = 1

                lastLosers = min([int(r) for r in self.rounds.keys()])
                if roundKey == str(lastLosers):
                    targetIdW = 1

                gfsRound = max([int(r) for r in self.rounds.keys()]) - 1
                if roundKey == str(gfsRound):
                    targetIdW = 0
                    targetIdL = 1
                
                # When we have progressions in, force first (hidden) sets to double DQs
                # If we have a non-power of 2 number of progressions, we do it for 2 rounds
                if self.progressionsIn > 0 and not self.winnersOnlyProgressions:
                    if int(roundKey) == 1:
                        _set.score = [-1, -1]
                        _set.finished = True
                    
                    if int(roundKey) == 2 and not is_power_of_two(self.progressionsIn) and not self.customSeeding:
                        _set.score = [-1, -1]
                        _set.finished = True

                if _set.winNext:
                    # Both slots are bye OR slot 2 is bye, auto win for p1
                    if (self.IsBye(_set.playerIds[0]) and self.IsBye(_set.playerIds[1])) or \
                        (not self.IsBye(_set.playerIds[0]) and self.IsBye(_set.playerIds[1])):
                        won = 0
                        lost = 1
                        _set.winNext.playerIds[targetIdW] = _set.playerIds[won]
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = _set.playerIds[lost]
                    # Slot 1 is bye, auto win
                    elif self.IsBye(_set.playerIds[0]) and not self.IsBye(_set.playerIds[1]):
                        won = 1
                        lost = 0
                        _set.winNext.playerIds[targetIdW] = _set.playerIds[won]
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = _set.playerIds[lost]
                    # -1,-1 draw; advance higher seed
                    elif _set.score[0] == -1 and _set.score[1] == -1:
                        # Advance higher seed
                        won = 0 if _set.playerIds[0] < _set.playerIds[1] else 1
                        lost = 0 if won == 1 else 1
                        _set.winNext.playerIds[targetIdW] = _set.playerIds[won]
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = _set.playerIds[lost]
                    # Set not finished, pass pending state
                    elif not _set.finished:
                        _set.winNext.playerIds[targetIdW] = -2
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = -2
                    # Real match results
                    else:
                        # P1 wins
                        if _set.score[0] > _set.score[1]:
                            _set.winNext.playerIds[targetIdW] = _set.playerIds[0]
                            if _set.loseNext:
                                _set.loseNext.playerIds[targetIdL] = _set.playerIds[1]
                        # P2 wins
                        elif _set.score[0] < _set.score[1]:
                            _set.winNext.playerIds[targetIdW] = _set.playerIds[1]
                            if _set.loseNext:
                                _set.loseNext.playerIds[targetIdL] = _set.playerIds[0]
                        # Draw
                        else:
                            _set.winNext.playerIds[targetIdW] = -2
                            if _set.loseNext:
                                _set.loseNext.playerIds[targetIdL] = -2

        # Clear scores when no players in set
        # for k, round in sorted(self.rounds.items(), key=lambda x: (int(x[0]) < 0, abs(int(x[0])))):
        #     for j, _set in enumerate(round):
        #         if _set.playerIds[0] == -2 or _set.playerIds[1] == -2:
        #             _set.score[0] = 0
        #             _set.score[1] = 0

    # Get round names
    def GetRoundName(self, round: str, winnersCutout=[0,0], losersCutout=[0,0]):
        roundNumber = int(round)

        gfsRound = max([int(r) for r in self.rounds.keys()]) - 1
        lastLosers = min([int(r) for r in self.rounds.keys()])

        if roundNumber > 0:
            if roundNumber == gfsRound:
                return TSHLocaleHelper.matchNames.get("grand_final")
            if roundNumber == gfsRound + 1:
                return TSHLocaleHelper.matchNames.get("grand_final_reset")
            if roundNumber == gfsRound - 1:
                return TSHLocaleHelper.matchNames.get("winners_final")
            if roundNumber == gfsRound - 2:
                return TSHLocaleHelper.matchNames.get("winners_semi_final")
            if roundNumber == gfsRound - 3:
                return TSHLocaleHelper.matchNames.get("winners_quarter_final")
        else:
            if roundNumber == lastLosers:
                return TSHLocaleHelper.matchNames.get("losers_final")
            if roundNumber == lastLosers + 1:
                return TSHLocaleHelper.matchNames.get("losers_semi_final")
            if roundNumber == lastLosers + 2:
                return TSHLocaleHelper.matchNames.get("losers_quarter_final")
        
        if roundNumber > 0:
            roundNumber -= winnersCutout[0]
            return TSHLocaleHelper.matchNames.get("winners_round").format(abs(roundNumber))
        if roundNumber < 0:
            roundNumber += losersCutout[0]
            return TSHLocaleHelper.matchNames.get("losers_round").format(abs(roundNumber))