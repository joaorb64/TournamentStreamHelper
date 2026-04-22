from qtpy.QtWidgets import *
from qtpy.QtCore import *

class CompleterProxyModel(QSortFilterProxyModel):
    def __init__(self, completer, parent=None):
        super().__init__(parent)
        self._completer = completer

    _SEARCH_KEYS = {"gamerTag", "prefix", "name", "twitter"}

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index0 = self.sourceModel().index(sourceRow, 0, sourceParent)
        prefix = self._completer.local_completion_prefix.lower()
        data = self.sourceModel().data(index0, Qt.ItemDataRole.UserRole)

        if data:
            for k in self._SEARCH_KEYS:
                v = data.get(k)
                if isinstance(v, str) and prefix in v.lower():
                    return True
            return False

        display = self.sourceModel().data(index0)
        return isinstance(display, str) and prefix in display.lower()


class TSHCustomPlayerCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.local_completion_prefix = ""
        self.source_model = None
        self._proxy_model = CompleterProxyModel(self)

    def setModel(self, model):
        self.source_model = model
        self._proxy_model.setSourceModel(model)
        super().setModel(self._proxy_model)

    def splitPath(self, path):
        self.local_completion_prefix = path
        self._proxy_model.invalidateFilter()
        return [""]