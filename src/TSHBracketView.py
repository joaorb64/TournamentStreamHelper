from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from .TSHBracket import *
from .TSHPlayerList import *
import traceback

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
            score.valueChanged.connect(lambda newVal, i=i: self.SetScore(i, newVal))
            score.setValue(-1)
        
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
            
            if self.bracketSet.playerIds[0] != -1:
                try:
                    if (self.bracketSet.playerIds[0]-1) < len(self.bracketView.playerList.slotWidgets) and self.bracketSet.playerIds[0] != -1:
                        self.name[0].setStyleSheet("font-style: normal;")
                        self.name[0].setText(self.bracketView.playerList.slotWidgets[self.bracketSet.playerIds[0]-1].findChild(QWidget, "name").text())
                    else:
                        self.name[0].setStyleSheet("font-style: italic;")
                        self.name[0].setText("bye")
                except:
                    pass
            else:
                self.name[0].setText("")

            if self.bracketSet.playerIds[1] != -1:
                try:
                    if (self.bracketSet.playerIds[1]-1) < len(self.bracketView.playerList.slotWidgets) and self.bracketSet.playerIds[1] != -1:
                        self.name[1].setStyleSheet("font-style: normal;")
                        self.name[1].setText(self.bracketView.playerList.slotWidgets[self.bracketSet.playerIds[1]-1].findChild(QWidget, "name").text())
                    else:
                        self.name[1].setStyleSheet("font-style: italic;")
                        self.name[1].setText("bye")
                except:
                    pass
            else:
                self.name[1].setText("")
            
            if self.name[0].text() == "" or self.name[1].text() == "":
                self.hide()
            else:
                self.show()

class TSHBracketView(QGraphicsView):
    def __init__(self, bracket: Bracket, playerList: TSHPlayerList = None, *args):
        super().__init__(*args)

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
            
        
            # Winners right side cutout
            if int(roundNum) > 0 and progressionsOut > 0:
                cutOut = math.sqrt(progressionsOut)/2 + 1
                if progressionsIn > 0: cutOut += 1
                if int(roundNum) + cutOut >= len(winnersRounds): continue
            
            # # Winners left side cutout
            if int(roundNum) == 1 and progressionsIn > 0: continue
            
            # Losers right side cutout
            if int(roundNum) < 0 and progressionsOut > 0:
                cutOut = math.sqrt(progressionsOut) - 1
                if progressionsIn > 0 and progressionsOut: cutOut += 2
                if abs(int(roundNum)) + cutOut >= len(losersRounds): continue
            
            # Losers left side cutout
            # Do not draw the mock losers round 1 & 2
            if int(roundNum) in [-1, -2]: continue
            if int(roundNum) == -3 and progressionsIn == 0: continue
            
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
    
    def Update(self):
        for round in self.bracketWidgets:
            for setWidget in round:
                setWidget.Update()
        self.DrawLines()
        
        StateManager.BlockSaving()

        data = {}

        for roundKey, round in self.bracket.rounds.items():
            
            if self.roundNameLabels.get(roundKey):
                roundName = self.roundNameLabels.get(roundKey).text()
                if roundName == "":
                    roundName = self.roundNameLabels.get(roundKey).placeholderText()
            else:
                roundName = ""

            data[roundKey] = {
                "name": roundName,
                "sets": {}
            }
            for j, bracketSet in enumerate(round):
                data[roundKey]["sets"][j] = {
                    "playerId": bracketSet.playerIds,
                    "score": bracketSet.score,
                    "nextWin": bracketSet.winNext.pos if bracketSet.winNext else None,
                    "nextLose": bracketSet.loseNext.pos if bracketSet.loseNext else None
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
                        if (i%2 == 0 and self.progressionsIn <= 0) or (i%2 == 1 and self.progressionsIn > 0):
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