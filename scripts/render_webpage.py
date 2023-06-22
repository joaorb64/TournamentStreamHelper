import os
from time import sleep
from PySide6 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebEngineCore

os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"


class PageShotter(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super(PageShotter, self).__init__(parent)

        settings = QtWebEngineWidgets.QWebEngineView.settings(self)

        for attr in (QtWebEngineCore.QWebEngineSettings.WebAttribute.PluginsEnabled,
                     QtWebEngineCore.QWebEngineSettings.WebAttribute.ScreenCaptureEnabled,
                     QtWebEngineCore.QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
                     QtWebEngineCore.QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls):
            settings.setAttribute(attr, True)

        self.loadFinished.connect(self.save)
        self.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.resize(1920, 1080)
        self.timer = QtCore.QTimer()
        self.show()
        self.current = []
        self.in_out = []

    def work(self):
        self.current = self.in_out[0]

        print(self.current)

        self.in_out = self.in_out[1:]

        # self.setUrl(QtCore.QUrl(self.current[0]))
        self.load(QtCore.QUrl(self.current[0]))

    @QtCore.Slot(bool)
    def save(self, finished):
        if finished:
            self.timer = QtCore.QTimer()
            self.timer.singleShot(8000, self.saveScreenshot)
        else:
            print("Error")

    def saveScreenshot(self):
        size = self.contentsRect()
        print(u"width: %d,hight: %d" % (size.width(), size.height()))
        img = QtGui.QImage(size.width(), size.height(),
                           QtGui.QImage.Format_ARGB32)
        painter = QtGui.QPainter(img)
        self.render(painter, QtCore.QPoint(0, 0),
                    QtCore.QRect(0, 0, 1920, 1080))
        painter.end()
        filename = self.current[1]
        if img.save(filename):
            filepath = os.path.join(os.path.dirname(__file__), filename)
            print(u"success:%s" % filepath)
        else:
            print(u"fail")

        if len(self.in_out) > 0:
            self.work()
        else:
            self.close()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    in_out = []

    for path, subdirs, files in os.walk(os.path.abspath("../layout/")):
        if not os.path.isdir("renders"):
            os.mkdir("renders")
        for name in files:
            if name.endswith(".html"):
                print(os.path.join(path, name))
                in_out.append([
                    f"file:///{os.path.join(path, name).replace(os.path.sep, '/')}",
                    path.replace(os.path.sep, '/')+"/" +
                    name.split(".")[0]+"_preview.png"
                ])
    print(in_out)

    shotter = PageShotter()
    shotter.in_out = in_out
    shotter.work()

    # shotter.close()
    app.exec()
