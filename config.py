"""All balance knobs, content definitions and the shared pixel-art palette."""
from dataclasses import dataclass

TITLE = "AGENTFALL"
VERSION = "1.0"
BASE_SIZE = (640, 360)
WINDOW_SCALE = 2
FPS = 60
MAX_DT = 0.05  # Ignore long stalls instead of teleporting through enemies.
RUN_DURATION = 8 * 60.0
TILE_SIZE = 32
GRID_CELL = 32
MAX_ENEMY_RADIUS = 15
MAX_ENEMIES = 320
MAX_PROJECTILES = 280
MAX_PARTICLES = 320
MAX_NUMBERS = 70
MAX_GEMS = 350  # Extra drops merge into a nearby gem; experience is preserved.

P = {
    "void": (10, 13, 23), "ground": (19, 25, 35), "tile": (24, 32, 43),
    "edge": (30, 41, 51), "moss": (32, 54, 54), "panel": (18, 23, 36),
    "raised": (29, 35, 52), "border": (53, 64, 82), "muted": (135, 151, 171),
    "white": (231, 240, 236), "cyan": (93, 229, 213), "cyan_dark": (38, 103, 111),
    "violet": (174, 137, 245), "violet_dark": (80, 59, 116),
    "amber": (255, 199, 103), "amber_dark": (123, 80, 50),
    "red": (246, 105, 116), "red_dark": (108, 44, 64),
    "green": (142, 216, 125), "blue": (104, 169, 239),
}

PLAYER = {
    "health": 100, "speed": 75.0, "radius": 6, "pickup": 29.0,
    "invulnerability": 0.85, "magnet_speed": 190.0,
    "critical_chance": 0.08, "critical_multiplier": 1.8,
    "max_cooldown_reduction": 0.65,
}
AUTOPILOT = {"avoid_radius": 95, "orbit_avoid_radius": 29, "orbit_engage_distance": 34,
             "orbit_seek_radius": 280, "avoid_strength": 2.0, "gem_attraction": 1.1}
SPAWN = {
    "initial_interval": 0.80, "minimum_interval": 0.16, "interval_decay": 0.0016,
    "pack_seconds": 100, "max_pack": 4, "health_per_second": 0.007,
    "speed_per_second": 0.0007, "elite_every": 75.0,
    "heal_drop": 0.035, "bonus_gem_drop": 0.10, "heal_amount": 15,
}
XP = {"base": 6, "per_level": 4, "curve": 0.30, "green": 1, "blue": 5, "violet": 12}
VFX = {"hit_flash": 0.08, "number_life": 0.65, "burst_particles": 7,
       "shake_decay": 18.0, "heavy_shake": 3.5, "damage_shake": 4.5}
AUDIO = {"rate": 22050, "volume": 0.22, "channels": 24,
         "throttle": {"shoot": 0.075, "hit": 0.055, "death": 0.04, "pickup": 0.04}}
# frequency, duration, end frequency, waveform; loaded WAV/OGG files override these.
SFX = {
    "shoot": (680, 0.055, 240, "square"),
    "hit": (180, 0.065, 70, "noise"),
    "death": (250, 0.13, 45, "square"),
    "pickup": (950, 0.075, 1450, "sine"),
    "level_up": (460, 0.48, 1350, "chord"),
    "damage": (200, 0.22, 60, "saw"),
    "ability": (180, 0.40, 1000, "chord"),
    "game_over": (390, 0.90, 65, "chord"),
    "victory": (480, 0.90, 1250, "chord"),
    "select": (650, 0.08, 850, "sine"),
}


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    role: str
    color: str
    weapon: str
    health: int
    speed: float
    damage: float
    cooldown_reduction: float
    pickup: float
    luck: float
    passive: str
    active_name: str
    active_desc: str
    active_cooldown: float


CHARACTERS = {
    "planner": CharacterSpec("PLANNER", "CONTROL / CADENCIA", "cyan", "pulse",
        95, 75, 1.0, 0.15, 29, 0,
        "15% menos espera entre ataques.", "TIEMPO COMPILADO",
        "Ralentiza enemigos 70% y acelera tus armas durante 5 s.", 23),
    "retriever": CharacterSpec("RETRIEVER", "ALCANCE / RECOLECCION", "amber", "orbit",
        110, 78, 1.0, 0, 48, 0.35,
        "+65% alcance de recogida y +35% suerte en botin.", "RECOLECCION TOTAL",
        "Atrae todas las gemas, cura 15 PV y repele enemigos.", 26),
    "generator": CharacterSpec("GENERATOR", "POTENCIA / CREACION", "violet", "shards",
        90, 72, 1.25, 0, 29, 0,
        "+25% de dano con todas las armas.", "ALUCINACION",
        "Emite 3 anillos de proyectiles perforantes y gana un escudo breve.", 20),
}
ACTIVE = {"planner_duration": 5.0, "planner_slow": 0.30, "planner_haste": 0.52,
          "retriever_heal": 15, "retriever_radius": 100, "retriever_damage": 18,
          "retriever_push": 35, "generator_rings": 3, "generator_count": 16,
          "generator_spacing": 0.16, "generator_damage": 19,
          "generator_invulnerability": 1.2, "generator_speed": 180,
          "generator_pierce": 4, "generator_projectile_life": 2.4,
          "generator_count_per_rank": 4, "retriever_heal_per_rank": 8,
          "cooldown_per_rank": 0.88}

WEAPON_MAX_LEVEL = 5
MAX_WEAPON_SLOTS = 4
WEAPON_DAMAGE_PER_LEVEL = 0.30
WEAPON_COOLDOWN_PER_LEVEL = 0.075
WEAPONS = {
    "pulse": {"name": "Pulso logico", "desc": "Dispara al enemigo mas cercano.",
        "damage": 13, "cooldown": 0.64, "speed": 215, "radius": 3,
        "color": "cyan", "evolution": "HIPERHILO",
        "evolution_desc": "Tres pulsos con perforacion adicional."},
    "shards": {"name": "Fragmentos", "desc": "Abanico de tres proyectiles.",
        "damage": 9, "cooldown": 1.25, "speed": 175, "radius": 3,
        "color": "violet", "evolution": "MULTIVERSO",
        "evolution_desc": "Siete fragmentos y mas perforacion."},
    "orbit": {"name": "Indice orbital", "desc": "Dos nodos orbitan y golpean de cerca.",
        "damage": 10, "cooldown": 0.68, "speed": 2.5, "radius": 34,
        "color": "amber", "evolution": "ARCHIVO VIVO",
        "evolution_desc": "Cinco nodos; orbita mas amplia y rapida."},
    "chain": {"name": "Red neuronal", "desc": "Rayo que salta entre tres enemigos.",
        "damage": 14, "cooldown": 1.65, "speed": 0, "radius": 82,
        "color": "blue", "evolution": "MENTE COLMENA",
        "evolution_desc": "Hasta ocho saltos; no pierde potencia."},
    "nova": {"name": "Recolector basura", "desc": "Pulso de area alrededor del agente.",
        "damage": 23, "cooldown": 3.10, "speed": 0, "radius": 48,
        "color": "green", "evolution": "REINICIO TOTAL",
        "evolution_desc": "Amplia explosion que repele amenazas."},
    "rail": {"name": "Vector lineal", "desc": "Lanza que atraviesa cuatro enemigos.",
        "damage": 22, "cooldown": 1.80, "speed": 305, "radius": 3,
        "color": "red", "evolution": "VECTOR INFINITO",
        "evolution_desc": "Doble lanza con perforacion masiva."},
}

ENEMIES = {
    "bug": {"name": "Bug", "health": 21, "speed": 25, "damage": 8,
            "radius": 6, "xp": 1, "color": "red", "unlock": 0, "weight": 6},
    "wisp": {"name": "Ruido", "health": 15, "speed": 43, "damage": 6,
             "radius": 5, "xp": 1, "color": "violet", "unlock": 25, "weight": 4},
    "brute": {"name": "Firewall", "health": 95, "speed": 17, "damage": 16,
              "radius": 10, "xp": 5, "color": "amber", "unlock": 55, "weight": 2},
    "hunter": {"name": "Inyector", "health": 47, "speed": 36, "damage": 12,
               "radius": 7, "xp": 3, "color": "green", "unlock": 125, "weight": 3},
    "titan": {"name": "DESBORDAMIENTO", "health": 750, "speed": 20, "damage": 24,
              "radius": 15, "xp": 30, "color": "red", "unlock": 0, "weight": 0},
}

# kind, title, description, maximum ranks, weight, increment.
PASSIVES = {
    "power": ("Potencia", "+12% de dano con todas las armas.", 5, 7, 0.12),
    "haste": ("Paralelismo", "-7% de espera entre ataques (limite 65%).", 5, 6, 0.07),
    "speed": ("Ruta optima", "+9% de velocidad de movimiento.", 4, 5, 0.09),
    "health": ("Redundancia", "+20 PV maximos y recupera 20 PV.", 4, 5, 20),
    "pickup": ("Contexto amplio", "+14 px de alcance para recoger gemas.", 4, 5, 14),
    "regen": ("Autorreparacion", "+0.4 PV por segundo.", 4, 3, 0.4),
    "armor": ("Sandbox", "Reduce el dano recibido en 2 (minimo 1).", 4, 4, 2),
    "luck": ("Muestreo", "+20% suerte de botin y +4% golpe critico.", 4, 3, 0.20),
    "growth": ("Aprendizaje", "+15% de experiencia de las gemas.", 4, 4, 0.15),
}
UNIQUE_UPGRADES = {
    "planner": ("Plan recursivo", "Habilidad: +1 s de duracion y -12% de recarga."),
    "retriever": ("Busqueda profunda", "Habilidad: +8 PV de cura y -12% de recarga."),
    "generator": ("Tokens infinitos", "Habilidad: +4 proyectiles por anillo y -12% de recarga."),
}
UPGRADE_WEIGHTS = {"new_weapon": 7, "weapon_level": 10, "unique": 6,
                   "unique_max": 3, "restore_amount": 30,
                   "luck_critical_bonus": 0.04, "supply_damage_bonus": 0.03}
