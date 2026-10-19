"""Game controller managing puzzle state, moves, undo stack, and clue feedback."""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from ..models.cell import CellState
from ..models.board import Board
from ..core.validator import Validator, ValidationResult
from ..core.generator import Generator, Difficulty, Puzzle


@dataclass
class ClueStatus:
    target: int
    current: int
    is_match: bool
    is_overflow: bool


@dataclass
class FleetProgress:
    length: int
    target: int
    current: int
    is_satisfied: bool


class GameController:
    """Manages the interactive game state for Battleship Solitaire."""

    def __init__(self, difficulty: Difficulty = Difficulty.EASY, seed: Optional[int] = None):
        self.difficulty = difficulty
        self.puzzle: Optional[Puzzle] = None
        self.board: Optional[Board] = None
        self.undo_stack: List[Tuple[int, int, CellState]] = []
        self.is_won: bool = False
        self.new_game(difficulty, seed=seed)

    def new_game(self, difficulty: Optional[Difficulty] = None, seed: Optional[int] = None) -> None:
        """Starts a new puzzle."""
        if difficulty is not None:
            self.difficulty = difficulty
        self.puzzle = Generator.generate_puzzle(difficulty=self.difficulty, seed=seed)
        self.board = self.puzzle.board
        self.undo_stack.clear()
        self.is_won = False

    def restart_game(self) -> None:
        """Resets the current board back to the initial puzzle state with initial hints."""
        if self.puzzle is None or self.board is None:
            return
        self.board.clear()
        for (r, c), state in self.puzzle.hints.items():
            self.board.set_cell(r, c, state)
        self.undo_stack.clear()
        self.is_won = False

    def is_hint_cell(self, r: int, c: int) -> bool:
        """Returns True if the cell is an immutable starting hint."""
        if self.puzzle is None:
            return False
        return (r, c) in self.puzzle.hints

    def handle_left_click(self, r: int, c: int) -> bool:
        """
        Left click action:
        - If locked hint: no-op.
        - If SHIP -> UNKNOWN.
        - If UNKNOWN or WATER -> SHIP.
        Returns True if state changed.
        """
        if self.board is None or self.is_hint_cell(r, c) or self.is_won:
            return False

        curr = self.board.get_cell(r, c)
        new_state = CellState.UNKNOWN if curr == CellState.SHIP else CellState.SHIP

        self.undo_stack.append((r, c, curr))
        self.board.set_cell(r, c, new_state)
        self._check_auto_win()
        return True

    def handle_right_click(self, r: int, c: int) -> bool:
        """
        Right click action:
        - If locked hint: no-op.
        - If WATER -> UNKNOWN.
        - If UNKNOWN or SHIP -> WATER.
        Returns True if state changed.
        """
        if self.board is None or self.is_hint_cell(r, c) or self.is_won:
            return False

        curr = self.board.get_cell(r, c)
        new_state = CellState.UNKNOWN if curr == CellState.WATER else CellState.WATER

        self.undo_stack.append((r, c, curr))
        self.board.set_cell(r, c, new_state)
        self._check_auto_win()
        return True

    def undo(self) -> bool:
        """Reverts the last player move."""
        if not self.undo_stack or self.board is None or self.is_won:
            return False
        r, c, prev_state = self.undo_stack.pop()
        self.board.set_cell(r, c, prev_state)
        self._check_auto_win()
        return True

    def give_hint(self) -> Optional[Tuple[int, int, CellState]]:
        """
        Finds a non-hint cell that is either UNKNOWN or incorrectly filled,
        and sets it to the solution state. Returns (r, c, state) or None.
        """
        if self.board is None or self.puzzle is None or self.is_won:
            return None

        # Prefer fixing an incorrect cell first
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                if self.is_hint_cell(r, c):
                    continue
                curr = self.board.get_cell(r, c)
                correct = self.puzzle.solution[r][c]
                if curr != CellState.UNKNOWN and curr != correct:
                    self.undo_stack.append((r, c, curr))
                    self.board.set_cell(r, c, correct)
                    self._check_auto_win()
                    return (r, c, correct)

        # Otherwise find an UNKNOWN cell to reveal
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                if self.is_hint_cell(r, c):
                    continue
                curr = self.board.get_cell(r, c)
                correct = self.puzzle.solution[r][c]
                if curr == CellState.UNKNOWN:
                    self.undo_stack.append((r, c, curr))
                    self.board.set_cell(r, c, correct)
                    self._check_auto_win()
                    return (r, c, correct)

        return None

    def get_row_clue_status(self, r: int) -> ClueStatus:
        target = self.board.row_clues[r]
        current = self.board.count_row_ships(r)
        return ClueStatus(
            target=target,
            current=current,
            is_match=current == target,
            is_overflow=current > target,
        )

    def get_col_clue_status(self, c: int) -> ClueStatus:
        target = self.board.col_clues[c]
        current = self.board.count_col_ships(c)
        return ClueStatus(
            target=target,
            current=current,
            is_match=current == target,
            is_overflow=current > target,
        )

    def get_fleet_progress(self) -> List[FleetProgress]:
        """Returns progress for each ship type in descending order of length."""
        if self.board is None:
            return []
        found_ships, _, _ = Validator.validate_ships(self.board)
        result = []
        for length in sorted(self.board.fleet_spec.keys(), reverse=True):
            target = self.board.fleet_spec[length]
            current = found_ships.get(length, 0)
            result.append(
                FleetProgress(
                    length=length,
                    target=target,
                    current=current,
                    is_satisfied=current == target,
                )
            )
        return result

    def validate_current(self) -> ValidationResult:
        if self.board is None:
            return ValidationResult(is_valid=False, is_complete=False)
        return Validator.validate_solution(self.board)

    def _check_auto_win(self) -> bool:
        if self.board is None:
            return False
        val_res = Validator.validate_solution(self.board)
        if val_res.is_complete:
            self.is_won = True
            return True
        self.is_won = False
        return False
