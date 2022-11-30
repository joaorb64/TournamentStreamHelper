import math

class BracketSet():
    def __init__(self, bracket: "Bracket", pos) -> None:
        self.bracket: Bracket = bracket
        self.playerIds = [-1, -1]
        self.score = [-1, -1]
        self.winNext: "BracketSet" = None
        self.loseNext: "BracketSet" = None
        self.pos = pos

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

def nextLayer(pls):
    out = []
    length = len(pls)*2+1
    
    for d in pls:
        out.append(d)
        out.append(length-d)
    return out

class Bracket():
    def __init__(self, playerNumber, seedMap=None) -> None:
        self.playerNumber = next_power_of_2(playerNumber)

        if seedMap:
            seeds = seedMap
        else:
            seeds = seeding(self.playerNumber)

        self.rounds = {}

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
            self.rounds["-1"].append(BracketSet(self, [-1, len(self.rounds["-1"])]))
            self.rounds["-2"].append(BracketSet(self, [-2, len(self.rounds["-2"])]))
        
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
                round = [BracketSet(self, [-3-len(subBracket), i]) for i in range(math.floor(i))]
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
                    except Exception as e:
                        print(e)
                    try:
                        if abs(roundNum)%4 == 0:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][(int(len(round)/2)+j)%len(round)]
                        elif abs(roundNum)%4 == 1:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][j]
                        elif abs(roundNum)%4 == 2:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][(-1-j)%len(round)]
                        elif abs(roundNum)%4 == 3:
                            _set.loseNext = self.rounds[str(-int(2*(roundNum)))][(int(len(round)/2)-1-j)%len(round)]
                    except Exception as e:
                        print(e)
            else:
                for j, _set in enumerate(round):
                    try:
                        if abs(roundNum)%2 == 0:
                            _set.winNext = self.rounds[str(roundNum-1)][math.floor(j/2)]
                        else:
                            _set.winNext = self.rounds[str(roundNum-1)][j]
                    except Exception as e:
                        print(e)
        
        # Connect losers to winners for grand finals
        lastLosers = min([int(r) for r in self.rounds.keys()])
        gfsRound = max([int(r) for r in self.rounds.keys()]) - 1
        self.rounds[str(lastLosers)][0].winNext = self.rounds[str(gfsRound)][0]

        # Connect grand finals to reset
        gfsResetRound = max([int(r) for r in self.rounds.keys()])
        gfsRound = gfsResetRound - 1
        self.rounds[str(gfsRound)][0].winNext = self.rounds[str(gfsResetRound)][0]
        self.rounds[str(gfsRound)][0].loseNext = self.rounds[str(gfsResetRound)][0]
    
    def UpdateBracket(self):
        for k, round in sorted(self.rounds.items()):
            for j, _set in enumerate(round):
                targetIdW = j%2
                targetIdL = 0
                if int(k) < 0 and abs(int(k))%2 == 1: targetIdW = 1

                lastLosers = min([int(r) for r in self.rounds.keys()])
                if k == str(lastLosers):
                    targetIdW = 1

                gfsRound = max([int(r) for r in self.rounds.keys()]) - 1
                if k == str(gfsRound):
                    targetIdW = 0
                    targetIdL = 1

                if _set.winNext:
                    if _set.score[0] > _set.score[1]:
                        _set.winNext.playerIds[targetIdW] = _set.playerIds[0]
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = _set.playerIds[1]
                    elif _set.score[0] < _set.score[1]:
                        _set.winNext.playerIds[targetIdW] = _set.playerIds[1]
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = _set.playerIds[0]
                    elif _set.score[0] == -1 and _set.score[1] == -1:
                        # Advance higher seed, but note that -1 would in theory be a smaller seed
                        won = 0
                        lost = 1
                        if _set.playerIds[1] == -1 and _set.playerIds[0] != -1:
                            won = 0
                            lost = 1
                        elif _set.playerIds[0] == -1 and _set.playerIds[1] != -1:
                            won = 1
                            lost = 0
                        else:
                            won = 0 if _set.playerIds[0] < _set.playerIds[1] else 1
                            lost = 0 if won == 1 else 1
                        _set.winNext.playerIds[targetIdW] = _set.playerIds[won]
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = _set.playerIds[lost]
                    else:
                        _set.winNext.playerIds[targetIdW] = -1
                        if _set.loseNext:
                            _set.loseNext.playerIds[targetIdL] = -1
    # Get round names
    def GetRoundName(self, round: str, progressionsIn=0, progressionsOut=0):
        roundNumber = int(round)

        prefix = "Winners" if roundNumber > 0 else "Losers"

        gfsRound = max([int(r) for r in self.rounds.keys()]) - 1

        if progressionsIn > 0:
            roundNumber -= 1

        # if roundNumber == gfsRound:
        #     return f"Grand Final"
        # if roundNumber == gfsRound + 1:
        #     return f"Grand Final Reset"
        # if roundNumber == gfsRound - 1:
        #     return f"{prefix} Final"
        # if roundNumber == gfsRound - 2:
        #     return f"{prefix} Semi-Final"
        # if roundNumber == gfsRound - 3:
        #     return f"{prefix} Quarter-Final"

        # lastLosers = min([int(r) for r in self.rounds.keys()])

        # if roundNumber == lastLosers:
        #     return f"{prefix} Final"
        # if roundNumber == lastLosers + 1:
        #     return f"{prefix} Semi-Final"
        # if roundNumber == lastLosers + 2:
        #     return f"{prefix} Quarter-Final"

        if roundNumber < 0:
            roundNumber += 3

        return f"{prefix} Round {abs(roundNumber)}"