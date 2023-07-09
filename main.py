#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import src
import multiprocessing
import sys
import os
os.environ["QT_API"] = "pyside6"

if __name__ == '__main__':
    # Pyinstaller fix
    multiprocessing.freeze_support()

    window = src.Window()
    sys.exit(src.App.exec_())