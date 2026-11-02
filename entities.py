"""Player, experience drops and swept projectiles. Positions are world coordinates."""
from dataclasses import dataclass, field
import math
import pygame
from config import ACTIVE, CHARACTERS, PLAYER, XP

Vec = pygame.Vector2


@dataclass
class Player:
    character: str
    pos: Vec = field(default_factory=Vec)
    level: int = 1
    xp: float = 0.0
    total_xp: float = 0.0
    invulnerable: float = 0.0
    active_timer: float = 0.0
    buff_timer: float = 0.0
    unique_rank: int = 0
    autopilot: bool = False
    facing: Vec = field(default_factory=lambda: Vec(1, 0))
    moving: bool = False
    armor: int = 0
    regen: float = 0.0
    growth: float = 1.0

    def __post_init__(self) -> None:
        self.spec = CHARACTERS[self.character]
        self.max_health = float(self.spec.health)
        self.health = self.max_health
        self.speed = self.spec.speed
        self.damage = self.spec.damage
        self.cooldown_reduction = self.spec.cooldown_reduction
        self.pickup_range = self.spec.pickup
        self.luck = self.spec.luck
        self.critical_chance = PLAYER["critical_chance"]
        self.radius = PLAYER["radius"]

    @property
    def xp_needed(self) -> int:
        n = self.level - 1
        return int(XP["base"] + XP["per_level"] * n + XP["curve"] * n * n)

    @property
    def active_cooldown(self) -> float:
        return self.spec.active_cooldown * ACTIVE["cooldown_per_rank"] ** self.unique_rank

    @property
    def cooldown_multiplier(self) -> float:
        base = max(1 - PLAYER["max_cooldown_reduction"], 1 - self.cooldown_reduction)
        return base * (ACTIVE["planner_haste"] if self.buff_timer > 0 else 1)

    def gain_xp(self, value: float) -> None:
        earned = value * self.growth
        self.xp += earned
        self.total_xp += earned

    def take_damage(self, amount: float) -> float:
        if self.invulnerable > 0 or self.health <= 0:
            return 0
        taken = max(1, amount - self.armor)
        self.health = max(0.0, self.health - taken)
        self.invulnerable = PLAYER["invulnerability"]
        return taken

    def heal(self, amount: float) -> float:
        before = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - before

    def update(self, dt: float, direction: Vec) -> None:
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.active_timer = max(0.0, self.active_timer - dt)
        self.buff_timer = max(0.0, self.buff_timer - dt)
        self.heal(self.regen * dt)
        self.moving = direction.length_squared() > 0
        if self.moving:
            direction = direction.normalize()
            self.facing = direction
            self.pos += direction * self.speed * dt


@dataclass
class Gem:
    pos: Vec
    value: float = 1
    kind: str = "xp"
    magnetized: bool = False
    phase: float = 0

    def update(self, dt: float, player: Player) -> bool:
        """Return True when collected. Magnetization persists outside pickup range."""
        offset = player.pos - self.pos
        distance = offset.length()
        if distance <= player.pickup_range:
            self.magnetized = True
        if self.magnetized:
            step = PLAYER["magnet_speed"] * dt
            if distance <= player.radius + 4 + step:
                return True
            if distance:
                self.pos += offset / distance * step
        return False


def segment_distance_squared(point: Vec, start: Vec, end: Vec) -> float:
    """Circle against swept segment: fast shots do not tunnel through small mobs."""
    delta = end - start
    size = delta.length_squared()
    if size == 0:
        return point.distance_squared_to(start)
    t = max(0.0, min(1.0, (point - start).dot(delta) / size))
    return point.distance_squared_to(start + delta * t)


@dataclass
class Projectile:
    pos: Vec
    velocity: Vec
    damage: float
    color: tuple
    radius: float = 3
    pierce: int = 0
    life: float = 2.2
    kind: str = "pulse"
    hit_ids: set = field(default_factory=set)

    def update(self, dt: float, game) -> bool:
        old = self.pos.copy()
        self.pos += self.velocity * dt
        self.life -= dt
        if self.life <= 0:
            return False
        middle = (old + self.pos) * 0.5
        radius = old.distance_to(self.pos) * 0.5 + self.radius + game.max_enemy_radius
        candidates = game.spatial.query(middle, radius)
        # Visit hits in travel order, including enemies that span multiple grid cells.
        candidates.sort(key=lambda e: old.distance_squared_to(e.pos))
        for enemy in candidates:
            if not enemy.alive or enemy.uid in self.hit_ids:
                continue
            if segment_distance_squared(enemy.pos, old, self.pos) <= (enemy.radius + self.radius) ** 2:
                self.hit_ids.add(enemy.uid)
                game.damage_enemy(enemy, self.damage, self.velocity)
                self.pierce -= 1
                if self.pierce < 0:
                    return False
        return True


def radial_directions(count: int, offset: float = 0):
    for i in range(count):
        angle = offset + math.tau * i / count
        yield Vec(math.cos(angle), math.sin(angle))
