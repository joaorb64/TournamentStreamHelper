import os
import sys
from loguru import logger

is_in_bundle = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def TSHResolve(filename):
    return os.path.join(sys._MEIPASS if is_in_bundle else '.', filename)
