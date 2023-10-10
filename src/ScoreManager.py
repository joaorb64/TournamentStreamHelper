

# The current score of the match, as well as individual games, are managed by the ScoreManager ; the Scoreboard widget owns a ScoreManager instance
# When the score changes in the ScoreManager, it is reflected in the state (by OnScoreChanged)
# When the score is changed in the UI, instead of directly changing the state, the scoreboard widget informs the ScoreManager of the change (via OnScoreUIChanged)
# When an external source attemps to change the score (auto-update or stage strike app), instead of directly changing the value if the UI,
# we call ScoreManager.CommandScoreChange, which changes the score in the UI.  
# Note that CommandScoreChange calls OnScoreChanged to update the state with the new data, then updates the UI, which calls OnScoreUIChanged, which calls OnScoreChanged a second time.
# This is because there doesn't seem to be a safe way to make a difference between a code-induced change and an user-made change in the UI. I'm starting to hate Qt. 
# (It isn't a problem anyway, as OnScoreChanged will check for differences and see that there isn't any -> doing nothing)

# The ScoreManager *can* track individual games, when the information it receives allows it to ; but it may as well stop tracking them. 

# Example 1 : The score is manually changed in the UI
# - ScoreManager.OnScoreUIChanged is called with the new score
# - Calls ScoreManager.OnScoreChanged
# - Change self.score
# - If the difference with the previous score is 1 (or -1), add a game (with no info) or remove one
# - If the difference was greater, forget the games, we are now in score only mode
# - The state is updated

# Example 2 : data is received from start.gg, with chars and stage : 
# - ScoreManager.CommandScoreChange is called with all the data. It updates self.games with it, as well as the score; OnScoreChanged is called, updates the state
# - ScoreManager.CommandScoreChange also changes the values in the score widgets
# - This (unfortunately) triggers the valueChanged signal, which calls ScoreManager.OnScoreChanged (see TSHScoreboardWidget.py:356)
# - ScoreManager.OnScoreChanged sees that nothing changed since the last time we changed the score (as that was during the CommandScoreChange call)

# REGARDING THE STAGE STRIKE WEB APP (SSWA)
# It should be possible to do what we want to do here without really touching the way the SSWA works, but i think this is a good occasion to try doing so. 
# My proposal is : 
# - When the Web server tries to update the score :
#   - IF the "allow sswa to change score setting" is true, call ScoreManager.ReportGame directly (without using any method of TSHScoreboardWidget)
#   - In that case, IF the new "keep score updated in the sswa" setting is also true, send a message to the sswa with the new score. 
# - Add a "Sync SSWA", which forces the synchronization. The information sent here include the score but also who won last (useful for stage strike).
#   If that information is not known (we are in score-only mode or the last game has no winner), the user is prompted for it before the sync message is sent. 
# - Currently, from what i understand, the SSWA doesn't know the exact order of previous games (it knows who won on which stages, but not in which order). We should change that
# - Maybe when we receive an update from the SSWA and the data it holds doesn't match ours (different scores, or same score but different stages), a warning should be displayed,
#   with the option of overwriting the ScoreManager's data OR to sync the stage strike app instead

from .StateManager import StateManager


class ScoreManager:
    def __init__(self, parent) -> None:
        self.scoreboardNumber = parent.scoreboardNumber
        self.parent = parent
        self.games = []
        self.Reset()
        
    def Reset(self):
        self.games = []
        self.score = [0, 0]
        
    def Swap(self):
        temp = self.score[0]
        self.score[0] = self.score[1]
        self.score[1] = temp
        
        for game in self.games:
            if game and game["winner"]:
                game["winner"] = 1 - game["winner"]    
        
    
    def OnScoreUIChanged(self, team, value):
        if self.score[team] == value: 
            #If the new value is already the one we know, nothing to do (it's most likely because the change was done by the ScoreManager itself)
            return
        self.score[team] = value
        StateManager.BlockSaving()
        self.OnScoreChanged(team)
        StateManager.ReleaseSaving()
          
    #if team is given we only update the score for that team in the state 
    def OnScoreChanged(self, team = -1):
        if team > -1:
            #update just the score for the given team
            StateManager.Set(f"score.{self.scoreboardNumber}.team.${team + 1}.score", self.score[team])
            pass
        else:
            #Update EVERYTHING in the state
            pass
        
    def OnGamesChanged(self):
        
        #recalculate the score
        #only if it changed : 
        StateManager.BlockSaving()
        self.OnScoreChanged()
        self.UpdateScoreUI()
        StateManager.ReleaseSaving()
    
    def ReportGame(self, winner, p1Char, p2Char, stage):
        #if we are in score only mode, we just increment the score 
        #else : 
        
        self.games.append({
            winner: winner,
            p1Char: p1Char,
            p2Char: p2Char,
            stage: stage
        })
        self.OnGamesChanged()
    
    # We probably received data from startgg 
    def ChangeGames(self, games):
        #Process the games data
        self.OnGamesChanged()
    
    def CommandScoreChange(self, team, change):
        self.score[team] += change
        self.UpdateScoreUI(team)
        pass      
                
    def UpdateScoreUI(self, team = -1):
        if team < 0:
            self.UpdateScoreUI(0)
            self.UpdateScoreUI(1)
        else:
            self.parent.SetScore(team, self.score[team])
                
    def EditGamesUI(self):
        #Opens the UI allowing the user to edit each game. 
        #I still don't know if the modifications take effect as you do them or when pressing a Save button (like on start.gg) (we need to think about performances tho)
        pass
    
    def ReportGameUI(self):
        #Opens the UI allowing the user to report a game
        #display a warning if we are in score only mode
        self.ReportGame(None, None, None, None)
        pass
    
    

#FRENCH VERSION OF THE NOTES (SAME AS THE BEGINNING OF THIS FILE I JUST COULDNT BRING MYSELF TO DELETE THEM BECAUSE SOME DETAILS MAY HAVE BEEN LOST IN TRANSLATION)
# Le score du match,ainsi que les games, sont contenu dans le ScoreManager, propriété du Scoreboard.  
# Pour l'appli stage strike : 
# - Quand elle envoie un "x won", on ajoute une game avec les infos données (stage en gros)
# - Quand l'appli envoie une update de score, elle demande le score actuel, pour se mettre à jour (setting pour désactiver ça)
# - En + du setting actuel qui autorise l'appli stage strike à changer le score, un setting qui détemine si mettre le score à jour sur TSh le change dans l'appli. 
# UI additionnelle : 
# - Bouton "report game" : affiche un dialogue permettant de report une game (who won, chars, stage, final game ?). Report une game déclenche une modif startgg
# - Bouton "games" : affiche un dialogue listant les games, et permettant de les éditer
# - Bouton "modif startgg" (potentiellement dans l'UI de gestion des games ?) : update le score sur startgg
# - Peut être boutons x won dans le scoreboard directement ?
# - Bouton "update web app score" pour forcer une update du score sur l'app
# Pour le scoreboard : 
# SOLUTION 1 : Changer le score du ScoreManager sauvegarde le score dans le state ;
# Quand le score est modifié depuis le scoreboard, il modifie le ScoreManager : calcul de la différence avec le score précédent du joueur concerné  
# -> Si positif, ajout de x games (sans infos)  
# -> Si négatif, retrait des x dernières games 
# SOLUTION 2 : Changer le contenu des spinners change le state ; changer le ScoreManager change le contenu des spinners (donc changement du state)

# Autre possibilité : 
# Mode "score only", où on ne connait pas les games individuelles.
# - On entre dans ce mode si on change le score manuellement dans les spinners
# - Si on entre dans l'interface des games dans ce mode, on a juste un bouton qui propose de remettre le score à une valeur qui correspond aux games
