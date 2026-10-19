"""Fleet Dock component rendering graphical ships for drag-and-drop and orientation toggling."""
import tkinter as tk
from typing import Callable, Optional, Dict, Tuple, List

from .game_controller import GameController, DockShip
from .drawing_utils import (
    draw_ship_segment,
    ShipSegmentType,
)


class FleetDockCanvas(tk.Canvas):
    """
    Renders the fleet of ships as graphical pieces ready to be dragged onto the board.
    Supports double-clicking to rotate orientation (horizontal / vertical).
    """

    def __init__(
        self,
        master: tk.Widget,
        controller: GameController,
        on_drag_start: Optional[Callable[[DockShip, int, int], None]] = None,
        on_drag_move: Optional[Callable[[int, int], None]] = None,
        on_drag_release: Optional[Callable[[int, int], None]] = None,
        on_ship_double_click: Optional[Callable[[DockShip], None]] = None,
        **kwargs,
    ):
        super().__init__(master, bg="#ffffff", highlightthickness=0, **kwargs)
        self.controller = controller
        self.on_drag_start = on_drag_start
        self.on_drag_move = on_drag_move
        self.on_drag_release = on_drag_release
        self.on_ship_double_click = on_ship_double_click

        self.cell_size = 28  # Cell size for dock rendering
        self.ship_bounds: Dict[int, Tuple[float, float, float, float]] = {}  # ship_id -> (x1, y1, x2, y2)
        self.active_drag_ship: Optional[DockShip] = None

        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double_click)

    def _get_ship_at(self, x: float, y: float) -> Optional[DockShip]:
        for ship_id, (x1, y1, x2, y2) in self.ship_bounds.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return self.controller.get_dock_ship(ship_id)
        return None

    def _on_press(self, event: tk.Event) -> None:
        ds = self._get_ship_at(event.x, event.y)
        if ds is not None and not self.controller.is_won:
            self.active_drag_ship = ds
            if self.on_drag_start:
                # Pass root coordinates for seamless cross-canvas dragging
                self.on_drag_start(ds, event.x_root, event.y_root)

    def _on_motion(self, event: tk.Event) -> None:
        if self.active_drag_ship is not None and self.on_drag_move:
            self.on_drag_move(event.x_root, event.y_root)

    def _on_release(self, event: tk.Event) -> None:
        if self.active_drag_ship is not None:
            self.active_drag_ship = None
            if self.on_drag_release:
                self.on_drag_release(event.x_root, event.y_root)

    def _on_double_click(self, event: tk.Event) -> None:
        ds = self._get_ship_at(event.x, event.y)
        if ds is not None and not self.controller.is_won:
            self.controller.toggle_dock_ship_orientation(ds.id)
            self.redraw()
            if self.on_ship_double_click:
                self.on_ship_double_click(ds)

    def redraw(self) -> None:
        """Draws all fleet ships grouped by length."""
        self.delete("all")
        self.ship_bounds.clear()
        if self.controller.board is None:
            return

        cs = self.cell_size
        pad_x = 12
        pad_y = 10
        curr_y = pad_y

        # Group dock ships by length descending
        by_length: Dict[int, List[DockShip]] = {}
        for ds in self.controller.dock_ships:
            by_length.setdefault(ds.length, []).append(ds)

        for length in sorted(by_length.keys(), reverse=True):
            ships = by_length[length]
            curr_x = pad_x
            max_row_h = cs

            for ds in ships:
                # Calculate dimensions
                if ds.is_horizontal:
                    ship_w = ds.length * cs
                    ship_h = cs
                else:
                    ship_w = cs
                    ship_h = ds.length * cs

                # Check if wrapping to next row is needed within dock width
                dock_w = self.winfo_width() or 220
                if curr_x + ship_w > dock_w - pad_x and curr_x > pad_x:
                    curr_x = pad_x
                    curr_y += max_row_h + pad_y
                    max_row_h = cs

                x1 = curr_x
                y1 = curr_y
                x2 = x1 + ship_w
                y2 = y1 + ship_h

                self.ship_bounds[ds.id] = (x1, y1, x2, y2)

                # Colors based on whether already placed
                if ds.is_placed:
                    fill_col = "#94a3b8"       # Placed / Ghost gray
                    outline_col = "#64748b"
                else:
                    fill_col = "#15324d"       # Active dark navy
                    outline_col = "#0f172a"

                # Draw segments
                if ds.length == 1:
                    draw_ship_segment(
                        self, x1, y1, x2, y2,
                        ShipSegmentType.SUBMARINE,
                        fill_color=fill_col,
                        outline_color=outline_col,
                        inset=2
                    )
                elif ds.is_horizontal:
                    for i in range(ds.length):
                        cx1 = x1 + i * cs
                        cx2 = cx1 + cs
                        if i == 0:
                            seg = ShipSegmentType.CAP_LEFT
                        elif i == ds.length - 1:
                            seg = ShipSegmentType.CAP_RIGHT
                        else:
                            seg = ShipSegmentType.MIDDLE_HORIZ
                        draw_ship_segment(
                            self, cx1, y1, cx2, y2,
                            seg,
                            fill_color=fill_col,
                            outline_color=outline_col,
                            inset=2
                        )
                else:
                    for i in range(ds.length):
                        cy1 = y1 + i * cs
                        cy2 = cy1 + cs
                        if i == 0:
                            seg = ShipSegmentType.CAP_TOP
                        elif i == ds.length - 1:
                            seg = ShipSegmentType.CAP_BOTTOM
                        else:
                            seg = ShipSegmentType.MIDDLE_VERT
                        draw_ship_segment(
                            self, x1, cy1, x2, cy2,
                            seg,
                            fill_color=fill_col,
                            outline_color=outline_col,
                            inset=2
                        )

                max_row_h = max(max_row_h, ship_h)
                curr_x += ship_w + 14

            curr_y += max_row_h + 12

        # Adjust height
        needed_h = max(180, int(curr_y + 10))
        self.config(height=needed_h)
