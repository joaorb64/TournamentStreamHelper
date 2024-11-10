from os import path
import sys

is_in_bundle = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def TSHResolve(filename):
    return path.join(sys._MEIPASS if is_in_bundle else '.', filename)
