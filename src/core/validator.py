"""Rules and solution validator for Battleship Solitaire."""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple
from collections import deque

from ..models.cell import CellState
from ..models.ship import Ship
from ..models.board import Board


@dataclass
class ValidationResult:
    """Detailed result of board validation."""
    is_valid: bool
    is_complete: bool
    errors: List[str] = field(default_factory=list)
    found_ships: Dict[int, int] = field(default_factory=dict)
    invalid_components: List[Tuple[Tuple[int, int], ...]] = field(default_factory=list)
    row_errors: List[int] = field(default_factory=list)  # Row indices with errors
    col_errors: List[int] = field(default_factory=list)  # Col indices with errors


class Validator:
    """Validates game state and checks win conditions."""

    @staticmethod
    def extract_8_connected_components(board: Board) -> List[List[Tuple[int, int]]]:
        """Finds all 8-directionally connected components of SHIP cells."""
        visited: Set[Tuple[int, int]] = set()
        components: List[List[Tuple[int, int]]] = []

        for r in range(board.rows):
            for c in range(board.cols):
                if board.get_cell(r, c) == CellState.SHIP and (r, c) not in visited:
                    # BFS / DFS for 8-connected component
                    comp = []
                    queue = deque([(r, c)])
                    visited.add((r, c))

                    while queue:
                        curr_r, curr_c = queue.popleft()
                        comp.append((curr_r, curr_c))

                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = curr_r + dr, curr_c + dc
                                if board.in_bounds(nr, nc):
                                    if board.get_cell(nr, nc) == CellState.SHIP and (nr, nc) not in visited:
                                        visited.add((nr, nc))
                                        queue.append((nr, nc))

                    # Sort coordinates for determinism
                    comp.sort()
                    components.append(comp)

        return components

    @classmethod
    def validate_ships(cls, board: Board) -> Tuple[Dict[int, int], List[Tuple[Tuple[int, int], ...]], List[str]]:
        """
        Extracts ships from 8-connected components.
        Returns:
            - found_ships: {length: count} of valid straight ships
            - invalid_components: list of components that are not straight lines or violate rules
            - errors: list of error descriptions
        """
        components = cls.extract_8_connected_components(board)
        found_ships: Dict[int, int] = {}
        invalid_components: List[Tuple[Tuple[int, int], ...]] = []
        errors: List[str] = []

        for comp in components:
            ship = Ship(tuple(comp))
            if not ship.is_valid_shape():
                invalid_components.append(tuple(comp))
                errors.append(f"船隻結構無效或相碰 (包含斜角接觸): {comp}")
            else:
                length = ship.length
                found_ships[length] = found_ships.get(length, 0) + 1

        return found_ships, invalid_components, errors

    @classmethod
    def validate_clues(cls, board: Board, allow_deficit: bool = False) -> Tuple[List[int], List[int], List[str]]:
        """
        Validates row and column clues against current SHIP placements.
        If allow_deficit is True, having fewer ships than clue is allowed (useful for in-progress checks).
        """
        row_errors: List[int] = []
        col_errors: List[int] = []
        errors: List[str] = []

        for r in range(board.rows):
            count = board.count_row_ships(r)
            target = board.row_clues[r]
            if allow_deficit:
                if count > target:
                    row_errors.append(r)
                    errors.append(f"第 {r + 1} 列船隻格數 ({count}) 超過線索目標 ({target})")
            else:
                if count != target:
                    row_errors.append(r)
                    errors.append(f"第 {r + 1} 列船隻格數 ({count}) 與線索目標 ({target}) 不符")

        for c in range(board.cols):
            count = board.count_col_ships(c)
            target = board.col_clues[c]
            if allow_deficit:
                if count > target:
                    col_errors.append(c)
                    errors.append(f"第 {c + 1} 行船隻格數 ({count}) 超過線索目標 ({target})")
            else:
                if count != target:
                    col_errors.append(c)
                    errors.append(f"第 {c + 1} 行船隻格數 ({count}) 與線索目標 ({target}) 不符")

        return row_errors, col_errors, errors

    @classmethod
    def validate_solution(cls, board: Board) -> ValidationResult:
        """
        Full validation checking whether the board is a completely solved valid puzzle.
        """
        errors: List[str] = []

        # 1. Check clues
        row_errs, col_errs, clue_errors = cls.validate_clues(board, allow_deficit=False)
        errors.extend(clue_errors)

        # 2. Check ships and 8-direction isolation
        found_ships, invalid_comps, ship_errors = cls.validate_ships(board)
        errors.extend(ship_errors)

        # 3. Check fleet specification match
        all_lengths = set(board.fleet_spec.keys()) | set(found_ships.keys())
        fleet_match = True
        for length in sorted(all_lengths):
            expected = board.fleet_spec.get(length, 0)
            actual = found_ships.get(length, 0)
            if actual != expected:
                fleet_match = False
                errors.append(f"長度為 {length} 的船隻數量不符: 需要 {expected} 艘，目前找到 {actual} 艘")

        is_valid = len(invalid_comps) == 0 and len(row_errs) == 0 and len(col_errs) == 0
        is_complete = is_valid and fleet_match

        return ValidationResult(
            is_valid=is_valid,
            is_complete=is_complete,
            errors=errors,
            found_ships=found_ships,
            invalid_components=invalid_comps,
            row_errors=row_errs,
            col_errors=col_errs,
        )

    @classmethod
    def validate_in_progress(cls, board: Board) -> ValidationResult:
        """
        Validates intermediate player board state to detect immediate errors (overflows, invalid touches).
        """
        errors: List[str] = []

        # 1. Clues should not be exceeded
        row_errs, col_errs, clue_errors = cls.validate_clues(board, allow_deficit=True)
        errors.extend(clue_errors)

        # 2. Ships should not touch diagonally or have bent shapes
        found_ships, invalid_comps, ship_errors = cls.validate_ships(board)
        errors.extend(ship_errors)

        # 3. No ship length or count should exceed maximum defined in fleet_spec
        max_length = max(board.fleet_spec.keys(), default=0)
        for length, count in found_ships.items():
            if length > max_length:
                errors.append(f"船隻長度 {length} 超過允許的最大長度 {max_length}")
            elif count > board.fleet_spec.get(length, 0):
                errors.append(f"長度為 {length} 的船隻數量 ({count}) 超過題目規定 ({board.fleet_spec.get(length, 0)})")

        is_valid = len(errors) == 0

        # Check completeness
        full_res = cls.validate_solution(board)

        return ValidationResult(
            is_valid=is_valid,
            is_complete=full_res.is_complete,
            errors=errors,
            found_ships=found_ships,
            invalid_components=invalid_comps,
            row_errors=row_errs,
            col_errors=col_errs,
        )
