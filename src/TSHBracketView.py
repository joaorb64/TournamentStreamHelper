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

            idLabel = QLabel()
            idLabel.setMinimumWidth(30)
            idLabel.setFont(QFont(idLabel.font().family(), 8))
            idLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playerId.append(idLabel)
            hbox.layout().addWidget(idLabel)

            name = QLineEdit()
            name.setMinimumWidth(120)
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
        
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.sizePolicy().setRetainSizeWhenHidden(True)
        self.layout().setSpacing(2)

        self.Update()
    
    def SetScore(self, id, score, updateDisplay=True):
        self.bracketSet.score[id] = score
        if updateDisplay:
            self.bracketSet.bracket.UpdateBracket()
            self.bracketView.Update()

    def Update(self):
        if self.bracketSet:
            self.playerId[0].setText(str(self.bracketSet.playerIds[0]))
            self.playerId[1].setText(str(self.bracketSet.playerIds[1]))
            
            self.score[0].setValue(self.bracketSet.score[0])
            self.score[1].setValue(self.bracketSet.score[1])

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
                if (self.bracketSet.playerIds[0]-1) < len(self.bracketView.playerList.slotWidgets) and self.bracketSet.playerIds[0] != -1:
                    self.name[0].setStyleSheet("font-style: normal;")
                    self.name[0].setText(self.bracketView.playerList.slotWidgets[self.bracketSet.playerIds[0]-1].findChild(QWidget, "name").text())
                else:
                    self.name[0].setStyleSheet("font-style: italic;")
                    self.name[0].setText("bye")
            except:
                pass

            try:
                if (self.bracketSet.playerIds[1]-1) < len(self.bracketView.playerList.slotWidgets) and self.bracketSet.playerIds[1] != -1:
                    self.name[1].setStyleSheet("font-style: normal;")
                    self.name[1].setText(self.bracketView.playerList.slotWidgets[self.bracketSet.playerIds[1]-1].findChild(QWidget, "name").text())
                else:
                    self.name[1].setStyleSheet("font-style: italic;")
                    self.name[1].setText("bye")
            except:
                pass
            
            if (self.name[0].text() == "bye" and not self.name[1].text() == "bye") or (self.name[1].text() == "bye" and not self.name[0].text() == "bye"):
                self.hide()
            else:
                self.show()
            
            limitExportNumber, winnersOffset, losersOffset = self.bracketView.GetLimitedExportingBracketOffsets()

            if self.bracketSet.pos[0] > 0:
                if self.bracketSet.pos[0] + winnersOffset <= 0:
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
    
    def SetBracket(self, bracket, progressionsIn=0, progressionsOut=0):
        self.bracket = bracket

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

        winnersRounds = [r for r in self.bracket.rounds.keys() if int(r) > 0]
        losersRounds = [r for r in self.bracket.rounds.keys() if int(r) < 0]

        for roundNum, round in self.bracket.rounds.items():
            currentBracket = self.winnersBracket
            currentWidgets = self.winnersBracketWidgets
            
            if int(roundNum) < 0:
                currentBracket = self.losersBracket
                currentWidgets = self.losersBracketWidgets
            
            # Winners cutout
            if int(roundNum) > 0:
                # Winners right side cutout
                if progressionsOut > 0:
                    progressionsWinners = math.pow(2, int(math.log2(progressionsOut/2)))
                    cutOut = int(math.log2(progressionsWinners)) + 1
                    if int(roundNum) + cutOut >= len(winnersRounds): continue
            
                # Winners left side cutout
                if progressionsIn > 0:
                    if int(roundNum) == 1: continue

                    if not is_power_of_two(progressionsIn):
                        if int(roundNum) == 2: continue
            
            # Losers cutout
            if int(roundNum) < 0:
                if progressionsOut > 0:
                    # Losers right side cutout
                    progressionsLosers = progressionsOut - math.pow(2, int(math.log2(progressionsOut/2)))
                    cutOut = math.log2(progressionsLosers) * 2 - 1
                    if abs(int(roundNum)) + cutOut >= len(losersRounds): continue
            
                # Losers left side cutout
                cutOut = 2

                # Losers R1 has total_players/2 sets. If more than half of losers R1 players are byes,
                # it's an auto win for all players and R1 doesn't exist
                byes = self.bracket.playerNumber - self.bracket.originalPlayerNumber
                if progressionsIn == 0 and byes > 0 and byes/2 > self.bracket.originalPlayerNumber/4:
                    cutOut += 1

                if progressionsIn > 0 and not is_power_of_two(progressionsIn):
                    cutOut += 1
                
                if abs(int(roundNum)) <= cutOut: continue
            
            # Outer Round layout (column)
            layoutOuter = QWidget()
            currentBracket.layout().addWidget(layoutOuter)
            layoutOuter.setLayout(QVBoxLayout())

            # Round name
            roundNameLabel = QLineEdit()
            roundNameLabel.setPlaceholderText(self.bracket.GetRoundName(roundNum, progressionsIn, progressionsOut))
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
        
        self.fitInView()
        QGuiApplication.processEvents()
        self.DrawLines()

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
            losersRounds = math.floor(limitExportNumber/2) + 2

            if StateManager.Get("bracket.bracket.progressionsIn") > 0:
                StateManager.Set("bracket.bracket.progressionsIn", 0)
                losersRounds += 2
        
        totalWinnersRounds = len([i for i in self.bracket.rounds.keys() if int(i) > 0])
        totalLosersRounds = len([i for i in self.bracket.rounds.keys() if int(i) < 0])

        if self.bracketWidget.limitExport.isChecked():
            winnersOffset = -(totalWinnersRounds-winnersRounds)
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

        limitExportNumber, winnersOffset, losersOffset = self.GetLimitedExportingBracketOffsets()

        for roundKey, round in self.bracket.rounds.items():
            if self.roundNameLabels.get(roundKey):
                roundName = self.roundNameLabels.get(roundKey).text()
                if roundName == "":
                    roundName = self.roundNameLabels.get(roundKey).placeholderText()
            else:
                roundName = ""
            
            if limitExportNumber != -1:
                if int(roundKey) > 0:
                    roundKey = str(int(roundKey) + winnersOffset)
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

                if limitExportNumber != -1:
                    if nextWin:
                        if nextWin[0] > 0:
                            nextWin[0] += winnersOffset
                        else:
                            nextWin[0] += losersOffset
                    if nextLose:
                        nextLose[0] += losersOffset

                data[roundKey]["sets"][j] = {
                    "playerId": bracketSet.playerIds,
                    "score": bracketSet.score,
                    "nextWin": nextWin,
                    "nextLose": nextLose
                }

        StateManager.Set("bracket.bracket.rounds", data)

        StateManager.ReleaseSaving()
    
    def DrawLines(self):
        for element in self.bracketLines:
            self._scene.removeItem(element)

        self.bracketLines = []

        for i, round in enumerate(self.winnersBracketWidgets):
            for j, setWidget in enumerate(round):
                _set = setWidget

                if setWidget.isHidden():
                    continue

                if i < len(self.winnersBracketWidgets)-1:

                    nxtWidget = self.winnersBracketWidgets[i+1][math.floor(j/2)]
                    nxt = nxtWidget

                    pen = QPen(Qt.black, 2, Qt.SolidLine)

                    start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(_set.width(), _set.height()/2)
                    end = QPointF(nxtWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), nxt.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(0, _set.height()/2)

                    midpoint1 = QPointF(start.x()+(end.x()-start.x())/2, start.y())
                    midpoint2 = QPointF(start.x()+(end.x()-start.x())/2, end.y())

                    path = QPainterPath()
                    path.addPolygon(
                        QPolygonF([
                            start,
                            midpoint1,
                            midpoint2,
                            end
                        ])
                    )

                    item = self._scene.addPath(
                        path,
                        pen
                    )

                    self.bracketLines.append(item)
                elif self.progressionsOut > 0:
                    pen = QPen(Qt.black, 2, Qt.SolidLine)

                    start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(_set.width(), _set.height()/2)
                    end = start + QPointF(50, 0)

                    notch1 = end + QPointF(-10, +10)
                    notch2 = end + QPointF(-10, -10)
                    
                    path = QPainterPath()
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

                    item = self._scene.addPath(
                        path,
                        pen
                    )

                    self.bracketLines.append(item)

                # Progression in
                if self.progressionsIn > 0 and i == 0:
                    pen = QPen(Qt.black, 2, Qt.DashLine)

                    end = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                        QPointF(0, _set.height()/2)
                    start = end - QPointF(50, 0)
                    
                    path = QPainterPath()
                    path.addPolygon(
                        QPolygonF([
                            start,
                            end
                        ])
                    )

                    item = self._scene.addPath(
                        path,
                        pen
                    )

                    self.bracketLines.append(item)
        
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

                        pen = QPen(Qt.black, 2, Qt.SolidLine)

                        start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(_set.width(), _set.height()/2)
                        end = QPointF(nxtWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), nxt.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(0, _set.height()/2)

                        midpoint1 = QPointF(start.x()+(end.x()-start.x())/2, start.y())
                        midpoint2 = QPointF(start.x()+(end.x()-start.x())/2, end.y())

                        path = QPainterPath()
                        path.addPolygon(
                            QPolygonF([
                                start,
                                midpoint1,
                                midpoint2,
                                end
                            ])
                        )

                        item = self._scene.addPath(
                            path,
                            pen
                        )

                        self.bracketLines.append(item)
                    elif self.progressionsOut > 1:
                        pen = QPen(Qt.black, 2, Qt.SolidLine)

                        start = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(_set.width(), _set.height()/2)
                        end = start + QPointF(50, 0)

                        notch1 = end + QPointF(-10, +10)
                        notch2 = end + QPointF(-10, -10)
                        
                        path = QPainterPath()
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

                        item = self._scene.addPath(
                            path,
                            pen
                        )

                        self.bracketLines.append(item)

                    # Progression in
                    if self.progressionsIn > 1 and i == 0:
                        pen = QPen(Qt.black, 2, Qt.DashLine)

                        end = QPointF(setWidget.mapTo(self.bracketLayout, QPoint(0, 0)).x(), _set.mapTo(self.bracketLayout, QPoint(0, 0)).y()) + \
                            QPointF(0, _set.height()/2)
                        start = end - QPointF(50, 0)
                        
                        path = QPainterPath()
                        path.addPolygon(
                            QPolygonF([
                                start,
                                end
                            ])
                        )

                        item = self._scene.addPath(
                            path,
                            pen
                        )

                        self.bracketLines.append(item)
                except:
                    print(traceback.format_exc())

    def fitInView(self, scale=True):
        rect = QRectF(self.bracketLayout.rect())
        if not rect.isNull():
            # self.setSceneRect(rect)

            # unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
            # self.scale(1 / unity.width(), 1 / unity.height())
            # viewrect = self.viewport().rect()
            # scenerect = self.transform().mapRect(rect)
            # factor = min(viewrect.width() / scenerect.width(),
            #                 viewrect.height() / scenerect.height())
            # self.scale(factor, factor)
            
            self._zoom = 0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        # if self._zoom >= 0:
        self.scale(factor, factor)
        # elif self._zoom == 0:
        #     self.fitInView()
        # else:
        #     self._zoom = 0

    def mousePressEvent(self, event):
        super().mousePressEvent(event)