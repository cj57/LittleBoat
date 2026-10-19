"""Backtracking solver and uniqueness checker for Battleship Solitaire."""
from typing import List, Tuple, Dict, Set, Optional
from ..models.cell import CellState
from ..models.board import Board
from ..models.ship import Ship


class Solver:
    """Solves Battleship Solitaire puzzles using backtracking with constraint pruning."""

    def __init__(self, board: Board):
        self.rows = board.rows
        self.cols = board.cols
        self.row_clues = list(board.row_clues)
        self.col_clues = list(board.col_clues)
        self.fleet_spec = dict(board.fleet_spec)

        # Initial fixed cells from board (e.g. initial hints)
        self.fixed_water: Set[Tuple[int, int]] = set()
        self.fixed_ships: Set[Tuple[int, int]] = set()
        for r in range(self.rows):
            for c in range(self.cols):
                cell = board.get_cell(r, c)
                if cell == CellState.WATER:
                    self.fixed_water.add((r, c))
                elif cell == CellState.SHIP:
                    self.fixed_ships.add((r, c))

        # Flatten fleet into list of lengths sorted descending for efficient search
        self.ship_lengths: List[int] = []
        for length, count in sorted(self.fleet_spec.items(), reverse=True):
            self.ship_lengths.extend([length] * count)

    def find_solutions(self, max_solutions: int = 2) -> List[List[List[CellState]]]:
        """
        Finds up to max_solutions solutions.
        Returns a list of solution grids (each grid is List[List[CellState]]).
        """
        solutions: List[List[List[CellState]]] = []
        occupied_ships: Set[Tuple[int, int]] = set()
        blocked_cells: Set[Tuple[int, int]] = set(self.fixed_water)
        row_counts = [0] * self.rows
        col_counts = [0] * self.cols
        placed_ships: List[Ship] = []

        def can_place_ship(ship_cells: Tuple[Tuple[int, int], ...]) -> bool:
            # 1. No cells can overlap with blocked_cells or fixed_water
            for r, c in ship_cells:
                if (r, c) in blocked_cells:
                    return False

            # 2. Check row and col clue limits
            temp_row_counts = list(row_counts)
            temp_col_counts = list(col_counts)
            for r, c in ship_cells:
                temp_row_counts[r] += 1
                if temp_row_counts[r] > self.row_clues[r]:
                    return False
                temp_col_counts[c] += 1
                if temp_col_counts[c] > self.col_clues[c]:
                    return False

            # 3. Check 8-neighbor isolation from existing ships
            for r, c in ship_cells:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in occupied_ships:
                            return False

            return True

        def get_candidate_placements(length: int) -> List[Tuple[Tuple[int, int], ...]]:
            candidates = []
            if length == 1:
                for r in range(self.rows):
                    if row_counts[r] >= self.row_clues[r]:
                        continue
                    for c in range(self.cols):
                        if col_counts[c] >= self.col_clues[c]:
                            continue
                        cells = ((r, c),)
                        if can_place_ship(cells):
                            candidates.append(cells)
                return candidates

            # Horizontal placements
            for r in range(self.rows):
                if row_counts[r] + length > self.row_clues[r]:
                    continue
                for c in range(self.cols - length + 1):
                    cells = tuple((r, c + i) for i in range(length))
                    if can_place_ship(cells):
                        candidates.append(cells)

            # Vertical placements
            for c in range(self.cols):
                if col_counts[c] + length > self.col_clues[c]:
                    continue
                for r in range(self.rows - length + 1):
                    cells = tuple((r + i, c) for i in range(length))
                    if can_place_ship(cells):
                        candidates.append(cells)

            return candidates

        def backtrack(ship_idx: int):
            if len(solutions) >= max_solutions:
                return

            if ship_idx == len(self.ship_lengths):
                # All ships placed. Verify row clues and col clues are strictly satisfied
                if row_counts == self.row_clues and col_counts == self.col_clues:
                    # Also verify all fixed_ships are covered
                    if self.fixed_ships.issubset(occupied_ships):
                        # Construct solution grid
                        grid = [
                            [
                                CellState.SHIP if (r, c) in occupied_ships else CellState.WATER
                                for c in range(self.cols)
                            ]
                            for r in range(self.rows)
                        ]
                        solutions.append(grid)
                return

            length = self.ship_lengths[ship_idx]
            candidates = get_candidate_placements(length)

            # Optimization: If identical length to previous ship, enforce ordering to eliminate permutations
            if ship_idx > 0 and self.ship_lengths[ship_idx - 1] == length:
                prev_cells = placed_ships[-1].cells
                candidates = [c for c in candidates if c > prev_cells]

            for cells in candidates:
                # Place ship
                ship = Ship(cells)
                placed_ships.append(ship)
                for r, c in cells:
                    occupied_ships.add((r, c))
                    row_counts[r] += 1
                    col_counts[c] += 1

                # Recurse
                backtrack(ship_idx + 1)

                # Unplace ship
                placed_ships.pop()
                for r, c in cells:
                    occupied_ships.remove((r, c))
                    row_counts[r] -= 1
                    col_counts[c] -= 1

                if len(solutions) >= max_solutions:
                    return

        backtrack(0)
        return solutions

    def solve(self) -> Optional[List[List[CellState]]]:
        """Returns the first solution found, or None if unsolvable."""
        solutions = self.find_solutions(max_solutions=1)
        return solutions[0] if solutions else None

    def has_unique_solution(self) -> bool:
        """Returns True if the puzzle has exactly one valid solution."""
        solutions = self.find_solutions(max_solutions=2)
        return len(solutions) == 1
