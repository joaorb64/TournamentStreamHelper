from .StateManager import StateManager
from copy import deepcopy

class TSHStageStrikeState:
    def __init__(self) -> None:
        self.currGame = 0
        self.currPlayer = -1
        self.currStep = 0
        self.strikedStages = [[]]
        self.strikedBy = [[], []]
        self.stagesWon = [[], []]
        self.stagesPicked = []
        self.selectedStage = None
        self.lastWinner = -1
        self.playerNames = []
        self.phase = None
        self.match = None
        self.bestOf = None
        self.timestamp = 0
        self.serverTimestamp = 0
        self.gentlemans = False
    
    def Clone(self):
        clone = TSHStageStrikeState()
        clone.__dict__ = deepcopy(self.__dict__)
        return clone

class TSHStageStrikeLogic():
    def __init__(self) -> None:
        self.ruleset: "Ruleset" = None
        self.history: list(TSHStageStrikeState) = [TSHStageStrikeState()]
        self.historyIndex = 0
    
    def AddHistory(self, state, justOverwrite=False):
        self.history = self.history[:self.historyIndex+1]

        if justOverwrite:
            self.history[self.historyIndex] = state
        else:
            self.history.append(state)
            self.historyIndex += 1

        if len(self.history) > 10:
            self.history.pop(0)
            self.historyIndex -= 1
        
        self.ExportState()
    
    def Undo(self):
        self.historyIndex -= 1
        if self.historyIndex < 0:
            self.historyIndex = 0
        self.ExportState()
    
    def Redo(self):
        self.historyIndex += 1
        if self.historyIndex > len(self.history) - 1:
            self.historyIndex = len(self.history) - 1
        self.ExportState()
    
    def ExportState(self):
        StateManager.Set("score.stage_strike", {
            "currGame": self.CurrentState().currGame,
            "currPlayer": self.CurrentState().currPlayer,
            "currStep": self.CurrentState().currStep,
            "strikedStages": self.CurrentState().strikedStages,
            "strikedBy": self.CurrentState().strikedBy,
            "stagesWon": self.CurrentState().stagesWon,
            "stagesPicked": self.CurrentState().stagesPicked,
            "selectedStage": self.CurrentState().selectedStage,
            "lastWinner": self.CurrentState().lastWinner,
            "gentlemans": self.CurrentState().gentlemans,
            "canUndo": self.historyIndex > 0,
            "canRedo": self.historyIndex < len(self.history) - 1
        })

    def SetRuleset(self, ruleset):
        self.ruleset = ruleset
        self.Initialize()
    
    def Initialize(self, resetStreamScore = False):
        print("Initialize")
        self.AddHistory(TSHStageStrikeState())
        self.ExportState()
    
    def CurrentState(self) -> TSHStageStrikeState:
        return self.history[self.historyIndex]
    
    def RpsResult(self, player):
        print("RPS won by", player)
        newState = self.CurrentState().Clone()
        newState.lastWinner = player
        newState.currPlayer = player
        self.AddHistory(newState)
    
    def IsStageStriked(self, stage, previously = False):
        for i in range(len(self.CurrentState().strikedStages)):
            if i == len(self.CurrentState().strikedStages) - 1 and previously:
                continue
            round = self.CurrentState().strikedStages[i]
            if stage in round:
                return True
        return False
    
    def GetBannedStages(self):
        banList = [];

        if self.ruleset.useDSR:
            banList = self.CurrentState().stagesPicked
        elif self.ruleset.useMDSR and self.CurrentState().lastWinner != -1:
            banList = self.CurrentState().stagesWon[(self.CurrentState().lastWinner + 1) % 2]

        return banList
    
    def IsStageBanned(self, stage):
        banList = self.GetBannedStages();

        found = next((i for i, e in enumerate(banList) if e == stage), None)
        if found != None:
            return True
        return False
    
    def GetStrikeNumber(self):
        # For game 1, follow strike order (1, 2, 1...)
        if self.CurrentState().currGame == 0:
            return self.ruleset.strikeOrder[self.CurrentState().currStep]
        # For other games
        else:
            # Fixed ban count
            if self.ruleset.banCount != 0:
                return self.ruleset.banCount
            # Ban by max games
            elif self.ruleset.banByMaxGames and str(self.CurrentState().bestOf) in self.ruleset.banByMaxGames:
                return self.ruleset.banByMaxGames[str(self.CurrentState().bestOf)]
            else:
                return 0

    def StageClicked(self, stage):
        print("Clicked on stage", stage.get("codename"))

        if (self.CurrentState().currGame > 0 and self.CurrentState().currStep > 0) or self.CurrentState().gentlemans:
            # we're picking
            if (not self.IsStageBanned(stage.get("codename")) and not self.IsStageStriked(stage.get("codename"))) or self.CurrentState().gentlemans:
                newState = self.CurrentState().Clone()
                newState.selectedStage = stage.get("codename")
                print("Stage picked")
                self.AddHistory(newState)
        elif not self.IsStageStriked(stage.get("codename"), True) and not self.IsStageBanned(stage.get("codename")):
            # we're banning
            foundIndex = next((i for i, e in enumerate(self.CurrentState().strikedStages[self.CurrentState().currStep]) if e == stage.get("codename")), None)
            
            if foundIndex == None:
                if len(self.CurrentState().strikedStages[self.CurrentState().currStep]) < self.GetStrikeNumber():
                    print("Stage banned")
                    newState = self.CurrentState().Clone()
                    newState.strikedStages[newState.currStep].append(stage.get("codename"));
                    newState.strikedBy[newState.currPlayer].append(stage.get("codename"));
                    self.AddHistory(newState)
            else:
                print("Stage unbanned")

                newState = self.CurrentState().Clone()
                newState.strikedStages[newState.currStep].pop(foundIndex)

                foundIndex = next((i for i, e in enumerate(newState.strikedBy[newState.currPlayer]) if e == stage.get("codename")), None)

                if foundIndex != None:
                    newState.strikedBy[newState.currPlayer].pop(foundIndex)
                    self.AddHistory(newState)
    
    def ConfirmClicked(self, justOverwrite=False):
        # For first game, user should have banned the correct number of stages before confirming
        if self.CurrentState().currGame == 0:
            if len(self.CurrentState().strikedStages[self.CurrentState().currStep]) == self.ruleset.strikeOrder[self.CurrentState().currStep]:
                newState = self.CurrentState().Clone()
                newState.currStep += 1
                newState.currPlayer = (newState.currPlayer + 1) % 2
                newState.strikedStages.append([])
                self.AddHistory(newState, justOverwrite=justOverwrite)
        # For other games, user should have banned the correct bancount
        else:
            if len(self.CurrentState().strikedStages[self.CurrentState().currStep]) == self.ruleset.banCount:
                newState = self.CurrentState().Clone()
                newState.currStep += 1
                newState.currPlayer = (newState.currPlayer + 1) % 2
                newState.strikedStages.append([])
                self.AddHistory(newState, justOverwrite=justOverwrite)
        
        # For first game, when no more stages are available we know the remaining one is the picked stage
        if self.CurrentState().currGame == 0 and self.CurrentState().currStep >= len(self.ruleset.strikeOrder):
            newState = self.CurrentState().Clone()
            selectedStage = next((stage for stage in self.ruleset.neutralStages if not self.IsStageStriked(stage.get("codename"))), None)
            newState.selectedStage = selectedStage.get("codename")
            newState.stagesPicked.append(selectedStage.get("codename"))
            self.AddHistory(newState, justOverwrite=True)
    
    def MatchWinner(self, id):
        newState = self.CurrentState().Clone()
        newState.currGame += 1
        newState.currStep = 0

        newState.stagesWon[id].append(newState.selectedStage)
        newState.stagesPicked.append(newState.selectedStage)

        newState.currPlayer = id
        newState.strikedStages = [[]]
        newState.selectedStage = None
        newState.strikedBy = [[], []]
        newState.gentlemans = False

        newState.lastWinner = id

        self.AddHistory(newState)

        # If next step has no bans, skip it
        if self.GetStrikeNumber() == 0:
            self.ConfirmClicked(justOverwrite=True)
    
    def SetGentlemans(self, value):
        print(f"Setting gentlemans to {value}")
        newState = self.CurrentState().Clone()

        newState.gentlemans = value

        newState.currPlayer = newState.lastWinner
        newState.currStep = 0
        newState.strikedStages = [[]]
        newState.strikedBy = [[], []]
        newState.selectedStage = None

        self.AddHistory(newState)