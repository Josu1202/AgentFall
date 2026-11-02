"""Swarm movement, weighted spawning and timed elite encounters."""
from dataclasses import dataclass
import math
import pygame
from config import BASE_SIZE, ENEMIES, MAX_ENEMIES, SPAWN


@dataclass
class Enemy:
    uid: int
    kind: str
    pos: pygame.Vector2
    health: float
    max_health: float
    speed: float
    damage: float
    radius: float
    xp: int
    flash: float = 0
    alive: bool = True
    phase: float = 0

    @classmethod
    def create(cls, uid, kind, pos, elapsed):
        spec = ENEMIES[kind]
        health = spec["health"] * (1 + elapsed * SPAWN["health_per_second"])
        speed = spec["speed"] * (1 + elapsed * SPAWN["speed_per_second"])
        return cls(uid, kind, pygame.Vector2(pos), health, health, speed,
                   spec["damage"], spec["radius"], spec["xp"], phase=uid * 1.618)

    def update(self, dt, player, slow=1.0):
        self.flash = max(0.0, self.flash - dt)
        self.phase += dt * 5
        offset = player.pos - self.pos
        distance = offset.length()
        if distance:
            direction = offset / distance
            # Wisps meander but keep closing in; melee remains contact based.
            if self.kind == "wisp":
                direction = direction.rotate(math.sin(self.phase) * 28)
            self.pos += direction * min(distance, self.speed * slow * dt)


class SpawnDirector:
    def __init__(self):
        self.timer = 0.15
        self.next_elite = SPAWN["elite_every"]
        self.uid = 0

    def spawn(self, game, kind):
        width, height = BASE_SIZE
        x, y = game.player.pos
        margin = 28
        side = game.rng.randrange(4)
        if side < 2:
            x += (-1 if side == 0 else 1) * (width / 2 + margin)
            y += game.rng.uniform(-height / 2, height / 2)
        else:
            x += game.rng.uniform(-width / 2, width / 2)
            y += (-1 if side == 2 else 1) * (height / 2 + margin)
        self.uid += 1
        game.enemies.append(Enemy.create(self.uid, kind, (x, y), game.elapsed))

    def update(self, dt, game):
        self.timer -= dt
        if game.elapsed >= self.next_elite:
            # Reserve a slot for each encounter even at the population cap.
            if len(game.enemies) >= MAX_ENEMIES:
                game.enemies.pop(0)
            self.spawn(game, "titan")
            self.next_elite += SPAWN["elite_every"]
            game.announce("DESBORDAMIENTO DETECTADO", "red")
            game.effects.shake = 2
        if self.timer > 0:
            return
        interval = max(SPAWN["minimum_interval"],
                       SPAWN["initial_interval"] - game.elapsed * SPAWN["interval_decay"])
        self.timer += interval
        kinds = [key for key, spec in ENEMIES.items()
                 if spec["weight"] > 0 and spec["unlock"] <= game.elapsed]
        weights = [ENEMIES[key]["weight"] for key in kinds]
        pack = min(SPAWN["max_pack"], 1 + int(game.elapsed / SPAWN["pack_seconds"]))
        for _ in range(min(pack, MAX_ENEMIES - len(game.enemies))):
            self.spawn(game, game.rng.choices(kinds, weights=weights, k=1)[0])
