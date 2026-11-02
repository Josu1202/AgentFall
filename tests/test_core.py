"""Headless integration checks. Uses only the standard library and pygame."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import math
import random
import unittest
from unittest.mock import patch
import pygame
from audio import Audio
from config import (ACTIVE, AUDIO, CHARACTERS, ENEMIES, MAX_ENEMIES, MAX_GEMS,
                    P, PASSIVES, PLAYER, RUN_DURATION, SFX, UPGRADE_WEIGHTS,
                    WEAPONS, WEAPON_MAX_LEVEL)
from enemies import Enemy
from entities import Gem, Player, Projectile, segment_distance_squared
from game import Game
from spatial import SpatialHash
from upgrades import Upgrade, apply_upgrade, available_upgrades, roll_upgrades
from weapons import Weapon


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.mixer.pre_init(AUDIO["rate"], -16, 1, 512)
        pygame.init()
        cls.game = Game(seed=71, muted=True)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.game.start_run("planner")

    def enemy(self, uid=1, pos=(25, 0), kind="bug", health=None):
        enemy = Enemy.create(uid, kind, pos, self.game.elapsed)
        if health is not None:
            enemy.health = enemy.max_health = health
        self.game.enemies.append(enemy)
        self.game.spatial.rebuild(self.game.enemies)
        return enemy

    def test_all_character_passives_and_starting_weapons(self):
        for key, spec in CHARACTERS.items():
            self.game.start_run(key)
            self.assertEqual(self.game.weapons[0].kind, spec.weapon)
            self.assertEqual(self.game.player.health, spec.health)
            self.assertEqual(self.game.player.damage, spec.damage)
        self.assertGreater(Player("retriever").pickup_range, Player("planner").pickup_range)
        self.assertLess(Player("planner").cooldown_multiplier, Player("generator").cooldown_multiplier)

    def test_diagonal_movement_is_normalized(self):
        p = self.game.player
        p.update(1, pygame.Vector2(1, 1))
        self.assertAlmostEqual(p.pos.length(), p.speed)

    def test_invulnerability_and_armor_minimum(self):
        p = self.game.player
        p.armor = 100
        self.assertEqual(p.take_damage(5), 1)
        self.assertEqual(p.take_damage(5), 0)
        p.update(PLAYER["invulnerability"] + 0.01, pygame.Vector2())
        self.assertEqual(p.take_damage(5), 1)

    def test_pause_and_upgrade_freeze_simulation(self):
        enemy = self.enemy()
        for state in ("paused", "upgrade", "game_over"):
            self.game.state = state
            old_pos, old_time = enemy.pos.copy(), self.game.elapsed
            self.game.update(0.05, pygame.Vector2(1, 0))
            self.assertEqual(enemy.pos, old_pos)
            self.assertEqual(self.game.elapsed, old_time)

    def test_exact_threshold_and_surplus_levels(self):
        game = self.game
        p = game.player
        first = p.xp_needed
        p.level += 1
        second = p.xp_needed
        p.level -= 1
        p.gain_xp(first + second + 1)
        self.assertTrue(game.check_level_up())
        self.assertEqual(p.level, 2)
        game.choose_upgrade(0)
        self.assertEqual(p.level, 3)
        self.assertEqual(game.state, "upgrade")
        game.choose_upgrade(0)
        self.assertEqual(game.state, "playing")
        self.assertAlmostEqual(p.xp, 1)

    def test_upgrade_offers_unique_and_legal_for_every_character(self):
        for key in CHARACTERS:
            p = Player(key)
            weapons = [Weapon(p.spec.weapon)]
            for seed in range(30):
                cards = roll_upgrades(p, weapons, {}, random.Random(seed))
                self.assertEqual(len(cards), 3)
                self.assertEqual(len({(o.kind, o.key) for o in cards}), 3)
                self.assertTrue(all(o.kind != "unique" or o.key == key for o in cards))
            weapons = [Weapon(k) for k in list(WEAPONS)[:4]]
            offered = available_upgrades(p, weapons, {})
            self.assertTrue(all(o.key in [w.kind for w in weapons]
                                for o in offered if o.kind == "weapon"))

    def test_evolution_and_maxed_build_fallbacks(self):
        p = self.game.player
        weapons = [Weapon(k) for k in list(WEAPONS)[:4]]
        for weapon in weapons:
            for _ in range(WEAPON_MAX_LEVEL - 1):
                weapon.upgrade()
            self.assertFalse(weapon.evolved)
            weapon.upgrade()
            self.assertTrue(weapon.evolved)
        ranks = {key: data[2] for key, data in PASSIVES.items()}
        p.unique_rank = UPGRADE_WEIGHTS["unique_max"]
        cards = roll_upgrades(p, weapons, ranks, random.Random(8))
        self.assertEqual(len(cards), 3)
        self.assertTrue(all(card.kind == "supply" for card in cards))

    def test_all_passives_apply_and_cooldown_cap(self):
        p = self.game.player
        before = p.max_health
        for key in PASSIVES:
            card = Upgrade(key, "passive", "", "", "", "cyan", 1)
            apply_upgrade(card, p, self.game.weapons, self.game.ranks)
        self.assertEqual(p.max_health, before + PASSIVES["health"][4])
        self.assertGreater(p.regen, 0)
        for _ in range(20):
            apply_upgrade(Upgrade("haste", "passive", "", "", "", "cyan", 1),
                          p, self.game.weapons, self.game.ranks)
        self.assertEqual(p.cooldown_reduction, PLAYER["max_cooldown_reduction"])

    def test_swept_projectile_and_piercing_do_not_rehit(self):
        game = self.game
        first = self.enemy(1, (10, 0), health=100)
        second = self.enemy(2, (28, 0), health=100)
        shot = Projectile(pygame.Vector2(), pygame.Vector2(1000, 0), 10, P["cyan"], pierce=1)
        self.assertFalse(shot.update(0.05, game))
        self.assertLess(first.health, 100)
        self.assertLess(second.health, 100)
        self.assertEqual(shot.hit_ids, {1, 2})
        self.assertEqual(segment_distance_squared(pygame.Vector2(10, 2), pygame.Vector2(), pygame.Vector2(20, 0)), 4)

    def test_hash_supports_negative_world_coordinates(self):
        enemy = self.enemy(pos=(-35, -35))
        grid = SpatialHash()
        grid.rebuild([enemy])
        self.assertIn(enemy, grid.query(pygame.Vector2(-32, -32), 10))

    def test_gem_cap_preserves_experience_and_magnetization(self):
        game = self.game
        for i in range(MAX_GEMS + 12):
            game.drop_gem(pygame.Vector2(i, 0), 2)
        self.assertEqual(len(game.gems), MAX_GEMS)
        self.assertEqual(sum(g.value for g in game.gems), (MAX_GEMS + 12) * 2)
        gem = Gem(pygame.Vector2(500, 0), 5, magnetized=True)
        for _ in range(300):
            if gem.update(1 / 60, game.player):
                break
        else:
            self.fail("Magnetized gem did not reach the player")

    def test_character_actives_and_cooldown(self):
        game = self.game
        for key in CHARACTERS:
            game.start_run(key)
            game.player.health -= 30
            game.gems = [Gem(pygame.Vector2(500, 0), 5)]
            self.assertTrue(game.activate_ability())
            self.assertFalse(game.activate_ability())
            if key == "planner":
                self.assertGreater(game.player.buff_timer, 0)
            elif key == "retriever":
                self.assertTrue(game.gems[0].magnetized)
                self.assertEqual(game.player.health, game.player.max_health - 30 + ACTIVE["retriever_heal"])
            else:
                game.update(0.01, pygame.Vector2())
                self.assertGreaterEqual(len(game.projectiles), ACTIVE["generator_count"])
                self.assertGreater(game.player.invulnerable, 0)

    def test_each_weapon_can_kill_and_evolve(self):
        game = self.game
        for kind in WEAPONS:
            game.start_run("planner")
            weapon = Weapon(kind)
            weapon.level = WEAPON_MAX_LEVEL
            weapon.upgrade()
            game.weapons = [weapon]
            pos = weapon.orb_positions(game.player)[0] if kind == "orbit" else pygame.Vector2(20, 0)
            self.enemy(pos=pos, health=1)
            for _ in range(60):
                game.update(1 / 60, pygame.Vector2())
            self.assertGreaterEqual(game.kills, 1, kind)

    def test_elites_and_population_cap(self):
        game = self.game
        game.elapsed = 76
        for i in range(MAX_ENEMIES):
            self.enemy(uid=i, pos=(200, 0))
        game.director.update(0.05, game)
        self.assertLessEqual(len(game.enemies), MAX_ENEMIES)
        self.assertTrue(any(e.kind == "titan" for e in game.enemies))

    def test_run_finish_death_victory_and_clean_restart(self):
        game = self.game
        game.player.health = 0
        game.update(0.01, pygame.Vector2())
        self.assertEqual(game.state, "game_over")
        self.assertFalse(game.victory)
        game.start_run("generator")
        self.assertEqual(game.kills, 0)
        self.assertEqual(game.elapsed, 0)
        self.assertFalse(game.enemies)
        self.assertFalse(game.active_bursts)
        game.elapsed = RUN_DURATION - 0.01
        game.update(0.02, pygame.Vector2())
        self.assertEqual(game.state, "game_over")
        self.assertTrue(game.victory)

    def test_keyboard_and_mouse_state_navigation(self):
        game = self.game
        game.state = "select"
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3))
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(game.player.character, "generator")
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
        self.assertEqual(game.state, "paused")
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(game.state, "playing")
        game.player.xp = game.player.xp_needed
        game.check_level_up()
        game.draw()
        rect = game.ui.upgrade_rects[1]
        pos = (game.viewport.x + rect.centerx * 2, game.viewport.y + rect.centery * 2)
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
        self.assertEqual(game.state, "playing")

    def test_orbit_autopilot_engages_outside_contact_radius(self):
        game = self.game
        game.start_run("retriever")
        self.enemy(pos=(110, 0))
        self.assertGreater(game.auto_direction().x, 0)

    def test_lethal_hit_cannot_be_revived_by_same_frame_pickup(self):
        game = self.game
        game.player.health = 1
        self.enemy(pos=(0, 0))
        game.gems = [Gem(pygame.Vector2(), 15, "heal")]
        game.update(0.01, pygame.Vector2())
        self.assertEqual(game.state, "game_over")
        self.assertEqual(game.player.health, 0)

    def test_audio_device_failure_has_silent_fallback(self):
        with patch("audio.pygame.mixer.get_init", return_value=None), \
                patch("audio.pygame.mixer.init", side_effect=pygame.error("No audio device")):
            audio = Audio()
            self.assertFalse(audio.available)
            audio.play("shoot")

    def test_mixer_generated_all_sfx_and_all_screens_render(self):
        game = self.game
        self.assertTrue(game.audio.available)
        self.assertEqual(set(game.audio.sounds), set(SFX))
        for sound in game.audio.sounds.values():
            self.assertGreater(sound.get_length(), 0)
        game.draw()
        for state in ("select", "paused", "game_over"):
            game.state = state
            game.draw()
        game.state = "playing"
        game.player.xp = game.player.xp_needed
        game.check_level_up()
        game.draw()


if __name__ == "__main__":
    unittest.main()
