"""Procedural, cached pixel art. Every asset shares config.P and integer pixels."""
import random
import pygame
from config import CHARACTERS, ENEMIES, P, TILE_SIZE, WEAPONS


def surface(size):
    return pygame.Surface(size, pygame.SRCALPHA)


class Sprites:
    def __init__(self):
        self.players = {(key, frame): self.make_player(key, frame)
                        for key in CHARACTERS for frame in range(2)}
        self.enemies = {(key, frame): self.make_enemy(key, frame)
                        for key in ENEMIES for frame in range(2)}
        self.flashes = {}
        for key, sprite in self.enemies.items():
            flash = sprite.copy()
            flash.fill(P["white"], special_flags=pygame.BLEND_RGB_MAX)
            self.flashes[key] = flash
        self.tiles = [self.make_tile(i) for i in range(12)]
        self.icons = {key: self.make_icon(key) for key in WEAPONS}
        self.gems = {key: self.make_gem(color) for key, color in
                     (("green", "cyan"), ("blue", "blue"), ("violet", "violet"))}
        self.heart = self.make_heart()

    def make_player(self, kind, frame):
        s = surface((18, 22))
        color = P[CHARACTERS[kind].color]
        dark = P[CHARACTERS[kind].color + "_dark"]
        rect = pygame.draw.rect
        # Outline and cloak; feet alternate on a two-frame walk cycle.
        rect(s, P["void"], (4, 3, 11, 15))
        rect(s, dark, (3, 12, 12, 6))
        rect(s, P["border"], (6, 11, 7, 7))
        rect(s, color, (6, 11, 6, 4))
        rect(s, P["white"], (8, 12, 2, 2))
        rect(s, P["void"], (5, 17, 4, 4 - frame))
        rect(s, P["void"], (11, 17, 4, 3 + frame))
        rect(s, color, (5, 19 - frame, 3, 1))
        rect(s, color, (11, 19 + frame, 3, 1))
        rect(s, P["void"], (3, 11, 3, 5))
        rect(s, P["void"], (14, 11, 3, 5))
        rect(s, color, (3, 11, 2, 3))
        rect(s, dark, (14, 11, 2, 4))
        if kind == "planner":
            rect(s, dark, (5, 3, 9, 7))
            rect(s, color, (5, 3, 8, 2))
            rect(s, P["void"], (6, 6, 8, 3))
            rect(s, P["white"], (7, 6, 2, 2))
            rect(s, color, (11, 6, 2, 2))
            rect(s, P["border"], (9, 0, 1, 3))
            rect(s, color, (8, 0, 3, 1))
        elif kind == "retriever":
            rect(s, P["amber_dark"], (5, 3, 10, 7))
            rect(s, color, (4, 3, 11, 2))
            rect(s, color, (3, 5, 3, 3))
            rect(s, P["void"], (7, 5, 7, 3))
            rect(s, P["cyan"], (8, 5, 5, 1))
            rect(s, P["border"], (0, 9, 4, 8))
            rect(s, color, (0, 10, 2, 4))
            rect(s, color, (12, 14, 4, 3))
        else:
            pygame.draw.polygon(s, dark, [(4, 8), (8, 1), (12, 1), (16, 8), (14, 11), (5, 11)])
            pygame.draw.line(s, color, (6, 4), (9, 1), 2)
            rect(s, P["void"], (6, 5, 8, 5))
            rect(s, P["white"], (8, 6, 2, 2))
            rect(s, color, (11, 6, 2, 2))
            rect(s, color, (1, 11, 2, 2))
            rect(s, color, (16, 10, 2, 2))
        return s

    def make_enemy(self, kind, frame):
        color = P[ENEMIES[kind]["color"]]
        if kind == "bug":
            s = surface((16, 15))
            for x in (1, 12):
                for y in (4, 9):
                    pygame.draw.rect(s, P["red_dark"], (x, y + frame, 3, 3))
            pygame.draw.rect(s, P["void"], (3, 2, 10, 11))
            pygame.draw.rect(s, P["red_dark"], (4, 3, 8, 9))
            pygame.draw.rect(s, color, (4, 3, 8, 4))
            pygame.draw.rect(s, P["void"], (5, 5, 2, 2))
            pygame.draw.rect(s, P["white"], (9, 5, 2, 2))
            pygame.draw.rect(s, color, (7, 10, 2, 2))
        elif kind == "wisp":
            s = surface((13, 17))
            pygame.draw.polygon(s, P["violet_dark"], [(6, 0), (11, 5), (12, 12),
                (9, 16 - frame * 2), (6, 13), (3, 16), (1, 11), (2, 4)])
            pygame.draw.rect(s, color, (3, 4, 7, 6))
            pygame.draw.rect(s, P["void"], (4, 6, 2, 3))
            pygame.draw.rect(s, P["white"], (8, 6, 2, 2))
            pygame.draw.rect(s, color, (4, 12 + frame, 2, 2))
        elif kind == "hunter":
            s = surface((18, 18))
            pygame.draw.polygon(s, P["void"], [(8, 0), (16, 6), (17, 12), (10, 16), (1, 13), (2, 4)])
            pygame.draw.polygon(s, P["moss"], [(8, 1), (15, 6), (14, 13), (5, 14), (3, 6)])
            pygame.draw.line(s, color, (8, 3), (13, 6), 2)
            pygame.draw.rect(s, color, (6, 7, 8, 2))
            pygame.draw.rect(s, P["white"], (11, 7, 2, 2))
            pygame.draw.rect(s, color, (1, 12 + frame, 3, 3))
            pygame.draw.rect(s, color, (13, 13 - frame, 3, 3))
        else:
            titan = kind == "titan"
            size = 34 if titan else 25
            s = surface((size, size))
            cx = size // 2
            pygame.draw.rect(s, P["void"], (3, 3, size - 6, size - 7))
            pygame.draw.rect(s, P["red_dark"] if titan else P["amber_dark"], (4, 4, size - 8, size - 9))
            pygame.draw.rect(s, color, (5, 3, size - 10, 4))
            pygame.draw.rect(s, P["raised"], (7, 8, size - 14, size - 16))
            pygame.draw.rect(s, color, (8, 9, size - 16, 3))
            pygame.draw.rect(s, P["white"], (cx, 9, 3, 3))
            for x in (1, size - 6):
                pygame.draw.rect(s, P["void"], (x, 9, 5, size - 12))
                pygame.draw.rect(s, color, (x + 1, 10, 3, 4))
            pygame.draw.rect(s, P["void"], (5, size - 6, 5, 5 - frame))
            pygame.draw.rect(s, P["void"], (size - 10, size - 6, 5, 4 + frame))
            if titan:
                for x in (6, 14, 24):
                    pygame.draw.rect(s, color, (x, 0, 3, 4))
                pygame.draw.rect(s, color, (cx - 3, size - 13, 6, 5))
        return s

    def make_tile(self, seed):
        rng = random.Random(seed * 793)
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.fill(P["ground"])
        pygame.draw.line(s, P["tile"], (0, 0), (31, 0))
        pygame.draw.line(s, P["tile"], (0, 0), (0, 31))
        for _ in range(10):
            x, y = rng.randrange(2, 29), rng.randrange(2, 29)
            pygame.draw.rect(s, P["tile"], (x, y, rng.randrange(1, 4), 1))
        if seed < 3:
            for _ in range(5):
                x, y = rng.randrange(4, 28), rng.randrange(4, 28)
                pygame.draw.rect(s, P["moss"], (x, y, 2, 1))
        elif seed == 4:
            pygame.draw.lines(s, P["edge"], False, [(4, 29), (10, 20), (10, 10), (18, 4)], 1)
            pygame.draw.rect(s, P["moss"], (16, 3, 3, 2))
        elif seed == 7:
            pygame.draw.rect(s, P["void"], (9, 8, 14, 17))
            pygame.draw.rect(s, P["edge"], (9, 7, 14, 15))
            pygame.draw.rect(s, P["tile"], (10, 9, 11, 10))
            for y in (11, 14, 17):
                pygame.draw.line(s, P["ground"], (12, y), (19, y))
            pygame.draw.rect(s, P["cyan_dark"], (11, 8, 2, 1))
        return s

    def make_icon(self, kind):
        s = surface((16, 16))
        color = P[WEAPONS[kind]["color"]]
        if kind in ("pulse", "rail"):
            pygame.draw.line(s, color, (3, 12), (12, 3), 3)
            pygame.draw.rect(s, P["white"], (10, 3, 3, 3))
        elif kind == "shards":
            for x, y in ((3, 8), (7, 4), (11, 8)):
                pygame.draw.polygon(s, color, [(x, y), (x + 2, y - 3), (x + 3, y + 3)])
        elif kind == "orbit":
            pygame.draw.circle(s, P["amber_dark"], (8, 8), 5, 1)
            for point in ((4, 4), (12, 10)):
                pygame.draw.rect(s, color, (*point, 3, 3))
        elif kind == "chain":
            pygame.draw.lines(s, color, False, [(12, 1), (5, 8), (10, 8), (4, 15)], 2)
        else:
            pygame.draw.circle(s, color, (8, 8), 6, 1)
            pygame.draw.circle(s, P["white"], (8, 8), 2)
        return s

    @staticmethod
    def make_gem(color):
        s = surface((8, 10))
        pygame.draw.polygon(s, P["void"], [(4, 0), (7, 4), (4, 9), (0, 4)])
        pygame.draw.polygon(s, P[color], [(4, 1), (6, 4), (4, 7), (1, 4)])
        pygame.draw.line(s, P["white"], (3, 3), (4, 2))
        return s

    @staticmethod
    def make_heart():
        s = surface((10, 10))
        pygame.draw.polygon(s, P["red"], [(1, 2), (3, 1), (5, 3), (7, 1), (9, 2), (9, 5), (5, 9), (1, 5)])
        pygame.draw.rect(s, P["white"], (2, 2, 2, 1))
        return s

    def background(self, target, camera):
        left, top = int(camera.x // TILE_SIZE), int(camera.y // TILE_SIZE)
        width, height = target.get_size()
        for row in range(height // TILE_SIZE + 2):
            y = row + top
            for column in range(width // TILE_SIZE + 2):
                x = column + left
                index = ((x * 73856093) ^ (y * 19349663)) % len(self.tiles)
                target.blit(self.tiles[index], (round(x * TILE_SIZE - camera.x), round(y * TILE_SIZE - camera.y)))
