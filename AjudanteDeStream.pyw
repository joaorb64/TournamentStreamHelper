#!/usr/bin/env python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import shutil
import tarfile

import requests
import urllib
import json
import traceback, sys
import time
import os

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress 

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(object)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()    

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress        

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            if self.signals.finished:
                self.signals.finished.emit()  # Done

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icons/icon.png'))

        if not os.path.exists("out/"):
            os.mkdir("out/")

        if not os.path.exists("character_icon/"):
            os.mkdir("character_icon/")
        
        f = open('character_name_to_codename.json')
        self.character_to_codename = json.load(f)

        try:
            f = open('estados.json')
            estados_json = json.load(f)
            print("States loaded")
            self.estados = {e["uf"]: "("+e["nome"]+")" for e in estados_json}
        except Exception as e:
            print(e)
            exit()
        
        try:
            f = open('settings.json')
            self.settings = json.load(f)
            print("Settings loaded")
        except Exception as e:
            self.settings = {}
            self.SaveSettings()
            print("Settings created")

        self.font_small = QFont("font/RobotoCondensed-Regular.ttf", pointSize=8)
        
        self.stockIcons = {}
        
        for c in self.character_to_codename.keys():
            self.stockIcons[c] = {}
            for i in range(0, 8):
                self.stockIcons[c][i] = QIcon('character_icon/chara_2_'+self.character_to_codename[c]+'_0'+str(i)+'.png')

        self.portraits = {}

        for c in self.character_to_codename.keys():
            self.portraits[c] = {}
            for i in range(0, 8):
                self.portraits[c][i] = QIcon('character_icon/chara_0_'+self.character_to_codename[c]+'_0'+str(i)+'.png')

        self.threadpool = QThreadPool()

        self.player_layouts = []

        self.allplayers = None

        self.setGeometry(300, 300, 800, 100)
        self.setWindowTitle("Ajudante de Stream")

        # Layout base
        base_layout = QHBoxLayout()
        self.setLayout(base_layout)

        # Inputs do jogador 1 na vertical
        p1 = PlayerColumn(self, 1)
        self.player_layouts.append(p1)
        base_layout.addWidget(p1.group_box)
    
        # Botoes no meio
        layout_middle = QGridLayout()

        group_box = QGroupBox("Score")
        group_box.setLayout(layout_middle)
        group_box.setFont(self.font_small)

        base_layout.addWidget(group_box)

        self.tournament_phase = QComboBox()
        self.tournament_phase.setEditable(True)
        layout_middle.addWidget(self.tournament_phase, 0, 0, 1, 2)

        self.scoreLeft = QSpinBox()
        self.scoreLeft.setFont(QFont("font/RobotoCondensed-Regular.ttf", pointSize=20))
        layout_middle.addWidget(self.scoreLeft, 1, 0, 2, 1)
        self.scoreRight = QSpinBox()
        self.scoreRight.setFont(QFont("font/RobotoCondensed-Regular.ttf", pointSize=20))
        layout_middle.addWidget(self.scoreRight, 1, 1, 2, 1)

        self.reset_score_bt = QPushButton()
        layout_middle.addWidget(self.reset_score_bt, 3, 0, 1, 2)
        self.reset_score_bt.setIcon(QIcon('icons/undo.svg'))
        self.reset_score_bt.setText("Zerar")
        self.reset_score_bt.setFont(self.font_small)
        self.reset_score_bt.clicked.connect(self.ResetScoreButtonClicked)

        self.invert_bt = QPushButton()
        layout_middle.addWidget(self.invert_bt, 4, 0, 1, 2)
        self.invert_bt.setIcon(QIcon('icons/swap.svg'))
        self.invert_bt.setText("Inverter")
        self.invert_bt.setFont(self.font_small)
        self.invert_bt.clicked.connect(self.InvertButtonClicked)
        
        # Inputs do jogador 2 na vertical
        p2 = PlayerColumn(self, 2)
        self.player_layouts.append(p2)
        base_layout.addWidget(p2.group_box)

        # Botoes no final
        layout_end = QGridLayout()
        base_layout.addLayout(layout_end)

        self.optionsBt = QToolButton()
        self.optionsBt.setIcon(QIcon('icons/menu.svg'))
        self.optionsBt.setText("Opções")
        self.optionsBt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.optionsBt.setPopupMode(QToolButton.InstantPopup)
        layout_end.addWidget(self.optionsBt, 0, 0, 1, 2)
        self.optionsBt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.optionsBt.setMenu(QMenu())
        action = self.optionsBt.menu().addAction("Sempre no topo")
        action.setCheckable(True)
        action.toggled.connect(self.ToggleAlwaysOnTop)
        action = self.optionsBt.menu().addAction("Baixar ícones de personagens")
        action.setIcon(QIcon('icons/download.svg'))
        action.triggered.connect(self.DownloadAssets)

        self.downloadBt = QPushButton("Baixar dados do PowerRankings")
        self.downloadBt.setIcon(QIcon('icons/download.svg'))
        layout_end.addWidget(self.downloadBt, 1, 0, 1, 2)
        self.downloadBt.clicked.connect(self.DownloadButtonClicked)

        self.downloadBt = QPushButton("Baixar dados de um torneio")
        self.downloadBt.setIcon(QIcon('icons/smashgg.png'))
        layout_end.addWidget(self.downloadBt, 2, 0, 1, 2)
        self.downloadBt.clicked.connect(self.DownloadButtonClicked)

        # save button
        self.saveBt = QToolButton()
        self.saveBt.setText("Salvar e exportar")
        self.saveBt.setIcon(QIcon('icons/save.svg'))
        self.saveBt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        pal = self.saveBt.palette()
        pal.setColor(QPalette.Button, QColor(Qt.green))
        self.saveBt.setPalette(pal)
        layout_end.addWidget(self.saveBt, 3, 0, 2, 2)
        self.saveBt.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.saveBt.setPopupMode(QToolButton.MenuButtonPopup)
        self.saveBt.clicked.connect(self.SaveButtonClicked)
        
        self.saveBt.setMenu(QMenu())
        action = self.saveBt.menu().addAction("Automático")
        action.setCheckable(True)

        if "autosave" in self.settings:
            if self.settings["autosave"] == True:
                action.setChecked(True)
        
        action.toggled.connect(self.ToggleAutosave)

        self.LoadData()

        self.show()
    
    def ResetScoreButtonClicked(self):
        self.scoreLeft.setValue(0)
        self.scoreRight.setValue(0)
    
    def InvertButtonClicked(self):
        nick = self.player_layouts[0].player_name.text()
        prefix = self.player_layouts[0].player_org.text()
        name = self.player_layouts[0].player_real_name.text()
        twitter = self.player_layouts[0].player_twitter.text()
        state = self.player_layouts[0].player_state.currentIndex()
        character = self.player_layouts[0].player_character.currentIndex()
        color = self.player_layouts[0].player_character_color.currentIndex()
        score = self.scoreLeft.value()

        self.player_layouts[0].player_name.setText(self.player_layouts[1].player_name.text())
        self.player_layouts[0].player_org.setText(self.player_layouts[1].player_org.text())
        self.player_layouts[0].player_real_name.setText(self.player_layouts[1].player_real_name.text())
        self.player_layouts[0].player_twitter.setText(self.player_layouts[1].player_twitter.text())
        self.player_layouts[0].player_state.setCurrentIndex(self.player_layouts[1].player_state.currentIndex())
        self.player_layouts[0].player_character.setCurrentIndex(self.player_layouts[1].player_character.currentIndex())
        self.player_layouts[0].player_character_color.setCurrentIndex(self.player_layouts[1].player_character_color.currentIndex())
        self.scoreLeft.setValue(self.scoreRight.value())

        self.player_layouts[1].player_name.setText(nick)
        self.player_layouts[1].player_org.setText(prefix)
        self.player_layouts[1].player_real_name.setText(name)
        self.player_layouts[1].player_twitter.setText(twitter)
        self.player_layouts[1].player_state.setCurrentIndex(state)
        self.player_layouts[1].player_character.setCurrentIndex(character)
        self.player_layouts[1].player_character_color.setCurrentIndex(color)
        self.scoreRight.setValue(score)
    
    def DownloadAssets(self):
        self.downloadDialogue = QProgressDialog("Baixando imagens...", "Cancelar", 0, 100, self)
        self.downloadDialogue.setAutoClose(False)
        self.downloadDialogue.setWindowTitle("Download de imagens")
        self.downloadDialogue.setWindowModality(Qt.WindowModal)
        self.downloadDialogue.show()

        worker = Worker(self.DownloadAssetsWorker)
        worker.signals.progress.connect(self.DownloadAssetsProgress)
        worker.signals.finished.connect(self.DownloadAssetsFinished)
        self.threadpool.start(worker)
    
    def DownloadAssetsWorker(self, progress_callback):
        response = requests.get("https://api.github.com/repos/joaorb64/AjudanteDeStream/releases/latest")
        release = json.loads(response.text)

        files = release["assets"]

        totalSize = 0
        for f in files:
            totalSize += f["size"]

        downloaded = 0

        for f in files:
            with open("character_icon/"+f["name"], 'wb') as downloadFile:
                print("Downloading "+str(f["name"]))
                progress_callback.emit("Baixando "+str(f["name"])+"...")

                response = urllib.request.urlopen(f["browser_download_url"])

                while(True):
                    chunk = response.read(1024*1024)

                    if not chunk:
                        break

                    downloaded += len(chunk)
                    downloadFile.write(chunk)

                    if self.downloadDialogue.wasCanceled():
                        return
                    
                    progress_callback.emit(int(downloaded/totalSize*100))
                downloadFile.close()

                print("OK")
        
        progress_callback.emit(100)

        for f in files:
            print("Extracting "+f["name"])
            progress_callback.emit("Extraindo "+f["name"])
            
            tar = tarfile.open("character_icon/"+f["name"])
            tar.extractall("character_icon/")
            tar.close()
            os.remove("character_icon/"+f["name"])

            print("OK")
    
    def DownloadAssetsProgress(self, n):
        if type(n) == int:
            self.downloadDialogue.setValue(n)

            if n == 100:
                self.downloadDialogue.setMaximum(0)
                self.downloadDialogue.setValue(0)
        else:
            self.downloadDialogue.setLabelText(n)
    
    def DownloadAssetsFinished(self):
        self.downloadDialogue.close()
    
    def DownloadButtonClicked(self):
        self.downloadBt.setEnabled(False)
        self.downloadBt.setText("Baixando...")

        worker = Worker(self.DownloadData)
        worker.signals.finished.connect(self.DownloadButtonComplete)
        worker.signals.progress.connect(self.DownloadButtonProgress)
        
        self.threadpool.start(worker)
    
    def DownloadButtonProgress(self, n):
        self.downloadBt.setText("Baixando..."+str(n[0])+"/"+str(n[1]))
    
    def DownloadButtonComplete(self):
        self.downloadBt.setEnabled(True)
        self.downloadBt.setText("Baixar dados do PowerRankings")
        self.LoadData()
    
    def SetupAutocomplete(self):
        # auto complete options
        names = [p["name"] for i, p in enumerate(self.allplayers["players"])]

        model = QStandardItemModel()

        model.appendRow([QStandardItem(""), QStandardItem("")])

        for i, n in enumerate(names):
            model.appendRow([QStandardItem(n), QStandardItem(str(i))])

        for p in self.player_layouts:
            completer = QCompleter(completionColumn=0, caseSensitivity=Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setModel(model)
            #p.player_name.setModel(model)
            p.player_name.setCompleter(completer)
            completer.activated[QModelIndex].connect(p.AutocompleteSelected)
            #p.player_name.currentIndexChanged.connect(p.AutocompleteSelected)
        print("Autocomplete reloaded")
    
    def LoadData(self):
        try:
            f = open('powerrankings_player_data.json')
            self.allplayers = json.load(f)
            print("Data loaded")
            self.SetupAutocomplete()
        except Exception as e:
            print(e)
    
    def ToggleAlwaysOnTop(self, checked):
        if checked:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()
    
    def ToggleAutosave(self, checked):
        if checked:
            self.settings["autosave"] = True
        else:
            self.settings["autosave"] = False
        self.SaveSettings()
    
    def SaveButtonClicked(self):
        for p in self.player_layouts:
            p.ExportName()
            p.ExportRealName()
            p.ExportTwitter()
            p.ExportState()
            p.ExportCharacter()

    def DownloadData(self, progress_callback):
        with open('powerrankings_player_data.json', 'wb') as f:
            print("Download start")

            response = requests.get('https://raw.githubusercontent.com/joaorb64/tournament_api/master/allplayers.json', stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None: # no content length header
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = [dl, total_length]
                    progress_callback.emit(done)
                    sys.stdout.flush()
                sys.stdout.flush()
                f.close()

            print("Download successful")
    
    def SaveSettings(self):
        with open('settings.json', 'w') as outfile:
            json.dump(self.settings, outfile, indent=4, sort_keys=True)

class PlayerColumn():
    def __init__(self, parent, id, inverted=False):
        super().__init__()

        self.parent = parent
        self.id = id

        self.group_box = QGroupBox("Player")

        self.layout_grid = QGridLayout()
        self.group_box.setLayout(self.layout_grid)

        self.group_box.setFont(self.parent.font_small)

        pos_labels = 0
        pos_forms = 1
        text_alignment = Qt.AlignRight|Qt.AlignVCenter

        if inverted:
            pos_labels = 1
            pos_forms = 0
            text_alignment = Qt.AlignLeft|Qt.AlignVCenter

        nick_label = QLabel("Nick")
        nick_label.setFont(self.parent.font_small)
        nick_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(nick_label, 0, pos_labels)
        self.player_name = QLineEdit()
        self.layout_grid.addWidget(self.player_name, 0, pos_forms)
        self.player_name.setMinimumWidth(128)
        self.player_name.setFont(self.parent.font_small)
        self.player_name.textChanged.connect(self.AutoExportName)

        prefix_label = QLabel("Prefixo")
        prefix_label.setFont(self.parent.font_small)
        prefix_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(prefix_label, 1, pos_labels)
        self.player_org = QLineEdit()
        self.layout_grid.addWidget(self.player_org, 1, pos_forms)
        self.player_org.setFont(self.parent.font_small)
        self.player_org.textChanged.connect(self.AutoExportName)

        real_name_label = QLabel("Nome")
        real_name_label.setFont(self.parent.font_small)
        real_name_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(real_name_label, 2, pos_labels)
        self.player_real_name = QLineEdit()
        self.layout_grid.addWidget(self.player_real_name, 2, pos_forms)
        self.player_real_name.setFont(self.parent.font_small)
        self.player_real_name.textChanged.connect(self.AutoExportRealName)

        player_twitter_label = QLabel("Twitter")
        player_twitter_label.setFont(self.parent.font_small)
        player_twitter_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_twitter_label, 3, pos_labels)
        self.player_twitter = QLineEdit()
        self.layout_grid.addWidget(self.player_twitter, 3, pos_forms)
        self.player_twitter.setFont(self.parent.font_small)
        self.player_twitter.editingFinished.connect(self.AutoExportTwitter)

        player_state_label = QLabel("Estado")
        player_state_label.setFont(self.parent.font_small)
        player_state_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_state_label, 0, pos_labels+2)
        self.player_state = QComboBox()
        self.player_state.addItem("")
        for i, estado in enumerate(self.parent.estados):
            item = self.player_state.addItem(QIcon("state_icon/"+estado+".png"), estado + " " + self.parent.estados[estado])
            self.player_state.setItemData(i+1, estado)
        self.player_state.setEditable(True)
        self.layout_grid.addWidget(self.player_state, 0, pos_forms+2)
        self.player_state.setMinimumWidth(128)
        self.player_state.setFont(self.parent.font_small)
        self.player_state.currentIndexChanged.connect(self.AutoExportState)

        player_character_label = QLabel("Char")
        player_character_label.setFont(self.parent.font_small)
        player_character_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_character_label, 1, pos_labels+2)
        self.player_character = QComboBox()
        self.player_character.addItem("")
        for c in self.parent.stockIcons:
            self.player_character.addItem(self.parent.stockIcons[c][0], c)
        self.player_character.setEditable(True)
        self.layout_grid.addWidget(self.player_character, 1, pos_forms+2)
        self.player_character.currentTextChanged.connect(self.LoadSkinOptions)
        self.player_character.setMinimumWidth(128)
        self.player_character.setFont(self.parent.font_small)
        self.player_character.currentIndexChanged.connect(self.AutoExportCharacter)

        player_character_color_label = QLabel("Cor")
        player_character_color_label.setFont(self.parent.font_small)
        player_character_color_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_character_color_label, 2, pos_labels+2)
        self.player_character_color = QComboBox()
        self.layout_grid.addWidget(self.player_character_color, 2, pos_forms+2, 2, 1)
        self.player_character_color.setIconSize(QSize(64, 64))
        self.player_character_color.setMinimumHeight(64)
        self.player_character_color.setMinimumWidth(128)
        self.player_character_color.setFont(self.parent.font_small)
        self.player_character_color.currentIndexChanged.connect(self.AutoExportCharacter)

        self.optionsBt = QToolButton()
        self.optionsBt.setIcon(QIcon('icons/menu.svg'))
        self.optionsBt.setPopupMode(QToolButton.InstantPopup)
        self.layout_grid.addWidget(self.optionsBt, 0, 5)
        self.optionsBt.setMenu(QMenu())
        action = self.optionsBt.menu().addAction("Salvar como novo jogador")
        action.setIcon(QIcon('icons/add_user.svg'))
    
    def LoadSkinOptions(self, text):
        self.player_character_color.clear()
        for c in self.parent.portraits[self.player_character.currentText()]:
            self.player_character_color.addItem(self.parent.portraits[text][c], str(c))
    
    def AutoExportName(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportName()

    def ExportName(self):
        with open('out/p'+str(self.id)+'_name.txt', 'w') as outfile:
            outfile.write(self.player_name.text())
        with open('out/p'+str(self.id)+'_name+prefix.txt', 'w') as outfile:
            if len(self.player_org.text()) > 0:
                outfile.write(self.player_org.text()+" | "+self.player_name.text())
            else:
                outfile.write(self.player_name.text())
        with open('out/p'+str(self.id)+'_prefix.txt', 'w') as outfile:
            outfile.write(self.player_org.text())
        with open('out/p'+str(self.id)+'_twitter.txt', 'w') as outfile:
            outfile.write(self.player_twitter.text())
        with open('out/p'+str(self.id)+'_state.txt', 'w') as outfile:
            outfile.write(self.player_state.currentText())
    
    def AutoExportRealName(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportRealName()
    
    def ExportRealName(self):
        with open('out/p'+str(self.id)+'_real_name.txt', 'w') as outfile:
            outfile.write(self.player_real_name.text())
    
    def AutoExportTwitter(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportTwitter()
    
    def ExportTwitter(self):
        try:
            if(self.player_twitter.displayText() != None):
                r = requests.get("http://twitter-avatar.now.sh/"+self.player_twitter.text().split("/")[-1], stream=True)
                if r.status_code == 200:
                    with open('out/p'+str(self.id)+'_picture.png', 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print(e)
    
    def AutoExportState(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportState()

    def ExportState(self):
        try:
            shutil.copy(
                "state_icon/"+self.player_state.currentData()+".png",
                "out/p"+str(self.id)+"_flag.png"
            )
        except Exception as e:
            print(e)
    
    def AutoExportCharacter(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportCharacter()
            
    def ExportCharacter(self):
        try:
            shutil.copy(
                "character_icon/chara_0_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_portrait.png"
            )
        except Exception as e:
            print(e)
        try:
            shutil.copy(
                "character_icon/chara_1_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_big.png"
            )
        except Exception as e:
            print(e)
        try:
            shutil.copy(
                "character_icon/chara_3_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_full.png"
            )
        except Exception as e:
            print(e)
        try:
            shutil.copy(
                "character_icon/chara_3_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+"-halfres.png",
                "out/p"+str(self.id)+"_character_full-halfres.png"
            )
        except Exception as e:
            print(e)
        try:
            shutil.copy(
                "character_icon/chara_2_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_stockicon.png"
            )
        except Exception as e:
            print(e)
    
    def AutocompleteSelected(self, selected):
        if type(selected) == QModelIndex:
            index = int(selected.sibling(selected.row(), 1).data())
        elif type(selected) == int:
            index = selected-1
            if index < 0:
                index = None
        else:
            index = None

        if index is not None:
            player = self.parent.allplayers["players"][index]
            
            self.player_name.setText(player["name"])
            self.player_org.setText(player.get("org", ""))
            self.player_real_name.setText(player.get("full_name", ""))
            self.player_twitter.setText(player.get("twitter", ""))

            if player.get("state") is not None:
                self.player_state.setCurrentIndex(list(self.parent.estados.keys()).index(player.get("state"))+1)
            else:
                self.player_state.setCurrentIndex(0)
            
            if player.get("mains") is not None and len(player["mains"]) > 0 and player["mains"][0] != "":
                self.player_character.setCurrentIndex(list(self.parent.stockIcons.keys()).index(player.get("mains", [""])[0])+1)
                self.player_character_color.setCurrentIndex(player.get("skins", [""])[0])
            else:
                self.player_character.setCurrentIndex(0)
            
            self.AutoExportTwitter()


App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec())