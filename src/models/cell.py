"""Cell state definition for Battleship Solitaire."""
from enum import Enum


class CellState(Enum):
    """Represents the state of a single grid cell."""
    UNKNOWN = 0   # 未知/未標記
    WATER = 1     # 水域 (波浪)
    SHIP = 2      # 船隻 (船身)

    def __str__(self) -> str:
        if self == CellState.UNKNOWN:
            return "."
        elif self == CellState.WATER:
            return "~"
        elif self == CellState.SHIP:
            return "O"
        return "?"
