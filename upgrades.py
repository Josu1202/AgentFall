"""Weighted, duplicate-free upgrade offers. Applying an offer is explicit."""
from dataclasses import dataclass
from config import (MAX_WEAPON_SLOTS, PASSIVES, PLAYER, UNIQUE_UPGRADES,
                    UPGRADE_WEIGHTS, WEAPONS, WEAPON_MAX_LEVEL)
from weapons import Weapon


@dataclass(frozen=True)
class Upgrade:
    key: str
    kind: str
    title: str
    description: str
    label: str
    color: str
    weight: float


def available_upgrades(player, weapons, ranks):
    offers = []
    owned = {weapon.kind: weapon for weapon in weapons}
    for kind, spec in WEAPONS.items():
        if kind in owned:
            weapon = owned[kind]
            if not weapon.can_upgrade:
                continue
            evolve = weapon.level == WEAPON_MAX_LEVEL
            title = spec["evolution"] if evolve else spec["name"]
            if evolve:
                description = spec["evolution_desc"]
            else:
                next_weapon = Weapon(kind)
                next_weapon.level = weapon.level + 1
                description = (f"Dano {weapon.damage(player):.0f} > {next_weapon.damage(player):.0f}. "
                               f"Espera {weapon.cooldown(player):.2f} > {next_weapon.cooldown(player):.2f}s.")
                if kind == "pulse" and next_weapon.level == 4:
                    description += " +1 pulso por ataque."
                elif kind == "shards" and next_weapon.level == 3:
                    description += " +1 fragmento por ataque."
                elif kind == "orbit" and next_weapon.level == 3:
                    description += " +1 nodo orbital."
                elif kind == "chain" and next_weapon.level % 2 == 0:
                    description += " +1 salto del rayo."
                elif kind == "nova":
                    description += " +4 px de radio."
            offers.append(Upgrade(kind, "weapon", title, description,
                "EVOLUCION" if evolve else f"ARMA / NIVEL {weapon.level + 1}",
                spec["color"], UPGRADE_WEIGHTS["weapon_level"]))
        elif len(weapons) < MAX_WEAPON_SLOTS:
            offers.append(Upgrade(kind, "weapon", spec["name"], spec["desc"],
                "NUEVA ARMA", spec["color"], UPGRADE_WEIGHTS["new_weapon"]))
    for key, (title, description, maximum, weight, _) in PASSIVES.items():
        rank = ranks.get(key, 0)
        if rank < maximum and not (key == "haste" and
                                  player.cooldown_reduction >= PLAYER["max_cooldown_reduction"]):
            offers.append(Upgrade(key, "passive", title, description,
                                  f"PASIVA / {rank + 1} DE {maximum}", "cyan", weight))
    if player.unique_rank < UPGRADE_WEIGHTS["unique_max"]:
        title, description = UNIQUE_UPGRADES[player.character]
        offers.append(Upgrade(player.character, "unique", title, description,
            f"EXCLUSIVA / {player.unique_rank + 1} DE 3", player.spec.color,
            UPGRADE_WEIGHTS["unique"]))
    return offers


def roll_upgrades(player, weapons, ranks, rng):
    pool = available_upgrades(player, weapons, ranks)
    chosen = []
    while pool and len(chosen) < 3:
        offer = rng.choices(pool, weights=[item.weight for item in pool], k=1)[0]
        chosen.append(offer)
        pool.remove(offer)
    # Endgame still offers exactly three distinct choices once builds are maxed.
    fallbacks = [
        Upgrade("restore", "supply", "Parche de emergencia", "+30 PV; se limita a la salud maxima.", "SUMINISTRO", "green", 1),
        Upgrade("overclock", "supply", "Ciclo adicional", "+3% de dano para esta partida.", "SUMINISTRO", "violet", 1),
        Upgrade("refresh", "supply", "Cache lista", "La habilidad activa queda lista de inmediato.", "SUMINISTRO", "amber", 1),
    ]
    for offer in fallbacks:
        if len(chosen) == 3:
            break
        chosen.append(offer)
    rng.shuffle(chosen)
    return chosen


def apply_upgrade(offer, player, weapons, ranks):
    if offer.kind == "weapon":
        weapon = next((w for w in weapons if w.kind == offer.key), None)
        if weapon:
            weapon.upgrade()
        elif len(weapons) < MAX_WEAPON_SLOTS:
            weapons.append(Weapon(offer.key))
    elif offer.kind == "unique":
        player.unique_rank += 1
        player.active_timer = min(player.active_timer, player.active_cooldown)
    elif offer.kind == "passive":
        ranks[offer.key] = ranks.get(offer.key, 0) + 1
        amount = PASSIVES[offer.key][4]
        if offer.key == "power":
            player.damage += amount
        elif offer.key == "haste":
            player.cooldown_reduction = min(PLAYER["max_cooldown_reduction"], player.cooldown_reduction + amount)
        elif offer.key == "speed":
            player.speed += player.spec.speed * amount
        elif offer.key == "health":
            player.max_health += amount
            player.heal(amount)
        elif offer.key == "pickup":
            player.pickup_range += amount
        elif offer.key == "regen":
            player.regen += amount
        elif offer.key == "armor":
            player.armor += amount
        elif offer.key == "luck":
            player.luck += amount
            player.critical_chance += UPGRADE_WEIGHTS["luck_critical_bonus"]
        elif offer.key == "growth":
            player.growth += amount
    elif offer.key == "restore":
        player.heal(UPGRADE_WEIGHTS["restore_amount"])
    elif offer.key == "overclock":
        player.damage += UPGRADE_WEIGHTS["supply_damage_bonus"]
    elif offer.key == "refresh":
        player.active_timer = 0
