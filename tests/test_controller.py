"""Tests for GameController and UI component logic."""
import unittest
import tkinter as tk

from src.models.cell import CellState
from src.core.generator import Difficulty
from src.ui.game_controller import GameController
from src.ui.app import BattleshipApp


class TestGameController(unittest.TestCase):
    def setUp(self):
        # Deterministic seed for reproducible testing
        self.controller = GameController(difficulty=Difficulty.EASY, seed=12345)

    def test_controller_initialization(self):
        self.assertEqual(self.controller.difficulty, Difficulty.EASY)
        self.assertIsNotNone(self.controller.board)
        self.assertEqual(self.controller.board.rows, 6)
        self.assertEqual(len(self.controller.undo_stack), 0)
        self.assertFalse(self.controller.is_won)

    def test_left_click_cycle(self):
        # Find a non-hint cell
        r, c = (0, 0)
        if self.controller.is_hint_cell(r, c):
            r, c = (0, 1)

        # Initially UNKNOWN -> Left click -> SHIP
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.UNKNOWN)
        res = self.controller.handle_left_click(r, c)
        self.assertTrue(res)
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.SHIP)

        # Left click again -> UNKNOWN
        res = self.controller.handle_left_click(r, c)
        self.assertTrue(res)
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.UNKNOWN)

    def test_right_click_cycle(self):
        r, c = (0, 0)
        if self.controller.is_hint_cell(r, c):
            r, c = (0, 1)

        # Initially UNKNOWN -> Right click -> WATER
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.UNKNOWN)
        res = self.controller.handle_right_click(r, c)
        self.assertTrue(res)
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.WATER)

        # Right click again -> UNKNOWN
        res = self.controller.handle_right_click(r, c)
        self.assertTrue(res)
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.UNKNOWN)

    def test_locked_hint_cannot_be_modified(self):
        # Force a hint cell
        self.controller.puzzle.hints[(1, 1)] = CellState.WATER
        self.controller.board.set_cell(1, 1, CellState.WATER)

        self.assertTrue(self.controller.is_hint_cell(1, 1))
        # Left click should be rejected
        self.assertFalse(self.controller.handle_left_click(1, 1))
        self.assertEqual(self.controller.board.get_cell(1, 1), CellState.WATER)

        # Right click should be rejected
        self.assertFalse(self.controller.handle_right_click(1, 1))
        self.assertEqual(self.controller.board.get_cell(1, 1), CellState.WATER)

    def test_undo(self):
        r, c = (2, 2)
        if self.controller.is_hint_cell(r, c):
            r, c = (2, 3)

        self.controller.handle_left_click(r, c)
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.SHIP)
        self.assertEqual(len(self.controller.undo_stack), 1)

        # Undo
        self.assertTrue(self.controller.undo())
        self.assertEqual(self.controller.board.get_cell(r, c), CellState.UNKNOWN)
        self.assertEqual(len(self.controller.undo_stack), 0)

        # Undo on empty stack returns False
        self.assertFalse(self.controller.undo())

    def test_restart_game(self):
        # Make several moves
        self.controller.handle_left_click(0, 0)
        self.controller.handle_right_click(0, 1)
        self.assertGreater(len(self.controller.undo_stack), 0)

        self.controller.restart_game()
        self.assertEqual(len(self.controller.undo_stack), 0)
        self.assertFalse(self.controller.is_won)

    def test_give_hint(self):
        hint = self.controller.give_hint()
        self.assertIsNotNone(hint)
        r, c, state = hint
        self.assertEqual(self.controller.board.get_cell(r, c), state)
        self.assertEqual(self.controller.puzzle.solution[r][c], state)

    def test_clue_status_and_fleet_progress(self):
        row_status = self.controller.get_row_clue_status(0)
        self.assertIsNotNone(row_status)
        self.assertIsInstance(row_status.is_match, bool)

        col_status = self.controller.get_col_clue_status(0)
        self.assertIsNotNone(col_status)
        self.assertIsInstance(col_status.is_match, bool)

        fleet_prog = self.controller.get_fleet_progress()
        self.assertEqual(len(fleet_prog), 3)  # 3 types: length 3, 2, 1
        lengths = [p.length for p in fleet_prog]
        self.assertEqual(lengths, [3, 2, 1])

    def test_victory_detection(self):
        # Fill board completely with ground truth solution
        for r in range(self.controller.board.rows):
            for c in range(self.controller.board.cols):
                if not self.controller.is_hint_cell(r, c):
                    solution_val = self.controller.puzzle.solution[r][c]
                    if solution_val == CellState.SHIP:
                        self.controller.handle_left_click(r, c)
                    else:
                        self.controller.handle_right_click(r, c)

        self.assertTrue(self.controller.is_won)
        val = self.controller.validate_current()
        self.assertTrue(val.is_complete)


class TestAppUI(unittest.TestCase):
    def test_app_window_creation(self):
        """Verify BattleshipApp instantiates and tears down cleanly without display error."""
        try:
            app = BattleshipApp()
            app.withdraw()  # Hide window during test
            app.update_idletasks()
            self.assertEqual(app.controller.difficulty, Difficulty.EASY)
            # Switch difficulty
            app.diff_var.set(Difficulty.MEDIUM.value)
            app._on_change_difficulty()
            self.assertEqual(app.controller.board.rows, 8)
            app.destroy()
        except tk.TclError:
            # Headless environment fallback
            pass


if __name__ == "__main__":
    unittest.main()
