"""Board model representing the game grid, clues, and fleet specification."""
from typing import List, Dict, Optional, Tuple
from .cell import CellState


class Board:
    """Represents a Battleship Solitaire board."""

    def __init__(
        self,
        rows: int,
        cols: int,
        row_clues: List[int],
        col_clues: List[int],
        fleet_spec: Dict[int, int],
    ):
        if len(row_clues) != rows:
            raise ValueError(f"Expected {rows} row clues, got {len(row_clues)}")
        if len(col_clues) != cols:
            raise ValueError(f"Expected {cols} col clues, got {len(col_clues)}")

        self.rows = rows
        self.cols = cols
        self.row_clues = list(row_clues)
        self.col_clues = list(col_clues)
        # fleet_spec: {ship_length: count}, e.g. {3: 1, 2: 2, 1: 3}
        self.fleet_spec = dict(fleet_spec)

        # Initialize grid with UNKNOWN state
        self.grid: List[List[CellState]] = [
            [CellState.UNKNOWN for _ in range(cols)] for _ in range(rows)
        ]

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_cell(self, r: int, c: int) -> CellState:
        if not self.in_bounds(r, c):
            raise IndexError(f"Cell ({r}, {c}) is out of bounds for {self.rows}x{self.cols} board")
        return self.grid[r][c]

    def set_cell(self, r: int, c: int, state: CellState) -> None:
        if not self.in_bounds(r, c):
            raise IndexError(f"Cell ({r}, {c}) is out of bounds for {self.rows}x{self.cols} board")
        self.grid[r][c] = state

    def clear(self) -> None:
        """Reset all cells to UNKNOWN."""
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[r][c] = CellState.UNKNOWN

    def count_row_ships(self, r: int) -> int:
        """Returns the number of SHIP cells in row r."""
        if not (0 <= r < self.rows):
            raise IndexError(f"Row {r} out of bounds")
        return sum(1 for c in range(self.cols) if self.grid[r][c] == CellState.SHIP)

    def count_col_ships(self, c: int) -> int:
        """Returns the number of SHIP cells in column c."""
        if not (0 <= c < self.cols):
            raise IndexError(f"Column {c} out of bounds")
        return sum(1 for r in range(self.rows) if self.grid[r][c] == CellState.SHIP)

    def total_ships_needed(self) -> int:
        """Total number of ship cells defined by fleet_spec."""
        return sum(length * count for length, count in self.fleet_spec.items())

    def total_ships_placed(self) -> int:
        """Total number of SHIP cells currently placed on the grid."""
        return sum(
            1
            for r in range(self.rows)
            for c in range(self.cols)
            if self.grid[r][c] == CellState.SHIP
        )
