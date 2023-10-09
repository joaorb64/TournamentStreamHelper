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

# CU1 : les joueurs ont fail sur l'appli, on veut corriger
# - Si SSWA->TSH désactivé : on report les games 

# Idée de GENIE : en fait ScoreManager est une class parente de TSHScoreboardWidget

class ScoreManager:
    def __init__(self, scoreboardNumber) -> None:
        self.scoreboardNumber = scoreboardNumber
        self.Reset()
        
    def Reset(self):
        self.games = []
        self.p1Score = 0
        self.p2Score = 0
        
    def ReportGame(self, winner, p1Char, p2Char, stage):
        pass
    
    def Swap(self):
        temp = self.p1Score
        self.p1Score = self.p2Score
        self.p2Score = temp
        
        for game in self.games:
            if game and game["winner"]:
                game["winner"] = 1 - game["winner"]
          
    def SetScore():
        pass
    
    def SetScoreExt():
        #edit the score containers
        pass      
                
    def EditGamesUI(self):
        #Opens the UI allowing the user to edit each game
        pass
    
    def ReportGameUI(self):
        #Opens the UI allowing the yser to report a game
        pass