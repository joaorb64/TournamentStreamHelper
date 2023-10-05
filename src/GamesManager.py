# I'm gonna use this file to take notes for now 

# Process
# Clic sur un boutou au niveau du scoreboard
# Appel de TSHDataManager.instance.ReportGame, avec en paramètre le GameManager
# Selon la réponse, le dialogue appelle GamesManager.report
# Puis utilise self.SetSetGames en récupérant GamesManager.getGames

# This should actually become a SetManager and straight up replace the current system for auto updates (which keeps the current set in the closure of a lambda)
# SetManager would contain 
# - The current set id
# - The entrant IDs
# Maybe it would completely manage the autoUpdate timer ? Or maybe it would just keep the information and get called by the autoUpdate timer ?
# In any case, this class would represent the "current set", which could be
# - Nonexistent : The current match is not linked to a specific bracket match. No need for a SetManager.
# - Linked : This object exists and contains all the IDs required to update the score. 
# - Updating : Same but also auto-updating

# Voir comment ça interagit avec le stage strike !!!!

class GamesManager:
    def __init__(self, p1Id, p2Id) -> None:
        self.games = []
        
    def GetGames(self) -> dict:
        return self.games
    
    def ReportGame(self, winnerId, p1Id, p2Id):
        pass
        
        
    