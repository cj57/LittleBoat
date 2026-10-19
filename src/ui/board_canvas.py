"""Tkinter Canvas component for rendering the Battleship Solitaire grid, clues, realistic ships, and waves."""
import tkinter as tk
from typing import Callable, Optional, Tuple, List, Set

from ..models.cell import CellState
from .game_controller import GameController
from .drawing_utils import (
    draw_ship_segment,
    draw_water_wave,
    determine_segment_type,
    ShipSegmentType,
)


class BoardCanvas(tk.Canvas):
    """Renders the game board, row/column clues, realistic ships, and water waves."""

    def __init__(
        self,
        master: tk.Widget,
        controller: GameController,
        on_cell_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.on_cell_change = on_cell_change

        self.clue_margin = 44  # Margin size for row/col clue numbers
        self.cell_size = 48   # Default cell size in pixels
        self.hover_cell: Optional[Tuple[int, int]] = None

        # Drag and drop preview overlay state
        self.preview_cells: List[Tuple[int, int]] = []
        self.preview_is_legal: bool = True

        # Bindings
        self.bind("<Button-1>", self._on_left_click)
        self.bind("<Button-2>", self._on_right_click)  # macOS / middle
        self.bind("<Button-3>", self._on_right_click)  # Windows / Linux right click
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)

    def update_sizing(self) -> None:
        """Adapts cell dimensions based on board size."""
        board = self.controller.board
        if board is None:
            return
        if board.rows <= 6:
            self.cell_size = 52
            self.clue_margin = 48
        elif board.rows <= 8:
            self.cell_size = 46
            self.clue_margin = 44
        else:
            self.cell_size = 40
            self.clue_margin = 40

        total_width = self.clue_margin + board.cols * self.cell_size + 10
        total_height = self.clue_margin + board.rows * self.cell_size + 10
        self.config(width=total_width, height=total_height, bg="#ffffff", highlightthickness=0)

    def get_cell_at_xy(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        board = self.controller.board
        if board is None:
            return None
        grid_x = x - self.clue_margin
        grid_y = y - self.clue_margin
        if grid_x < 0 or grid_y < 0:
            return None
        c = int(grid_x // self.cell_size)
        r = int(grid_y // self.cell_size)
        if 0 <= r < board.rows and 0 <= c < board.cols:
            return (r, c)
        return None

    def get_cell_rect(self, r: int, c: int) -> Tuple[float, float, float, float]:
        """Returns canvas coordinates (x1, y1, x2, y2) for cell (r, c)."""
        x1 = self.clue_margin + c * self.cell_size
        y1 = self.clue_margin + r * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        return x1, y1, x2, y2

    def set_drag_preview(self, cells: List[Tuple[int, int]], is_legal: bool) -> None:
        """Sets the ghost preview cells during drag and drop."""
        self.preview_cells = list(cells)
        self.preview_is_legal = is_legal
        self.redraw()

    def clear_drag_preview(self) -> None:
        """Clears the drag preview overlay."""
        if self.preview_cells:
            self.preview_cells.clear()
            self.redraw()

    def _on_left_click(self, event: tk.Event) -> None:
        cell = self.get_cell_at_xy(event.x, event.y)
        if cell is not None:
            r, c = cell
            # If clicked on existing ship, remove it
            if self.controller.board and self.controller.board.get_cell(r, c) == CellState.SHIP:
                if not self.controller.is_hint_cell(r, c):
                    self.controller.remove_ship_at(r, c)
                    self.redraw()
                    if self.on_cell_change:
                        self.on_cell_change()
                    return

            if self.controller.handle_left_click(r, c):
                self.redraw()
                if self.on_cell_change:
                    self.on_cell_change()

    def _on_right_click(self, event: tk.Event) -> None:
        cell = self.get_cell_at_xy(event.x, event.y)
        if cell is not None:
            r, c = cell
            if self.controller.handle_right_click(r, c):
                self.redraw()
                if self.on_cell_change:
                    self.on_cell_change()

    def _on_mouse_move(self, event: tk.Event) -> None:
        cell = self.get_cell_at_xy(event.x, event.y)
        if cell != self.hover_cell:
            self.hover_cell = cell
            self.redraw()

    def _on_mouse_leave(self, event: tk.Event) -> None:
        if self.hover_cell is not None:
            self.hover_cell = None
            self.redraw()

    def redraw(self) -> None:
        """Full redraw of board, clues, cells, and drag preview overlay."""
        self.delete("all")
        board = self.controller.board
        if board is None:
            return

        cs = self.cell_size
        cm = self.clue_margin

        # 1. Draw Column Clues (Top header)
        for c in range(board.cols):
            x1 = cm + c * cs
            y1 = 4
            x2 = x1 + cs
            y2 = cm - 4

            status = self.controller.get_col_clue_status(c)
            bg_color, text_color = self._get_clue_colors(status)

            self.create_rectangle(x1 + 3, y1, x2 - 3, y2, fill=bg_color, outline="#cbd5e1", width=1)
            label = f"{status.target}"
            if status.is_match:
                label += "✓"
            self.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=label,
                fill=text_color,
                font=("Segoe UI", 11, "bold"),
            )

        # 2. Draw Row Clues (Left column)
        for r in range(board.rows):
            x1 = 4
            y1 = cm + r * cs
            x2 = cm - 4
            y2 = y1 + cs

            status = self.controller.get_row_clue_status(r)
            bg_color, text_color = self._get_clue_colors(status)

            self.create_rectangle(x1, y1 + 3, x2, y2 - 3, fill=bg_color, outline="#cbd5e1", width=1)
            label = f"{status.target}"
            if status.is_match:
                label += "✓"
            self.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=label,
                fill=text_color,
                font=("Segoe UI", 11, "bold"),
            )

        # 3. Draw Grid Cells
        for r in range(board.rows):
            for c in range(board.cols):
                x1 = cm + c * cs
                y1 = cm + r * cs
                x2 = x1 + cs
                y2 = y1 + cs

                cell_state = board.get_cell(r, c)
                is_hint = self.controller.is_hint_cell(r, c)
                is_hover = (r, c) == self.hover_cell and not is_hint and not self.controller.is_won

                self._draw_cell(r, c, x1, y1, x2, y2, cell_state, is_hint, is_hover)

        # 4. Draw Drag Preview Overlay
        if self.preview_cells:
            overlay_fill = "#bbf7d0" if self.preview_is_legal else "#fecaca"
            overlay_border = "#16a34a" if self.preview_is_legal else "#dc2626"
            for r, c in self.preview_cells:
                if board.in_bounds(r, c):
                    px1, py1, px2, py2 = self.get_cell_rect(r, c)
                    self.create_rectangle(
                        px1 + 2, py1 + 2, px2 - 2, py2 - 2,
                        fill=overlay_fill, outline=overlay_border, width=2,
                        stipple="gray50" if hasattr(self, "tk") else ""
                    )

    def _get_clue_colors(self, status) -> Tuple[str, str]:
        if status.is_overflow:
            return ("#fee2e2", "#b91c1c")  # Red badge for error
        if status.is_match:
            return ("#dcfce7", "#15803d")  # Green badge for satisfied
        return ("#f1f5f9", "#475569")      # Neutral slate

    def _draw_cell(
        self,
        r: int,
        c: int,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        state: CellState,
        is_hint: bool,
        is_hover: bool,
    ) -> None:
        # Base background
        if is_hint:
            bg = "#fef9c3"  # Soft amber hint background
        elif is_hover:
            bg = "#e2e8f0"  # Subtle hover slate
        else:
            bg = "#ffffff"  # Clean crisp white

        self.create_rectangle(x1, y1, x2, y2, fill=bg, outline="#cbd5e1", width=1)

        # Draw content
        if state == CellState.WATER:
            draw_water_wave(self, x1 + 1, y1 + 1, x2 - 1, y2 - 1, color="#38bdf8", bg_color=bg)

        elif state == CellState.SHIP:
            seg_type = determine_segment_type(self.controller.board, r, c)
            ship_fill = "#15324d" if not is_hint else "#0f172a"
            draw_ship_segment(
                self, x1, y1, x2, y2,
                segment_type=seg_type,
                fill_color=ship_fill,
                outline_color="#0f172a",
                inset=3.0,
            )

        # Hint lock badge indicator
        if is_hint:
            self.create_polygon(
                x1 + 1, y1 + 1,
                x1 + 9, y1 + 1,
                x1 + 1, y1 + 9,
                fill="#eab308", outline=""
            )
