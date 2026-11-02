"""Bounded particle pools, damage labels, shockwaves and lightning traces."""
from dataclasses import dataclass
import math
import pygame
from config import MAX_NUMBERS, MAX_PARTICLES, P, VFX


@dataclass
class Particle:
    pos: pygame.Vector2
    velocity: pygame.Vector2
    life: float
    color: tuple
    size: int


@dataclass
class Number:
    pos: pygame.Vector2
    text: str
    color: tuple
    life: float = VFX["number_life"]


@dataclass
class Ring:
    pos: pygame.Vector2
    radius: float
    max_radius: float
    life: float
    total: float
    color: tuple


class Effects:
    def __init__(self, rng):
        self.rng = rng
        self.particles = []
        self.numbers = []
        self.rings = []
        self.traces = []
        self.shake = 0.0

    def burst(self, pos, color, count=VFX["burst_particles"]):
        for _ in range(min(count, MAX_PARTICLES - len(self.particles))):
            angle = self.rng.random() * math.tau
            speed = self.rng.uniform(12, 65)
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            self.particles.append(Particle(pos.copy(), velocity, self.rng.uniform(0.18, 0.5), color,
                                           self.rng.choice((1, 1, 2))))

    def number(self, pos, value, color=P["white"]):
        if len(self.numbers) < MAX_NUMBERS:
            text = str(value) if isinstance(value, str) else str(round(value))
            self.numbers.append(Number(pos.copy() + (self.rng.randrange(-4, 5), -12), text, color))

    def ring(self, pos, radius, color, life=0.4):
        self.rings.append(Ring(pos.copy(), 3, radius, life, life, color))
        self.rings = self.rings[-24:]

    def trace(self, points, color):
        self.traces.append([list(points), color, 0.15])
        self.traces = self.traces[-20:]

    def update(self, dt):
        self.shake = max(0.0, self.shake - VFX["shake_decay"] * dt)
        for p in self.particles:
            p.life -= dt
            p.pos += p.velocity * dt
            p.velocity *= max(0, 1 - dt * 3)
        self.particles = [p for p in self.particles if p.life > 0]
        for number in self.numbers:
            number.life -= dt
            number.pos.y -= dt * 21
        self.numbers = [n for n in self.numbers if n.life > 0]
        for ring in self.rings:
            ring.life -= dt
            ring.radius = ring.max_radius * (1 - (max(0, ring.life) / ring.total) ** 2)
        self.rings = [r for r in self.rings if r.life > 0]
        for trace in self.traces:
            trace[2] -= dt
        self.traces = [t for t in self.traces if t[2] > 0]

    def draw(self, target, camera, ui):
        for p in self.particles:
            point = p.pos - camera
            pygame.draw.rect(target, p.color, (round(point.x), round(point.y), p.size, p.size))
        for ring in self.rings:
            point = ring.pos - camera
            pygame.draw.circle(target, ring.color, (round(point.x), round(point.y)),
                               max(1, round(ring.radius)), 1 if ring.life < 0.12 else 2)
        for points, color, _ in self.traces:
            points = [(round(p.x - camera.x), round(p.y - camera.y)) for p in points]
            if len(points) > 1:
                pygame.draw.lines(target, color, False, points, 2)
                pygame.draw.lines(target, P["white"], False, points, 1)
        for number in self.numbers:
            ui.text(target, number.text, number.pos - camera, 14, number.color, center=True)
