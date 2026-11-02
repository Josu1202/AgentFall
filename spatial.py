"""Uniform spatial hash; broad-phase projectile/orbit collision stays local."""
import math
from config import GRID_CELL


class SpatialHash:
    def __init__(self, cell_size: int = GRID_CELL):
        self.cell_size = cell_size
        self.cells = {}

    def rebuild(self, enemies) -> None:
        self.cells.clear()
        for enemy in enemies:
            if enemy.alive:
                key = (math.floor(enemy.pos.x / self.cell_size), math.floor(enemy.pos.y / self.cell_size))
                self.cells.setdefault(key, []).append(enemy)

    def query(self, pos, radius: float) -> list:
        result = []
        left = math.floor((pos.x - radius) / self.cell_size)
        right = math.floor((pos.x + radius) / self.cell_size)
        top = math.floor((pos.y - radius) / self.cell_size)
        bottom = math.floor((pos.y + radius) / self.cell_size)
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                result.extend(self.cells.get((x, y), ()))
        return result
