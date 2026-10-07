import math
from array import array

import pygame


def _tone(freq, ms, sample_rate, volume=0.4):
    """Mono 16-bit samples of a sine wave with short fade in/out (no clicks)."""
    n = int(sample_rate * ms / 1000)
    fade = max(1, int(sample_rate * 0.008))  # 8 ms
    samples = []
    for i in range(n):
        env = min(1.0, i / fade, (n - i) / fade)
        samples.append(int(32767 * volume * env * math.sin(2 * math.pi * freq * i / sample_rate)))
    return samples


class Sounds:
    """Generates the game's sound effects in code (no audio files needed).

    If audio isn't available (no device, unsupported format), every call to
    play() silently does nothing so the game still runs.
    """

    def __init__(self):
        self.sounds = {}
        self.enabled = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=1)
            rate, fmt, channels = pygame.mixer.get_init()
            if fmt != -16:  # only signed 16-bit buffers are generated here
                return
            self.sounds = {
                # short high beep when the screen turns green
                "go": self._make(_tone(1000, 150, rate), channels),
                # low, longer buzz for a false start
                "false_start": self._make(_tone(160, 400, rate, volume=0.5), channels),
                # rising C-E-G arpeggio when the session ends
                "end": self._make(
                    _tone(523, 160, rate) + _tone(659, 160, rate) + _tone(784, 320, rate),
                    channels),
            }
            self.enabled = True
        except pygame.error:
            self.sounds = {}
            self.enabled = False

    @staticmethod
    def _make(mono_samples, channels):
        data = array("h")
        for s in mono_samples:
            data.extend([s] * channels)  # same sample on every channel
        return pygame.mixer.Sound(buffer=data.tobytes())

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()
