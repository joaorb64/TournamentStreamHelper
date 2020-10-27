from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import shutil

import requests
import json
import traceback, sys
import time
import os

CHARACTER_TO_CODENAME = {
    "Mario": "mario",
    "Donkey Kong": "donkey",
    "Link": "link",
    "Samus": "samus",
    "Dark Samus": "samusd",
    "Yoshi": "yoshi",
    "Kirby": "kirby",
    "Fox": "fox",
    "Pikachu": "pikachu",
    "Luigi": "luigi",
    "Ness": "ness",
    "Captain Falcon": "captain",
    "Jigglypuff": "purin",
    "Peach": "peach",
    "Daisy": "daisy",
    "Bowser": "koopa",
    "Ice Climbers": "ice_climber",
    "Sheik": "sheik",
    "Zelda": "zelda",
    "Dr Mario": "mariod",
    "Pichu": "pichu",
    "Falco": "falco",
    "Marth": "marth",
    "Lucina": "lucina",
    "Young Link": "younglink",
    "Ganondorf": "ganon",
    "Mewtwo": "mewtwo",
    "Roy": "roy",
    "Chrom": "chrom",
    "Mr Game And Watch": "gamewatch",
    "Meta Knight": "metaknight",
    "Pit": "pit",
    "Dark Pit": "pitb",
    "Zero Suit Samus": "szerosuit",
    "Wario": "wario",
    "Snake": "snake",
    "Ike": "ike",
    "Pokemon Trainer": "ptrainer",
    "Diddy Kong": "diddy",
    "Lucas": "lucas",
    "Sonic": "sonic",
    "King Dedede": "dedede",
    "Olimar": "pikmin",
    "Lucario": "lucario",
    "Rob": "robot",
    "Toon Link": "toonlink",
    "Wolf": "wolf",
    "Villager": "murabito",
    "Mega Man": "rockman",
    "Wii Fit Trainer": "wiifit",
    "Rosalina And Luma": "rosetta",
    "Little Mac": "littlemac",
    "Greninja": "gekkouga",
    "Mii Brawler": "miifighter",
    "Mii Swordfighter": "miiswordsman",
    "Mii Gunner": "miigunner",
    "Palutena": "palutena",
    "Pac Man": "pacman",
    "Robin": "reflet",
    "Shulk": "shulk",
    "Bowser Jr": "koopajr",
    "Duck Hunt": "duckhunt",
    "Ryu": "ryu",
    "Ken": "ken",
    "Cloud": "cloud",
    "Corrin": "kamui",
    "Bayonetta": "bayonetta",
    "Inkling": "inkling",
    "Ridley": "ridley",
    "Simon": "simon",
    "Richter": "richter",
    "King K Rool": "krool",
    "Isabelle": "shizue",
    "Incineroar": "gaogaen",
    "Piranha Plant": "packun",
    "Joker": "jack",
    "Hero": "brave",
    "Banjo-Kazooie": "buddy",
    "Terry": "dolly",
    "Byleth": "master",
    "Min Min": "tantan",
    "Steve": "pickel",
    "Random": "random"
}

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
            self.signals.finished.emit()  # Done

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icons/icon.png'))

        if not os.path.exists("out/"):
            os.mkdir("out/")

        try:
            f = open('estados.json')
            estados_json = json.load(f)
            print("States loaded")
            self.estados = {e["uf"]: "("+e["nome"]+")" for e in estados_json}
        except Exception as e:
            print(e)
            exit()
        
        self.stockIcons = {}
        
        for c in CHARACTER_TO_CODENAME.keys():
            self.stockIcons[c] = {}
            for i in range(0, 8):
                self.stockIcons[c][i] = QIcon('character_icon/chara_2_'+CHARACTER_TO_CODENAME[c]+'_0'+str(i)+'.png')

        self.portraits = {}

        for c in CHARACTER_TO_CODENAME.keys():
            self.portraits[c] = {}
            for i in range(0, 8):
                self.portraits[c][i] = QIcon('character_icon/chara_0_'+CHARACTER_TO_CODENAME[c]+'_0'+str(i)+'.png')

        self.threadpool = QThreadPool()

        self.player_layouts = []

        self.allplayers = None

        self.setGeometry(300, 300, 800, 100)
        self.setWindowTitle("Ajudante de Stream")

        # Layout base
        base_layout = QHBoxLayout()
        self.setLayout(base_layout)

        # Inputs do jogador 1 na vertical
        p1 = PlayerColumn(self)
        self.player_layouts.append(p1)
        base_layout.addWidget(p1.group_box)
    
        # Botoes no meio
        layout_middle = QGridLayout()

        group_box = QGroupBox("Score")
        group_box.setLayout(layout_middle)

        base_layout.addWidget(group_box)

        self.scoreLeft = QSpinBox()
        self.scoreLeft.setMinimumSize(48, 64)
        fnt = self.scoreLeft.font()
        fnt.setPointSize(20)
        self.scoreLeft.setFont(fnt)
        layout_middle.addWidget(self.scoreLeft, 0, 0)
        self.scoreRight = QSpinBox()
        self.scoreRight.setMinimumSize(48, 64)
        self.scoreRight.setFont(fnt)
        layout_middle.addWidget(self.scoreRight, 0, 1)

        self.invert_bt = QToolButton()
        layout_middle.addWidget(self.invert_bt, 1, 0, 1, 2, Qt.AlignCenter)
        #self.invert_bt.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.invert_bt.setIcon(QIcon('icons/swap.svg'))
        self.invert_bt.setText("Inverter")
        self.invert_bt.setIconSize(QSize(32, 32))
        self.invert_bt.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Inputs do jogador 2 na vertical
        p2 = PlayerColumn(self, True)
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
        layout_end.addWidget(self.optionsBt)
        self.optionsBt.setMenu(QMenu())
        self.optionsBt.menu().addAction("Sempre no topo")

        self.downloadBt = QPushButton("Baixar dados do PowerRankings")
        self.downloadBt.setIcon(QIcon('icons/download.svg'))
        layout_end.addWidget(self.downloadBt)
        self.downloadBt.clicked.connect(self.DownloadButtonClicked)

        self.downloadBt = QPushButton("Baixar dados de um torneio do SmashGG")
        self.downloadBt.setIcon(QIcon('icons/smashgg.png'))
        layout_end.addWidget(self.downloadBt)
        self.downloadBt.clicked.connect(self.DownloadButtonClicked)

        self.LoadData()

        self.show()
    
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
    
    def SetupAutocomplete(self):
        # auto complete options
        names = [p["name"] for i, p in enumerate(self.allplayers["players"])]

        model = QStandardItemModel()

        for i, n in enumerate(names):
            model.appendRow(QStandardItem(n))

        for p in self.player_layouts:
            completer = QCompleter(completionColumn=0, caseSensitivity=Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setModel(model)
            p.player_name.setModel(model)
            p.player_name.setCompleter(completer)
            p.player_name.activated.connect(p.AutocompleteSelected)
        print("Autocomplete reloaded")
    
    def LoadData(self):
        try:
            f = open('powerrankings_player_data.json')
            self.allplayers = json.load(f)
            print("Data loaded")
            self.SetupAutocomplete()
        except Exception as e:
            print(e)

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

            print("Download successful")
            self.LoadData()
        
    def ExportData(self):
        for i, pl in enumerate(self.player_layouts):
            with open('out/p'+str(i+1)+'_name.txt', 'w') as outfile:
                outfile.write(pl.player_name.currentText())
            with open('out/p'+str(i+1)+'_name+prefix.txt', 'w') as outfile:
                if len(pl.player_org.text()) > 0:
                    outfile.write(pl.player_org.text()+" | "+pl.player_name.currentText())
                else:
                    outfile.write(pl.player_name.currentText())
            with open('out/p'+str(i+1)+'_prefix.txt', 'w') as outfile:
                outfile.write(pl.player_org.text())
            with open('out/p'+str(i+1)+'_twitter.txt', 'w') as outfile:
                outfile.write(pl.player_twitter.text())
            with open('out/p'+str(i+1)+'_state.txt', 'w') as outfile:
                outfile.write(pl.player_state.currentText())
            
            try:
                if(pl.player_twitter.text() != None):
                    r = requests.get("http://twitter-avatar.now.sh/"+pl.player_twitter.text().split("/")[-1], stream=True)
                    if r.status_code == 200:
                        with open('out/p'+str(i+1)+'_picture.png', 'wb') as f:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, f)
            except Exception as e:
                print(e)
            
            try:
                shutil.copy(
                    "state_icon/"+pl.player_state.currentData()+".png",
                    "out/p"+str(i+1)+"_flag.png"
                )
            except Exception as e:
                print(e)
            
            try:
                shutil.copy(
                    "character_icon/chara_0_"+CHARACTER_TO_CODENAME[pl.player_character.currentText()]+"_0"+str(pl.player_character_color.currentIndex())+".png",
                    "out/p"+str(i+1)+"_character_portrait.png"
                )
                shutil.copy(
                    "character_icon/chara_1_"+CHARACTER_TO_CODENAME[pl.player_character.currentText()]+"_0"+str(pl.player_character_color.currentIndex())+".png",
                    "out/p"+str(i+1)+"_character_big.png"
                )
                shutil.copy(
                    "character_icon/chara_3_"+CHARACTER_TO_CODENAME[pl.player_character.currentText()]+"_0"+str(pl.player_character_color.currentIndex())+".png",
                    "out/p"+str(i+1)+"_character_full.png"
                )
                shutil.copy(
                    "character_icon/chara_2_"+CHARACTER_TO_CODENAME[pl.player_character.currentText()]+"_0"+str(pl.player_character_color.currentIndex())+".png",
                    "out/p"+str(i+1)+"_character_stockicon.png"
                )
            except Exception as e:
                print(e)
            

class PlayerColumn():
    def __init__(self, parent, inverted=False):
        super().__init__()

        self.parent = parent

        self.group_box = QGroupBox("Player")

        self.layout_grid = QGridLayout()
        self.group_box.setLayout(self.layout_grid)

        pos_labels = 0
        pos_forms = 1

        if inverted:
            pos_labels = 1
            pos_forms = 0

        self.layout_grid.addWidget(QLabel("Nick"), 0, pos_labels)
        self.player_name = QComboBox()
        self.player_name.setEditable(True)
        self.layout_grid.addWidget(self.player_name, 0, pos_forms)

        self.layout_grid.addWidget(QLabel("Prefixo"), 1, pos_labels)
        self.player_org = QLineEdit()
        self.layout_grid.addWidget(self.player_org, 1, pos_forms)

        self.layout_grid.addWidget(QLabel("Nome real"), 2, pos_labels)
        self.player_real_name = QLineEdit()
        self.layout_grid.addWidget(self.player_real_name, 2, pos_forms)

        self.layout_grid.addWidget(QLabel("Twitter"), 3, pos_labels)
        self.player_twitter = QLineEdit()
        self.layout_grid.addWidget(self.player_twitter, 3, pos_forms)

        self.layout_grid.addWidget(QLabel("Estado"), 4, pos_labels)
        self.player_state = QComboBox()
        self.player_state.addItem("")
        for i, estado in enumerate(self.parent.estados):
            item = self.player_state.addItem(QIcon("state_icon/"+estado+".png"), estado + " " + self.parent.estados[estado])
            self.player_state.setItemData(i+1, estado)
        self.player_state.setEditable(True)
        self.layout_grid.addWidget(self.player_state, 4, pos_forms)

        self.layout_grid.addWidget(QLabel("Personagem"), 5, pos_labels)
        self.player_character = QComboBox()
        self.player_character.addItem("")
        for c in self.parent.stockIcons:
            self.player_character.addItem(self.parent.stockIcons[c][0], c)
        self.player_character.setEditable(True)
        self.layout_grid.addWidget(self.player_character, 5, pos_forms)
        self.player_character.currentTextChanged.connect(self.LoadSkinOptions)

        self.layout_grid.addWidget(QLabel("Cor"), 6, pos_labels)
        self.player_character_color = QComboBox()
        self.layout_grid.addWidget(self.player_character_color, 6, pos_forms)
        self.player_character_color.setIconSize(QSize(64, 64))
        self.player_character_color.setMinimumHeight(64)
    
    def LoadSkinOptions(self, text):
        self.player_character_color.clear()
        for c in self.parent.portraits[self.player_character.currentText()]:
            self.player_character_color.addItem(self.parent.portraits[text][c], str(c))
    
    def AutocompleteSelected(self, index):
        if index is not None:
            player = self.parent.allplayers["players"][index]
            
            self.player_name.setCurrentText(player["name"])
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
        
        self.parent.ExportData()


App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec())