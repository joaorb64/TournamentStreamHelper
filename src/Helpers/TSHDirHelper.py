import sys
from pathlib import Path

is_in_bundle = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
current_dir = Path.cwd()

def TSHResolve(filename):
    fullPath = Path(current_dir, filename)
    if not fullPath.exists() and is_in_bundle:
        fullPath = Path(sys._MEIPASS, filename)

    return str(fullPath.resolve())
