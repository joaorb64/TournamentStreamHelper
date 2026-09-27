import os
import re
from ..StateManager import StateManager


class TSHDynamicExport:

    # Callers hold dataLock and run on the Qt main thread; no additional lock needed here.
    _exported: dict[str, set[str]] = {}

    def ExportCustomPlayerData(player_name: str, path: str):
        sanitized = re.sub(r"[,/|;:<>\\?*]", "_", player_name)

        matched_folder = None
        base_dir = "./user_data/custom_player_export"

        if os.path.isdir(base_dir):
            for entry in os.scandir(base_dir):
                if entry.is_dir() and entry.name.upper() == sanitized.upper():
                    matched_folder = entry.path
                    break

        previous_stems = TSHDynamicExport._exported.get(path, set())

        if matched_folder is None:
            for stem in previous_stems:
                StateManager.Unset(f"{path}.{stem}")
            TSHDynamicExport._exported.pop(path, None)
            return

        current_stems = set()

        for entry in os.scandir(matched_folder):
            if not entry.is_file():
                continue

            stem, ext = os.path.splitext(entry.name)
            if not stem:
                continue
            ext = ext.lower()

            match ext:
                case ".txt" | ".json" | ".csv" | ".xml" | ".html" | ".md":
                    try:
                        with open(entry.path, "r", encoding="utf-8") as f:
                            value = f.read()
                    except (OSError, UnicodeDecodeError):
                        continue
                case _:
                    value = entry.path

            StateManager.Set(f"{path}.{stem}", value)
            current_stems.add(stem)

        for stem in previous_stems - current_stems:
            StateManager.Unset(f"{path}.{stem}")

        TSHDynamicExport._exported[path] = current_stems
