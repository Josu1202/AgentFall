"""Readable low-resolution HUD, character dossiers and keyboard/mouse menus."""
from functools import lru_cache
import math
import pygame
from config import (BASE_SIZE, CHARACTERS, MAX_WEAPON_SLOTS, P, RUN_DURATION,
                    TITLE, VERSION, WEAPONS)


def time_string(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02}:{seconds % 60:02}"


class UI:
    character_rects = [pygame.Rect(24 + i * 200, 99, 192, 214) for i in range(3)]
    upgrade_rects = [pygame.Rect(24 + i * 200, 104, 192, 202) for i in range(3)]
    deploy_rect = pygame.Rect(438, 325, 178, 24)
    restart_rect = pygame.Rect(189, 274, 262, 27)
    menu_rect = pygame.Rect(189, 306, 262, 22)

    def __init__(self, sprites):
        self.sprites = sprites
        self.fonts = {}

    @lru_cache(maxsize=1200)
    def rendered(self, text, size, color):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size].render(text, False, color)

    def text(self, target, text, pos, size=16, color=P["white"], center=False, right=False):
        image = self.rendered(str(text), size, tuple(color))
        rect = image.get_rect()
        if center:
            rect.midtop = (round(pos[0]), round(pos[1]))
        elif right:
            rect.topright = (round(pos[0]), round(pos[1]))
        else:
            rect.topleft = (round(pos[0]), round(pos[1]))
        target.blit(image, rect)
        return rect

    def wrapped(self, target, text, pos, width, size=16, color=P["muted"], line_height=None):
        line_height = line_height or size
        words = text.split()
        line = ""
        y = pos[1]
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and self.rendered(candidate, size, tuple(color)).get_width() > width:
                self.text(target, line, (pos[0], y), size, color)
                y += line_height
                line = word
            else:
                line = candidate
        if line:
            self.text(target, line, (pos[0], y), size, color)
            y += line_height
        return y

    @staticmethod
    def panel(target, rect, color=P["border"], fill=P["panel"], selected=False):
        pygame.draw.rect(target, P["void"], rect.move(3, 4))
        pygame.draw.rect(target, fill, rect)
        pygame.draw.rect(target, color, rect, 2 if selected else 1)
        # Small cut-corner marks give panels the same terminal-like visual language.
        pygame.draw.rect(target, color, (rect.x, rect.y, 6, 3))
        pygame.draw.rect(target, color, (rect.right - 6, rect.bottom - 3, 6, 3))

    @staticmethod
    def bar(target, rect, fraction, color, back=P["raised"]):
        pygame.draw.rect(target, back, rect)
        fill = rect.copy()
        fill.width = max(0, min(rect.width, round(rect.width * fraction)))
        if fill.width:
            pygame.draw.rect(target, color, fill)
            pygame.draw.line(target, P["white"], fill.topleft, (fill.right - 1, fill.top))

    @staticmethod
    def dim(target, alpha=190):
        shade = pygame.Surface(BASE_SIZE, pygame.SRCALPHA)
        shade.fill((*P["void"], alpha))
        target.blit(shade, (0, 0))

    def button(self, target, rect, label, selected=True, color=P["cyan"]):
        self.panel(target, rect, color if selected else P["border"],
                   P["raised"] if selected else P["panel"], selected)
        self.text(target, label, (rect.centerx, rect.y + 6), 17,
                  color if selected else P["muted"], center=True)

    def selection(self, target, selected, elapsed, muted):
        self.dim(target, 125)
        self.text(target, "SISTEMA DE CONTENCION / 08:00", (25, 15), 15, P["cyan"])
        self.text(target, TITLE, (23, 31), 56)
        self.text(target, "SOBREVIVE AL DESBORDAMIENTO", (26, 76), 15, P["muted"])
        self.text(target, f"V{VERSION}  /  LOCAL", (614, 22), 14, P["muted"], right=True)
        self.text(target, "TRES AGENTES. UNA ULTIMA EJECUCION.", (614, 46), 15, P["amber"], right=True)
        keys = list(CHARACTERS)
        for index, rect in enumerate(self.character_rects):
            key = keys[index]
            spec = CHARACTERS[key]
            color = P[spec.color]
            active = selected == index
            self.panel(target, rect, color if active else P["border"], selected=active)
            pygame.draw.rect(target, color if active else P["border"], (rect.x + 1, rect.y + 1, rect.w - 2, 3))
            self.text(target, spec.name, (rect.x + 12, rect.y + 12), 22, color)
            self.text(target, f"0{index + 1}", (rect.right - 12, rect.y + 14), 17, P["muted"], right=True)
            self.text(target, spec.role, (rect.x + 12, rect.y + 32), 13, P["muted"])
            portrait = pygame.transform.scale(self.sprites.players[(key, int(elapsed * 3) % 2)], (36, 44))
            target.blit(portrait, (rect.x + 15, rect.y + 54))
            self.text(target, f"PV  {spec.health}", (rect.x + 66, rect.y + 52), 16)
            self.text(target, f"DANO  {round(spec.damage * 100)}%", (rect.x + 66, rect.y + 68), 15, P["muted"])
            self.text(target, f"VEL  {spec.speed:.0f}   CD -{spec.cooldown_reduction:.0%}",
                      (rect.x + 66, rect.y + 83), 13, P["muted"])
            icon = self.sprites.icons[spec.weapon]
            target.blit(icon, (rect.x + 11, rect.y + 103))
            self.text(target, WEAPONS[spec.weapon]["name"], (rect.x + 31, rect.y + 105), 16)
            self.wrapped(target, spec.passive, (rect.x + 12, rect.y + 126), rect.w - 24, 14, line_height=13)
            pygame.draw.line(target, P["border"], (rect.x + 12, rect.y + 155), (rect.right - 12, rect.y + 155))
            self.text(target, f"[ESP] {spec.active_name}", (rect.x + 12, rect.y + 164), 13, color)
            self.wrapped(target, f"{spec.active_desc} Recarga: {spec.active_cooldown:.0f}s.",
                         (rect.x + 12, rect.y + 180), rect.w - 24, 13, line_height=11)
        self.text(target, "1-3 / FLECHAS: ELEGIR   |   M: " + ("SONIDO OFF" if muted else "SONIDO ON"),
                  (25, 327), 14, P["muted"])
        self.text(target, "WASD: MOVER   ESPACIO: HABILIDAD   E: AUTOPILOTO", (25, 343), 12, P["muted"])
        self.button(target, self.deploy_rect, "ENTER  /  DESPLEGAR")

    def hud(self, target, game):
        player = game.player
        pygame.draw.rect(target, P["void"], (0, 0, 640, 35))
        pygame.draw.rect(target, P["border"], (0, 35, 640, 1))
        color = P[player.spec.color]
        self.text(target, player.spec.name, (11, 6), 17, color)
        self.bar(target, pygame.Rect(11, 23, 123, 5), player.health / player.max_health, P["red"])
        self.text(target, f"{math.ceil(player.health)}/{int(player.max_health)}", (142, 20), 13, P["muted"])
        self.text(target, time_string(game.elapsed), (320, 2), 27, center=True)
        self.text(target, f"OBJETIVO  {time_string(RUN_DURATION)}", (320, 23), 12, P["muted"], center=True)
        self.text(target, f"{game.kills:04}  ELIMINADOS", (627, 6), 18, right=True)
        self.text(target, f"SECTOR {1 + int(game.elapsed // 60):02}  /  NIVEL {player.level:02}",
                  (627, 23), 13, P["muted"], right=True)
        self.bar(target, pygame.Rect(0, 36, 640, 3), player.xp / player.xp_needed, color)
        pygame.draw.rect(target, P["void"], (0, 322, 640, 38))
        pygame.draw.line(target, P["border"], (0, 322), (640, 322))
        for index in range(MAX_WEAPON_SLOTS):
            rect = pygame.Rect(10 + index * 45, 327, 39, 25)
            pygame.draw.rect(target, P["raised"], rect)
            if index < len(game.weapons):
                weapon = game.weapons[index]
                target.blit(self.sprites.icons[weapon.kind], (rect.x + 3, rect.y + 3))
                self.text(target, "E" if weapon.evolved else str(weapon.level),
                          (rect.right - 9, rect.y + 6), 15, P[WEAPONS[weapon.kind]["color"]])
            else:
                self.text(target, "+", (rect.x + 14, rect.y + 6), 17, P["border"])
        ready = player.active_timer <= 0
        self.text(target, "[ESP] " + player.spec.active_name, (205, 328), 15,
                  color if ready else P["muted"])
        self.bar(target, pygame.Rect(205, 345, 185, 3), 1 - player.active_timer / player.active_cooldown, color)
        self.text(target, "LISTA" if ready else f"{player.active_timer:.1f}s", (399, 335), 14,
                  color if ready else P["muted"])
        self.text(target, "[E] AUTO " + ("ON" if player.autopilot else "OFF"), (629, 328), 14,
                  color if player.autopilot else P["muted"], right=True)
        self.text(target, "[P] PAUSA   [M] " + ("MUDO" if game.audio.muted else "SONIDO"),
                  (629, 344), 12, P["muted"], right=True)
        if game.notice_timer > 0:
            rect = pygame.Rect(145, 48, 350, 23)
            self.panel(target, rect, P[game.notice_color])
            self.text(target, game.notice, (320, 54), 16, P[game.notice_color], center=True)
        if game.elapsed < 8:
            self.text(target, "LAS ARMAS DISPARAN SOLAS. RECOGE GEMAS PARA MEJORAR.",
                      (320, 296), 14, P["muted"], center=True)

    def upgrades(self, target, game, selected):
        self.dim(target, 215)
        self.text(target, "APRENDIZAJE COMPLETADO", (320, 31), 17, P["cyan"], center=True)
        self.text(target, f"NIVEL {game.player.level:02}", (320, 51), 42, center=True)
        self.text(target, "ELIGE UNA MEJORA PARA CONTINUAR", (320, 87), 14, P["muted"], center=True)
        for index, (rect, offer) in enumerate(zip(self.upgrade_rects, game.offers)):
            color = P[offer.color]
            self.panel(target, rect, color if index == selected else P["border"], selected=index == selected)
            self.text(target, f"0{index + 1}", (rect.x + 13, rect.y + 13), 22, color)
            self.text(target, offer.label, (rect.x + 13, rect.y + 43), 13, color)
            if offer.kind == "weapon":
                icon = pygame.transform.scale(self.sprites.icons[offer.key], (32, 32))
                target.blit(icon, (rect.right - 49, rect.y + 12))
            else:
                pygame.draw.rect(target, color, (rect.right - 38, rect.y + 20, 13, 13), 2)
                pygame.draw.line(target, color, (rect.right - 32, rect.y + 15), (rect.right - 32, rect.y + 38))
                pygame.draw.line(target, color, (rect.right - 43, rect.y + 26), (rect.right - 20, rect.y + 26))
            bottom = self.wrapped(target, offer.title, (rect.x + 13, rect.y + 69), rect.w - 26, 23,
                                  P["white"], line_height=21)
            self.wrapped(target, offer.description, (rect.x + 13, bottom + 13), rect.w - 26, 17, line_height=17)
            self.text(target, "ELEGIR  >" if index == selected else "DISPONIBLE", (rect.x + 13, rect.bottom - 24),
                      14, color if index == selected else P["border"])
        self.text(target, "1 / 2 / 3 O CLIC PARA ELEGIR  |  FLECHAS + ENTER", (320, 327), 15,
                  P["muted"], center=True)
        self.text(target, "SIMULACION EN PAUSA", (320, 346), 12, P["border"], center=True)

    def paused(self, target):
        self.dim(target, 200)
        rect = pygame.Rect(154, 89, 332, 181)
        self.panel(target, rect, P["cyan"])
        self.text(target, "EJECUCION SUSPENDIDA", (320, 110), 29, center=True)
        self.text(target, "WASD / FLECHAS   MOVER", (320, 154), 17, P["muted"], center=True)
        self.text(target, "ESPACIO   HABILIDAD     E   AUTOPILOTO", (320, 178), 16, P["muted"], center=True)
        self.text(target, "M   SONIDO     F11   PANTALLA COMPLETA", (320, 201), 16, P["muted"], center=True)
        self.text(target, "P / ESC PARA CONTINUAR", (320, 241), 18, P["cyan"], center=True)

    def game_over(self, target, game):
        self.dim(target, 215)
        color = P["cyan"] if game.victory else P["red"]
        self.text(target, "CONTENCION COMPLETA" if game.victory else "CONEXION PERDIDA", (320, 26), 18,
                  color, center=True)
        self.text(target, "EJECUCION EXITOSA" if game.victory else "FIN DE LA PARTIDA", (320, 49), 42,
                  center=True)
        self.text(target, game.player.spec.name + "  /  " + time_string(game.elapsed), (320, 91), 18,
                  P["muted"], center=True)
        rect = pygame.Rect(139, 123, 362, 127)
        self.panel(target, rect)
        stats = [("ELIMINADOS", str(game.kills)), ("NIVEL", str(game.player.level)),
                 ("DANO TOTAL", f"{int(game.damage_dealt):,}"),
                 ("EXPERIENCIA", str(int(game.player.total_xp)))]
        for i, (label, value) in enumerate(stats):
            x = 158 + (i % 2) * 178
            y = 134 + (i // 2) * 40
            self.text(target, label, (x, y), 13, P["muted"])
            self.text(target, value, (x, y + 13), 25, color)
        build = "  /  ".join(w.name for w in game.weapons)
        self.wrapped(target, build, (158, 220), 330, 13, P["muted"], line_height=12)
        self.button(target, self.restart_rect, "R / ENTER   REINTENTAR", color=color)
        self.button(target, self.menu_rect, "ESC   CAMBIAR AGENTE", False)
        self.text(target, "OTRA EJECUCION. OTRA POSIBILIDAD.", (320, 344), 12, P["muted"], center=True)
