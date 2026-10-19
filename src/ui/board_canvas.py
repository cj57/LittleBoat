"""Tkinter Canvas component for rendering the Battleship Solitaire grid and clues."""
import tkinter as tk
from typing import Callable, Optional, Tuple

from ..models.cell import CellState
from .game_controller import GameController


class BoardCanvas(tk.Canvas):
    """Renders the game board, row/column clues, ships, and water."""

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

    def _get_cell_at_xy(self, x: int, y: int) -> Optional[Tuple[int, int]]:
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

    def _on_left_click(self, event: tk.Event) -> None:
        cell = self._get_cell_at_xy(event.x, event.y)
        if cell is not None:
            r, c = cell
            if self.controller.handle_left_click(r, c):
                self.redraw()
                if self.on_cell_change:
                    self.on_cell_change()

    def _on_right_click(self, event: tk.Event) -> None:
        cell = self._get_cell_at_xy(event.x, event.y)
        if cell is not None:
            r, c = cell
            if self.controller.handle_right_click(r, c):
                self.redraw()
                if self.on_cell_change:
                    self.on_cell_change()

    def _on_mouse_move(self, event: tk.Event) -> None:
        cell = self._get_cell_at_xy(event.x, event.y)
        if cell != self.hover_cell:
            self.hover_cell = cell
            self.redraw()

    def _on_mouse_leave(self, event: tk.Event) -> None:
        if self.hover_cell is not None:
            self.hover_cell = None
            self.redraw()

    def redraw(self) -> None:
        """Full redraw of board, clues, and cells."""
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

            # Clue badge
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

                self._draw_cell(x1, y1, x2, y2, cell_state, is_hint, is_hover)

    def _get_clue_colors(self, status) -> Tuple[str, str]:
        if status.is_overflow:
            return ("#fee2e2", "#b91c1c")  # Red badge for error
        if status.is_match:
            return ("#dcfce7", "#15803d")  # Green badge for satisfied
        return ("#f1f5f9", "#475569")      # Neutral slate

    def _draw_cell(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        state: CellState,
        is_hint: bool,
        is_hover: bool,
    ) -> None:
        pad = 2

        # Base background
        if is_hint:
            bg = "#fef9c3"  # Soft amber hint background
        elif is_hover:
            bg = "#e2e8f0"  # Subtle hover slate
        else:
            bg = "#f8fafc"  # Standard clean background

        self.create_rectangle(x1, y1, x2, y2, fill=bg, outline="#cbd5e1", width=1)

        # Draw content
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        inset = 5

        if state == CellState.WATER:
            # Water background and wave symbol
            self.create_rectangle(
                x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                fill="#e0f2fe", outline="#bae6fd", width=1
            )
            self.create_text(
                cx, cy,
                text="~",
                fill="#0284c7",
                font=("Segoe UI", 18, "bold")
            )

        elif state == CellState.SHIP:
            # Sleek navy ship block with subtle border
            ship_fill = "#1e293b" if not is_hint else "#0f172a"
            self.create_rectangle(
                x1 + inset, y1 + inset, x2 - inset, y2 - inset,
                fill=ship_fill, outline="#0f172a", width=2
            )
            # Center subtle accent dot / hatch
            dot_r = 3
            self.create_oval(
                cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r,
                fill="#94a3b8", outline=""
            )

        # Hint lock badge indicator
        if is_hint:
            # Tiny golden corner triangle / tag
            self.create_polygon(
                x1 + 1, y1 + 1,
                x1 + 9, y1 + 1,
                x1 + 1, y1 + 9,
                fill="#eab308", outline=""
            )
