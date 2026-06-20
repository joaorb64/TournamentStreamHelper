from qtpy.QtCore import QObject, Signal


class _AppSignals(QObject):
    # message, is_error
    status_message = Signal(str, bool)


app_signals = _AppSignals()
