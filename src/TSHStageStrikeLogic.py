from .StateManager import StateManager

class TSHStageStrikeLogic():
    def __init__(self) -> None:
        self.ruleset: "Ruleset" = None
        self.currGame = 0
        self.currPlayer = -1
        self.currStep = 0
        self.strikedStages = []
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
    
    def ExportState(self):
        StateManager.Set("score.stage_strike", {
            "currGame": self.currGame,
            "currPlayer": self.currPlayer,
            "currStep": self.currStep,
            "strikedStages": self.strikedStages,
            "strikedBy": self.strikedBy,
            "stagesWon": self.stagesWon,
            "stagesPicked": self.stagesPicked,
            "selectedStage": self.selectedStage,
            "lastWinner": self.lastWinner
        })

    def SetRuleset(self, ruleset):
        self.ruleset = ruleset
        self.Initialize()
    
    def Initialize(self, resetStreamScore = False):
        print("Initialize")
        self.currGame = 0
        self.currPlayer = -1
        self.currStep = 0
        self.strikedStages = [[]]
        self.strikedBy = [[], []]
        self.stagesWon = [[], []]
        self.stagesPicked = []
        self.selectedStage = None
        self.lastWinner = -1
        self.serverTimestamp = 0

        self.ExportState()

        # if (resetStreamScore) this.ResetStreamScore();
    
    def RpsResult(self, player):
        print("RPS won by", player)
        self.currPlayer = player
        self.ExportState()
    
    def IsStageStriked(self, stage, previously = False):
        for i in range(len(self.strikedStages)):
            if i == len(self.strikedStages) - 1 and previously:
                continue
            round = self.strikedStages[i]
            if stage in round:
                return True
        return False
    
    def GetBannedStages(self):
        banList = [];

        if self.ruleset.useDSR:
            banList = self.stagesPicked
        elif self.ruleset.useMDSR and self.lastWinner != -1:
            banList = self.stagesWon[(self.lastWinner + 1) % 2]

        return banList
    
    def IsStageBanned(self, stage):
        banList = self.GetBannedStages();

        found = next((i for i, e in enumerate(banList) if e == stage), None)
        if found != None:
            return True
        return False
    
    def GetStrikeNumber(self):
        # For game 1, follow strike order (1, 2, 1...)
        if self.currGame == 0:
            return self.ruleset.strikeOrder[self.currStep]
        # For other games
        else:
            # Fixed ban count
            if self.ruleset.banCount != 0:
                return self.ruleset.banCount
            # Ban by max games
            elif self.ruleset.banByMaxGames and str(self.bestOf) in self.ruleset.banByMaxGames:
                return self.ruleset.banByMaxGames[str(self.bestOf)]
            else:
                return 0

    def StageClicked(self, stage):
        print("Clicked on stage", stage.get("codename"))

        if self.currGame > 0 and self.currStep > 0:
            # we're picking
            if not self.IsStageBanned(stage.get("codename")) and not self.IsStageStriked(stage.get("codename")):
                self.selectedStage = stage.get("codename")
                print("Stage picked")
                self.ExportState()
        elif not self.IsStageStriked(stage.get("codename"), True) and not self.IsStageBanned(stage.get("codename")):
            # we're banning
            foundIndex = next((i for i, e in enumerate(self.strikedStages[self.currStep]) if e == stage.get("codename")), None)
            
            if foundIndex == None:
                if len(self.strikedStages[self.currStep]) < self.GetStrikeNumber():
                    self.strikedStages[self.currStep].append(stage.get("codename"));
                    self.strikedBy[self.currPlayer].append(stage.get("codename"));
                    print("Stage banned")
                    self.ExportState()
            else:
                self.strikedStages[self.currStep].pop(foundIndex)

                foundIndex = next((i for i, e in enumerate(self.strikedBy[self.currPlayer]) if e == stage.get("codename")), None)

                if foundIndex != None:
                    self.strikedBy[self.currPlayer].pop(foundIndex)
                    print("Stage unbanned")
                    self.ExportState()
    
    def ConfirmClicked(self):
        # For first game, user should have banned the correct number of stages before confirming
        if self.currGame == 0:
            if len(self.strikedStages[self.currStep]) == self.ruleset.strikeOrder[self.currStep]:
                self.currStep += 1
                self.currPlayer = (self.currPlayer + 1) % 2
                self.strikedStages.append([])
        # For other games, user should have banned the correct bancount
        else:
            if len(self.strikedStages[self.currStep]) == self.ruleset.banCount:
                self.currStep += 1;
                self.currPlayer = (self.currPlayer + 1) % 2;
                self.strikedStages.append([])
        
        # For first game, when no more stages are available we know the remaining one is the picked stage
        if self.currGame == 0 and self.currStep >= len(self.ruleset.strikeOrder):
            selectedStage = next((stage for stage in self.ruleset.neutralStages if not self.IsStageStriked(stage.get("codename"))), None)
            self.selectedStage = selectedStage.get("codename")
            self.stagesPicked.append(selectedStage.get("codename"))

        self.ExportState()
    
    def MatchWinner(self, id):
        self.currGame += 1
        self.currStep = 0

        self.stagesWon[id].append(self.selectedStage)
        self.stagesPicked.append(self.selectedStage)

        self.currPlayer = id
        self.strikedStages = [[]]
        self.selectedStage = None
        self.strikedBy = [[], []]

        self.lastWinner = id

        # If next step has no bans, skip it
        if self.GetStrikeNumber() == 0:
            self.ConfirmClicked()

        self.ExportState()
        #self.UpdateStreamScore();