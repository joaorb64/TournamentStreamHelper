from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import json
from .TSHBracket import *
from .TSHPlayerList import *

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
            self.playerId.append(idLabel)
            hbox.layout().addWidget(idLabel)

            name = QLineEdit()
            name.setDisabled(True)
            self.name.append(name)
            hbox.layout().addWidget(name)

            score = QSpinBox()
            self.score.append(score)
            hbox.layout().addWidget(score)
            score.valueChanged.connect(lambda newVal, i=i: self.SetScore(i, newVal))
        
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.layout().setSpacing(2)

        self.Update()
    
    def SetScore(self, id, score):
        self.bracketSet.score[id] = score
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
                    self.name[0].setText(self.bracketView.playerList.slotWidgets[self.bracketSet.playerIds[0]-1].findChild(QWidget, "name").text())
                except:
                    pass
            else:
                self.name[0].setText("")

            if self.bracketSet.playerIds[1] != -1:
                try:
                    self.name[1].setText(self.bracketView.playerList.slotWidgets[self.bracketSet.playerIds[1]-1].findChild(QWidget, "name").text())
                except:
                    pass
            else:
                self.name[1].setText("")

class TSHBracketView(QGraphicsView):
    def __init__(self, bracket: Bracket, playerList: TSHPlayerList = None, *args):
        super().__init__(*args)

        self.playerList = playerList
        self.bracket = bracket

        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)

        self.bracketLayout = QWidget()
        self.bracketLayout.setLayout(QHBoxLayout())
        self._scene.addWidget(self.bracketLayout)

        self.bracketWidgets = []

        for x, round in enumerate(self.bracket.rounds):
            print("round", len(round), x)
            round[0].score = [1,0]
        self.bracket.UpdateBracket()

        for round in self.bracket.rounds:
            layoutOuter = QWidget()
            self.bracketLayout.layout().addWidget(layoutOuter)
            layoutOuter.setLayout(QVBoxLayout())
            roundWidgets = []
            for _set in round:
                wid = BracketSetWidget(_set, self)
                layoutOuter.layout().addWidget(wid)
                roundWidgets.append(wid)
            self.bracketWidgets.append(roundWidgets)

        self.toggleDragMode()

        brush = QBrush()
        brush.setColor(QColor(0, 0, 0, 0))

        pen = QPen()
        pen.setColor(QColor(0,0,0,0))

        self.repaint()
        qApp.processEvents()

        self.bracketLines = []

        self.fitInView()
    
    def Update(self):
        for round in self.bracketWidgets:
            for setWidget in round:
                setWidget.Update()
        self.DrawLines()
        
        StateManager.BlockSaving()

        data = {}

        for i, round in enumerate(self.bracketWidgets):
            data[i] = {}
            for j, setWidget in enumerate(round):
                data[i][j] = {
                    "playerId": setWidget.bracketSet.playerIds,
                    "score": setWidget.bracketSet.score
                }

        StateManager.Set("bracket.bracket.rounds", data)

        StateManager.ReleaseSaving()
    
    def DrawLines(self):
        for element in self.bracketLines:
            self._scene.removeItem(element)

        self.bracketLines = []

        for i, round in enumerate(self.bracketWidgets[:-1]):
            for j, setWidget in enumerate(round):
                _set = setWidget

                nxtWidget = self.bracketWidgets[i+1][math.floor(j/2)]
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

                self._scene.addPath(
                    path,
                    pen
                )

                self.bracketLines.append(path)

    def fitInView(self, scale=True):
        rect = QRectF(self.bracketLayout.rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            # if self.hasPhoto():
            #     unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
            #     self.scale(1 / unity.width(), 1 / unity.height())
            #     viewrect = self.viewport().rect()
            #     scenerect = self.transform().mapRect(rect)
            #     factor = min(viewrect.width() / scenerect.width(),
            #                  viewrect.height() / scenerect.height())
            #     self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        self._empty = False
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._photo.setPixmap(pixmap)
        self.fitInView()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        if self._zoom >= 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView()
        else:
            self._zoom = 0

    def toggleDragMode(self):
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super().mousePressEvent(event)