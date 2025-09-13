# https://www.pythonguis.com/widgets/qcolorbutton-a-color-selector-tool-for-pyqt/

from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *


class TSHColorButton(QToolButton):
    '''
    Custom Qt Widget to show a chosen color.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).
    '''

    colorChanged = Signal(object)

    def __init__(self, *args, color=None, disable_right_click=False, enable_alpha_selection=False, ignore_same_color=True, **kwargs):
        super(TSHColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self._default = color
        self.disable_right_click = disable_right_click
        self.enable_alpha_selection = enable_alpha_selection
        self.ignore_same_color = ignore_same_color
        self.pressed.connect(self.onColorPicker)

        # Set the initial/default state.
        self.setColor(self._default)

    def setColor(self, color):
        if self.ignore_same_color:
            if color != self._color:
                self._color = color
                self.colorChanged.emit(color)
        else:
            self._color = color
            self.colorChanged.emit(color)

        if self._color:
            self.setStyleSheet("QToolButton { background-color: %s; }" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        '''
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        '''
        dlg = QColorDialog(self)
        if self.enable_alpha_selection:
            dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if self._color:
            dlg.setCurrentColor(QColor(self._color))

        if dlg.exec_():
            if self.enable_alpha_selection:
                self.setColor(dlg.currentColor().name(QColor.NameFormat.HexArgb))
            else:
                self.setColor(dlg.currentColor().name(QColor.NameFormat.HexRgb))

    def mousePressEvent(self, e):
        if not self.disable_right_click and e.button() == Qt.RightButton:
            self.setColor(self._default)

        return super(TSHColorButton, self).mousePressEvent(e)
