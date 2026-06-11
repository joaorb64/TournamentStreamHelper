
import math

from loguru import logger
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

from .TSHGameAssetManager import TSHGameAssetManager
from .Helpers.TSHQtHelper import assert_gui_thread
from .Helpers.TSHVersionHelper import add_beta_label
from .SettingsManager import SettingsManager
from .StateManager import StateManager


class TSHIndividualGameTrackerSignals(QObject):
    stageResultsUpdate = Signal(int, int)
    syncCharToMain = Signal(int, int, int, object)  # team, player, char_slot, char_data


class TSHIndividualGameTracker(QWidget):
    def __init__(self, scoreboard_number, parent=None):
        super().__init__()

        self._layout = QVBoxLayout()
        self.signals = TSHIndividualGameTrackerSignals(self)
        self.players_per_team = 1
        self.chars_per_player = 1
        self.best_of = 0
        self._syncing_chars = False

        label = QLabel(
            text=add_beta_label(
                QApplication.translate(
                    "app",
                    "Individual game data").upper(),
                "game_tracker"
            )
        )

        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setBold(True)
        label.setFont(label_font)
        self.scoreboard_number = scoreboard_number
        self._layout.addWidget(label)
        self.setLayout(self._layout)
        self.stage_widget_list = []
        self.stage_order_list_widget = QWidget()

    @assert_gui_thread
    def CreateStage(self, index=0):
        """ Creates a new stage in the list of stage results. """

        def uncheck_buttons_if_true(value, list_buttons):
            if value:
                for button in list_buttons:
                    button.setChecked(False)

        stageWidget = QWidget()
        outerLayout = QVBoxLayout()
        outerLayout.setContentsMargins(0, 0, 0, 0)
        outerLayout.setSpacing(2)

        topRow = QWidget()
        stageLayout = QHBoxLayout()
        stageLayout.setContentsMargins(0, 0, 0, 0)

        gameLabel = QLabel()
        gameLabel.setText(QApplication.translate("app", "Game {0}").format(index + 1))

        stageMenu = QComboBox()
        stageMenu.setMaximumWidth(300)
        stageMenu.setEditable(True)
        stageMenu.setObjectName(f"stageMenu_{index}")
        stageMenu.setModel(TSHGameAssetManager.instance.stageModelWithBlank)
        stageMenu.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        stageMenu.completer().setCompletionMode(QCompleter.PopupCompletion)
        stageTeam1Check = QPushButton()
        stageTeam1Check.setMaximumWidth(40)
        stageTeam1Check.setObjectName(f"stageTeam1Check_{index}")
        stageTeam1Check.setText(QApplication.translate("app", "T{0}").format(1))
        stageTeam1Check.setCheckable(True)
        stageTeam2Check = QPushButton()
        stageTeam2Check.setMaximumWidth(40)
        stageTeam2Check.setObjectName(f"stageTeam2Check_{index}")
        stageTeam2Check.setText(QApplication.translate("app", "T{0}").format(2))
        stageTeam2Check.setCheckable(True)
        stageTieCheck = QPushButton()
        stageTieCheck.setMaximumWidth(40)
        stageTieCheck.setObjectName(f"stageTieCheck_{index}")
        stageTieCheck.setText(QApplication.translate("app", "Tie"))
        stageTieCheck.setCheckable(True)

        # Add Logic
        stageMenu.currentIndexChanged.connect(
            lambda: [
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index+1}", stageMenu.currentData()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t1_win", stageTeam1Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t2_win", stageTeam2Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.tie", stageTieCheck.isChecked()),
                self._SyncStageToStrike(index, stageMenu.currentData()),
            ]
        )
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t1_win", False)
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t2_win", False)
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.tie", False)

        stageTeam1Check.clicked.connect(
            lambda: [
                uncheck_buttons_if_true(stageTeam1Check.isChecked(), [stageTeam2Check, stageTieCheck]),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t1_win", stageTeam1Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t2_win", stageTeam2Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.tie", stageTieCheck.isChecked()),
                self.StageResultsChanged()
            ]
        )
        stageTeam2Check.clicked.connect(
            lambda: [
                uncheck_buttons_if_true(stageTeam2Check.isChecked(), [stageTeam1Check, stageTieCheck]),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t1_win", stageTeam1Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t2_win", stageTeam2Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.tie", stageTieCheck.isChecked()),
                self.StageResultsChanged()
            ]
        )
        stageTieCheck.clicked.connect(
            lambda: [
                uncheck_buttons_if_true(stageTieCheck.isChecked(), [stageTeam1Check, stageTeam2Check]),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t1_win", stageTeam1Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.t2_win", stageTeam2Check.isChecked()),
                StateManager.Set(f"score.{self.scoreboard_number}.stages.{index + 1}.tie", stageTieCheck.isChecked()),
                self.StageResultsChanged()
            ]
        )

        stageLayout.addWidget(gameLabel)
        if StateManager.Get("game.has_stages", False): # Only add stage column if the game supports stage
            stageLayout.addWidget(stageMenu)
        stageLayout.addWidget(stageTeam1Check)
        stageLayout.addWidget(stageTieCheck)
        stageLayout.addWidget(stageTeam2Check)

        topRow.setLayout(stageLayout)
        outerLayout.addWidget(topRow)

        charRow = self._CreateCharRow(index)
        outerLayout.addWidget(charRow)

        stageWidget.setLayout(outerLayout)
        return stageWidget

    def _CreateCharRow(self, index):
        """Creates the per-game character picker row for the given game index."""
        charRow = QWidget()
        charRow.setObjectName(f"charRow_{index}")
        charLayout = QHBoxLayout()
        charLayout.setContentsMargins(0, 0, 0, 0)
        charLayout.setSpacing(4)

        has_chars = (
            TSHGameAssetManager.instance.characterModel.rowCount() > 1
            and self.players_per_team > 0
            and self.chars_per_player > 0
        )
        charRow.setVisible(has_chars)

        for t in range(2):
            if t == 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setFrameShadow(QFrame.Shadow.Sunken)
                charLayout.addWidget(sep)

            teamWidget = QWidget()
            teamLayout = QVBoxLayout()
            teamLayout.setContentsMargins(0, 0, 0, 0)
            teamLayout.setSpacing(1)

            for p in range(self.players_per_team):
                playerContainer = QWidget()
                playerContainerLayout = QVBoxLayout()
                playerContainerLayout.setContentsMargins(0, 0, 0, 0)
                playerContainerLayout.setSpacing(1)

                raw_name = StateManager.Get(
                    f"score.{self.scoreboard_number}.team.{t+1}.player.{p+1}.mergedName", "") or ""
                display_name = raw_name.strip() if raw_name.strip() else f"P{p+1}"
                nameLbl = QLabel(display_name)
                nameLbl.setObjectName(f"nameLabel_{index}_{t}_{p}")
                nameLbl.setFont(QFont(nameLbl.font().family(), 8))
                nameLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                playerContainerLayout.addWidget(nameLbl)

                playerRow = QWidget()
                playerLayout = QHBoxLayout()
                playerLayout.setContentsMargins(0, 0, 0, 0)
                playerLayout.setSpacing(2)

                for c in range(self.chars_per_player):
                    combo = QComboBox()
                    combo.setEditable(True)
                    combo.setObjectName(f"charCombo_{index}_{t}_{p}_{c}")
                    combo.setModel(TSHGameAssetManager.instance.characterModel)
                    combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
                    combo.completer().setCompletionMode(QCompleter.PopupCompletion)
                    combo.setIconSize(QSize(24, 24))
                    combo.setFixedHeight(28)
                    combo.setMinimumWidth(80)
                    combo.setFont(QFont(combo.font().family(), 9))
                    combo.lineEdit().setFont(QFont(combo.font().family(), 9))

                    combo.currentIndexChanged.connect(
                        lambda _idx, t=t, p=p, c=c, combo=combo: self._OnCharChanged(index, t, p, c, combo)
                    )
                    playerLayout.addWidget(combo)

                playerRow.setLayout(playerLayout)
                playerContainerLayout.addWidget(playerRow)
                playerContainer.setLayout(playerContainerLayout)
                teamLayout.addWidget(playerContainer)

            teamWidget.setLayout(teamLayout)
            charLayout.addWidget(teamWidget)

        charLayout.addStretch()
        charRow.setLayout(charLayout)
        return charRow

    def _OnCharChanged(self, game_idx, team, player, char_slot, combo):
        data = combo.currentData()
        path = f"score.{self.scoreboard_number}.stages.{game_idx+1}.team.{team+1}.player.{player+1}.character"
        existing = StateManager.Get(path, {}) or {}
        if data:
            existing[char_slot + 1] = data
        else:
            existing.pop(char_slot + 1, None)
        StateManager.Set(path, existing)

        # Sync to main selector if this is the current (last) game
        if game_idx == len(self.stage_widget_list) - 1 and not self._syncing_chars:
            self._syncing_chars = True
            try:
                self.signals.syncCharToMain.emit(team, player, char_slot, data)
            finally:
                self._syncing_chars = False

    def RefreshNameLabel(self, team_0idx, player_0idx, name):
        """Updates name labels in all game rows for the given team/player."""
        display = name.strip() if name and name.strip() else f"P{player_0idx + 1}"
        for game_idx, widget in enumerate(self.stage_widget_list):
            lbl = widget.findChild(QLabel, f"nameLabel_{game_idx}_{team_0idx}_{player_0idx}")
            if lbl:
                lbl.setText(display)

    def SetStageCount(self, stage_count=0):
        """Resets the game tracker completely and starts with a single row. Called on new set / game asset load."""

        self._layout.removeWidget(self.stage_order_list_widget)
        self.stage_widget_list = []
        self.stage_order_list_layout = QVBoxLayout()
        self.stage_order_list_widget = QWidget()
        self.stage_order_list_widget.setLayout(self.stage_order_list_layout)
        StateManager.Set(f"score.{self.scoreboard_number}.stages", {})
        self.best_of = stage_count
        if SettingsManager.Get('general.disable_individual_game_tracker', True):
            self.setVisible(False)
        else:
            self.setVisible(True)
            self._AddGameRow()
        self._layout.addWidget(self.stage_order_list_widget)

    def UpdateBestOf(self, stage_count=0):
        """Updates the best-of cap without resetting rows. Called when the spinbox changes."""
        self.best_of = stage_count

    def _AddGameRow(self):
        """Appends one new game row to the tracker, pre-filled with current set-level characters."""
        idx = len(self.stage_widget_list)
        widget = self.CreateStage(idx)
        self.stage_widget_list.append(widget)
        self.stage_order_list_layout.addWidget(widget)
        self._CopySetLevelCharactersToGame(idx)

    def _RemoveLastRow(self):
        """Removes the last game row and clears its state."""
        if not self.stage_widget_list:
            return
        widget = self.stage_widget_list.pop()
        self.stage_order_list_layout.removeWidget(widget)
        widget.deleteLater()
        idx = len(self.stage_widget_list)  # index of removed row
        StateManager.Unset(f"score.{self.scoreboard_number}.stages.{idx+1}")

    def _EnsureCorrectRowCount(self):
        """Trims excess trailing empty rows (keeps exactly 1), then adds one if all rows have results."""
        if not self.stage_widget_list:
            return

        # Trim trailing rows with no result, keeping at least 1 empty row at the end
        while len(self.stage_widget_list) > 1 and self._get_game_winner(len(self.stage_widget_list) - 1) == -1:
            # Second-to-last row also empty? Remove the last row.
            if self._get_game_winner(len(self.stage_widget_list) - 2) == -1:
                self._RemoveLastRow()
            else:
                break

        t1_wins = len(self.GetWonStages(0))
        t2_wins = len(self.GetWonStages(1))
        wins_needed = math.ceil(self.best_of / 2) if self.best_of > 0 else 999
        if t1_wins >= wins_needed or t2_wins >= wins_needed:
            return
        if self.best_of > 0 and len(self.stage_widget_list) >= self.best_of:
            return
        all_have_results = all(
            self._get_game_winner(i) != -1
            for i in range(len(self.stage_widget_list))
        )
        if all_have_results:
            self._AddGameRow()

    @assert_gui_thread
    def GetFirstEmptyStage(self, start_idx=None) -> int:
        idx = start_idx if start_idx is not None else 0

        while idx < len(self.stage_widget_list):
            game_winner = self._get_game_winner(idx)
            if game_winner == -1:
                return idx
            idx += 1

        return -1

    @assert_gui_thread
    def GetWonStages(self, team) -> list[int]:
        idx = len(self.stage_widget_list)-1

        return [
            idx
            for idx
            in range(len(self.stage_widget_list))
            if self._get_game_winner(idx) == (team + 1)
        ]

    def _get_game_winner(self, game_idx):
        """
        -1 = unreported, 0 = draw, 1 = team 1, 2 = team 2
        """
        current_stage_widget = self.stage_widget_list[game_idx]
        stageTeam1Check: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTeam1Check_{game_idx}")
        stageTeam2Check: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTeam2Check_{game_idx}")
        stageTieCheck: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTieCheck_{game_idx}")

        if stageTeam1Check is None:
            raise RuntimeError(f"stageTeam1Check_{game_idx} not found")
        if stageTeam2Check is None:
            raise RuntimeError(f"stageTeam2Check_{game_idx} not found")
        if stageTieCheck is None:
            raise RuntimeError(f"stageTieCheck_{game_idx} not found")

        if stageTieCheck.isChecked(): return 0
        elif stageTeam1Check.isChecked(): return 1
        elif stageTeam2Check.isChecked(): return 2
        else: return -1

    @Slot(int, int)
    @assert_gui_thread
    def UpdateScore(self, team, new_value):
        """Responds to the score being modified in a non-per-game context."""

        old_value = StateManager.Get(f"score.{self.scoreboard_number}.team.{team + 1}.score", 0)
        StateManager.Set(f"score.{self.scoreboard_number}.team.{team + 1}.score", new_value)

        logger.info(f"UpdateScore: old[{old_value}] new[{new_value}]")

        # Disable individual game tracker logic if ties were reported
        has_ties = False
        game_data = StateManager.Get(f"score.{self.scoreboard_number}.stages")
        for key in game_data.keys():
            if game_data[key].get("tie"):
                has_ties = True

        if has_ties:
            logger.warning("Disabling individual game tracker due to detected tie results.")
            return

        counter = old_value
        for _ in range(abs(new_value - old_value)):
            if new_value > old_value:
                self.IncrementScore(team)
                counter += 1
            else:
                self.DecrementScore(team, counter)
                counter -= 1

    def IncrementScore(self, team, current_stage=None):
        """Sets the next stage to be won by the provided team."""

        if not current_stage:
            current_stage = 0

        current_stage = self.GetFirstEmptyStage(current_stage)

        if current_stage == -1:
            logger.warning(f"Attempted to increment score for team {team+1}, but all stages are completed.")
            return

        logger.info(f"Setting a win for team {team+1} on game {current_stage}")

        if current_stage >= len(self.stage_widget_list):
            logger.warning(f"Attempted to increment score for team {team+1} on stage {current_stage+1}, but there are only {len(self.stage_widget_list)} stages.")

        current_stage_widget = self.stage_widget_list[current_stage]
        stageTeam1Check: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTeam1Check_{current_stage}")
        stageTeam2Check: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTeam2Check_{current_stage}")
        stageTieCheck: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTieCheck_{current_stage}")
        if team == 0:
            stageTeam1Check.setChecked(True)
            stageTeam2Check.setChecked(False)
        else:
            stageTeam2Check.setChecked(True)
            stageTeam1Check.setChecked(False)

        stageTieCheck.setChecked(False)
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{current_stage+1}.t1_win", stageTeam1Check.isChecked())
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{current_stage+1}.t2_win", stageTeam2Check.isChecked())
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{current_stage+1}.tie", stageTieCheck.isChecked())

        self._CopySetLevelCharactersToGame(current_stage)
        self._EnsureCorrectRowCount()

    def _CopySetLevelCharactersToGame(self, game_idx):
        """Copies current set-level character selections into a specific game's tracker slots."""
        if self._syncing_chars or game_idx >= len(self.stage_widget_list):
            return
        self._syncing_chars = True
        try:
            self._CopySetLevelCharactersToGameImpl(game_idx)
        finally:
            self._syncing_chars = False

    def _CopySetLevelCharactersToGameImpl(self, game_idx):
        for t in range(2):
            for p in range(self.players_per_team):
                char_data = StateManager.Get(
                    f"score.{self.scoreboard_number}.team.{t+1}.player.{p+1}.character", {}) or {}
                for c_key, char in char_data.items():
                    c = int(c_key) - 1
                    if c >= self.chars_per_player:
                        continue
                    combo: QComboBox = self.stage_widget_list[game_idx].findChild(
                        QComboBox, f"charCombo_{game_idx}_{t}_{p}_{c}")
                    if combo is None:
                        continue
                    codename = char.get("codename") if isinstance(char, dict) else None
                    if codename:
                        for row in range(TSHGameAssetManager.instance.characterModel.rowCount()):
                            item_data = TSHGameAssetManager.instance.characterModel.item(row).data(
                                Qt.ItemDataRole.UserRole)
                            if item_data and item_data.get("codename") == codename:
                                combo.setCurrentIndex(row)
                                break

    @assert_gui_thread
    def DecrementScore(self, team=None, original_score=None):
        """ Removes the last reported stage result. Optionally bounded to team. """

        won_stages = self.GetWonStages(team)

        if original_score and len(won_stages) < original_score:
            logger.warning(f"Failed to decrement score for team {team} because they have won fewer stages than their score. {len(won_stages)} < {original_score}")
            return

        current_stage = won_stages[-1]
        if current_stage == -1:
            logger.warning(f"Could not decrement score for team {team}, could not find a stage to clear.")
            return

        logger.info(f"Clearing result for stage {current_stage+1}")

        current_stage_widget = self.stage_widget_list[current_stage]
        stageTeam1Check: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTeam1Check_{current_stage}")
        stageTeam2Check: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTeam2Check_{current_stage}")
        stageTieCheck: QPushButton = current_stage_widget.findChild(QPushButton, f"stageTieCheck_{current_stage}")
        stageTeam1Check.setChecked(False)
        stageTeam2Check.setChecked(False)
        stageTieCheck.setChecked(False)
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{current_stage+1}.t1_win", stageTeam1Check.isChecked())
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{current_stage+1}.t2_win", stageTeam2Check.isChecked())
        StateManager.Set(f"score.{self.scoreboard_number}.stages.{current_stage+1}.tie", stageTieCheck.isChecked())
        self._EnsureCorrectRowCount()

    @assert_gui_thread
    def StageResultsChanged(self):
        team_1_score, team_2_score = 0, 0
        for i in range(len(self.stage_widget_list)):
            stageTeam1Check = self.stage_widget_list[i].findChild(QPushButton, f"stageTeam1Check_{i}")
            stageTeam2Check = self.stage_widget_list[i].findChild(QPushButton, f"stageTeam2Check_{i}")
            if stageTeam1Check.isChecked():
                team_1_score += 1
            if stageTeam2Check.isChecked():
                team_2_score += 1

        StateManager.Set(f"score.{self.scoreboard_number}.team.1.score", team_1_score)
        StateManager.Set(f"score.{self.scoreboard_number}.team.2.score", team_2_score)
        self.signals.stageResultsUpdate.emit(team_1_score, team_2_score)
        self._EnsureCorrectRowCount()

    @assert_gui_thread
    def SwapStageResults(self):
        for i in range(len(self.stage_widget_list)):
            stageTeam1Check = self.stage_widget_list[i].findChild(QPushButton, f"stageTeam1Check_{i}")
            stageTeam2Check = self.stage_widget_list[i].findChild(QPushButton, f"stageTeam2Check_{i}")
            stageTieCheck = self.stage_widget_list[i].findChild(QPushButton, f"stageTieCheck_{i}")
            team_1_old_state, team_2_old_state = stageTeam1Check.isChecked(), stageTeam2Check.isChecked()
            stageTeam1Check.setChecked(team_2_old_state)
            stageTeam2Check.setChecked(team_1_old_state)
            StateManager.Set(f"score.{self.scoreboard_number}.stages.{i+1}.t1_win", stageTeam1Check.isChecked()),
            StateManager.Set(f"score.{self.scoreboard_number}.stages.{i+1}.t2_win", stageTeam2Check.isChecked()),
            StateManager.Set(f"score.{self.scoreboard_number}.stages.{i+1}.tie", stageTieCheck.isChecked()),


    @assert_gui_thread
    def UpdateCharacterLayout(self, players_per_team, chars_per_player):
        """Rebuilds only the character picker rows when player/char counts change."""
        if self.players_per_team == players_per_team and self.chars_per_player == chars_per_player:
            return
        self.players_per_team = players_per_team
        self.chars_per_player = chars_per_player
        for i, stageWidget in enumerate(self.stage_widget_list):
            old = stageWidget.findChild(QWidget, f"charRow_{i}")
            if old:
                stageWidget.layout().removeWidget(old)
                old.deleteLater()
            stageWidget.layout().addWidget(self._CreateCharRow(i))

    @assert_gui_thread
    def SetPerGameData(self, games_data):
        """Populates stage, characters, and winner for each game from provider data."""
        StateManager.BlockSaving()
        # Expand rows to fit incoming data before iterating
        while len(self.stage_widget_list) < len(games_data):
            if self.best_of > 0 and len(self.stage_widget_list) >= self.best_of:
                break
            self._AddGameRow()
        for i, game in enumerate(games_data):
            if i >= len(self.stage_widget_list):
                break

            if game.get("stage_codename"):
                self.SetStage(i, game["stage_codename"])

            winner = game.get("winner")
            if winner in (1, 2):
                stageWidget = self.stage_widget_list[i]
                t1 = stageWidget.findChild(QPushButton, f"stageTeam1Check_{i}")
                t2 = stageWidget.findChild(QPushButton, f"stageTeam2Check_{i}")
                tie = stageWidget.findChild(QPushButton, f"stageTieCheck_{i}")
                if t1 and t2 and tie:
                    t1.setChecked(winner == 1)
                    t2.setChecked(winner == 2)
                    tie.setChecked(False)
                    StateManager.Set(f"score.{self.scoreboard_number}.stages.{i+1}.t1_win", winner == 1)
                    StateManager.Set(f"score.{self.scoreboard_number}.stages.{i+1}.t2_win", winner == 2)
                    StateManager.Set(f"score.{self.scoreboard_number}.stages.{i+1}.tie", False)

            for t, chars in enumerate([game.get("team1_chars") or [], game.get("team2_chars") or []]):
                for p, char_data in enumerate(chars):
                    if char_data is None:
                        continue
                    for c in range(self.chars_per_player):
                        combo: QComboBox = self.stage_widget_list[i].findChild(
                            QComboBox, f"charCombo_{i}_{t}_{p}_{c}")
                        if combo is None:
                            continue
                        codename = char_data.get("codename") if isinstance(char_data, dict) else None
                        if codename:
                            for row in range(TSHGameAssetManager.instance.characterModel.rowCount()):
                                item_data = TSHGameAssetManager.instance.characterModel.item(row).data(
                                    Qt.ItemDataRole.UserRole)
                                if item_data and item_data.get("codename") == codename:
                                    combo.setCurrentIndex(row)
                                    break
                        break  # one char per player slot from provider data

        self.StageResultsChanged()
        StateManager.ReleaseSaving()

    def _SyncStageToStrike(self, game_idx, stage_data):
        """When the last game row's stage changes, push it to stage_strike.selectedStage."""
        if game_idx == len(self.stage_widget_list) - 1:
            codename = stage_data.get("codename") if isinstance(stage_data, dict) else None
            StateManager.Set(f"score.{self.scoreboard_number}.stage_strike.selectedStage", codename)

    def SetStage(self, index=0, stage_codename=None):
        StateManager.BlockSaving()
        if self.stage_widget_list:
            target = self.findChild(QComboBox, f"stageMenu_{index}")
            if target is None:
                StateManager.ReleaseSaving()
                return
            if stage_codename:
                for i in range(1, TSHGameAssetManager.instance.stageModelWithBlank.rowCount()):
                    current_menu_item_data = TSHGameAssetManager.instance.stageModelWithBlank.item(i).data(Qt.ItemDataRole.UserRole)
                    if current_menu_item_data.get("codename") in stage_codename:
                        target.setCurrentIndex(i)
                        target.currentIndexChanged.emit(i)
            else:
                target.setCurrentIndex(0)
                target.currentIndexChanged.emit(0)

        StateManager.ReleaseSaving()

    def ResetAllStages(self):
        StateManager.BlockSaving()
        print(f"Reset all stages in the game tracker")
        if self.stage_widget_list:
            for index in range(len(self.stage_widget_list)):
                target = self.findChild(QComboBox, f"stageMenu_{index}")
                target.setCurrentIndex(0)
                target.currentIndexChanged.emit(0)
        StateManager.ReleaseSaving()
