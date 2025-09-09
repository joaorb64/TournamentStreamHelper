from qtpy.QtCore import *
from loguru import logger

class TSHTeamBattleSignals(QObject):
    # GENERAL SIGNALS
    reset_all_stocks = Signal()
    reset_everything = Signal()

    # TEAM 1 SIGNALS
    team1_next_active_player = Signal()
    team1_reset_player_stocks = Signal()
    team1_stock_up = Signal()
    team1_stock_down = Signal()
    team1_active_player_changed = Signal(int)

    # TEAM 2 SIGNALS
    team2_next_active_player = Signal()
    team2_reset_player_stocks = Signal()
    team2_stock_up = Signal()
    team2_stock_down = Signal()
    team2_active_player_changed = Signal(int)

class TSHTeamBattleWidget:

    def __init__(self):
        logger.info("BATTLE START")
        self.signals = TSHTeamBattleSignals()

        # Hook into Signals for Control
        self.signals.reset_all_stocks.connect(self.ResetAllStocks)
        self.signals.reset_everything.connect(self.ResetEverything)

        self.signals.team1_stock_up.connect(self.T1_Stock_Up)
        self.signals.team1_stock_down.connect(self.T1_Stock_Down)
        self.signals.team2_stock_up.connect(self.T2_Stock_Up)
        self.signals.team2_stock_down.connect(self.T2_Stock_Down)

    # =====================================================
    # GENERAL CONTROL METHODS
    # =====================================================
    def ResetAllStocks(self):
        logger.info("RESET ALL STOCKS")

    def ResetEverything(self):
        logger.info("RESET EVERYTHING")

    # =====================================================
    # NEXT ACTIVE PLAYERS
    # =====================================================


    # =====================================================
    # TEAM 1 STOCK CONTROL
    # =====================================================
    def T1_Stock_Up(self):
        logger.info("T1 STOCK UP")
        
    def T1_Stock_Down(self):
        logger.info("T1 STOCK DOWN")

    # =====================================================
    # TEAM 2 STOCK CONTROL
    # =====================================================
    def T2_Stock_Up(self):
        logger.info("T2 STOCK UP")
        
    def T2_Stock_Down(self):
        logger.info("T2 STOCK DOWN")