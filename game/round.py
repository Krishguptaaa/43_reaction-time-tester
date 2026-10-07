import random
import pygame

class Round:
    def __init__(self, min_wait_ms=1000, max_wait_ms=3000):
        self.wait_delay_ms = random.randint(min_wait_ms, max_wait_ms)
        # "waiting" -> "go" -> "result"
        # "waiting" -> "false_start"  (input before the screen turned green)
        self.state = "waiting"
        self.start_time = pygame.time.get_ticks()
        self.go_time = None
        self.reaction_ms = None

    def update(self):
        if self.state == "waiting":
            now = pygame.time.get_ticks()
            if now - self.start_time >= self.wait_delay_ms:
                self.state = "go"
                self.go_time = now

    def register_input(self):
        """Handle a click/Space press.

        Returns the reaction time in ms for a valid reaction, or None if the
        input was a false start (pressed during the grey wait phase) or the
        round was already finished.
        """
        if self.state == "waiting":
            # Too early: not a reaction, so no time is recorded.
            self.state = "false_start"
            return None

        if self.state == "go":
            # Measure from the moment the screen turned green.
            self.reaction_ms = pygame.time.get_ticks() - self.go_time
            self.state = "result"
            return self.reaction_ms

        # "result" / "false_start": round already decided, ignore.
        return None
