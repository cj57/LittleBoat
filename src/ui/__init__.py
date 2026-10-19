"""UI module for Battleship Solitaire."""
from .game_controller import GameController, ClueStatus, FleetProgress, DockShip
from .board_canvas import BoardCanvas
from .fleet_dock_canvas import FleetDockCanvas
from .drawing_utils import (
    draw_ship_segment,
    draw_water_wave,
    determine_segment_type,
    ShipSegmentType,
)
from .app import BattleshipApp, run_app

__all__ = [
    "GameController",
    "ClueStatus",
    "FleetProgress",
    "DockShip",
    "BoardCanvas",
    "FleetDockCanvas",
    "draw_ship_segment",
    "draw_water_wave",
    "determine_segment_type",
    "ShipSegmentType",
    "BattleshipApp",
    "run_app",
]
