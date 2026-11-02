"""Swappable WAV/OGG loader with self-contained synthesized PCM fallbacks."""
from array import array
from pathlib import Path
import math
import random
import pygame
from config import AUDIO, SFX


class Audio:
    def __init__(self, muted=False, asset_dir=None):
        self.muted = muted
        self.available = False
        self.sounds = {}
        self.clock = 0.0
        self.last_played = {}
        self.asset_dir = Path(asset_dir or Path(__file__).parent / "assets" / "audio")
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(AUDIO["rate"], -16, 1, 512, allowedchanges=0)
            pygame.mixer.set_num_channels(AUDIO["channels"])
            for name, params in SFX.items():
                self.sounds[name] = self.load_sound(name, params)
                self.sounds[name].set_volume(AUDIO["volume"])
            self.available = True
        except (pygame.error, OSError, ValueError):
            # A missing device must never prevent the game from being playable.
            self.available = False

    def load_sound(self, name, params):
        for extension in ("wav", "ogg"):
            path = self.asset_dir / f"{name}.{extension}"
            if path.exists():
                try:
                    return pygame.mixer.Sound(str(path))
                except pygame.error:
                    pass
        rate, sample_size, channels = pygame.mixer.get_init()
        if sample_size != -16:
            raise ValueError("Synthesized sounds require signed 16-bit PCM")
        frequency, duration, end, waveform = params
        samples = array("h")
        rng = random.Random(name)
        phase = 0.0
        for i in range(int(rate * duration)):
            t = i / rate
            fraction = t / duration
            phase += math.tau * (frequency + (end - frequency) * fraction) / rate
            if waveform == "square":
                value = 0.55 if math.sin(phase) >= 0 else -0.55
            elif waveform == "saw":
                value = 2 * ((phase / math.tau) % 1) - 1
            elif waveform == "noise":
                value = rng.uniform(-1, 1) * 0.7 + math.sin(phase) * 0.3
            elif waveform == "chord":
                value = (math.sin(phase) + 0.5 * math.sin(phase * 1.25)
                         + 0.4 * math.sin(phase * 1.5)) / 1.9
            else:
                value = math.sin(phase)
            envelope = min(1.0, t / 0.008) * (1 - fraction) ** 1.5
            sample = int(value * envelope * 21000)
            samples.extend([sample] * channels)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def update(self, dt):
        self.clock += dt

    def play(self, name):
        if not self.available or self.muted or name not in self.sounds:
            return
        throttle = AUDIO["throttle"].get(name, 0.08)
        if self.clock - self.last_played.get(name, -100) < throttle:
            return
        self.last_played[name] = self.clock
        self.sounds[name].play()

    def toggle(self):
        self.muted = not self.muted
        if self.muted and self.available:
            pygame.mixer.stop()
