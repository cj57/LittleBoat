"""Ship data model for Battleship Solitaire."""
from dataclasses import dataclass
from typing import List, Tuple, Set


@dataclass(frozen=True)
class Ship:
    """Represents a placed ship composed of contiguous grid cells."""
    cells: Tuple[Tuple[int, int], ...]  # Tuple of (row, col)

    @property
    def length(self) -> int:
        return len(self.cells)

    @property
    def is_horizontal(self) -> bool:
        if self.length <= 1:
            return True
        rows = {r for r, _ in self.cells}
        return len(rows) == 1

    @property
    def is_vertical(self) -> bool:
        if self.length <= 1:
            return True
        cols = {c for _, c in self.cells}
        return len(cols) == 1

    def is_valid_shape(self) -> bool:
        """A valid ship must be a straight horizontal or vertical contiguous line of cells."""
        if self.length == 0:
            return False
        if self.length == 1:
            return True

        if self.is_horizontal:
            row = self.cells[0][0]
            cols = sorted(c for r, c in self.cells)
            # Must all share the same row, and columns must be strictly consecutive
            return (
                all(r == row for r, _ in self.cells) and
                cols == list(range(cols[0], cols[0] + self.length))
            )
        elif self.is_vertical:
            col = self.cells[0][1]
            rows = sorted(r for r, c in self.cells)
            # Must all share the same column, and rows must be strictly consecutive
            return (
                all(c == col for _, c in self.cells) and
                rows == list(range(rows[0], rows[0] + self.length))
            )

        return False

    def surrounding_cells(self, max_rows: int, max_cols: int) -> Set[Tuple[int, int]]:
        """Returns all 8-neighbor cells surrounding the ship that are within board bounds."""
        ship_set = set(self.cells)
        surrounding = set()
        for r, c in self.cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < max_rows and 0 <= nc < max_cols:
                        if (nr, nc) not in ship_set:
                            surrounding.add((nr, nc))
        return surrounding
