import functools
import threading

from qtpy.QtCore import *


def invokeSlot(meth, *args):
    """
    This will invoke a QObject's slot using the auto connection type, in the same
    way that it would be triggered from a signal. The auto connection type will either:

    - execute immediately if we are in the QObject's native thread.
    - be queued for execution if we are in a different thread.

    This lets us call other methods in a thread-safe way without having to bother with connecting
    a signal and cleaning it up. WARNING: If the invocation is queued, the effects of the invoked method
    may or may not be applied at any given time and if the caller is expecting this function
    to execute immediately there will likely be a race condition.

    Here is an example of a concrete call to invokeMethod() that this function constructs::

        QMetaObject.invokeMethod(self.tshTdp, 'SetTournament',
            Q_ARG(str, "https://start.gg/"+deep_get(userSet, "event.slug"))
        )

    :param meth: The bound object method to call via slot mechanism
    :param args: The function arguments to pass in.
    """
    obj = getattr(meth, '__self__', None)
    meth_name = getattr(meth, '__name__', None)

    if not obj:
        raise ValueError(f"The provided method {meth} does not have a bound object instance.")

    if not meth_name:
        raise ValueError(f"The provided method {meth} does not have a __name__")

    QMetaObject.invokeMethod(
        obj,
        meth_name,
        *(Q_ARG(type(arg), arg) for arg in args)
    )


class GuiExecutor(QObject):
    _invoke = Signal(object)
    _invokeWithResult = Signal(object, dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Autoconnection makes this almost-free if the gui thread uses it.
        self._invoke.connect(self._run, Qt.ConnectionType.AutoConnection)
        self._invokeWithResult.connect(self._run, Qt.ConnectionType.AutoConnection)

    @Slot(object)
    @Slot(object, dict)
    def _run(self, fn, resultHolder=None):
        if resultHolder is not None:
            try:
                resultHolder["result"] = fn()
            except Exception as e:
                resultHolder["result"] = None
                resultHolder["exc"] = e

            if ((doneEvent := resultHolder.get("done", None)) is not None
                    and isinstance(doneEvent, threading.Event)):
                doneEvent.set()
        else:
            fn()

    def __call__(self, fn, result_holder=None):
        if result_holder is None:
            self._invoke.emit(fn)
        else:
            self._invokeWithResult.emit(fn, result_holder)

    def run_sync(self, fn):
        result_holder = {'done': threading.Event()}
        # Fine if this throws exception... we want to re-throw anyway.
        self(fn, result_holder)
        result_holder['done'].wait()

        if (exc := result_holder.get("exc", None)) is not None:
            raise exc
        else:
            return result_holder["result"]


gui_executor: GuiExecutor = None
def init_gui_executor():
    global gui_executor
    gui_executor = GuiExecutor(None)


def gui_thread_async(fn):
    """
    Helper decorator that automatically dispatches the target function to the gui thread. Note that there
    is no waiting and any changes caused by the dispatched function likely will not happen in the flow of the
    calling thread. If that is desired, look at `gui_thread_sync`
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if gui_executor is None:
            raise ValueError("Can't marshal action to gui thread if the gui executor has not been initialized.")

        return gui_executor(lambda: fn(*args, **kwargs))
    return wrapper


def gui_thread_sync(fn):
    """
    Helper decorator that automatically dispatches the target function to the gui thread. Note that this
    function will block the calling thread until enough GUI cycles have completed to process the dispatched event.
    This is useful if it is desirable for changes to propagate before progressing, but it is slower than the async
    fire-and-forget version of this method.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if gui_executor is None:
            raise ValueError("Can't marshal action to gui thread if the gui executor has not been initialized.")

        return gui_executor.run_sync(lambda: fn(*args, **kwargs))

    return wrapper

