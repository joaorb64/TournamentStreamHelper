from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from .Helpers.TSHCountryHelper import TSHCountryHelper
from .StateManager import StateManager
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHPlayerDB import TSHPlayerDB
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHPlayerListSlotWidget import TSHPlayerListSlotWidget
from .TSHBracketView import TSHBracketView
from .TSHPlayerList import TSHPlayerList
from .TSHBracket import *

# Checks if a number is power of 2
def is_power_of_two(n):
    return (n != 0) and (n & (n-1) == 0)

class TSHBracketWidgetSignals(QObject):
    UpdateData = pyqtSignal(object)

class TSHBracketWidget(QDockWidget):
    def __init__(self, *args):
        StateManager.BlockSaving()
        super().__init__(*args)

        uic.loadUi("src/layout/TSHBracket.ui", self)

        TSHTournamentDataProvider.instance.signals.tournament_phases_updated.connect(self.UpdatePhases)
        TSHTournamentDataProvider.instance.signals.tournament_phasegroup_updated.connect(self.UpdatePhaseGroup)

        self.signals = TSHBracketWidgetSignals()

        self.bracket = Bracket(8)

        self.setFloating(True)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        self.mainLayout = self.findChild(QWidget, "bracket")
        self.mainLayout.setLayout(QVBoxLayout())

        self.setFloating(True)
        self.setWindowFlags(Qt.WindowType.Window)

        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        outerLayout: QWidget = self.findChild(QWidget, "bracket")
        self.playerList = TSHPlayerList(base="bracket.players")
        list: QWidget = self.findChild(QWidget, "listContainer")
        list.layout().addWidget(self.playerList)

        self.bracketView = TSHBracketView(self.bracket, self.playerList)
        outerLayout.layout().addWidget(self.bracketView)

        self.playerList.SetSlotNumber(8)
        self.playerList.SetPlayersPerTeam(1)
        self.playerList.SetCharactersPerPlayer(1)

        self.phaseSelection: QComboBox = self.findChild(QComboBox, "phaseSelection")
        self.phaseSelection.currentIndexChanged.connect(self.UpdatePhaseGroups)

        self.phaseGroupSelection: QComboBox = self.findChild(QComboBox, "phaseGroupSelection")
        self.phaseGroupSelection.currentIndexChanged.connect(self.PhaseGroupChanged)

        self.progressionsIn: QSpinBox = self.findChild(QSpinBox, "progressionsIn")
        self.progressionsIn.valueChanged.connect(lambda val: StateManager.Set("bracket.bracket.progressionsIn", val))

        self.progressionsOut: QSpinBox = self.findChild(QSpinBox, "progressionsOut")
        self.progressionsOut.valueChanged.connect(lambda val: StateManager.Set("bracket.bracket.progressionsOut", val))

        self.playerList.signals.DataChanged.connect(self.bracketView.Update)

        StateManager.ReleaseSaving()
    
    def UpdatePhases(self, phases):
        print("phases", phases)
        self.phaseSelection.clear()
        self.phaseSelection.addItem("")

        for phase in phases:
            self.phaseSelection.addItem(phase.get("name"), phase)
        
    def UpdatePhaseGroups(self):
        self.phaseGroupSelection.clear()

        if self.phaseSelection.currentData() != None:
            print(self.phaseSelection.currentData().get("groups", []))
            for phaseGroup in self.phaseSelection.currentData().get("groups", []):
                self.phaseGroupSelection.addItem(phaseGroup.get("name"), phaseGroup)

                # Let's only allow double elimination for now
                if phaseGroup.get("bracketType") != "DOUBLE_ELIMINATION":
                    itemModel: QStandardItemModel = self.phaseGroupSelection.model()
                    item = itemModel.item(itemModel.rowCount()-1)
                    item.setEnabled(False)
    
    def PhaseGroupChanged(self):
        if self.phaseGroupSelection.currentData() != None:
            TSHTournamentDataProvider.instance.GetTournamentPhaseGroup(self.phaseGroupSelection.currentData().get("id"))

    def UpdatePhaseGroup(self, phaseGroupData):
        StateManager.BlockSaving()

        print(phaseGroupData)

        if phaseGroupData.get("progressionsIn", {}) != None:
            self.progressionsIn.setValue(len(phaseGroupData.get("progressionsIn", {})))
        else:
            self.progressionsIn.setValue(0)
        
        if phaseGroupData.get("progressionsOut", {}) != None:
            self.progressionsOut.setValue(len(phaseGroupData.get("progressionsOut", {})))
        else:
            self.progressionsOut.setValue(0)

        self.playerList.LoadFromStandings(phaseGroupData.get("entrants"))
        self.bracket = Bracket(
            len(phaseGroupData.get("entrants")),
            phaseGroupData.get("seedMap")
        )

        self.bracketView.SetBracket(
            self.bracket,
            progressionsIn=self.progressionsIn.value(),
            progressionsOut=self.progressionsOut.value()
        )

        for r, round in phaseGroupData.get("sets", {}).items():
            for s, _set in enumerate(round):
                try:
                    score = _set.get("score")
                    if score[0] == None: score[0] = -1
                    if score[1] == None: score[1] = -1

                    roundIndex = str(r)

                    if int(r) > 0:
                        if self.progressionsIn.value() > 0 and not is_power_of_two(self.progressionsIn.value()):
                            roundIndex = str(int(r)+1)

                    self.bracket.rounds[roundIndex][s].score = score
                except Exception as e:
                    print(e)
        
        self.bracket.UpdateBracket()
        self.bracketView.Update()
        StateManager.ReleaseSaving()