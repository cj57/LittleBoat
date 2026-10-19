"""Tests for Drag & Drop dock ships, orientation toggle, and realistic segment detection."""
import unittest

from src.models.cell import CellState
from src.models.board import Board
from src.core.generator import Difficulty
from src.ui.game_controller import GameController
from src.ui.drawing_utils import (
    determine_segment_type,
    ShipSegmentType,
)


class TestSegmentDetection(unittest.TestCase):
    def setUp(self):
        self.board = Board(
            rows=6,
            cols=6,
            row_clues=[3, 0, 2, 0, 1, 0],
            col_clues=[1, 1, 1, 0, 2, 1],
            fleet_spec={3: 1, 2: 1, 1: 1},
        )

    def test_submarine_segment(self):
        # Single cell at (4, 4)
        self.board.set_cell(4, 4, CellState.SHIP)
        seg = determine_segment_type(self.board, 4, 4)
        self.assertEqual(seg, ShipSegmentType.SUBMARINE)

    def test_horizontal_ship_segments(self):
        # Horizontal 3-cell ship at (0, 0), (0, 1), (0, 2)
        for c in range(3):
            self.board.set_cell(0, c, CellState.SHIP)

        self.assertEqual(determine_segment_type(self.board, 0, 0), ShipSegmentType.CAP_LEFT)
        self.assertEqual(determine_segment_type(self.board, 0, 1), ShipSegmentType.MIDDLE_HORIZ)
        self.assertEqual(determine_segment_type(self.board, 0, 2), ShipSegmentType.CAP_RIGHT)

    def test_vertical_ship_segments(self):
        # Vertical 2-cell ship at (2, 4), (3, 4)
        self.board.set_cell(2, 4, CellState.SHIP)
        self.board.set_cell(3, 4, CellState.SHIP)

        self.assertEqual(determine_segment_type(self.board, 2, 4), ShipSegmentType.CAP_TOP)
        self.assertEqual(determine_segment_type(self.board, 3, 4), ShipSegmentType.CAP_BOTTOM)


class TestDockAndDragDrop(unittest.TestCase):
    def setUp(self):
        self.controller = GameController(difficulty=Difficulty.EASY, seed=123)

    def test_dock_ships_initialization(self):
        # 6x6 fleet has {3: 1, 2: 2, 1: 3} -> 6 ships
        self.assertEqual(len(self.controller.dock_ships), 6)
        lengths = [ds.length for ds in self.controller.dock_ships]
        self.assertEqual(lengths, [3, 2, 2, 1, 1, 1])
        # Initially none placed (unless hints exist)
        unplaced = [ds for ds in self.controller.dock_ships if not ds.is_placed]
        self.assertEqual(len(unplaced), 6)

    def test_toggle_orientation(self):
        ds = self.controller.dock_ships[0]
        self.assertTrue(ds.is_horizontal)
        self.assertTrue(self.controller.toggle_dock_ship_orientation(ds.id))
        self.assertFalse(ds.is_horizontal)
        self.assertTrue(self.controller.toggle_dock_ship_orientation(ds.id))
        self.assertTrue(ds.is_horizontal)

    def test_legal_dock_ship_placement(self):
        ds = self.controller.dock_ships[0]  # length 3
        # Place horizontally at (0, 0)
        success = self.controller.place_dock_ship(ds.id, start_r=0, start_c=0, is_horizontal=True)
        self.assertTrue(success)
        self.assertTrue(ds.is_placed)
        self.assertEqual(ds.placed_coords, [(0, 0), (0, 1), (0, 2)])
        for c in range(3):
            self.assertEqual(self.controller.board.get_cell(0, c), CellState.SHIP)

    def test_illegal_placement_out_of_bounds(self):
        ds = self.controller.dock_ships[0]  # length 3
        # Start at col 5 horizontally -> extends to 5, 6, 7 (out of bounds for 6x6)
        success = self.controller.place_dock_ship(ds.id, start_r=0, start_c=5, is_horizontal=True)
        self.assertFalse(success)
        self.assertFalse(ds.is_placed)

    def test_illegal_placement_touching_existing_ship(self):
        # Place ship 1 at (0, 0)-(0, 2)
        s1 = self.controller.dock_ships[0]
        self.controller.place_dock_ship(s1.id, start_r=0, start_c=0, is_horizontal=True)

        # Attempt to place ship 2 diagonally touching at (1, 3)
        s2 = self.controller.dock_ships[1]  # length 2
        success = self.controller.place_dock_ship(s2.id, start_r=1, start_c=3, is_horizontal=True)
        # (1, 3) touches (0, 2) diagonally! Must be rejected
        self.assertFalse(success)
        self.assertFalse(s2.is_placed)

    def test_remove_ship_at(self):
        ds = self.controller.dock_ships[0]
        self.controller.place_dock_ship(ds.id, start_r=0, start_c=0, is_horizontal=True)
        self.assertTrue(ds.is_placed)

        # Remove by clicking any of its cells
        res = self.controller.remove_ship_at(0, 1)
        self.assertTrue(res)
        self.assertFalse(ds.is_placed)
        for c in range(3):
            self.assertEqual(self.controller.board.get_cell(0, c), CellState.UNKNOWN)

    def test_move_already_placed_ship(self):
        ds = self.controller.dock_ships[0]
        self.controller.place_dock_ship(ds.id, start_r=0, start_c=0, is_horizontal=True)
        # Move to (2, 0)
        success = self.controller.place_dock_ship(ds.id, start_r=2, start_c=0, is_horizontal=True)
        self.assertTrue(success)
        self.assertEqual(ds.placed_coords, [(2, 0), (2, 1), (2, 2)])
        # Old cells at row 0 must be UNKNOWN
        for c in range(3):
            self.assertEqual(self.controller.board.get_cell(0, c), CellState.UNKNOWN)
        # New cells at row 2 must be SHIP
        for c in range(3):
            self.assertEqual(self.controller.board.get_cell(2, c), CellState.SHIP)


if __name__ == "__main__":
    unittest.main()
