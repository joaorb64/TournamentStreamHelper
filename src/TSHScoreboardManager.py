from qtpy.QtCore import *
from loguru import logger

from .TSHScoreboardWidget import *

class TSHScoreboardManagerSignals(QObject):
    ScoreboardAmountChanged = Signal(int)

class TSHScoreboardManager(QDockWidget):
    instance: "TSHScoreboardManager" = None


    def __init__(self, *args):
        super().__init__(*args)
        
        StateManager.Unset("score")

        self.signals: TSHScoreboardManagerSignals = TSHScoreboardManagerSignals()
        logger.info("Scoreboard Manager - Initializing")

        self.setWindowTitle(QApplication.translate("app", "Scoreboard Manager"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())

        self.tabs = QTabWidget()
        self.widget.layout().addWidget(self.tabs)

        self.signals.ScoreboardAmountChanged.connect(
            lambda val: self.updateAmount(val)
        )

        self.scoreboardholder = []

    def updateAmount(self, amount):
        if amount > len(self.scoreboardholder):
            logger.info("Scoreboard Manager - Creating Scoreboard " + str(amount))
            
            scoreboard = QWidget()
            scoreboard.setLayout(QVBoxLayout())
            scoreboardObj = TSHScoreboardWidget(scoreboardNumber=amount)
            scoreboard.layout().addWidget(scoreboardObj)
            self.tabs.addTab(scoreboard
                 , QApplication.translate("app", "Scoreboard") + " " + str(amount))
            self.scoreboardholder.append(scoreboardObj)
        else:
            logger.info("Scoreboard Manager - Removing Scoreboard " + str(amount+1))
            self.tabs.removeTab(amount)
            self.scoreboardholder[amount].deleteLater()
            self.scoreboardholder.pop(amount)
            StateManager.Unset(f"score.{amount+1}")

    def GetScoreboard(self, number):
        if int(number)-1 <= len(self.scoreboardholder):
            return self.scoreboardholder[int(number)-1]
        else:
            return None


TSHScoreboardManager.instance = TSHScoreboardManager()