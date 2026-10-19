"""Puzzle generator for Battleship Solitaire."""
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Dict, Set, Optional

from ..models.cell import CellState
from ..models.ship import Ship
from ..models.board import Board
from .solver import Solver


class Difficulty(Enum):
    EASY = "easy"        # 6x6
    MEDIUM = "medium"    # 8x8
    HARD = "hard"        # 10x10


DIFFICULTY_PRESETS: Dict[Difficulty, Dict] = {
    Difficulty.EASY: {
        "rows": 6,
        "cols": 6,
        "fleet_spec": {3: 1, 2: 2, 1: 3},  # 10 cells total
        "default_hints": 0,
    },
    Difficulty.MEDIUM: {
        "rows": 8,
        "cols": 8,
        "fleet_spec": {4: 1, 3: 1, 2: 2, 1: 3},  # 14 cells total
        "default_hints": 1,
    },
    Difficulty.HARD: {
        "rows": 10,
        "cols": 10,
        "fleet_spec": {4: 1, 3: 2, 2: 3, 1: 4},  # 20 cells total
        "default_hints": 2,
    },
}


@dataclass
class Puzzle:
    """Represents a generated puzzle ready for gameplay."""
    difficulty: str
    board: Board
    solution: List[List[CellState]]
    ships: List[Ship]
    hints: Dict[Tuple[int, int], CellState] = field(default_factory=dict)


class Generator:
    """Generates random valid Battleship Solitaire puzzles."""

    @staticmethod
    def _place_fleet_randomly(
        rows: int,
        cols: int,
        fleet_spec: Dict[int, int],
        rng: random.Random,
    ) -> Optional[List[Ship]]:
        """
        Attempts to place all ships randomly on a grid of rows x cols.
        Returns a list of Ship objects, or None if failed.
        """
        # Flatten ship lengths descending
        ship_lengths: List[int] = []
        for length, count in sorted(fleet_spec.items(), reverse=True):
            ship_lengths.extend([length] * count)

        placed_ships: List[Ship] = []
        occupied: Set[Tuple[int, int]] = set()
        surrounding_mask: Set[Tuple[int, int]] = set()

        def can_place(cells: Tuple[Tuple[int, int], ...]) -> bool:
            for r, c in cells:
                if (r, c) in surrounding_mask or (r, c) in occupied:
                    return False
            return True

        def get_all_placements(length: int) -> List[Tuple[Tuple[int, int], ...]]:
            placements = []
            if length == 1:
                for r in range(rows):
                    for c in range(cols):
                        cells = ((r, c),)
                        if can_place(cells):
                            placements.append(cells)
                return placements

            # Horizontal
            for r in range(rows):
                for c in range(cols - length + 1):
                    cells = tuple((r, c + i) for i in range(length))
                    if can_place(cells):
                        placements.append(cells)

            # Vertical
            for c in range(cols):
                for r in range(rows - length + 1):
                    cells = tuple((r + i, c) for i in range(length))
                    if can_place(cells):
                        placements.append(cells)

            return placements

        def backtrack(idx: int) -> bool:
            if idx == len(ship_lengths):
                return True

            length = ship_lengths[idx]
            candidates = get_all_placements(length)
            rng.shuffle(candidates)

            for cells in candidates:
                ship = Ship(cells)
                placed_ships.append(ship)
                new_surrounding = ship.surrounding_cells(rows, cols)

                # Update masks
                occupied.update(cells)
                prev_mask = set(surrounding_mask)
                surrounding_mask.update(new_surrounding)

                if backtrack(idx + 1):
                    return True

                # Revert
                placed_ships.pop()
                for c in cells:
                    occupied.remove(c)
                surrounding_mask.clear()
                surrounding_mask.update(prev_mask)

            return False

        # Try placement
        success = backtrack(0)
        return placed_ships if success else None

    @classmethod
    def generate_puzzle(
        cls,
        difficulty: Difficulty = Difficulty.EASY,
        hints_count: Optional[int] = None,
        seed: Optional[int] = None,
        max_attempts: int = 50,
    ) -> Puzzle:
        """
        Generates a valid puzzle according to specified difficulty.
        """
        rng = random.Random(seed)
        preset = DIFFICULTY_PRESETS[difficulty]
        rows: int = preset["rows"]
        cols: int = preset["cols"]
        fleet_spec: Dict[int, int] = preset["fleet_spec"]
        if hints_count is None:
            hints_count = preset["default_hints"]

        ships: Optional[List[Ship]] = None
        for _ in range(max_attempts):
            ships = cls._place_fleet_randomly(rows, cols, fleet_spec, rng)
            if ships is not None:
                break

        if ships is None:
            raise RuntimeError(f"Failed to place fleet within {max_attempts} attempts")

        # Build solution grid
        solution_grid = [
            [CellState.WATER for _ in range(cols)] for _ in range(rows)
        ]
        for ship in ships:
            for r, c in ship.cells:
                solution_grid[r][c] = CellState.SHIP

        # Calculate row and col clues
        row_clues = [
            sum(1 for c in range(cols) if solution_grid[r][c] == CellState.SHIP)
            for r in range(rows)
        ]
        col_clues = [
            sum(1 for r in range(rows) if solution_grid[r][c] == CellState.SHIP)
            for c in range(cols)
        ]

        # Create playable board
        board = Board(
            rows=rows,
            cols=cols,
            row_clues=row_clues,
            col_clues=col_clues,
            fleet_spec=fleet_spec,
        )

        # Select hints if requested
        hints: Dict[Tuple[int, int], CellState] = {}
        if hints_count > 0:
            all_coords = [(r, c) for r in range(rows) for c in range(cols)]
            rng.shuffle(all_coords)
            selected_coords = all_coords[:hints_count]
            for r, c in selected_coords:
                state = solution_grid[r][c]
                hints[(r, c)] = state
                board.set_cell(r, c, state)

        return Puzzle(
            difficulty=difficulty.value,
            board=board,
            solution=solution_grid,
            ships=ships,
            hints=hints,
        )
