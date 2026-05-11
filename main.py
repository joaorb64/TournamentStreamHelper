#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import src
import multiprocessing
import signal
import sys
import os
import asyncio
from qasync import QEventLoop
os.environ["QT_API"] = "PyQt6"


if __name__ == '__main__':
    # Pyinstaller fix
    multiprocessing.freeze_support()

    try:
        loop = QEventLoop(src.App)
        asyncio.set_event_loop(loop)
        window = src.Window(loop)
        try:
            loop.add_signal_handler(signal.SIGINT, lambda: window.close())
            loop.add_signal_handler(signal.SIGTERM, lambda: window.close())
        except NotImplementedError:  # windows...
            pass

        # To run synchronously, you would do something like the following:
        # sys.exit(src.App.exec())

        # Since this is a QEventLoop, afaik it will run App.exec() in the background.
        with loop:
            loop.run_forever()

    except asyncio.exceptions.CancelledError:
        sys.exit(255)
    except RuntimeError:
        sys.exit(255)

