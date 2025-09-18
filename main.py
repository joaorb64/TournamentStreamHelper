#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import src
import multiprocessing
import signal
import sys
import os
import asyncio
from qasync import run, QEventLoop
from functools import partial
os.environ["QT_API"] = "PyQt6"


async def main(event_loop):
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    future = asyncio.Future()

    window = src.Window(event_loop)
    if hasattr(src.App, "aboutToQuit"):
        getattr(src.App, "aboutToQuit").connect(
            partial(close_future, future, event_loop))

    try:
        event_loop.add_signal_handler(signal.SIGINT, lambda: window.close())
        event_loop.add_signal_handler(signal.SIGTERM, lambda: window.close())
    except NotImplementedError:  # windows...
        pass

    await future
    if isinstance(future.result(), int):
        return future.result()

    return 0


if __name__ == '__main__':
    # Pyinstaller fix
    multiprocessing.freeze_support()

    try:
        loop = QEventLoop()
        asyncio.set_event_loop(loop)
        sys.exit(loop.run_until_complete(main(loop)))
    except asyncio.exceptions.CancelledError:
        sys.exit(0)
