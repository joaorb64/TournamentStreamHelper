from qtpy.QtCore import *
from qtpy.QtWidgets import *
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

class TSHTeamBattleWidget(QDockWidget):

    def __init__(self, *args):
        super().__init__(*args)
        logger.info("BATTLE START")
        self.signals = TSHTeamBattleSignals()

        self.setWindowTitle(QApplication.translate("app", "Crew/Team Battle"))
        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.widget.setLayout(QVBoxLayout())
        self.setWindowFlags(Qt.WindowType.Window)

        label = QLabel()
        label.setText("CREW/TEAM BATTLE")
        self.widget.layout().addWidget(label)

        topOptions = QWidget()
        topOptions.setLayout(QHBoxLayout())
        topOptions.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.widget.layout().addWidget(topOptions)

        col = QWidget()
        col.setLayout(QVBoxLayout())
        topOptions.layout().addWidget(col)
        self.commentatorNumber = QSpinBox()
        row = QWidget()
        row.setLayout(QHBoxLayout())
        commsNumber = QLabel(QApplication.translate("app", "Number of commentators"))
        commsNumber.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        row.layout().addWidget(commsNumber)
        row.layout().addWidget(self.commentatorNumber)
        # self.commentatorNumber.valueChanged.connect(
        #     lambda val: self.SetCommentatorNumber(val))
        
        self.characterNumber = QSpinBox()
        charNumber = QLabel(QApplication.translate("app", "Characters per player"))
        charNumber.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        row.layout().addWidget(charNumber)
        row.layout().addWidget(self.characterNumber)
        # self.characterNumber.valueChanged.connect(self.SetCharacterNumber)

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