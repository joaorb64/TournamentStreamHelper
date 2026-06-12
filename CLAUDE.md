# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

TournamentStreamHelper (TSH) is a PyQt6 desktop application for managing stream overlays at fighting game tournaments. It fetches bracket data from StartGG/ParryGG (tries to fetch from providers in a normalized way), maintains a central state, and pushes updates via WebSocket to HTML overlay templates that are captured in OBS, while also outputting individual files and a json state.

## Running the application

```bash
# Linux/Mac
./TSH.sh

# Or directly (requires Python 3.13+ with dependencies installed)
python main.py

# Install dependencies manually
pip install -r dependencies/requirements.txt
```

The app must be run from the project root — it resolves paths relative to `./` (e.g. `./user_data/settings.json`, `./layout/`, `./out/`).

## Stage strike React app

```bash
cd stage_strike_app
npm install
npm start        # dev server on port 3000
npm run build    # production build
```

## Architecture

### Entry point & event loop

`main.py` creates a `QEventLoop` backed by `qasync` so that PyQt6 and `asyncio` share one event loop. `src/TournamentStreamHelper.py` is imported at module level and immediately instantiates `App` (QApplication) and the loguru logging setup — this is a side-effect-on-import pattern. `Window` (QMainWindow) is created afterwards in `main.py`.

### State management

`StateManager` (src/StateManager.py) is the single source of truth. It holds a class-level `state` dict that mirrors to JSON files under `out/` on every change. It uses `deepdiff` to compute deltas and emits Qt signals (`state_updated`, `state_big_change`) so UI widgets and the web server can react. Use `StateManager.SaveBlock()` as a context manager when making many mutations to batch the write.

`SettingsManager` (src/SettingsManager.py) is a simpler class-level store persisted to `user_data/settings.json`. Access via `SettingsManager.Get(key, default)` / `SettingsManager.Set(key, value)` with dot-path keys.

Both managers use all-static/class-method patterns (no instances).

### Web server & overlay communication

`TSHWebServer.py` runs a Flask + Flask-SocketIO server in a `QThread`. It serves the `layout/` HTML files as static files and exposes REST and WebSocket endpoints. When `StateManager` emits `state_updated`, the web server broadcasts the delta over SocketIO to all connected overlays.

Layout HTML files (in `layout/`) include `/include/globals.js` which handles SocketIO connection, receives state diffs, and merges them into a local copy of the state. Character and game assets are served from `user_data/games/<game_id>/`.

### Tournament data providers

`src/TournamentDataProvider/TournamentDataProvider.py` defines the abstract base class. `StartGGDataProvider` and `ParryGGDataProvider` implement it. GraphQL queries for StartGG are stored as `.txt` files alongside the provider. `TSHTournamentDataProvider.py` is the Qt widget that owns the active provider instance and orchestrates fetching.

### UI widgets

Each major panel is its own `QWidget` subclass (`TSHScoreboardWidget`, `TSHPlayerListWidget`, `TSHCommentaryWidget`, etc.). They read/write `StateManager` directly and connect to its signals for updates. `TSHScoreboardManager` coordinates multiple scoreboard slots.

### Asset pipeline

`TSHGameAssetManager` loads game definitions from `assets/characters.json` and resolves character art from `user_data/games/<game_id>/`. The `thumbnail/` module generates preview images. `TSHAssetDownloader` handles downloading asset packs from GitHub releases.

## Key paths

| Path | Purpose |
|---|---|
| `out/` | Live state JSON files read by overlay HTML |
| `user_data/settings.json` | Persisted user settings |
| `user_data/games/` | Downloaded character/game asset packs |
| `layout/` | HTML overlay templates |
| `include/globals.js` | Shared JS for overlays (SocketIO, state helpers) |
| `assets/characters.json` | Master character/game definitions |
| `logs/` | App logs (tsh.log, tsh-error.log, tsh-crash.log) |

## Layout development

To test HTML overlays locally in Chrome, launch Chrome with `--allow-file-access-from-files`, open the layout `.html` file, set device toolbar to 1920×1080, and use DevTools for live CSS editing.
