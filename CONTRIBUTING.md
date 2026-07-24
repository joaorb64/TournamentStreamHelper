# Contributing to TournamentStreamHelper

## Tech Stack Overview

| Layer | Technology |
|-------|-----------|
| Desktop UI | Python 3.10+ with PyQt6 |
| UI layout files | Qt Designer XML (`.ui` files) |
| State management | `StateManager.py` (custom, signal-based) |
| Web component | React 19 + Redux (stage strike feature only) |
| Executable build | PyInstaller |

---

## Setting Up the Dev Environment

### Prerequisites

- Python 3.10+
- Qt Designer (bundled with `pyqt6-tools`, or standalone via Qt installation)

### Install dependencies

```bash
pip install -r dependencies/requirements.txt
```

### Run the app

```bash
python main.py
```

You do **not** need to compile the executable to develop or test — running from Python is the standard dev workflow.

---

## Project Structure

```
TournamentStreamHelper/
├── main.py                  # Entry point
├── src/
│   ├── layout/              # Qt Designer .ui files (UI definitions)
│   │   ├── TSHTournamentInfo.ui
│   │   ├── TSHScoreboardPlayer.ui
│   │   ├── TSHCommentary.ui
│   │   └── ...
│   ├── TSHTournamentInfoWidget.py   # Python widget classes
│   ├── TSHScoreboardPlayerWidget.py
│   ├── TSHCommentaryWidget.py
│   ├── StateManager.py      # Central state (read/write/signals)
│   └── ...
├── assets/                  # Icons, characters, rulesets, etc.
├── stage_strike_app/        # React web app (stage strike only)
├── dependencies/
│   ├── requirements.txt     # Python dependencies
│   └── tsh.spec             # PyInstaller build spec
└── .github/workflows/       # CI/CD (build + release)
```

The naming convention is consistent: `TSHFoo.ui` is loaded and managed by `TSHFooWidget.py`.

---

## Adding a New UI Field

### Step 1 — Edit the `.ui` file in Qt Designer

1. Open the relevant `src/layout/TSH*.ui` file in Qt Designer.
2. Drag in a new widget (e.g. `QLineEdit`, `QSpinBox`, `QCheckBox`).
3. Set a descriptive `objectName` in the Properties panel (e.g. `myNewField`).
4. Save the file.

### Step 2 — Wire the widget up in the Python class

Open the matching `src/TSH*Widget.py` file. Follow the pattern of existing fields:

**Reading state on load:**
```python
self.ui.myNewField.setText(StateManager.get_state("my_new_field") or "")
```

**Saving state on change:**
```python
self.ui.myNewField.editingFinished.connect(
    lambda: StateManager.set_state("my_new_field", self.ui.myNewField.text())
)
```

Common signal-to-use mapping:

| Widget | Signal | Value accessor |
|--------|--------|----------------|
| `QLineEdit` | `editingFinished` | `.text()` |
| `QSpinBox` | `valueChanged` | `.value()` |
| `QCheckBox` | `stateChanged` | `.isChecked()` |
| `QDateEdit` | `dateChanged` | `.date().toString(...)` |
| `QPushButton` | `clicked` | — |

### Step 3 — Expose the value to layouts (optional)

If the field value should be available to OBS browser source overlays, add the state key to the output in the relevant scoreboard/state export logic. Search for similar keys in `StateManager.py` to find the right place.

---

## Building the Executable

> For pull request contributions, you typically don't need to build the executable — maintainers handle releases via CI.

If you need to build locally:

```bash
# 1. Generate Qt translation files (requires pyside6-lrelease)
pyside6-lrelease <path/to/*.ts files>

# 2. Build the executable
pyinstaller --noconfirm ./dependencies/tsh.spec

# Output: dist/TSH.exe
```

The CI pipeline (`.github/workflows/build_app.yml`) runs these steps automatically on push.

---

## Making a Pull Request

1. Fork the repository and create a branch from `main`.
2. Make your changes and test locally with `python main.py`.
3. Keep commits focused — one logical change per commit.
4. Open a PR against `main` with a clear description of what the change does and why.

---

## Tips

- The `StateManager` is the single source of truth. All UI fields should read from and write to it — never store widget state separately.
- `.ui` files are XML and can be diff'd normally in PRs; prefer Qt Designer over hand-editing them.
- The `stage_strike_app/` React app has its own `package.json` and is built separately with `npm run build` if you need to modify the stage strike web UI.
