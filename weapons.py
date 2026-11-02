"""Six automatic weapons; a level-five weapon evolves on its next upgrade."""
import math
import pygame
from config import (P, WEAPONS, WEAPON_MAX_LEVEL, WEAPON_DAMAGE_PER_LEVEL,
                    WEAPON_COOLDOWN_PER_LEVEL, MAX_PROJECTILES)
from entities import Projectile


class Weapon:
    def __init__(self, kind):
        self.kind = kind
        self.level = 1
        self.evolved = False
        self.timer = 0.2
        self.phase = 0.0
        self.hit_timers = {}

    @property
    def spec(self):
        return WEAPONS[self.kind]

    @property
    def name(self):
        return self.spec["evolution"] if self.evolved else self.spec["name"]

    @property
    def can_upgrade(self):
        return not self.evolved

    def upgrade(self):
        if self.level < WEAPON_MAX_LEVEL:
            self.level += 1
        else:
            self.evolved = True

    def damage(self, player):
        return (self.spec["damage"] * player.damage *
                (1 + (self.level - 1) * WEAPON_DAMAGE_PER_LEVEL) *
                (1.5 if self.evolved else 1))

    def cooldown(self, player):
        return self.spec["cooldown"] * (1 - (self.level - 1) * WEAPON_COOLDOWN_PER_LEVEL) * player.cooldown_multiplier

    def orb_positions(self, player):
        count = 5 if self.evolved else 2 + (self.level >= 3)
        radius = self.spec["radius"] + self.level * 2 + (12 if self.evolved else 0)
        return [player.pos + pygame.Vector2(math.cos(self.phase + i * math.tau / count),
                  math.sin(self.phase + i * math.tau / count)) * radius for i in range(count)]

    def projectile(self, game, direction, damage, pierce=0, origin=None):
        if len(game.projectiles) >= MAX_PROJECTILES:
            return
        game.projectiles.append(Projectile(
            (origin if origin is not None else game.player.pos).copy(),
            direction * self.spec["speed"], damage, P[self.spec["color"]],
            self.spec["radius"], pierce, kind=self.kind))

    def update(self, dt, game):
        player = game.player
        if self.kind == "orbit":
            self.phase += dt * self.spec["speed"] * (1.3 if self.evolved else 1)
            self.update_orbit(game)
            return
        self.timer -= dt
        if self.timer > 0:
            return
        target = game.nearest_enemy(player.pos, 430)
        if target is None:
            self.timer = 0
            return
        self.timer = self.cooldown(player)
        damage = self.damage(player)
        delta = target.pos - player.pos
        direction = delta.normalize() if delta.length_squared() else player.facing
        if self.kind == "pulse":
            count = 3 if self.evolved else 1 + (self.level >= 4)
            for i in range(count):
                self.projectile(game, direction.rotate((i - (count - 1) / 2) * 9), damage,
                                2 if self.evolved else (self.level >= 3))
        elif self.kind == "shards":
            count = 7 if self.evolved else 3 + (self.level >= 3)
            for i in range(count):
                self.projectile(game, direction.rotate((i - (count - 1) / 2) * 13), damage,
                                3 if self.evolved else (self.level >= 4))
        elif self.kind == "rail":
            perpendicular = pygame.Vector2(-direction.y, direction.x)
            offsets = (-5, 5) if self.evolved else (0,)
            for offset in offsets:
                self.projectile(game, direction, damage, 20 if self.evolved else 3 + self.level // 2,
                                player.pos + perpendicular * offset)
        elif self.kind == "nova":
            radius = self.spec["radius"] + self.level * 4 + (35 if self.evolved else 0)
            game.effects.ring(player.pos, radius, P["green"])
            for enemy in game.spatial.query(player.pos, radius + game.max_enemy_radius):
                if enemy.alive and enemy.pos.distance_squared_to(player.pos) <= (radius + enemy.radius) ** 2:
                    game.damage_enemy(enemy, damage, enemy.pos - player.pos,
                                      knockback=24 if self.evolved else 6)
            game.effects.shake = max(game.effects.shake, 1.8)
        elif self.kind == "chain":
            visited = set()
            points = [player.pos.copy()]
            current = target
            count = 8 if self.evolved else 3 + self.level // 2
            for jump in range(count):
                if current is None:
                    break
                visited.add(current.uid)
                points.append(current.pos.copy())
                game.damage_enemy(current, damage * (1 if self.evolved else 0.9 ** jump))
                current = game.nearest_enemy(points[-1], self.spec["radius"] + self.level * 5, visited)
            game.effects.trace(points, P["blue"])
        game.audio.play("shoot")

    def update_orbit(self, game):
        self.hit_timers = {uid: time for uid, time in self.hit_timers.items() if time > game.elapsed}
        for pos in self.orb_positions(game.player):
            for enemy in game.spatial.query(pos, 7 + game.max_enemy_radius):
                if (enemy.alive and enemy.uid not in self.hit_timers
                        and enemy.pos.distance_squared_to(pos) < (enemy.radius + 6) ** 2):
                    self.hit_timers[enemy.uid] = game.elapsed + self.cooldown(game.player)
                    game.damage_enemy(enemy, self.damage(game.player), enemy.pos - game.player.pos, knockback=5)
                    game.audio.play("shoot")

    def draw(self, target, camera, player):
        if self.kind != "orbit":
            return
        for pos in self.orb_positions(player):
            point = pos - camera
            x, y = round(point.x), round(point.y)
            pygame.draw.circle(target, P["amber_dark"], (x, y), 5)
            pygame.draw.rect(target, P["amber"], (x - 3, y - 3, 6, 6), 1)
            pygame.draw.rect(target, P["white"], (x - 1, y - 1, 2, 2))
