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

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        self.page().setBackgroundColor(QtCore.Qt.transparent)

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
        img.fill(QtGui.QColor(255, 192, 203))
        painter = QtGui.QPainter(img)
        # Generate a light diagonal stripes background
        stripe_color = QtGui.QColor(240, 240, 240)
        painter.setPen(QtGui.QPen(stripe_color, 2))
        for i in range(0, size.width() + size.height(), 20):
            painter.drawLine(i, 0, 0, i)

        # Check for a background image
        bg_image = None

        game_screenshot = self.current[1].rsplit("_preview")[0]+".png"
        if os.path.isfile(game_screenshot):
            bg_image = game_screenshot
            print("Found background image")
        else:
            default_game_screenshot = os.path.join(
                os.path.dirname(self.current[1]), "default.png")

            if os.path.isfile(default_game_screenshot):
                bg_image = default_game_screenshot
                print("Found default background image")

        if bg_image:
            bg = QtGui.QImage(bg_image)
            scaled_bg = bg.scaled(
                1920, 1080, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            x_offset = (1920 - scaled_bg.width()) // 2
            y_offset = (1080 - scaled_bg.height()) // 2
            painter.drawImage(QtCore.QRect(x_offset, y_offset,
                              scaled_bg.width(), scaled_bg.height()), scaled_bg)

        # Render html
        self.render(painter, QtCore.QPoint(0, 0),
                    QtCore.QRect(0, 0, 1920, 1080))

        painter.end()
        filename = self.current[1]

        # Resize the image to 720p
        img_720p = img.scaled(
            1280, 720,
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )

        if img_720p.save(filename):
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
        for name in files:
            if name.endswith(".html"):
                print(os.path.join(path, name))
                in_out.append([f"file:///{os.path.join(path, name).replace(os.path.sep, '/')}",
                               path.replace(os.path.sep, '/')+"/" +
                               name.split(".")[0]+"_preview.png"
                               ])
    print(in_out)

    shotter = PageShotter()
    shotter.in_out = in_out
    shotter.work()

    # shotter.close()
    app.exec()
