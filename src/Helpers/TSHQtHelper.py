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

