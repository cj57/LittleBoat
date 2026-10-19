"""Utility functions for rendering realistic Battleship Solitaire ship segments and water waves."""
import tkinter as tk
from typing import Tuple, Optional
from enum import Enum

from ..models.cell import CellState
from ..models.board import Board


class ShipSegmentType(Enum):
    SUBMARINE = "submarine"      # Single cell circle
    CAP_LEFT = "cap_left"        # Horizontal ship left end
    CAP_RIGHT = "cap_right"      # Horizontal ship right end
    MIDDLE_HORIZ = "mid_horiz"   # Horizontal ship middle segment
    CAP_TOP = "cap_top"          # Vertical ship top end
    CAP_BOTTOM = "cap_bottom"    # Vertical ship bottom end
    MIDDLE_VERT = "mid_vert"     # Vertical ship middle segment
    BLOCK = "block"              # Fallback square block


def determine_segment_type(board: Board, r: int, c: int) -> ShipSegmentType:
    """
    Examines 4 orthogonal neighbors of a SHIP cell to determine its segment shape.
    """
    has_up = (r > 0 and board.get_cell(r - 1, c) == CellState.SHIP)
    has_down = (r < board.rows - 1 and board.get_cell(r + 1, c) == CellState.SHIP)
    has_left = (c > 0 and board.get_cell(r, c - 1) == CellState.SHIP)
    has_right = (c < board.cols - 1 and board.get_cell(r, c + 1) == CellState.SHIP)

    # Isolated single cell
    if not (has_up or has_down or has_left or has_right):
        return ShipSegmentType.SUBMARINE

    # Horizontal alignments
    if has_left and has_right:
        return ShipSegmentType.MIDDLE_HORIZ
    if has_right and not has_left and not (has_up or has_down):
        return ShipSegmentType.CAP_LEFT
    if has_left and not has_right and not (has_up or has_down):
        return ShipSegmentType.CAP_RIGHT

    # Vertical alignments
    if has_up and has_down:
        return ShipSegmentType.MIDDLE_VERT
    if has_down and not has_up and not (has_left or has_right):
        return ShipSegmentType.CAP_TOP
    if has_up and not has_down and not (has_left or has_right):
        return ShipSegmentType.CAP_BOTTOM

    # Non-linear / in-progress L-shapes
    return ShipSegmentType.BLOCK


def draw_water_wave(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = "#38bdf8",
    bg_color: str = "#ffffff",
) -> None:
    """
    Draws multi-tier realistic water waves as seen in standard Battleship Solitaire puzzles.
    """
    # Background
    canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color, outline="", width=0)

    width = x2 - x1
    height = y2 - y1

    # Draw 3 horizontal wavy lines
    margin_x = width * 0.18
    num_waves = 3
    spacing_y = height * 0.18
    start_y = y1 + height * 0.32

    for row_idx in range(num_waves):
        cy = start_y + row_idx * spacing_y
        pts = []
        steps = 4
        dx = (width - 2 * margin_x) / steps
        for i in range(steps + 1):
            px = x1 + margin_x + i * dx
            py = cy + (-2.5 if i % 2 == 1 else 2.5)
            pts.extend([px, py])

        # Smooth wave spline
        canvas.create_line(pts, fill=color, width=2, smooth=True, capstyle=tk.ROUND)


def draw_ship_segment(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    segment_type: ShipSegmentType,
    fill_color: str = "#15324d",
    outline_color: str = "#0f172a",
    inset: float = 3.0,
) -> None:
    """
    Renders realistic ship parts:
    - SUBMARINE: Round solid circle
    - CAP_LEFT / CAP_RIGHT / CAP_TOP / CAP_BOTTOM: Bullet-nosed caps
    - MIDDLE_HORIZ / MIDDLE_VERT: Straight body blocks
    """
    w = x2 - x1
    h = y2 - y1
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    sx1 = x1 + inset
    sy1 = y1 + inset
    sx2 = x2 - inset
    sy2 = y2 - inset
    r = (min(w, h) - 2 * inset) / 2

    if segment_type == ShipSegmentType.SUBMARINE:
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=fill_color, outline=outline_color, width=1.5
        )

    elif segment_type == ShipSegmentType.CAP_LEFT:
        # Left half circle arc + right rect filling to right border
        canvas.create_arc(
            sx1, cy - r, sx1 + 2 * r, cy + r,
            start=90, extent=180, fill=fill_color, outline=fill_color
        )
        canvas.create_rectangle(
            sx1 + r, sy1, x2, sy2,
            fill=fill_color, outline=fill_color
        )
        # Smooth outer stroke arc
        canvas.create_arc(
            sx1, cy - r, sx1 + 2 * r, cy + r,
            start=90, extent=180, style=tk.ARC, outline=outline_color, width=1.5
        )
        canvas.create_line(sx1 + r, sy1, x2, sy1, fill=outline_color, width=1.5)
        canvas.create_line(sx1 + r, sy2, x2, sy2, fill=outline_color, width=1.5)

    elif segment_type == ShipSegmentType.CAP_RIGHT:
        # Right half circle arc + left rect filling to left border
        canvas.create_arc(
            sx2 - 2 * r, cy - r, sx2, cy + r,
            start=270, extent=180, fill=fill_color, outline=fill_color
        )
        canvas.create_rectangle(
            x1, sy1, sx2 - r, sy2,
            fill=fill_color, outline=fill_color
        )
        # Outline
        canvas.create_arc(
            sx2 - 2 * r, cy - r, sx2, cy + r,
            start=270, extent=180, style=tk.ARC, outline=outline_color, width=1.5
        )
        canvas.create_line(x1, sy1, sx2 - r, sy1, fill=outline_color, width=1.5)
        canvas.create_line(x1, sy2, sx2 - r, sy2, fill=outline_color, width=1.5)

    elif segment_type == ShipSegmentType.CAP_TOP:
        # Top half circle arc + bottom rect filling to bottom border
        canvas.create_arc(
            cx - r, sy1, cx + r, sy1 + 2 * r,
            start=0, extent=180, fill=fill_color, outline=fill_color
        )
        canvas.create_rectangle(
            sx1, sy1 + r, sx2, y2,
            fill=fill_color, outline=fill_color
        )
        canvas.create_arc(
            cx - r, sy1, cx + r, sy1 + 2 * r,
            start=0, extent=180, style=tk.ARC, outline=outline_color, width=1.5
        )
        canvas.create_line(sx1, sy1 + r, sx1, y2, fill=outline_color, width=1.5)
        canvas.create_line(sx2, sy1 + r, sx2, y2, fill=outline_color, width=1.5)

    elif segment_type == ShipSegmentType.CAP_BOTTOM:
        # Bottom half circle arc + top rect filling to top border
        canvas.create_arc(
            cx - r, sy2 - 2 * r, cx + r, sy2,
            start=180, extent=180, fill=fill_color, outline=fill_color
        )
        canvas.create_rectangle(
            sx1, y1, sx2, sy2 - r,
            fill=fill_color, outline=fill_color
        )
        canvas.create_arc(
            cx - r, sy2 - 2 * r, cx + r, sy2,
            start=180, extent=180, style=tk.ARC, outline=outline_color, width=1.5
        )
        canvas.create_line(sx1, y1, sx1, sy2 - r, fill=outline_color, width=1.5)
        canvas.create_line(sx2, y1, sx2, sy2 - r, fill=outline_color, width=1.5)

    elif segment_type == ShipSegmentType.MIDDLE_HORIZ:
        # Connects seamlessly from left boundary to right boundary
        canvas.create_rectangle(
            x1, sy1, x2, sy2,
            fill=fill_color, outline=fill_color
        )
        canvas.create_line(x1, sy1, x2, sy1, fill=outline_color, width=1.5)
        canvas.create_line(x1, sy2, x2, sy2, fill=outline_color, width=1.5)

    elif segment_type == ShipSegmentType.MIDDLE_VERT:
        # Connects seamlessly from top boundary to bottom boundary
        canvas.create_rectangle(
            sx1, y1, sx2, y2,
            fill=fill_color, outline=fill_color
        )
        canvas.create_line(sx1, y1, sx1, y2, fill=outline_color, width=1.5)
        canvas.create_line(sx2, y1, sx2, y2, fill=outline_color, width=1.5)

    else:
        # Standard block
        canvas.create_rectangle(
            sx1, sy1, sx2, sy2,
            fill=fill_color, outline=outline_color, width=1.5
        )
