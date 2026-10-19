"""Game controller managing puzzle state, moves, undo stack, dock ships, and clue feedback."""
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field

from ..models.cell import CellState
from ..models.ship import Ship
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


@dataclass
class DockShip:
    id: int
    length: int
    is_horizontal: bool = True
    is_placed: bool = False
    placed_coords: List[Tuple[int, int]] = field(default_factory=list)


class GameController:
    """Manages the interactive game state for Battleship Solitaire."""

    def __init__(self, difficulty: Difficulty = Difficulty.EASY, seed: Optional[int] = None):
        self.difficulty = difficulty
        self.puzzle: Optional[Puzzle] = None
        self.board: Optional[Board] = None
        self.undo_stack: List[Tuple[int, int, CellState]] = []
        self.dock_ships: List[DockShip] = []
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
        self._init_dock_ships()
        self.sync_dock_ships_from_board()

    def restart_game(self) -> None:
        """Resets the current board back to the initial puzzle state with initial hints."""
        if self.puzzle is None or self.board is None:
            return
        self.board.clear()
        for (r, c), state in self.puzzle.hints.items():
            self.board.set_cell(r, c, state)
        self.undo_stack.clear()
        self.is_won = False
        self._init_dock_ships()
        self.sync_dock_ships_from_board()

    def _init_dock_ships(self) -> None:
        """Initializes dock ships according to fleet_spec sorted descending by length."""
        self.dock_ships.clear()
        if self.board is None:
            return
        ship_id = 0
        for length in sorted(self.board.fleet_spec.keys(), reverse=True):
            count = self.board.fleet_spec[length]
            for _ in range(count):
                self.dock_ships.append(
                    DockShip(
                        id=ship_id,
                        length=length,
                        is_horizontal=True,
                        is_placed=False,
                        placed_coords=[],
                    )
                )
                ship_id += 1

    def sync_dock_ships_from_board(self) -> None:
        """
        Extracts currently formed valid ships on board and synchronizes
        each dock ship's is_placed state and placed_coords.
        """
        if self.board is None:
            return

        components = Validator.extract_8_connected_components(self.board)
        # Find all valid ships on board
        board_ships: List[Tuple[int, bool, List[Tuple[int, int]]]] = []
        for comp in components:
            ship = Ship(tuple(comp))
            if ship.is_valid_shape():
                board_ships.append((ship.length, ship.is_horizontal, list(comp)))

        # Reset dock placement
        for ds in self.dock_ships:
            ds.is_placed = False
            ds.placed_coords = []

        # Match board ships to dock ships of matching length
        used_board_ships = set()
        for ds in self.dock_ships:
            for b_idx, (length, is_horiz, coords) in enumerate(board_ships):
                if b_idx not in used_board_ships and length == ds.length:
                    used_board_ships.add(b_idx)
                    ds.is_placed = True
                    ds.is_horizontal = is_horiz
                    ds.placed_coords = coords
                    break

    def get_dock_ship(self, ship_id: int) -> Optional[DockShip]:
        for ds in self.dock_ships:
            if ds.id == ship_id:
                return ds
        return None

    def toggle_dock_ship_orientation(self, ship_id: int) -> bool:
        """Toggles a dock ship between horizontal and vertical."""
        ds = self.get_dock_ship(ship_id)
        if ds is not None and not self.is_won:
            ds.is_horizontal = not ds.is_horizontal
            return True
        return False

    def can_place_ship_at(
        self,
        length: int,
        is_horizontal: bool,
        start_r: int,
        start_c: int,
        ignore_cells: Optional[Set[Tuple[int, int]]] = None,
    ) -> Tuple[bool, List[Tuple[int, int]]]:
        """
        Checks whether placing a ship of given length and orientation at (start_r, start_c)
        is completely legal (inside bounds, no overlap with water or hint cells, 8-neighbor isolated).
        """
        if self.board is None:
            return False, []

        ignore = set(ignore_cells or [])
        target_cells: List[Tuple[int, int]] = []

        if is_horizontal:
            for i in range(length):
                r = start_r
                c = start_c + i
                if not self.board.in_bounds(r, c):
                    return False, []
                target_cells.append((r, c))
        else:
            for i in range(length):
                r = start_r + i
                c = start_c
                if not self.board.in_bounds(r, c):
                    return False, []
                target_cells.append((r, c))

        target_set = set(target_cells)

        # Check cell contents
        for r, c in target_cells:
            # Cannot overwrite water or immutable hint cell
            if self.is_hint_cell(r, c):
                return False, []
            if self.board.get_cell(r, c) == CellState.WATER:
                return False, []

        # Check 8-neighbor isolation from existing ships outside target_set and ignore
        for r, c in target_cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if self.board.in_bounds(nr, nc):
                        if (nr, nc) not in target_set and (nr, nc) not in ignore:
                            if self.board.get_cell(nr, nc) == CellState.SHIP:
                                return False, []

        return True, target_cells

    def place_dock_ship(
        self,
        ship_id: int,
        start_r: int,
        start_c: int,
        is_horizontal: Optional[bool] = None,
    ) -> bool:
        """
        Places a dock ship at the given grid coordinates.
        If it was already placed elsewhere, moves it.
        """
        if self.board is None or self.is_won:
            return False

        ds = self.get_dock_ship(ship_id)
        if ds is None:
            return False

        horiz = is_horizontal if is_horizontal is not None else ds.is_horizontal
        ignore = set(ds.placed_coords) if ds.is_placed else set()

        legal, target_cells = self.can_place_ship_at(
            length=ds.length,
            is_horizontal=horiz,
            start_r=start_r,
            start_c=start_c,
            ignore_cells=ignore,
        )

        if not legal:
            return False

        # Clear old cells if was placed elsewhere
        if ds.is_placed:
            for r, c in ds.placed_coords:
                if not self.is_hint_cell(r, c):
                    self.undo_stack.append((r, c, self.board.get_cell(r, c)))
                    self.board.set_cell(r, c, CellState.UNKNOWN)

        # Place new cells
        for r, c in target_cells:
            self.undo_stack.append((r, c, self.board.get_cell(r, c)))
            self.board.set_cell(r, c, CellState.SHIP)

        ds.is_horizontal = horiz
        self.sync_dock_ships_from_board()
        self._check_auto_win()
        return True

    def remove_ship_at(self, r: int, c: int) -> bool:
        """
        Removes the ship occupying (r, c) back into UNKNOWN cells.
        """
        if self.board is None or self.is_won:
            return False
        if self.board.get_cell(r, c) != CellState.SHIP or self.is_hint_cell(r, c):
            return False

        # Find the 8-connected component this cell belongs to
        components = Validator.extract_8_connected_components(self.board)
        target_comp = None
        for comp in components:
            if (r, c) in comp:
                target_comp = comp
                break

        if target_comp is None:
            return False

        for cr, cc in target_comp:
            if not self.is_hint_cell(cr, cc):
                self.undo_stack.append((cr, cc, self.board.get_cell(cr, cc)))
                self.board.set_cell(cr, cc, CellState.UNKNOWN)

        self.sync_dock_ships_from_board()
        self._check_auto_win()
        return True

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
        self.sync_dock_ships_from_board()
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
        self.sync_dock_ships_from_board()
        self._check_auto_win()
        return True

    def undo(self) -> bool:
        """Reverts the last player move."""
        if not self.undo_stack or self.board is None or self.is_won:
            return False
        r, c, prev_state = self.undo_stack.pop()
        self.board.set_cell(r, c, prev_state)
        self.sync_dock_ships_from_board()
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
                    self.sync_dock_ships_from_board()
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
                    self.sync_dock_ships_from_board()
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
