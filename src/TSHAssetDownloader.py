from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from src.TSHGameAssetManager import TSHGameAssetManager
from src.Workers import Worker

import requests
import shutil
import py7zr
import urllib
import json
import os


class TSHAssetDownloader(QObject):
    instance: "TSHAssetDownloader" = None

    def __init__(self) -> None:
        super().__init__()
        self.threadpool = QThreadPool()

    def UiMounted(self):
        pass

    def DownloadAssets(self):
        assets = self.DownloadAssetsFetch()

        if assets is None:
            return

        self.preDownloadDialogue = QDialog()
        self.preDownloadDialogue.setWindowTitle("Download assets")
        self.preDownloadDialogue.setWindowModality(
            Qt.WindowModality.ApplicationModal)
        self.preDownloadDialogue.setLayout(QVBoxLayout())
        self.preDownloadDialogue.resize(1400, 500)
        self.preDownloadDialogue.show()

        select = QComboBox()
        selectProxy = QSortFilterProxyModel()
        selectProxy.setSourceModel(select.model())
        select.model().setParent(selectProxy)
        selectProxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        select.setModel(selectProxy)
        select.setEditable(True)
        select.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        select.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.preDownloadDialogue.layout().addWidget(select)

        model = QStandardItemModel()

        proxyModel = QSortFilterProxyModel()
        proxyModel.setSourceModel(model)
        proxyModel.setFilterKeyColumn(-1)
        proxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        def filterList(text):
            proxyModel.setFilterFixedString(text)

        searchBar = QLineEdit()
        searchBar.setPlaceholderText("Filter...")
        self.preDownloadDialogue.layout().addWidget(searchBar)
        searchBar.textEdited.connect(filterList)

        downloadList = QTableView()
        self.preDownloadDialogue.layout().addWidget(downloadList)
        downloadList.setSortingEnabled(True)
        downloadList.setSelectionBehavior(QAbstractItemView.SelectRows)
        downloadList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        downloadList.setModel(proxyModel)
        downloadList.verticalHeader().hide()
        downloadList.horizontalHeader().setStretchLastSection(True)
        downloadList.setWordWrap(True)
        downloadList.resizeColumnsToContents()
        downloadList.resizeRowsToContents()

        for i, game in enumerate(assets):
            select.addItem(assets[game]["name"], i)

        select.model().sort(0)

        def ReloadGameAssets(index=None):
            nonlocal self

            index = select.currentData()

            if index == None:
                index = select.currentIndex()

            model.clear()
            model.setHorizontalHeaderLabels([
                "game", "asset_id", "Name", "Installed version", "Latest version", "Size", "Stage data", "Eyesight data", "Description", "Credits"
            ])
            downloadList.hideColumn(0)
            downloadList.hideColumn(1)
            downloadList.horizontalHeader().setStretchLastSection(True)
            downloadList.setWordWrap(True)
            downloadList.resizeColumnsToContents()
            downloadList.resizeRowsToContents()
            downloadList.setStyleSheet(
                "QTableView::item { padding: 6px 0px; }")

            key = list(assets.keys())[index]

            hasBaseFiles = TSHGameAssetManager.instance.games.get(
                key, {}).get("assets", {}).get("base_files", None) != None

            sortedKeys = list(assets[key]["assets"].keys())
            sortedKeys.sort(
                key=lambda x: chr(0) if x == "base_files" else x)

            for asset in sortedKeys:
                dlSize = "{:.2f}".format(sum(
                    [f.get("size", 0) for f in list(
                        assets[key]["assets"][asset]["files"].values())]
                )/1024/1024) + " MB"

                currVersion = str(TSHGameAssetManager.instance.games.get(key, {}).get(
                    "assets", {}).get(asset, {}).get("version", ""))

                version = str(assets[key]["assets"][asset].get("version"))

                if currVersion != version and currVersion != "":
                    version += " [!]"

                items = [
                    QStandardItem(key),
                    QStandardItem(asset),
                    QStandardItem(assets[key]["assets"][asset].get("name")),
                    QStandardItem(currVersion),
                    QStandardItem(version),
                    QStandardItem(dlSize),
                    QStandardItem("☑" if assets[key]["assets"][asset].get(
                        "has_stage_data", False) else ""),
                    QStandardItem("☑" if assets[key]["assets"][asset].get(
                        "has_eyesight_data", False) else ""),
                    QStandardItem(assets[key]["assets"]
                                  [asset].get("description")),
                    QStandardItem(assets[key]["assets"][asset].get("credits"))
                ]

                items[3].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                items[4].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                items[5].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                items[6].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                items[7].setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                model.appendRow(items)

                if not hasBaseFiles and asset != "base_files":
                    for col in range(model.columnCount()):
                        item = model.item(model.rowCount()-1, col)
                        item.setEnabled(False)
                        item.setSelectable(False)

                if currVersion == version:
                    for col in range(model.columnCount()):
                        model.item(model.rowCount()-1,
                                   col).setBackground(QColor(0, 255, 0, 120))

                if currVersion != version and currVersion != "":
                    for col in range(model.columnCount()):
                        model.item(model.rowCount()-1,
                                   col).setBackground(QColor(255, 255, 0, 120))

            downloadList.horizontalHeader().setStretchLastSection(True)
            # downloadList.resizeColumnsToContents()
            downloadList.resizeRowsToContents()
            downloadList.setColumnWidth(2, 200)
            downloadList.setColumnWidth(3, 120)
            downloadList.setColumnWidth(4, 120)
            downloadList.setColumnWidth(5, 120)
            downloadList.setColumnWidth(6, 120)
            downloadList.setColumnWidth(7, 120)
            downloadList.setColumnWidth(8, 400)

        self.reloadDownloadsList = ReloadGameAssets
        select.activated.connect(ReloadGameAssets)
        ReloadGameAssets(0)

        TSHGameAssetManager.instance.signals.onLoadAssets.connect(
            ReloadGameAssets)

        btOk = QPushButton("Download")
        self.preDownloadDialogue.layout().addWidget(btOk)

        def DownloadStart():
            nonlocal self

            if len(downloadList.selectionModel().selectedRows()) == 0:
                return

            row = downloadList.selectionModel().selectedRows()[0].row()
            game = downloadList.model().index(row, 0).data()
            key = downloadList.model().index(row, 1).data()

            filesToDownload = assets[game]["assets"][key]["files"]

            for f in filesToDownload:
                filesToDownload[f]["path"] = "https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/" + \
                    filesToDownload[f]["name"]
                filesToDownload[f]["extractpath"] = "./user_data/games/"+game

            self.downloadDialogue = QProgressDialog(
                "Downloading assets", "Cancel", 0, 100)
            self.downloadDialogue.setMinimumWidth(1200)
            self.downloadDialogue.setWindowModality(
                Qt.WindowModality.WindowModal)
            self.downloadDialogue.show()
            worker = Worker(self.DownloadAssetsWorker, *
                            [list(filesToDownload.values())])
            worker.signals.progress.connect(self.DownloadAssetsProgress)
            worker.signals.finished.connect(self.DownloadAssetsFinished)
            self.threadpool.start(worker)

        btOk.clicked.connect(DownloadStart)

    def DownloadAssetsFetch(self):
        assets = None
        try:
            response = requests.get(
                "https://raw.githubusercontent.com/joaorb64/StreamHelperAssets/main/assets.json")
            assets = json.loads(response.text)
        except Exception as e:
            messagebox = QMessageBox()
            messagebox.setText("Failed to fetch github:\n"+str(e))
            messagebox.exec()
        return assets

    def DownloadAssetsWorker(self, files, progress_callback):
        totalSize = sum(f["size"] for f in files)
        downloaded = 0

        for f in files:
            with open("user_data/games/"+f["name"], 'wb') as downloadFile:
                print("Downloading "+f["name"])
                progress_callback.emit("Downloading "+f["name"]+"...")

                response = urllib.request.urlopen(f["path"])

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

        filenames = ["./user_data/games/"+f["name"] for f in files]
        mergedFile = "./user_data/games/"+files[0]["name"].split(".")[0]+'.7z'

        is7z = next((f for f in files if ".7z" in f["name"]), None)

        if is7z:
            with open(mergedFile, 'ab') as outfile:
                for fname in filenames:
                    with open(fname, 'rb') as infile:
                        outfile.write(infile.read())

            print("Extracting "+mergedFile)
            progress_callback.emit("Extracting "+mergedFile)

            with py7zr.SevenZipFile(mergedFile, 'r') as parent_zip:
                parent_zip.extractall(files[0]["extractpath"])

            for f in files:
                os.remove("./user_data/games/"+f["name"])

            os.remove(mergedFile)
        else:
            for f in files:
                if os.path.isfile(f["extractpath"]+"/"+f["name"]):
                    os.remove(f["extractpath"]+"/"+f["name"])
                shutil.move("./user_data/games/"+f["name"], f["extractpath"])

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
        TSHGameAssetManager.instance.LoadGames()


TSHAssetDownloader.instance = TSHAssetDownloader()
