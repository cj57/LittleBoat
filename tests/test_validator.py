"""Tests for Validator logic and solution checking."""
import unittest
from src.models.cell import CellState
from src.models.board import Board
from src.core.validator import Validator


class TestValidator(unittest.TestCase):
    def setUp(self):
        # 6x6 board with verified clues
        self.board = Board(
            rows=6,
            cols=6,
            row_clues=[3, 0, 3, 0, 2, 2],
            col_clues=[3, 2, 1, 1, 1, 2],
            fleet_spec={3: 1, 2: 2, 1: 3},
        )

    def _setup_valid_solution(self):
        """Populates self.board with a completely valid layout."""
        # Cruiser (3)
        for c in range(3):
            self.board.set_cell(0, c, CellState.SHIP)
        # Destroyer (2) horizontal
        self.board.set_cell(2, 4, CellState.SHIP)
        self.board.set_cell(2, 5, CellState.SHIP)
        # Destroyer (2) vertical
        self.board.set_cell(4, 0, CellState.SHIP)
        self.board.set_cell(5, 0, CellState.SHIP)
        # Submarines (1) x 3
        self.board.set_cell(2, 1, CellState.SHIP)
        self.board.set_cell(4, 3, CellState.SHIP)
        self.board.set_cell(5, 5, CellState.SHIP)

    def test_empty_board_in_progress(self):
        res = Validator.validate_in_progress(self.board)
        self.assertTrue(res.is_valid)
        self.assertFalse(res.is_complete)
        self.assertEqual(len(res.errors), 0)

    def test_empty_board_solution_validation(self):
        res = Validator.validate_solution(self.board)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_complete)
        # Should have clue errors and fleet mismatch
        self.assertGreater(len(res.errors), 0)

    def test_valid_solution_complete(self):
        self._setup_valid_solution()
        res = Validator.validate_solution(self.board)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_complete)
        self.assertEqual(len(res.errors), 0)
        self.assertEqual(res.found_ships, {3: 1, 2: 2, 1: 3})

    def test_diagonal_touch_detected(self):
        # Two ships touching diagonally at (0,0) and (1,1)
        self.board.set_cell(0, 0, CellState.SHIP)
        self.board.set_cell(1, 1, CellState.SHIP)

        res = Validator.validate_in_progress(self.board)
        self.assertFalse(res.is_valid)
        self.assertGreater(len(res.invalid_components), 0)
        self.assertTrue(any("包含斜角接觸" in err for err in res.errors))

    def test_orthogonal_touch_forming_l_shape(self):
        # L-shape: (0,0), (0,1), (1,0)
        self.board.set_cell(0, 0, CellState.SHIP)
        self.board.set_cell(0, 1, CellState.SHIP)
        self.board.set_cell(1, 0, CellState.SHIP)

        res = Validator.validate_in_progress(self.board)
        self.assertFalse(res.is_valid)
        self.assertGreater(len(res.invalid_components), 0)

    def test_row_clue_overflow(self):
        # Row 1 target is 0, placing a ship in Row 1 should trigger overflow
        self.board.set_cell(1, 0, CellState.SHIP)
        res = Validator.validate_in_progress(self.board)
        self.assertFalse(res.is_valid)
        self.assertIn(1, res.row_errors)
        self.assertTrue(any("超過線索目標" in err for err in res.errors))

    def test_ship_too_long(self):
        # Max ship in 6x6 fleet is length 3. Placing length 4 horizontal ship:
        for c in range(4):
            self.board.set_cell(0, c, CellState.SHIP)

        res = Validator.validate_in_progress(self.board)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("超過允許的最大長度" in err for err in res.errors))

    def test_ship_count_overflow(self):
        # Fleet spec has only 1 ship of length 3.
        # Place two length 3 ships
        for c in range(3):
            self.board.set_cell(0, c, CellState.SHIP)
        for c in range(3):
            self.board.set_cell(2, c, CellState.SHIP)

        res = Validator.validate_in_progress(self.board)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("超過題目規定" in err for err in res.errors))


if __name__ == "__main__":
    unittest.main()
