import math

class BracketSet():
    def __init__(self, bracket: "Bracket") -> None:
        self.bracket: Bracket = bracket
        self.playerIds = [-1, -1]
        self.score = [0, 0]
        self.winNext: "BracketSet" = None
        self.loseNext: "BracketSet" = None

# Bracket always has a power of 2 number of players
# if there are less than that, we round up and add
# 'bye's as the lower seeded players
def next_power_of_2(x):
    return 1 if x == 0 else 2**math.ceil(math.log2(x))

class Bracket():
    def __init__(self, playerNumber) -> None:
        self.playerNumber = next_power_of_2(playerNumber)

        self.slots = [BracketSet(self) for i in range(int(self.playerNumber/2))]

        x = [0] * int(self.playerNumber/2)
        y = [0] * int(self.playerNumber/2)

        a = 1

        for i in range(1, int(self.playerNumber/4)+int(self.playerNumber/4)+1):
            if i == 1:
                x[i-1] = a
                y[i-1] = a+1
            elif i % 2 == 0:
                x[i-1] = 2*i
                y[i-1] = x[i-1]-1
            else:
                x[i-1] = 2*i-1
                y[i-1] = x[i-1]+1
            a += 1

        print(x)
        print(y)

        a = 0
        b = 0

        for i in range(0, int(len(x)/2)):
            if i % 2 == 0:
                self.slots[i].playerIds[0] = x[a]
                self.slots[i].playerIds[1] = x[-a-1]

                self.slots[i + int(self.playerNumber/4)].playerIds[0] = y[a]
                self.slots[i + int(self.playerNumber/4)].playerIds[1] = y[-a-1]

                a += 1
            else:
                self.slots[i].playerIds[0] = x[int(len(x)/2)-b-1]
                self.slots[i].playerIds[1] = x[int(len(x)/2)+b]

                self.slots[i + int(self.playerNumber/4)].playerIds[0] = y[int(len(x)/2)-b-1]
                self.slots[i + int(self.playerNumber/4)].playerIds[1] = y[int(len(x)/2)+b]

                b += 1

        self.rounds = []
        self.rounds.append(self.slots)

        i = len(self.slots)
        
        while i > 1:
            i = math.floor(i/2)
            round = [BracketSet(self) for i in range(int(i))]
            self.rounds.append(round)

        for i, round in enumerate(self.rounds[:-1]):
            for j, _set in enumerate(round):
                _set.winNext = self.rounds[i+1][math.floor(j/2)]
    
    def UpdateBracket(self):
        for i, round in enumerate(self.rounds):
            for j, _set in enumerate(round):
                if _set.winNext:
                    if _set.score[0] > _set.score[1]:
                        _set.winNext.playerIds[j%2] = _set.playerIds[0]
                    elif _set.score[0] < _set.score[1]:
                        _set.winNext.playerIds[j%2] = _set.playerIds[1]
                    else:
                        _set.winNext.playerIds[j%2] = -1