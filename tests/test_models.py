"""Tests for CellState, Ship, and Board models."""
import unittest
from src.models.cell import CellState
from src.models.ship import Ship
from src.models.board import Board


class TestCellState(unittest.TestCase):
    def test_cell_state_values(self):
        self.assertEqual(CellState.UNKNOWN.value, 0)
        self.assertEqual(CellState.WATER.value, 1)
        self.assertEqual(CellState.SHIP.value, 2)

    def test_cell_state_str(self):
        self.assertEqual(str(CellState.UNKNOWN), ".")
        self.assertEqual(str(CellState.WATER), "~")
        self.assertEqual(str(CellState.SHIP), "O")


class TestShip(unittest.TestCase):
    def test_single_cell_ship(self):
        ship = Ship(((2, 3),))
        self.assertEqual(ship.length, 1)
        self.assertTrue(ship.is_horizontal)
        self.assertTrue(ship.is_vertical)
        self.assertTrue(ship.is_valid_shape())

    def test_horizontal_ship(self):
        ship = Ship(((1, 2), (1, 3), (1, 4)))
        self.assertEqual(ship.length, 3)
        self.assertTrue(ship.is_horizontal)
        self.assertFalse(ship.is_vertical)
        self.assertTrue(ship.is_valid_shape())

    def test_vertical_ship(self):
        ship = Ship(((2, 1), (3, 1), (4, 1), (5, 1)))
        self.assertEqual(ship.length, 4)
        self.assertFalse(ship.is_horizontal)
        self.assertTrue(ship.is_vertical)
        self.assertTrue(ship.is_valid_shape())

    def test_invalid_shapes(self):
        # Empty
        self.assertFalse(Ship(()).is_valid_shape())
        # Diagonal
        diag_ship = Ship(((0, 0), (1, 1)))
        self.assertFalse(diag_ship.is_valid_shape())
        # L-shape
        l_ship = Ship(((0, 0), (0, 1), (1, 0)))
        self.assertFalse(l_ship.is_valid_shape())
        # Gap in line
        gap_ship = Ship(((0, 0), (0, 2)))
        self.assertFalse(gap_ship.is_valid_shape())

    def test_surrounding_cells(self):
        ship = Ship(((1, 1),))
        surrounding = ship.surrounding_cells(max_rows=3, max_cols=3)
        self.assertEqual(len(surrounding), 8)
        self.assertNotIn((1, 1), surrounding)

        # Corner ship
        corner_ship = Ship(((0, 0),))
        corner_surrounding = corner_ship.surrounding_cells(max_rows=3, max_cols=3)
        self.assertEqual(corner_surrounding, {(0, 1), (1, 0), (1, 1)})


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(
            rows=6,
            cols=6,
            row_clues=[3, 0, 3, 0, 2, 2],
            col_clues=[3, 1, 1, 1, 2, 2],
            fleet_spec={3: 1, 2: 2, 1: 3},
        )

    def test_board_initialization(self):
        self.assertEqual(self.board.rows, 6)
        self.assertEqual(self.board.cols, 6)
        self.assertEqual(self.board.row_clues, [3, 0, 3, 0, 2, 2])
        self.assertEqual(self.board.col_clues, [3, 1, 1, 1, 2, 2])
        self.assertEqual(self.board.total_ships_needed(), 1 * 3 + 2 * 2 + 3 * 1)
        self.assertEqual(self.board.total_ships_placed(), 0)

    def test_mismatched_clues_raises(self):
        with self.assertRaises(ValueError):
            Board(rows=6, cols=6, row_clues=[1, 2], col_clues=[1, 2, 3, 4, 5, 6], fleet_spec={})

    def test_get_and_set_cell(self):
        self.assertEqual(self.board.get_cell(0, 0), CellState.UNKNOWN)
        self.board.set_cell(0, 0, CellState.SHIP)
        self.assertEqual(self.board.get_cell(0, 0), CellState.SHIP)
        self.assertEqual(self.board.total_ships_placed(), 1)

    def test_out_of_bounds(self):
        with self.assertRaises(IndexError):
            self.board.get_cell(6, 0)
        with self.assertRaises(IndexError):
            self.board.set_cell(-1, 0, CellState.WATER)

    def test_clear_board(self):
        self.board.set_cell(1, 1, CellState.SHIP)
        self.board.set_cell(2, 2, CellState.WATER)
        self.board.clear()
        self.assertEqual(self.board.get_cell(1, 1), CellState.UNKNOWN)
        self.assertEqual(self.board.get_cell(2, 2), CellState.UNKNOWN)
        self.assertEqual(self.board.total_ships_placed(), 0)

    def test_row_and_col_counts(self):
        self.board.set_cell(0, 0, CellState.SHIP)
        self.board.set_cell(0, 3, CellState.SHIP)
        self.board.set_cell(2, 0, CellState.SHIP)
        self.assertEqual(self.board.count_row_ships(0), 2)
        self.assertEqual(self.board.count_row_ships(1), 0)
        self.assertEqual(self.board.count_col_ships(0), 2)
        self.assertEqual(self.board.count_col_ships(3), 1)


if __name__ == "__main__":
    unittest.main()
