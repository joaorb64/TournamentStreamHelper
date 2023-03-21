from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from .TSHBracket import *
from .TSHPlayerList import *
import traceback

# Checks if a number is power of 2
def is_power_of_two(n):
    return (n != 0) and (n & (n-1) == 0)

class BracketSetWidget(QWidget):
    def __init__(self, bracketSet: BracketSet = None, bracketView: "TSHBracketView" = None, *args) -> None:
        super().__init__(*args)
        self.setLayout(QVBoxLayout())

        self.playerId: list(QLabel) = []
        self.name: list(QLineEdit) = []
        self.score: list(QSpinBox) = []

        self.bracketSet = bracketSet
        self.bracketView = bracketView

        for i in [0, 1]:
            hbox = QWidget()
            hbox.setLayout(QHBoxLayout())
            hbox.layout().setContentsMargins(0,0,0,0)
            hbox.layout().setSpacing(2)
            self.layout().addWidget(hbox)
            hbox.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

            idLabel = QLineEdit()
            idLabel.setDisabled(True)
            idLabel.setMinimumWidth(30)
            idLabel.setMaximumWidth(30)
            idLabel.setFont(QFont(idLabel.font().family(), 8))
            idLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playerId.append(idLabel)
            hbox.layout().addWidget(idLabel)

            name = QLineEdit()
            name.setMinimumWidth(120)
            name.setMaximumWidth(120)
            name.setDisabled(True)
            self.name.append(name)
            hbox.layout().addWidget(name)
            name.sizePolicy().setRetainSizeWhenHidden(True)

            score = QSpinBox()
            score.setMinimum(-1)
            self.score.append(score)
            hbox.layout().addWidget(score)
            score.setValue(-1)
            score.valueChanged.connect(lambda newVal, i=i: self.SetScore(i, newVal))

        self.finished = QCheckBox("Finished")
        self.layout().addWidget(self.finished)
        self.finished.toggled.connect(lambda newVal: self.SetFinished(newVal)) 
        
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.sizePolicy().setRetainSizeWhenHidden(True)
        self.layout().setSpacing(2)

        self.Update()
    
    def SetScore(self, id, score, updateDisplay=True):
        self.bracketSet.score[id] = score
        if updateDisplay:
            self.bracketSet.bracket.UpdateBracket()
            self.bracketView.Update()
    
    def SetFinished(self, finished, updateDisplay=True):
        self.bracketSet.finished = finished

        if updateDisplay:
            self.bracketSet.bracket.UpdateBracket()
            self.bracketView.Update()

    def Update(self):
        if self.bracketSet is not None:
            self.playerId[0].setText(str(self.bracketSet.playerIds[0]))
            self.playerId[1].setText(str(self.bracketSet.playerIds[1]))

            if self.playerId[0].text() == "-2":
                self.playerId[0].setText("")
            if self.playerId[1].text() == "-2":
                self.playerId[1].setText("")
            
            self.score[0].blockSignals(True)
            self.score[1].blockSignals(True)
            self.score[0].setValue(min(self.bracketSet.score[0], self.score[0].maximum()))
            self.score[1].setValue(min(self.bracketSet.score[1], self.score[1].maximum()))
            self.score[0].blockSignals(False)
            self.score[1].blockSignals(False)

            if self.bracketSet.score[0] > self.bracketSet.score[1]:
                self.score[0].setStyleSheet("background-color: rgba(0, 255, 0, 50);")
                self.score[1].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
            elif self.bracketSet.score[0] < self.bracketSet.score[1]:
                self.score[1].setStyleSheet("background-color: rgba(0, 255, 0, 50);")
                self.score[0].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
            else:
                self.score[0].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
                self.score[1].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
            
            try:
                if (self.bracketSet.playerIds[0]-1) < len(self.bracketView.playerList.slotWidgets) and self.bracketSet.playerIds[0] > 0:
                    team = StateManager.Get(f"bracket.players.slot.{self.bracketSet.playerIds[0]}", {})
                    if team.get("name"):
                        teamName = team.get("name")
                    else:
                        teamName = " / ".join([p.get("name", "") for p in team.get("player", {}).values()])
                    self.name[0].setText(teamName)
                else:
                    self.name[0].setText("")
            except:
                print(traceback.format_exc())

            try:
                if (self.bracketSet.playerIds[1]-1) < len(self.bracketView.playerList.slotWidgets) and self.bracketSet.playerIds[1] > 0:
                    team = StateManager.Get(f"bracket.players.slot.{self.bracketSet.playerIds[1]}", {})
                    if team.get("name"):
                        teamName = team.get("name")
                    else:
                        teamName = " / ".join([p.get("name", "") for p in team.get("player", {}).values()])
                    self.name[1].setText(teamName)
                else:
                    self.name[1].setText("")
            except:
                print(traceback.format_exc())

            if self.bracketSet.finished is not None:
                self.finished.blockSignals(True)
                self.finished.setChecked(self.bracketSet.finished)
                self.finished.blockSignals(False)
            
            winnersCutout, losersCutout = self.bracketView.GetCutouts()
            hasBye = \
                ((self.bracketSet.playerIds[0] == -1 and not self.bracketSet.playerIds[1] == -1) or \
                (self.bracketSet.playerIds[1] == -1 and not self.bracketSet.playerIds[0] == -1))

            if self.bracketSet.pos[0] < 0 and hasBye:
                self.hide()
            elif self.bracketSet.pos[0] > 0 and self.bracketSet.pos[0] == 1 and hasBye:
                self.hide()
            else:
                self.show()
            
            limitExportNumber, winnersOffset, losersOffset = self.bracketView.GetLimitedExportingBracketOffsets()

            if self.bracketSet.pos[0] > 0:
                if self.bracketSet.pos[0] - winnersOffset <= 0:
                    self.name[0].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
                    self.name[1].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
                else:
                    self.name[0].setStyleSheet("background-color: rgba(0, 0, 0, 0);")
                    self.name[1].setStyleSheet("background-color: rgba(0, 0, 0, 0);")
            elif self.bracketSet.pos[0] < 0:
                if self.bracketSet.pos[0] + losersOffset >= 0:
                    self.name[0].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
                    self.name[1].setStyleSheet("background-color: rgba(0, 0, 0, 80);")
                else:
                    self.name[0].setStyleSheet("background-color: rgba(0, 0, 0, 0);")
                    self.name[1].setStyleSheet("background-color: rgba(0, 0, 0, 0);")

class TSHBracketView(QGraphicsView):
    def __init__(self, bracket: Bracket, playerList: TSHPlayerList = None, bracketWidget = None, *args):
        super().__init__(*args)

        self.bracketWidget = bracketWidget

        self.playerList = playerList

        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        #self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self.SetBracket(bracket)

        self.bracketLines = []
    
    def GetCutouts(self, forExport=False):
        winnersRounds = [r for r in self.bracket.rounds.keys() if int(r) > 0]
        losersRounds = [r for r in self.bracket.rounds.keys() if int(r) < 0]

        winnersCutout = [0, len(winnersRounds)+1]
        losersCutout = [0, len(losersRounds)+1]

        # Winners right side cutout
        if self.progressionsOut > 0:
            progressionsWinners = math.pow(2, int(math.log2(self.progressionsOut/2)))
            winnersCutout[1] = len(winnersRounds) - (int(math.log2(progressionsWinners)) + 1)
    
        # Winners left side cutout
        if self.progressionsIn > 0 and not self.bracket.winnersOnlyProgressions:
            if not is_power_of_two(self.progressionsIn) and not self.bracket.customSeeding:
                winnersCutout[0] = 2
            else:
                winnersCutout[0] = 1
        
        # Losers right side cutout
        if self.progressionsOut > 0:
            progressionsLosers = self.progressionsOut - math.pow(2, int(math.log2(self.progressionsOut/2)))
            losersCutout[1] = len(losersRounds) - (math.log2(progressionsLosers) * 2 - 1)
    
        # Losers left side cutout
        losersCutout[0] = 2

        # Losers R1 skipping
        # Losers R1 has bracket_size / 2 (half bracket is sent to losers from WR1) / 2 (2 players per set) sets
        # If WR1 has as many sets or less, LR1 will be all [player vs bye]
        # So this round is hidden
        validWR1Sets = self.bracket.originalPlayerNumber - self.bracket.playerNumber/2

        if not (self.bracketWidget.limitExport.isChecked() and self.bracketWidget.limitExportNumber.value() > 0):
            if self.progressionsIn == 0 and validWR1Sets <= self.bracket.playerNumber/2/2:
                losersCutout[0] += 1

        if self.progressionsIn > 0 and not is_power_of_two(self.progressionsIn):
            losersCutout[0] += 1
        
        if self.progressionsOut > 0 and not is_power_of_two(self.progressionsOut):
            losersCutout[1] += 1
    
        return (winnersCutout, losersCutout)


    def SetBracket(self, bracket, progressionsIn=0, progressionsOut=0, winnersOnlyProgressions=False, customSeeding=False):
        self.bracket = bracket

        bracket.progressionsIn = progressionsIn

        if bracket.progressionsIn > 0:
            bracket.winnersOnlyProgressions = winnersOnlyProgressions
        else:
            bracket.winnersOnlyProgressions = True
        
        bracket.customSeeding = customSeeding

        self.bracketLines = []
        self._scene.clear()

        self.bracketLayout = QWidget()
        self.bracketLayout.setLayout(QVBoxLayout())

        self.winnersBracket = QWidget()
        self.winnersBracket.setLayout(QHBoxLayout())
        self.bracketLayout.layout().addWidget(self.winnersBracket)

        self.losersBracket = QWidget()
        self.losersBracket.setLayout(QHBoxLayout())
        self.bracketLayout.layout().addWidget(self.losersBracket)

        self.progressionsIn = progressionsIn
        self.progressionsOut = progressionsOut

        self._scene.addWidget(self.bracketLayout)

        self.bracketWidgets = []
        self.winnersBracketWidgets = []
        self.losersBracketWidgets = []

        self.roundNameLabels = {}

        self.bracket.UpdateBracket()

        winnersCutout, losersCutout = self.GetCutouts()

        for roundNum, round in self.bracket.rounds.items():
            currentBracket = self.winnersBracket
            currentWidgets = self.winnersBracketWidgets
            
            if int(roundNum) < 0:
                currentBracket = self.losersBracket
                currentWidgets = self.losersBracketWidgets
            
            # Winners cutout
            if int(roundNum) > 0:
                if int(roundNum) <= winnersCutout[0]: continue
                if int(roundNum) >= winnersCutout[1]: continue
            
            # Losers cutout
            if int(roundNum) < 0:
                if abs(int(roundNum)) <= losersCutout[0]: continue
                if abs(int(roundNum)) >= losersCutout[1]: continue
            
            # Outer Round layout (column)
            layoutOuter = QWidget()
            currentBracket.layout().addWidget(layoutOuter)
            layoutOuter.setLayout(QVBoxLayout())

            # Round name
            roundNameLabel = QLineEdit()
            roundNameLabel.setPlaceholderText(self.bracket.GetRoundName(int(roundNum), winnersCutout, losersCutout))
            layoutOuter.layout().addWidget(roundNameLabel)
            self.roundNameLabels[roundNum] = roundNameLabel

            layoutRound = QWidget()
            layoutOuter.layout().addWidget(layoutRound)
            layoutRound.setLayout(QVBoxLayout())

            roundWidgets = []
            for _set in round:
                wid = BracketSetWidget(_set, self)
                layoutRound.layout().addWidget(wid)
                roundWidgets.append(wid)
            self.bracketWidgets.append(roundWidgets)
            currentWidgets.append(roundWidgets)
        
        QGuiApplication.processEvents()
        self.DrawLines()
        self.fitInView()

    def GetLimitedExportingBracketOffsets(self):
        limitExportNumber = -1
        winnersRounds = 0
        losersRounds = 0

        # Offset caused by limited exporting
        winnersOffset = 0
        losersOffset = 0

        if self.bracketWidget.limitExport.isChecked():
            limitExportNumber = self.bracketWidget.limitExportNumber.value()
            winnersRounds = math.floor(limitExportNumber/8) + 3

            try:
                losersRounds = int(math.log2(limitExportNumber)) + int(math.log2((limitExportNumber-1)/2)) + 2
            except:
                print(traceback.format_exc())
                losersRounds = 0

            if self.bracketWidget.progressionsIn.value() > 0:
                StateManager.Set("bracket.bracket.progressionsIn", 0)
                losersRounds += 2
                winnersRounds += 1
        
        totalWinnersRounds = len([i for i in self.bracket.rounds.keys() if int(i) > 0])
        totalLosersRounds = len([i for i in self.bracket.rounds.keys() if int(i) < 0])

        if self.bracketWidget.limitExport.isChecked():
            winnersOffset = (totalWinnersRounds-winnersRounds)
            losersOffset = (totalLosersRounds-losersRounds)

        return (limitExportNumber, winnersOffset, losersOffset)
    
    def Update(self):
        self.bracket.UpdateBracket()

        for round in self.bracketWidgets:
            for setWidget in round:
                for w in setWidget.score:
                    w.blockSignals(True)
                setWidget.Update()
                for w in setWidget.score:
                    w.blockSignals(False)
        
        QGuiApplication.processEvents()

        self.DrawLines()
        
        StateManager.BlockSaving()

        data = {}

        StateManager.Set("bracket.bracket.progressionsIn", self.bracket.progressionsIn)
        StateManager.Set("bracket.bracket.progressionsOut", self.bracketWidget.progressionsOut.value())

        limitExportNumber, winnersOffset, losersOffset = self.GetLimitedExportingBracketOffsets()
        winnersCutout, losersCutout = self.GetCutouts(forExport=True)

        winnersOffset += winnersCutout[0]
        losersOffset += losersCutout[0]

        StateManager.Set("bracket.bracket.limitExportNumber", limitExportNumber)

        if limitExportNumber != -1 and limitExportNumber < self.bracket.playerNumber:
            StateManager.Set("bracket.bracket.winnersOnlyProgressions", False)
        else:
            StateManager.Set("bracket.bracket.winnersOnlyProgressions", self.bracket.winnersOnlyProgressions)

        for roundKey, round in self.bracket.rounds.items():
            # Winners cutout
            if int(roundKey) > 0:
                if int(roundKey) <= winnersCutout[0]: continue
                if int(roundKey) >= winnersCutout[1]: continue
            
            # Losers cutout
            if int(roundKey) < 0:
                if abs(int(roundKey)) <= losersCutout[0]: continue
                if abs(int(roundKey)) >= losersCutout[1]: continue
            
            # Get round name or placeholder name
            if self.roundNameLabels.get(roundKey):
                roundName = self.roundNameLabels.get(roundKey).text()
                if roundName == "":
                    roundName = self.roundNameLabels.get(roundKey).placeholderText()
            else:
                roundName = ""
            
            # Limited export number cutout
            if int(roundKey) > 0:
                roundKey = str(int(roundKey) - winnersOffset)
                if int(roundKey) <= 0: continue
            if int(roundKey) < 0:
                roundKey = str(int(roundKey) + losersOffset)
                if int(roundKey) >= 0: continue

            data[roundKey] = {
                "name": roundName,
                "sets": {}
            }
            for j, bracketSet in enumerate(round):
                nextWin = bracketSet.winNext.pos.copy() if bracketSet.winNext else None
                nextLose = bracketSet.loseNext.pos.copy() if bracketSet.loseNext else None

                # print(f"Round pos {bracketSet.pos} W→ {nextWin}")
                # print(f"Round pos {bracketSet.pos} L→ {nextLose}")

                # Reassign rounds based on export number
                if nextWin:
                    if nextWin[0] > 0:
                        nextWin[0] -= winnersOffset
                    else:
                        nextWin[0] += losersOffset - 2
                if nextLose:
                    if nextLose[0] < 0:
                        nextLose[0] += losersOffset - 2

                        """if self.bracket.progressionsIn <= 0:
                            nextLose[0] -= 1
                        else:
                            nextLose[0] -= 2"""
                    # For grand finals into reset, nextLose is a positive round
                    else:
                        nextLose[0] -= winnersOffset
                    
                p1name = ""

                if bracketSet.playerIds[0] > 0:
                    try:
                        p1tree: dict = StateManager.Get(f"bracket.players.slot.{bracketSet.playerIds[0]}.player")
                        p1name = " / ".join([p.get("name") for p in p1tree.values()])
                    except:
                        pass

                p2name = ""

                if bracketSet.playerIds[1] > 0:
                    try:
                        p2tree: dict = StateManager.Get(f"bracket.players.slot.{bracketSet.playerIds[1]}.player")
                        p2name = " / ".join([p.get("name") for p in p2tree.values()])
                    except:
                        pass

                data[roundKey]["sets"][j] = {
                    "playerId": bracketSet.playerIds,
                    "score": bracketSet.score,
                    "nextWin": nextWin,
                    "winSlot": bracketSet.winNextSlot,
                    "nextLose": nextLose,
                    "loseSlot": bracketSet.loseNextSlot,
                    "playerName": [
                        p1name,
                        p2name
                    ],
                    "completed": bracketSet.finished
                }

        StateManager.Set("bracket.bracket.rounds", data)

        StateManager.ReleaseSaving()
    
    def DrawLines(self):
        for element in self.bracketLines:
            self._scene.removeItem(element)

        self.bracketLines = []

        path = QPainterPath()
        dashedPath = QPainterPath()

        for i, round in enumerate(self.winnersBracketWidgets):
            for j, setWidget in enumerate(round):
                _set = setWidget

                if setWidget.isHidden():
                    continue

                if i < len(self.winnersBracketWidgets)-1:

                    nxtWidget = self.winnersBracketWidgets[i+1][math.floor(j/2)]
                    nxt = nxtWidget

                    start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(_set.width(), _set.height()/2)
                    end = QPointF(nxtWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), nxt.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(0, _set.height()/2)

                    midpoint1 = QPointF(start.x()+(end.x()-start.x())/2, start.y())
                    midpoint2 = QPointF(start.x()+(end.x()-start.x())/2, end.y())

                    path.addPolygon(
                        QPolygonF([
                            start,
                            midpoint1,
                            midpoint2,
                            end
                        ])
                    )
                elif self.progressionsOut > 0:
                    start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(_set.width(), _set.height()/2)
                    end = start + QPointF(50, 0)

                    notch1 = end + QPointF(-10, +10)
                    notch2 = end + QPointF(-10, -10)
                    
                    path.addPolygon(
                        QPolygonF([
                            start,
                            end
                        ])
                    )
                    path.addPolygon(
                        QPolygonF([
                            notch1,
                            end,
                            notch2
                        ])
                    )

                # Progression in
                if self.progressionsIn > 0 and i == 0:
                    end = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(0, _set.height()/2)
                    start = end - QPointF(50, 0)
                    
                    dashedPath.addPolygon(
                        QPolygonF([
                            start,
                            end
                        ])
                    )
        
        for i, round in enumerate(self.losersBracketWidgets):
            for j, setWidget in enumerate(round):
                try:
                    _set = setWidget

                    if setWidget.isHidden():
                        continue

                    if i < len(self.losersBracketWidgets)-1:
                        if len(self.losersBracketWidgets[i+1]) < len(self.losersBracketWidgets[i]):
                            nxtWidget = self.losersBracketWidgets[i+1][math.floor(j/2)]
                        else:
                            nxtWidget = self.losersBracketWidgets[i+1][j]
                        nxt = nxtWidget

                        start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(_set.width(), _set.height()/2)
                        end = QPointF(nxtWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), nxt.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(0, _set.height()/2)

                        midpoint1 = QPointF(start.x()+(end.x()-start.x())/2, start.y())
                        midpoint2 = QPointF(start.x()+(end.x()-start.x())/2, end.y())

                        path.addPolygon(
                            QPolygonF([
                                start,
                                midpoint1,
                                midpoint2,
                                end
                            ])
                        )
                    elif self.progressionsOut > 1:
                        start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(_set.width(), _set.height()/2)
                        end = start + QPointF(50, 0)

                        notch1 = end + QPointF(-10, +10)
                        notch2 = end + QPointF(-10, -10)
                        
                        path.addPolygon(
                            QPolygonF([
                                start,
                                end
                            ])
                        )
                        path.addPolygon(
                            QPolygonF([
                                notch1,
                                end,
                                notch2
                            ])
                        )

                    # Progression in
                    if self.progressionsIn > 1 and i == 0 and not self.bracket.winnersOnlyProgressions:
                        end = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(0, _set.height()/2)
                        start = end - QPointF(50, 0)
                        
                        dashedPath.addPolygon(
                            QPolygonF([
                                start,
                                end
                            ])
                        )
                except:
                    print(traceback.format_exc())
        
        pen = QPen(Qt.gray, 4, Qt.SolidLine)
        pen2 = QPen(Qt.black, 6, Qt.SolidLine)

        item = self._scene.addPath(path, pen2)
        self.bracketLines.append(item)

        item = self._scene.addPath(path, pen)
        self.bracketLines.append(item)

        item = self._scene.addPath(dashedPath, pen2)
        self.bracketLines.append(item)

        item = self._scene.addPath(dashedPath, pen)
        self.bracketLines.append(item)

    def fitInView(self):
        rect = QRectF(self.bracketLayout.rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                            viewrect.height() / scenerect.height())
            self.scale(factor, factor)
            self._zoom = 0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        
        if self._zoom > 0:
            self.scale(factor, factor)
        else:
            self.fitInView()
            self._zoom = 0

    def mousePressEvent(self, event):
        super().mousePressEvent(event)