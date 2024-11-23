import sys
from pathlib import Path
from loguru import logger

is_in_bundle = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
current_dir = Path.cwd()

def TSHResolve(full_path):
    full_file = Path(current_dir, full_path)
    file_does_exist = full_file.exists()
    if not file_does_exist and is_in_bundle:
        full_file = Path(sys._MEIPASS, full_path)

    full_file = str(full_file.resolve())
    logger.info(f"load: {full_file} [full_path={full_path}, exists={file_does_exist}, cwd={current_dir}]")
    return full_file
