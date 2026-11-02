"""State machine, delta-time simulation and nearest-neighbor presentation."""
from collections import deque
import math
import random
import pygame
from audio import Audio
from config import (ACTIVE, AUTOPILOT, BASE_SIZE, CHARACTERS, ENEMIES, FPS, MAX_DT,
                    MAX_ENEMY_RADIUS, MAX_GEMS, MAX_PROJECTILES, P, PLAYER,
                    RUN_DURATION, SPAWN, TITLE, VFX, WINDOW_SCALE)
from effects import Effects
from enemies import SpawnDirector
from entities import Gem, Player, Projectile, radial_directions
from spatial import SpatialHash
from sprites import Sprites
from ui import UI
from upgrades import apply_upgrade, roll_upgrades
from weapons import Weapon

Vec = pygame.Vector2


class Game:
    def __init__(self, seed=None, muted=False):
        self.seed = seed
        self.rng = random.Random(seed)
        # Cosmetics have a separate RNG: changing VFX never changes loot/spawns.
        self.fx_rng = random.Random(1391)
        self.screen = pygame.display.set_mode(tuple(n * WINDOW_SCALE for n in BASE_SIZE), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE + " / AI AGENT SURVIVAL")
        self.canvas = pygame.Surface(BASE_SIZE).convert()
        self.sprites = Sprites()
        self.ui = UI(self.sprites)
        self.audio = Audio(muted)
        self.clock = pygame.time.Clock()
        self.spatial = SpatialHash()
        self.effects = Effects(self.fx_rng)
        self.max_enemy_radius = MAX_ENEMY_RADIUS
        self.state = "select"
        self.selected = 0
        self.upgrade_selected = 0
        self.menu_time = 0.0
        self.running = True
        self.fullscreen = False
        self.window_size = self.screen.get_size()
        self.viewport = pygame.Rect((0, 0), self.screen.get_size())
        self.player = None
        self.enemies = []
        self.gems = []
        self.projectiles = []
        self.weapons = []

    def start_run(self, character):
        self.rng = random.Random(self.seed)
        self.player = Player(character)
        self.selected = list(CHARACTERS).index(character)
        self.weapons = [Weapon(self.player.spec.weapon)]
        self.enemies = []
        self.projectiles = []
        self.gems = []
        self.effects = Effects(self.fx_rng)
        self.spatial.rebuild([])
        self.director = SpawnDirector()
        self.ranks = {}
        self.offers = []
        self.active_bursts = deque()
        self.elapsed = 0.0
        self.kills = 0
        self.damage_dealt = 0.0
        self.victory = False
        self.notice = "PROTOCOLO ACTIVO / SOBREVIVE 08:00"
        self.notice_color = self.player.spec.color
        self.notice_timer = 3.0
        self.state = "playing"
        self.audio.play("select")

    def announce(self, text, color="cyan"):
        self.notice, self.notice_color, self.notice_timer = text, color, 2.5

    def nearest_enemy(self, pos, radius, excluded=None):
        nearest, best = None, radius * radius
        # Long-range targeting scans the bounded population once per firing event.
        candidates = self.enemies if radius > 150 else self.spatial.query(pos, radius)
        for enemy in candidates:
            if enemy.alive and (excluded is None or enemy.uid not in excluded):
                distance = enemy.pos.distance_squared_to(pos)
                if distance <= best:
                    nearest, best = enemy, distance
        return nearest

    def drop_gem(self, pos, value, kind="xp"):
        if len(self.gems) < MAX_GEMS:
            self.gems.append(Gem(pos.copy(), value, kind, phase=self.fx_rng.random() * math.tau))
        elif kind == "xp":
            xp_gems = [gem for gem in self.gems if gem.kind == "xp"]
            if xp_gems:
                nearest = min(xp_gems, key=lambda g: g.pos.distance_squared_to(pos))
                nearest.value += value
            else:
                # At an unlikely all-medkit cap, replace one kit rather than lose XP.
                self.gems[0] = Gem(pos.copy(), value)

    def damage_enemy(self, enemy, damage, direction=None, knockback=2):
        if not enemy.alive:
            return
        critical = self.rng.random() < self.player.critical_chance
        damage *= PLAYER["critical_multiplier"] if critical else 1
        self.damage_dealt += min(enemy.health, damage)
        enemy.health -= damage
        enemy.flash = VFX["hit_flash"]
        self.effects.number(enemy.pos, damage, P["amber"] if critical else P["white"])
        self.audio.play("hit")
        if direction is not None and direction.length_squared():
            enemy.pos += direction.normalize() * knockback * (0.25 if enemy.kind == "titan" else 1)
        if critical and damage > 35:
            self.effects.shake = max(self.effects.shake, VFX["heavy_shake"])
        if enemy.health <= 0:
            enemy.alive = False
            self.kills += 1
            color = P[ENEMIES[enemy.kind]["color"]]
            self.effects.burst(enemy.pos, color, 20 if enemy.kind == "titan" else VFX["burst_particles"])
            self.audio.play("death")
            self.drop_gem(enemy.pos, enemy.xp)
            if self.rng.random() < min(0.8, SPAWN["bonus_gem_drop"] * (1 + self.player.luck)):
                self.drop_gem(enemy.pos + (4, 0), enemy.xp)
            if enemy.kind == "titan" or self.rng.random() < SPAWN["heal_drop"] * (1 + self.player.luck):
                self.drop_gem(enemy.pos + (-5, 0), SPAWN["heal_amount"], "heal")
            if enemy.kind == "titan":
                self.effects.shake = 6
                self.announce("DESBORDAMIENTO NEUTRALIZADO", "amber")

    def activate_ability(self):
        player = self.player
        if self.state != "playing" or player.active_timer > 0:
            return False
        player.active_timer = player.active_cooldown
        self.audio.play("ability")
        self.effects.ring(player.pos, 105, P[player.spec.color], 0.7)
        self.effects.shake = 2.5
        if player.character == "planner":
            player.buff_timer = ACTIVE["planner_duration"] + player.unique_rank
            for weapon in self.weapons:
                weapon.timer = min(weapon.timer, 0.1)
        elif player.character == "retriever":
            for gem in self.gems:
                gem.magnetized = True
            healed = player.heal(ACTIVE["retriever_heal"] + player.unique_rank * ACTIVE["retriever_heal_per_rank"])
            if healed:
                self.effects.number(player.pos, f"+{round(healed)}", P["green"])
            radius = ACTIVE["retriever_radius"]
            for enemy in self.spatial.query(player.pos, radius + MAX_ENEMY_RADIUS):
                if enemy.alive and enemy.pos.distance_squared_to(player.pos) < radius * radius:
                    self.damage_enemy(enemy, ACTIVE["retriever_damage"] * player.damage,
                                      enemy.pos - player.pos, ACTIVE["retriever_push"])
        else:
            player.invulnerable = max(player.invulnerable, ACTIVE["generator_invulnerability"])
            for ring in range(ACTIVE["generator_rings"]):
                self.active_bursts.append((self.elapsed + ring * ACTIVE["generator_spacing"], ring))
        self.announce(player.spec.active_name, player.spec.color)
        return True

    def auto_direction(self):
        player = self.player
        force = Vec()
        orbit_only = all(w.kind == "orbit" for w in self.weapons)
        avoid_radius = AUTOPILOT["orbit_avoid_radius"] if orbit_only else AUTOPILOT["avoid_radius"]
        nearby = self.spatial.query(player.pos, avoid_radius + MAX_ENEMY_RADIUS)
        for enemy in nearby:
            if not enemy.alive:
                continue
            offset = player.pos - enemy.pos
            distance = offset.length()
            if 0 < distance < avoid_radius:
                force += (offset / distance * (avoid_radius - distance) / max(10, distance)
                          * AUTOPILOT["avoid_strength"])
        candidates = [g for g in self.gems if g.kind == "xp" or player.health < player.max_health]
        if candidates:
            target = min(candidates, key=lambda gem: player.pos.distance_squared_to(gem.pos))
            offset = target.pos - player.pos
            if offset.length_squared() > 16:
                force += offset.normalize() * AUTOPILOT["gem_attraction"]
        elif orbit_only and (target := self.nearest_enemy(player.pos, AUTOPILOT["orbit_seek_radius"])):
            offset = target.pos - player.pos
            distance = offset.length()
            if distance:
                direction = offset / distance
                # Orbit builds need to engage instead of endlessly fleeing at range.
                if distance > AUTOPILOT["orbit_engage_distance"]:
                    force += direction
                else:
                    force += Vec(-direction.y, direction.x) * 0.45
        elif force.length_squared() < 0.1:
            force += Vec(math.cos(self.elapsed * 0.4), math.sin(self.elapsed * 0.4))
        return force.normalize() if force.length_squared() else Vec()

    def check_level_up(self):
        if self.player.xp >= self.player.xp_needed:
            # Only one level is consumed per choice. Surplus XP opens further cards.
            self.player.xp -= self.player.xp_needed
            self.player.level += 1
            self.offers = roll_upgrades(self.player, self.weapons, self.ranks, self.rng)
            self.upgrade_selected = 0
            self.state = "upgrade"
            self.audio.play("level_up")
            return True
        return False

    def choose_upgrade(self, index):
        if self.state != "upgrade" or not 0 <= index < len(self.offers):
            return
        offer = self.offers[index]
        apply_upgrade(offer, self.player, self.weapons, self.ranks)
        self.state = "playing"
        self.effects.ring(self.player.pos, 45, P[offer.color])
        self.audio.play("select")
        self.check_level_up()

    def finish_run(self, victory=False):
        self.victory = victory
        self.state = "game_over"
        self.effects.shake = 0
        self.audio.play("victory" if victory else "game_over")

    def update(self, dt, movement=None):
        dt = min(MAX_DT, max(0.0, dt))
        self.menu_time += dt
        self.audio.update(dt)
        if self.state != "playing":
            return
        self.elapsed = min(RUN_DURATION, self.elapsed + dt)
        self.notice_timer = max(0, self.notice_timer - dt)
        if movement is None:
            keys = pygame.key.get_pressed()
            movement = Vec(int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                           int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
            if not movement.length_squared() and self.player.autopilot:
                movement = self.auto_direction()
        self.player.update(dt, movement)
        self.effects.update(dt)
        self.director.update(dt, self)
        slow = ACTIVE["planner_slow"] if self.player.buff_timer > 0 else 1
        far_limit = (BASE_SIZE[0] * 1.2) ** 2
        self.enemies = [e for e in self.enemies if e.alive and
                        (e.kind == "titan" or e.pos.distance_squared_to(self.player.pos) < far_limit)]
        for enemy in self.enemies:
            enemy.update(dt, self.player, slow)
        self.spatial.rebuild(self.enemies)
        for weapon in self.weapons:
            weapon.update(dt, self)
        while self.active_bursts and self.active_bursts[0][0] <= self.elapsed:
            _, ring = self.active_bursts.popleft()
            count = ACTIVE["generator_count"] + self.player.unique_rank * ACTIVE["generator_count_per_rank"]
            for direction in radial_directions(count, ring * 0.11):
                if len(self.projectiles) < MAX_PROJECTILES:
                    self.projectiles.append(Projectile(self.player.pos.copy(), direction * ACTIVE["generator_speed"],
                        ACTIVE["generator_damage"] * self.player.damage, P["violet"], 3,
                        ACTIVE["generator_pierce"], ACTIVE["generator_projectile_life"], "shards"))
        self.projectiles = [p for p in self.projectiles if p.update(dt, self)]
        for enemy in self.spatial.query(self.player.pos, MAX_ENEMY_RADIUS + self.player.radius):
            if enemy.alive and enemy.pos.distance_squared_to(self.player.pos) <= (enemy.radius + self.player.radius) ** 2:
                taken = self.player.take_damage(enemy.damage)
                if taken:
                    self.effects.number(self.player.pos, f"-{round(taken)}", P["red"])
                    self.effects.shake = VFX["damage_shake"]
                    self.audio.play("damage")
                    self.effects.ring(self.player.pos, 15, P["red"], 0.2)
        if self.player.health <= 0:
            self.finish_run()
            return
        remaining = []
        for gem in self.gems:
            if gem.update(dt, self.player):
                if gem.kind == "heal":
                    healed = self.player.heal(gem.value)
                    if healed:
                        self.effects.number(self.player.pos, f"+{round(healed)}", P["green"])
                else:
                    self.player.gain_xp(gem.value)
                self.audio.play("pickup")
            else:
                remaining.append(gem)
        self.gems = remaining
        # Death was resolved before pickups and wins a tie with the timer.
        if self.elapsed >= RUN_DURATION:
            self.finish_run(victory=True)
        else:
            self.check_level_up()

    def canvas_mouse(self, pos):
        if not self.viewport.collidepoint(pos):
            return (-1, -1)
        return ((pos[0] - self.viewport.x) * BASE_SIZE[0] / self.viewport.w,
                (pos[1] - self.viewport.y) * BASE_SIZE[1] / self.viewport.h)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST and self.state == "playing":
            self.state = "paused"
        elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
            size = (max(BASE_SIZE[0], event.w), max(BASE_SIZE[1], event.h))
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_m:
                self.audio.toggle()
            elif key == pygame.K_F11:
                self.toggle_fullscreen()
            elif self.state == "select":
                if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.selected = key - pygame.K_1
                elif key in (pygame.K_LEFT, pygame.K_a):
                    self.selected = (self.selected - 1) % 3
                elif key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected = (self.selected + 1) % 3
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.start_run(list(CHARACTERS)[self.selected])
                elif key == pygame.K_ESCAPE:
                    self.running = False
            elif self.state == "playing":
                if key in (pygame.K_p, pygame.K_ESCAPE):
                    self.state = "paused"
                elif key == pygame.K_SPACE:
                    self.activate_ability()
                elif key == pygame.K_e:
                    self.player.autopilot = not self.player.autopilot
            elif self.state == "paused":
                if key in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = "playing"
            elif self.state == "upgrade":
                if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.choose_upgrade(key - pygame.K_1)
                elif key in (pygame.K_LEFT, pygame.K_a):
                    self.upgrade_selected = (self.upgrade_selected - 1) % 3
                elif key in (pygame.K_RIGHT, pygame.K_d):
                    self.upgrade_selected = (self.upgrade_selected + 1) % 3
                elif key == pygame.K_RETURN:
                    self.choose_upgrade(self.upgrade_selected)
            elif self.state == "game_over":
                if key in (pygame.K_r, pygame.K_RETURN):
                    self.start_run(self.player.character)
                elif key in (pygame.K_ESCAPE, pygame.K_b):
                    self.state = "select"
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            pos = self.canvas_mouse(event.pos)
            clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            if self.state == "select":
                for i, rect in enumerate(self.ui.character_rects):
                    if rect.collidepoint(pos):
                        self.selected = i
                if clicked and self.ui.deploy_rect.collidepoint(pos):
                    self.start_run(list(CHARACTERS)[self.selected])
            elif self.state == "upgrade":
                for i, rect in enumerate(self.ui.upgrade_rects):
                    if rect.collidepoint(pos):
                        self.upgrade_selected = i
                        if clicked:
                            self.choose_upgrade(i)
                        break
            elif self.state == "game_over" and clicked:
                if self.ui.restart_rect.collidepoint(pos):
                    self.start_run(self.player.character)
                elif self.ui.menu_rect.collidepoint(pos):
                    self.state = "select"

    def draw_world(self):
        camera = self.player.pos - Vec(BASE_SIZE[0] / 2, BASE_SIZE[1] / 2 + 6)
        if self.effects.shake:
            camera += Vec(self.fx_rng.uniform(-1, 1), self.fx_rng.uniform(-1, 1)) * self.effects.shake
        self.sprites.background(self.canvas, camera)
        for gem in self.gems:
            point = gem.pos - camera
            if -12 < point.x < 652 and -12 < point.y < 372:
                key = "violet" if gem.value >= 12 else "blue" if gem.value >= 5 else "green"
                sprite = self.sprites.heart if gem.kind == "heal" else self.sprites.gems[key]
                bob = round(math.sin(self.menu_time * 4 + gem.phase))
                self.canvas.blit(sprite, (round(point.x) - 4, round(point.y) - 5 + bob))
        # All grounded sprites are sorted by their feet, keeping depth consistent.
        actors = [(enemy.pos.y, False, enemy) for enemy in self.enemies if enemy.alive]
        actors.append((self.player.pos.y, True, self.player))
        for _, is_player, actor in sorted(actors, key=lambda item: item[0]):
            point = actor.pos - camera
            if not (-40 < point.x < 680 and -40 < point.y < 400):
                continue
            frame = int(self.elapsed * 7 + (0 if is_player else actor.phase)) % 2
            if is_player:
                frame = frame if actor.moving else 0
                if actor.invulnerable > 0 and int(self.menu_time * 18) % 2:
                    continue
                sprite = self.sprites.players[(actor.character, frame)]
                if actor.facing.x < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                if actor.buff_timer > 0:
                    pygame.draw.circle(self.canvas, P["cyan_dark"], (round(point.x), round(point.y)), 17, 1)
            else:
                bank = self.sprites.flashes if actor.flash > 0 else self.sprites.enemies
                sprite = bank[(actor.kind, frame)]
                if actor.kind in ("brute", "titan") and actor.health < actor.max_health:
                    self.ui.bar(self.canvas, pygame.Rect(round(point.x) - 12, round(point.y) - 25, 24, 2),
                                actor.health / actor.max_health, P["red"])
            pygame.draw.ellipse(self.canvas, P["void"], (round(point.x) - 7, round(point.y) + 4, 14, 4))
            self.canvas.blit(sprite, (round(point.x) - sprite.get_width() // 2,
                                      round(point.y) - sprite.get_height() + 7))
        for weapon in self.weapons:
            weapon.draw(self.canvas, camera, self.player)
        for shot in self.projectiles:
            point = shot.pos - camera
            x, y = round(point.x), round(point.y)
            if -15 < x < 655 and -15 < y < 375:
                direction = shot.velocity.normalize() if shot.velocity.length_squared() else Vec(1, 0)
                tail = point - direction * (14 if shot.kind == "rail" else 6)
                pygame.draw.line(self.canvas, shot.color, tail, point, 3)
                pygame.draw.rect(self.canvas, P["white"], (x - 1, y - 1, 2, 2))
        self.effects.draw(self.canvas, camera, self.ui)

    def draw(self):
        if self.state == "select":
            self.sprites.background(self.canvas, Vec(self.menu_time * 4, self.menu_time * 2))
            self.ui.selection(self.canvas, self.selected, self.menu_time, self.audio.muted)
        else:
            self.draw_world()
            self.ui.hud(self.canvas, self)
            if self.state == "upgrade":
                self.ui.upgrades(self.canvas, self, self.upgrade_selected)
            elif self.state == "paused":
                self.ui.paused(self.canvas)
            elif self.state == "game_over":
                self.ui.game_over(self.canvas, self)
        # Integer nearest-neighbor scaling with centered letterboxing, never blur.
        width, height = self.screen.get_size()
        scale = max(1, min(width // BASE_SIZE[0], height // BASE_SIZE[1]))
        size = (BASE_SIZE[0] * scale, BASE_SIZE[1] * scale)
        self.viewport = pygame.Rect(((width - size[0]) // 2, (height - size[1]) // 2), size)
        self.screen.fill(P["void"])
        self.screen.blit(pygame.transform.scale(self.canvas, size), self.viewport)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
