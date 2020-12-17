#!/usr/bin/env python3
#-*- coding: utf-8 -*-

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

from collections import Counter

import unicodedata

def remove_accents_lower(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

characters = {
    "Mario": "Mario",
    "Donkey Kong": "Donkey Kong",
    "Link": "Link",
    "Samus": "Samus",
    "Dark Samus": "Dark Samus",
    "Yoshi": "Yoshi",
    "Kirby": "Kirby",
    "Fox": "Fox",
    "Pikachu": "Pikachu",
    "Luigi": "Luigi",
    "Ness": "Ness",
    "Captain Falcon": "Captain Falcon",
    "Jigglypuff": "Jigglypuff",
    "Peach": "Peach",
    "Daisy": "Daisy",
    "Bowser": "Bowser",
    "Ice Climbers": "Ice Climbers",
    "Sheik": "Sheik",
    "Zelda": "Zelda",
    "Dr. Mario": "Dr Mario",
    "Pichu": "Pichu",
    "Falco": "Falco",
    "Marth": "Marth",
    "Lucina": "Lucina",
    "Young Link": "Young Link",
    "Ganondorf": "Ganondorf",
    "Mewtwo": "Mewtwo",
    "Roy": "Roy",
    "Chrom": "Chrom",
    "Mr. Game & Watch": "Mr Game And Watch",
    "Meta Knight": "Meta Knight",
    "Pit": "Pit",
    "Dark Pit": "Dark Pit",
    "Zero Suit Samus": "Zero Suit Samus",
    "Wario": "Wario",
    "Snake": "Snake",
    "Ike": "Ike",
    "Pokemon Trainer": "Pokemon Trainer",
    "Diddy Kong": "Diddy Kong",
    "Lucas": "Lucas",
    "Sonic": "Sonic",
    "King Dedede": "King Dedede",
    "Olimar": "Olimar",
    "Lucario": "Lucario",
    "R.O.B.": "Rob",
    "Toon Link": "Toon Link",
    "Wolf": "Wolf",
    "Villager": "Villager",
    "Mega Man": "Mega Man",
    "Wii Fit Trainer": "Wii Fit Trainer",
    "Rosalina": "Rosalina And Luma",
    "Little Mac": "Little Mac",
    "Greninja": "Greninja",
    "Mii Brawler": "Mii Brawler",
    "Mii Swordfighter": "Mii Swordfighter",
    "Mii Gunner": "Mii Gunner",
    "Palutena": "Palutena",
    "Pac-Man": "Pac Man",
    "Robin": "Robin",
    "Shulk": "Shulk",
    "Bowser Jr.": "Bowser Jr",
    "Duck Hunt": "Duck Hunt",
    "Ryu": "Ryu",
    "Ken": "Ken",
    "Cloud": "Cloud",
    "Corrin": "Corrin",
    "Bayonetta": "Bayonetta",
    "Inkling": "Inkling",
    "Ridley": "Ridley",
    "Simon Belmont": "Simon",
    "Richter": "Richter",
    "King K. Rool": "King K Rool",
    "Isabelle": "Isabelle",
    "Incineroar": "Incineroar",
    "Piranha Plant": "Piranha Plant",
    "Joker": "Joker",
    "Hero": "Hero",
    "Banjo-Kazooie": "Banjo-Kazooie",
    "Terry": "Terry",
    "Byleth": "Byleth",
    "Min Min": "Min Min",
    "Steve": "Steve",
    "Random Character": "Random"
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
            if self.signals.finished:
                self.signals.finished.emit()  # Done

def removeFileIfExists(file):
    if os.path.exists(file):
        os.remove(file)

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icons/icon.png'))

        if not os.path.exists("out/"):
            os.mkdir("out/")

        if not os.path.exists("character_icon/"):
            os.mkdir("character_icon/")
        
        f = open('character_name_to_codename.json', encoding='utf-8')
        self.character_to_codename = json.load(f)

        f = open('ultimate.json', encoding='utf-8')
        self.smashgg_character_data = json.load(f)

        f = open('cities.json', encoding='utf-8')
        self.cities_json = json.load(f)

        try:
            f = open('countries+states.json', encoding='utf-8')
            self.countries_json = json.load(f)
            print("States loaded")
            self.countries = {c["iso2"]: [s["state_code"] for s in c["states"]] for c in self.countries_json}
        except Exception as e:
            print(e)
            exit()
        
        try:
            f = open('settings.json', encoding='utf-8')
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
        self.smashgg_players = None

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
        layout_middle.setVerticalSpacing(0)

        group_box = QGroupBox()
        group_box.setStyleSheet("QGroupBox{padding-top:0px;}")
        group_box.setLayout(layout_middle)
        group_box.setFont(self.font_small)
        group_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        base_layout.addWidget(group_box)

        tournament_phase_label = QLabel("Fase")
        tournament_phase_label.setFont(self.font_small)
        layout_middle.addWidget(tournament_phase_label, 0, 0, 1, 2)

        self.tournament_phase = QComboBox()
        self.tournament_phase.setEditable(True)
        self.tournament_phase.setFont(self.font_small)
        layout_middle.addWidget(self.tournament_phase, 1, 0, 1, 2)

        self.tournament_phase.addItems([
            "", "Friendlies", "Winners Bracket", "Losers Bracket",
            "Winners Finals", "Losers Finals", "Grand Finals"
        ])

        self.tournament_phase.currentTextChanged.connect(self.AutoExportScore)

        self.scoreLeft = QSpinBox()
        self.scoreLeft.setFont(QFont("font/RobotoCondensed-Regular.ttf", pointSize=12))
        self.scoreLeft.setAlignment(Qt.AlignHCenter)
        layout_middle.addWidget(self.scoreLeft, 2, 0, 1, 1)
        self.scoreLeft.valueChanged.connect(self.AutoExportScore)
        self.scoreRight = QSpinBox()
        self.scoreRight.setFont(QFont("font/RobotoCondensed-Regular.ttf", pointSize=12))
        self.scoreRight.setAlignment(Qt.AlignHCenter)
        self.scoreRight.valueChanged.connect(self.AutoExportScore)
        layout_middle.addWidget(self.scoreRight, 2, 1, 1, 1)

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

        self.downloadBt = QPushButton("Download PowerRankings data")
        self.downloadBt.setIcon(QIcon('icons/download.svg'))
        layout_end.addWidget(self.downloadBt, 1, 0, 1, 2)
        self.downloadBt.clicked.connect(self.DownloadButtonClicked)

        self.smashggConnectBt = QPushButton("Download players")
        self.smashggConnectBt.setIcon(QIcon('icons/smashgg.png'))
        layout_end.addWidget(self.smashggConnectBt, 2, 0, 1, 1)
        self.smashggConnectBt.clicked.connect(self.LoadPlayersFromSmashGGTournamentClicked)

        self.smashggSelectSetBt = QPushButton("Select set")
        self.smashggSelectSetBt.setIcon(QIcon('icons/smashgg.png'))
        layout_end.addWidget(self.smashggSelectSetBt, 2, 1, 1, 1)
        self.smashggSelectSetBt.clicked.connect(self.LoadSetsFromSmashGGTournamentClicked)

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
    
    def AutoExportScore(self):
        if self.settings.get("autosave") == True:
            self.ExportScore()
    
    def ExportScore(self):
        with open('out/p1_score.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(str(self.scoreLeft.value()))
        with open('out/p2_score.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(str(self.scoreRight.value()))
        with open('out/match_phase.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(self.tournament_phase.currentText())
    
    def ResetScoreButtonClicked(self):
        self.scoreLeft.setValue(0)
        self.scoreRight.setValue(0)
    
    def InvertButtonClicked(self):
        nick = self.player_layouts[0].player_name.text()
        prefix = self.player_layouts[0].player_org.text()
        name = self.player_layouts[0].player_real_name.text()
        twitter = self.player_layouts[0].player_twitter.text()
        country = self.player_layouts[0].player_country.currentIndex()
        state = self.player_layouts[0].player_state.currentIndex()
        character = self.player_layouts[0].player_character.currentIndex()
        color = self.player_layouts[0].player_character_color.currentIndex()
        score = self.scoreLeft.value()

        self.player_layouts[0].player_name.setText(self.player_layouts[1].player_name.text())
        self.player_layouts[0].player_org.setText(self.player_layouts[1].player_org.text())
        self.player_layouts[0].player_real_name.setText(self.player_layouts[1].player_real_name.text())
        self.player_layouts[0].player_twitter.setText(self.player_layouts[1].player_twitter.text())
        self.player_layouts[0].player_country.setCurrentIndex(self.player_layouts[1].player_country.currentIndex())
        self.player_layouts[0].player_state.setCurrentIndex(self.player_layouts[1].player_state.currentIndex())
        self.player_layouts[0].player_character.setCurrentIndex(self.player_layouts[1].player_character.currentIndex())
        self.player_layouts[0].player_character_color.setCurrentIndex(self.player_layouts[1].player_character_color.currentIndex())
        self.scoreLeft.setValue(self.scoreRight.value())

        self.player_layouts[1].player_name.setText(nick)
        self.player_layouts[1].player_org.setText(prefix)
        self.player_layouts[1].player_real_name.setText(name)
        self.player_layouts[1].player_twitter.setText(twitter)
        self.player_layouts[1].player_country.setCurrentIndex(country)
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
        names = []
        autocompleter_names = []
        autocompleter_mains = []
        autocompleter_players = []

        ap = self.allplayers["players"]
        
        for p in self.smashgg_players:
            found = next(
                (a for a in ap if a.get("smashgg_id", None) != None and a.get("smashgg_id", None) == p["smashgg_id"]),
                None
            )

            if found is None:
                p["from_smashgg"] = True
                ap.append(p)

        self.mergedPlayers = ap

        for i, p in enumerate(ap):
            name = ""
            if("org" in p.keys() and p["org"] != None):
                name += p["org"] + " "
            name += p["name"]
            if("country_code" in p.keys() and p["country_code"] != None):
                name += " ("+p["country_code"]+")"
            autocompleter_names.append(name)
            names.append(p["name"])

            if("mains" in p.keys() and p["mains"] != None and len(p["mains"]) > 0):
                autocompleter_mains.append(p["mains"][0])
            else:
                autocompleter_mains.append("Random")
            
            autocompleter_players.append(p)

        model = QStandardItemModel()

        model.appendRow([QStandardItem(""), QStandardItem(""), QStandardItem("")])

        for i, n in enumerate(names):
            item = QStandardItem(autocompleter_names[i])
            item.setIcon(QIcon(
                'character_icon/chara_2_'+
                self.character_to_codename[autocompleter_mains[i]]+
                '_00.png'))
            if "from_smashgg" in self.mergedPlayers[i]:
                pix = QPixmap(
                    'character_icon/chara_2_'+
                    self.character_to_codename[autocompleter_mains[i]]+
                    '_00.png'
                )
                p = QPainter(pix)
                p.drawImage(QPoint(32, 32), QImage("icons/smashgg.png"))
                p.end()
                item.setIcon(QIcon(pix))
            item.setData(autocompleter_players[i])
            model.appendRow([
                item,
                QStandardItem(n),
                QStandardItem(str(i))]
            )

        for p in self.player_layouts:
            completer = QCompleter(completionColumn=0, caseSensitivity=Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setModel(model)
            #p.player_name.setModel(model)
            p.player_name.setCompleter(completer)
            completer.activated[QModelIndex].connect(p.AutocompleteSelected, Qt.QueuedConnection)
            completer.popup().setMinimumWidth(500)
            #p.player_name.currentIndexChanged.connect(p.AutocompleteSelected)
        print("Autocomplete reloaded")
    
    def LoadData(self):
        try:
            f = open('powerrankings_player_data.json', encoding='utf-8')
            self.allplayers = json.load(f)
            print("Powerrankings data loaded")
            self.SetupAutocomplete()
        except Exception as e:
            print(e)
        
        try:
            f = open('tournament_players.json', encoding='utf-8')
            self.smashgg_players = json.load(f)
            print("Smashgg data loaded")
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
            p.ExportCountry()
            p.ExportState()
            p.ExportCharacter()
        self.ExportScore()

    def DownloadData(self, progress_callback):
        with open('powerrankings_player_data.json', 'wb', encoding='utf-8') as f:
            print("Download start")

            response = requests.get('https://raw.githubusercontent.com/joaorb64/tournament_api/sudamerica/out/allplayers.json', stream=True)
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
        with open('settings.json', 'w', encoding='utf-8') as outfile:
            json.dump(self.settings, outfile, indent=4, sort_keys=True)
    
    def LoadPlayersFromSmashGGTournamentClicked(self):
        text, okPressed = QInputDialog.getText(self, "Get text","Your name:", QLineEdit.Normal, "")
        if okPressed:
            self.LoadPlayersFromSmashGGTournamentStart(text)
    
    def LoadPlayersFromSmashGGTournamentStart(self, slug):
        if slug is None or slug=="":
            slug = "tournament/ultimate-xanadu-online-384/event/ultimate-singles"

        self.downloadDialogue = QProgressDialog("Fetching players...", "Cancel", 0, 100, self)
        self.downloadDialogue.setAutoClose(True)
        self.downloadDialogue.setWindowTitle("Download de imagens")
        self.downloadDialogue.setWindowModality(Qt.WindowModal)
        self.downloadDialogue.show()

        worker = Worker(self.LoadPlayersFromSmashGGTournamentWorker, **{"slug": slug})
        worker.signals.progress.connect(self.LoadPlayersFromSmashGGTournamentProgress)
        worker.signals.finished.connect(self.LoadPlayersFromSmashGGTournamentFinished)
        self.threadpool.start(worker)
    
    def LoadPlayersFromSmashGGTournamentWorker(self, progress_callback, slug):
        page = 1
        players = []

        while True:
            if self.downloadDialogue.wasCanceled():
                return

            r = requests.post(
                'https://api.smash.gg/gql/alpha',
                headers={
                    'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
                },
                json={
                    'query': '''
                    query evento($eventSlug: String!) {
                        event(slug: $eventSlug) {
                            entrants(query: {page: '''+str(page)+''', perPage: 10}) {
                                pageInfo {
                                    totalPages
                                }
                                nodes{
                                    name
                                    participants {
                                        user {
                                            id
                                            slug
                                            name
                                            authorizations(types: [TWITTER]) {
                                                type
                                                externalUsername
                                            }
                                            location {
                                                city
                                                country
                                            }
                                            images(type: "profile") {
                                                url
                                            }
                                        }
                                        player {
                                            id
                                            gamerTag
                                            prefix
                                            sets(page: 1, perPage: 3) {
                                                nodes {
                                                    games {
                                                        selections {
                                                            entrant {
                                                                participants {
                                                                    player {
                                                                        id
                                                                    }
                                                                }
                                                            }
                                                            selectionValue
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }''',
                    'variables': {
                        "eventSlug": slug
                    },
                }
            )
            resp = json.loads(r.text)

            totalPages = resp["data"]["event"]["entrants"]["pageInfo"]["totalPages"]

            if resp is None or \
            resp.get("data") is None or \
            resp["data"].get("event") is None or \
            resp["data"]["event"].get("entrants") is None:
                print(resp)
                return

            data_entrants = resp["data"]["event"]["entrants"]["nodes"]
            
            for entrant in data_entrants:
                user = entrant["participants"][0]["user"]
                player = entrant["participants"][0]["player"]

                player_obj = self.LoadSmashGGPlayer(user, player)
                
                players.append(player_obj)
            
            page += 1

            progress_callback.emit(page/totalPages*100)

            if page >= totalPages:
                break
        
        with open('tournament_players.json', 'w', encoding='utf-8') as outfile:
            json.dump(players, outfile, indent=4, sort_keys=True)
    
    def LoadSmashGGPlayer(self, user, player):
        player_obj = {}

        if user is not None:
            player_obj["smashgg_id"] = user["id"]
            player_obj["smashgg_slug"] = user["slug"]
            player_obj["full_name"] = user["name"]

            if user["authorizations"] is not None:
                for authorization in user["authorizations"]:
                    player_obj[authorization["type"].lower()] = authorization["externalUsername"]
            
            if user["location"] is not None:
                if user["location"]["city"] is not None:
                    player_obj["city"] = user["location"]["city"]
                if user["location"]["country"] is not None:
                    player_obj["country"] = user["location"]["country"]

            if user["images"] is not None:
                if len(user["images"]) > 0:
                    player_obj["smashgg_image"] = user["images"][0]["url"]

        if player is not None:
            player_obj["name"] = player["gamerTag"]
            player_obj["org"] = player["prefix"]

            # character usage, mains
            if player["sets"] is not None and \
            player["sets"]["nodes"] is not None:
                selections = Counter()

                for set_ in player["sets"]["nodes"]:
                    if set_["games"] is None:
                        continue
                    for game in set_["games"]:
                        if game["selections"] is None:
                            continue
                        for selection in game["selections"]:
                            if selection.get("entrant"):
                                if selection.get("entrant").get("participants"):
                                    if len(selection.get("entrant").get("participants")) > 0:
                                        if selection.get("entrant").get("participants") is None:
                                            continue
                                        if selection.get("entrant").get("participants")[0] is None:
                                            continue
                                        if selection.get("entrant").get("participants")[0]["player"] is None:
                                            continue
                                        participant_id = selection.get("entrant").get("participants")[0]["player"]["id"]
                                        if player["id"] == participant_id:
                                            if selection["selectionValue"] is not None:
                                                selections[selection["selectionValue"]] += 1
                
                mains = []
                
                most_common = selections.most_common(1)

                for character in selections.most_common(2):
                    if(character[1] > most_common[0][1]/3.0):
                        found = next((c for c in self.smashgg_character_data["character"] if c["id"] == character[0]), None)
                        if found:
                            mains.append(characters[found["name"]])
                
                if len(mains) > 0:
                    player_obj["mains"] = mains
        
        countries = self.countries_json
        cities = self.cities_json

        # match state
        if "country" in player_obj.keys() and player_obj["country"] is not None:
            country = next(
                (c for c in countries if remove_accents_lower(c["name"]) == remove_accents_lower(player_obj["country"])),
                None
            )

            if country is not None:
                player_obj["country_code"] = country["iso2"]

                if "city" in player_obj.keys() and player_obj["city"] is not None:
                    # State explicit?
                    split = player_obj["city"].split(" ")

                    for part in split:
                        state = next(
                            (st for st in country["states"] if remove_accents_lower(st["state_code"]) == remove_accents_lower(part)),
                            None
                        )
                        if state is not None:
                            player_obj["state"] = state["state_code"]
                            break

                    if "state" not in player_obj.keys() or player_obj["state"] is None:
                        # no, so get by City
                        city = next(
                            (c for c in cities if remove_accents_lower(c["name"]) == remove_accents_lower(player_obj["city"])
                            and c["country_code"] == player_obj["country_code"]),
                            None
                        )

                        if city is not None:
                            player_obj["state"] = city["state_code"]
        
        return player_obj
    
    def LoadPlayersFromSmashGGTournamentProgress(self, n):
        self.downloadDialogue.setValue(int(n))

        if n == 100:
            self.downloadDialogue.setMaximum(0)
            self.downloadDialogue.setValue(0)
    
    def LoadPlayersFromSmashGGTournamentFinished(self):
        self.downloadDialogue.close()
    
    def LoadSetsFromSmashGGTournamentClicked(self):
        text, okPressed = QInputDialog.getText(self, "Get sets","Tournament slug:", QLineEdit.Normal, "")
        if okPressed:
            self.LoadSetsFromSmashGGTournament(text)
    
    def LoadSetsFromSmashGGTournament(self, slug):
        if slug is None or slug == "":
            slug = "tournament/ultimate-xanadu-online-384/event/ultimate-singles"

        r = requests.post(
            'https://api.smash.gg/gql/alpha',
            headers={
                'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
            },
            json={
                'query': '''
                query evento($eventSlug: String!) {
                    event(slug: $eventSlug) {
                        tournament {
                            streamQueue {
                                sets {
                                    id
                                    fullRoundText
                                    slots {
                                        entrant {
                                            participants {
                                                gamerTag
                                            }                                        
                                        }
                                    }
                                }
                                stream {
                                    streamName
                                    streamSource
                                }
                            }
                        }
                        sets(page: 1, perPage: 32, sortType: MAGIC, filters: {state: 2}) {
                            nodes {
                                id
                                fullRoundText
                                slots {
                                    entrant {
                                        participants {
                                            gamerTag
                                        }                                        
                                    }
                                }
                            }
                        }
                    }
                }''',
                'variables': {
                    "eventSlug": slug
                },
            }
        )
        resp = json.loads(r.text)

        if resp is None or \
        resp.get("data") is None or \
        resp["data"].get("event") is None or \
        resp["data"]["event"].get("sets") is None:
            print(resp)
        
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Stream", "Set", "Player 1", "Player 2"])

        streamSets = resp["data"]["event"]["tournament"]["streamQueue"]
        sets = resp["data"]["event"]["sets"]["nodes"]

        print(streamSets)

        if streamSets is not None:
            for s in streamSets:
                model.appendRow([
                    QStandardItem(s["stream"]["streamName"]),
                    QStandardItem(s["sets"][0]["fullRoundText"]),
                    QStandardItem(s["sets"][0]["slots"][0]["entrant"]["participants"][0]["gamerTag"]),
                    QStandardItem(s["sets"][0]["slots"][1]["entrant"]["participants"][0]["gamerTag"]),
                    QStandardItem(str(s["sets"][0]["id"]))
                ])

        for s in sets:
            model.appendRow([
                QStandardItem(""),
                QStandardItem(s["fullRoundText"]),
                QStandardItem(s["slots"][0]["entrant"]["participants"][0]["gamerTag"]),
                QStandardItem(s["slots"][1]["entrant"]["participants"][0]["gamerTag"]),
                QStandardItem(str(s["id"]))
            ])

        self.smashGGSetSelecDialog = QDialog(self)
        self.smashGGSetSelecDialog.setWindowTitle("Selecione um set")
        self.smashGGSetSelecDialog.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        self.smashGGSetSelecDialog.setLayout(layout)

        self.smashggSetSelectionItemList = QTableView()
        layout.addWidget(self.smashggSetSelectionItemList)
        self.smashggSetSelectionItemList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.smashggSetSelectionItemList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.smashggSetSelectionItemList.setModel(model)
        self.smashggSetSelectionItemList.setColumnHidden(4, True)
        self.smashggSetSelectionItemList.setColumnHidden(5, True)
        self.smashggSetSelectionItemList.horizontalHeader().setStretchLastSection(True)
        self.smashggSetSelectionItemList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.smashggSetSelectionItemList.resizeColumnsToContents()

        btOk = QPushButton("OK")
        layout.addWidget(btOk)
        btOk.clicked.connect(self.LoadPlayersFromSmashGGSet)

        self.smashGGSetSelecDialog.show()
    
    def LoadPlayersFromSmashGGSet(self):
        row = self.smashggSetSelectionItemList.selectionModel().selectedRows()[0].row()

        # Set phase name
        self.tournament_phase.setCurrentText(self.smashggSetSelectionItemList.model().index(row, 1).data())

        # Fetch set players
        setId = self.smashggSetSelectionItemList.model().index(row, 4).data()

        r = requests.post(
            'https://api.smash.gg/gql/alpha',
            headers={
                'Authorization': 'Bearer'+self.settings["SMASHGG_KEY"],
            },
            json={
                'query': '''
                query set($setId: ID!) {
                    set(id: $setId) {
                        slots {
                            entrant {
                                participants {
                                    user {
                                        id
                                        slug
                                        name
                                        authorizations(types: [TWITTER]) {
                                            type
                                            externalUsername
                                        }
                                        location {
                                            city
                                            country
                                        }
                                        images(type: "profile") {
                                            url
                                        }
                                    }
                                    player {
                                        id
                                        gamerTag
                                        prefix
                                        sets(page: 1, perPage: 3) {
                                            nodes {
                                                games {
                                                    selections {
                                                        entrant {
                                                            participants {
                                                                player {
                                                                    id
                                                                }
                                                            }
                                                        }
                                                        selectionValue
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }''',
                'variables': {
                    "setId": setId
                },
            }
        )
        resp = json.loads(r.text)

        user = resp["data"]["set"]["slots"][0]["entrant"]["participants"][0]["user"]
        player = resp["data"]["set"]["slots"][0]["entrant"]["participants"][0]["player"]
        player_obj = self.LoadSmashGGPlayer(user, player)

        self.player_layouts[0].SetFromPlayerObj(player_obj)

        user = resp["data"]["set"]["slots"][1]["entrant"]["participants"][0]["user"]
        player = resp["data"]["set"]["slots"][1]["entrant"]["participants"][0]["player"]
        player_obj = self.LoadSmashGGPlayer(user, player)

        self.player_layouts[1].SetFromPlayerObj(player_obj)

        self.smashGGSetSelecDialog.close()

class PlayerColumn():
    def __init__(self, parent, id, inverted=False):
        super().__init__()

        self.parent = parent
        self.id = id

        self.group_box = QGroupBox()
        self.group_box.setStyleSheet("QGroupBox{padding-top:0px;}")
        self.group_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.layout_grid = QGridLayout()
        self.group_box.setLayout(self.layout_grid)
        self.layout_grid.setVerticalSpacing(0)

        self.group_box.setFont(self.parent.font_small)

        pos_labels = 0
        pos_forms = 1
        text_alignment = Qt.AlignRight|Qt.AlignVCenter

        if inverted:
            pos_labels = 1
            pos_forms = 0
            text_alignment = Qt.AlignLeft|Qt.AlignVCenter

        nick_label = QLabel("Player")
        nick_label.setFont(self.parent.font_small)
        nick_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(nick_label, 0, pos_labels)
        self.player_name = QLineEdit()
        self.layout_grid.addWidget(self.player_name, 0, pos_forms)
        self.player_name.setMinimumWidth(100)
        self.player_name.setFont(self.parent.font_small)
        self.player_name.textChanged.connect(self.AutoExportName)

        prefix_label = QLabel("Prefix")
        prefix_label.setFont(self.parent.font_small)
        prefix_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(prefix_label, 1, pos_labels)
        self.player_org = QLineEdit()
        self.layout_grid.addWidget(self.player_org, 1, pos_forms)
        self.player_org.setFont(self.parent.font_small)
        self.player_org.textChanged.connect(self.AutoExportName)
        self.player_org.setMinimumWidth(100)

        real_name_label = QLabel("Name")
        real_name_label.setFont(self.parent.font_small)
        real_name_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(real_name_label, 2, pos_labels)
        self.player_real_name = QLineEdit()
        self.layout_grid.addWidget(self.player_real_name, 2, pos_forms)
        self.player_real_name.setFont(self.parent.font_small)
        self.player_real_name.textChanged.connect(self.AutoExportRealName)
        self.player_real_name.setMinimumWidth(100)

        player_twitter_label = QLabel("Twitter")
        player_twitter_label.setFont(self.parent.font_small)
        player_twitter_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_twitter_label, 3, pos_labels)
        self.player_twitter = QLineEdit()
        self.layout_grid.addWidget(self.player_twitter, 3, pos_forms)
        self.player_twitter.setFont(self.parent.font_small)
        self.player_twitter.editingFinished.connect(self.AutoExportTwitter)
        self.player_twitter.setMinimumWidth(100)

        location_layout = QHBoxLayout()
        self.layout_grid.addLayout(location_layout, 0, pos_forms+2)

        player_country_label = QLabel("Location")
        player_country_label.setFont(self.parent.font_small)
        player_country_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_country_label, 0, pos_labels+2)
        self.player_country = QComboBox()
        self.player_country.addItem("")
        for i, country in enumerate(self.parent.countries):
            item = self.player_country.addItem(QIcon("country_icon/"+country.lower()+".png"), country)
            self.player_country.setItemData(i+1, country)
        self.player_country.setEditable(True)
        location_layout.addWidget(self.player_country)
        self.player_country.setMinimumWidth(75)
        self.player_country.setFont(self.parent.font_small)
        self.player_country.lineEdit().setFont(self.parent.font_small)
        self.player_country.currentIndexChanged.connect(self.AutoExportCountry)
        self.player_country.currentTextChanged.connect(self.LoadStateOptions)
        self.player_country.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        self.player_state = QComboBox()
        self.player_state.setEditable(True)
        location_layout.addWidget(self.player_state)
        self.player_state.setMinimumWidth(60)
        self.player_state.setFont(self.parent.font_small)
        self.player_state.lineEdit().setFont(self.parent.font_small)
        self.player_state.currentIndexChanged.connect(self.AutoExportCountry)
        self.player_state.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        player_character_label = QLabel("Character")
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
        self.player_character.setMinimumWidth(120)
        self.player_character.setFont(self.parent.font_small)
        self.player_character.lineEdit().setFont(self.parent.font_small)
        self.player_character.currentIndexChanged.connect(self.AutoExportCharacter)
        self.player_character.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        player_character_color_label = QLabel("Skin")
        player_character_color_label.setFont(self.parent.font_small)
        player_character_color_label.setAlignment(text_alignment)
        self.layout_grid.addWidget(player_character_color_label, 2, pos_labels+2)
        self.player_character_color = QComboBox()
        self.layout_grid.addWidget(self.player_character_color, 2, pos_forms+2, 2, 1)
        self.player_character_color.setIconSize(QSize(48, 48))
        self.player_character_color.setMinimumHeight(48)
        self.player_character_color.setMinimumWidth(120)
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
    
    def LoadStateOptions(self, text):
        self.player_state.clear()
        self.player_state.addItem("")
        for s in self.parent.countries[self.player_country.currentText()]:
            self.player_state.addItem(str(s))
    
    def AutoExportName(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportName()

    def ExportName(self):
        with open('out/p'+str(self.id)+'_name.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(self.player_name.text())
        with open('out/p'+str(self.id)+'_name+prefix.txt', 'w', encoding='utf-8') as outfile:
            if len(self.player_org.text()) > 0:
                outfile.write(self.player_org.text()+" | "+self.player_name.text())
            else:
                outfile.write(self.player_name.text())
        with open('out/p'+str(self.id)+'_prefix.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(self.player_org.text())
        with open('out/p'+str(self.id)+'_twitter.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(self.player_twitter.text())
    
    def AutoExportRealName(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportRealName()
    
    def ExportRealName(self):
        with open('out/p'+str(self.id)+'_real_name.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(self.player_real_name.text())
    
    def AutoExportTwitter(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportTwitter()
    
    def ExportTwitter(self):
        try:
            def myFun(self, progress_callback):
                removeFileIfExists('out/p'+str(self.id)+'_picture.png')

                if(self.player_twitter.displayText() != None and self.player_twitter.displayText() != ""):
                    r = requests.get("http://unavatar.now.sh/twitter/"+self.player_twitter.text().split("/")[-1], stream=True)
                    if r.status_code == 200:
                        with open('out/p'+str(self.id)+'_twitter_picture.png', 'wb') as f:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, f)
                
                if self.player_obj.get("smashgg_image", None) is not None:
                    r = requests.get(self.player_obj["smashgg_image"], stream=True)
                    if r.status_code == 200:
                        with open('out/p'+str(self.id)+'_smashgg_picture.png', 'wb') as f:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, f)
            
            worker = Worker(myFun, *{self})
            self.parent.threadpool.start(worker)
        except Exception as e:
            print(e)
    
    def AutoExportCountry(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportCountry()

    def ExportCountry(self):
        try:
            def myFun(self, progress_callback):
                removeFileIfExists("out/p"+str(self.id)+"_country_flag.png")
                removeFileIfExists("out/p"+str(self.id)+"_country.txt")
                removeFileIfExists("out/p"+str(self.id)+"_state.png")

                with open('out/p'+str(self.id)+'_country.txt', 'w', encoding='utf-8') as outfile:
                    outfile.write(self.player_country.currentText())
                
                if self.player_country.currentText().lower() != "":
                    shutil.copy(
                        "country_icon/"+self.player_country.currentText().lower()+".png",
                        "out/p"+str(self.id)+"_country_flag.png"
                    )
                
                with open('out/p'+str(self.id)+'_state.txt', 'w', encoding='utf-8') as outfile:
                    outfile.write(self.player_state.currentText())
                if(self.player_state.currentText() != ""):
                    r = requests.get("https://raw.githubusercontent.com/joaorb64/tournament_api/sudamerica/state_flag/"+
                        self.player_country.currentText().upper()+"/"+
                        self.player_state.currentText().upper()+".png", stream=True)
                    if r.status_code == 200:
                        with open('out/p'+str(self.id)+'_state.png', 'wb') as f:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, f)
            
            worker = Worker(myFun, *{self})
            self.parent.threadpool.start(worker)
        except Exception as e:
            print(e)
    
    def AutoExportState(self):
        if self.parent.settings.get("autosave") == True:
            self.ExportState()

    def ExportState(self):
        try:
            with open('out/p'+str(self.id)+'_state.txt', 'w', encoding='utf-8') as outfile:
                outfile.write(self.player_state.currentText())
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
            removeFileIfExists("out/p"+str(self.id)+"_character_portrait.png")
            shutil.copy(
                "character_icon/chara_0_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_portrait.png"
            )
        except Exception as e:
            print(e)
        try:
            removeFileIfExists("out/p"+str(self.id)+"_character_big.png")
            shutil.copy(
                "character_icon/chara_1_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_big.png"
            )
        except Exception as e:
            print(e)
        try:
            removeFileIfExists("out/p"+str(self.id)+"_character_full.png")
            shutil.copy(
                "character_icon/chara_3_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_full.png"
            )
        except Exception as e:
            print(e)
        try:
            removeFileIfExists("out/p"+str(self.id)+"_character_full-halfres.png")
            shutil.copy(
                "character_icon/chara_3_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+"-halfres.png",
                "out/p"+str(self.id)+"_character_full-halfres.png"
            )
        except Exception as e:
            print(e)
        try:
            removeFileIfExists("out/p"+str(self.id)+"_character_stockicon.png")
            shutil.copy(
                "character_icon/chara_2_"+self.parent.character_to_codename[self.player_character.currentText()]+"_0"+str(self.player_character_color.currentIndex())+".png",
                "out/p"+str(self.id)+"_character_stockicon.png"
            )
        except Exception as e:
            print(e)
    
    def AutocompleteSelected(self, selected):
        if type(selected) == QModelIndex:
            index = int(selected.sibling(selected.row(), 2).data())
        elif type(selected) == int:
            index = selected-1
            if index < 0:
                index = None
        else:
            index = None

        if index is not None:
            self.selectPRPlayer(index)
    
    def selectPRPlayer(self, index):
        player = self.parent.mergedPlayers[index]
        self.SetFromPlayerObj(player)
    
    def SetFromPlayerObj(self, player):
        self.player_name.setText(player["name"])
        self.player_org.setText(player.get("org", ""))
        self.player_real_name.setText(player.get("full_name", ""))
        self.player_twitter.setText(player.get("twitter", ""))

        self.player_obj = player

        if player.get("country_code") is not None and player.get("country_code")!="null":
            self.player_country.setCurrentIndex(list(self.parent.countries.keys()).index(player.get("country_code"))+1)
            if player.get("state") is not None and player.get("state")!="null":
                self.player_state.setCurrentIndex(list(self.parent.countries[player.get("country_code")]).index(player.get("state"))+1)
            else:
                self.player_state.setCurrentIndex(0)
        else:
            self.player_country.setCurrentIndex(0)
        
        if player.get("mains") is not None and len(player["mains"]) > 0 and player["mains"][0] != "":
            self.player_character.setCurrentIndex(list(self.parent.stockIcons.keys()).index(player.get("mains", [""])[0])+1)
            self.player_character_color.setCurrentIndex(player.get("skins", [0])[0])
        else:
            self.player_character.setCurrentIndex(list(self.parent.stockIcons.keys()).index("Random")+1)
            self.player_character_color.setCurrentIndex(player.get("skins", [0])[0])
            #self.player_character.setCurrentIndex(0)
        
        self.AutoExportTwitter()
    
    def selectPRPlayerBySmashGGId(self, smashgg_id):
        index = next((i for i, p in enumerate(self.parent.allplayers["players"]) if str(p.get("smashgg_id", None)) == smashgg_id), None)
        if index is not None:
            self.selectPRPlayer(index)


App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec_())