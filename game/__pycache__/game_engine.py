import pygame
from .round import Round

# Game Engine

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)
RED = (190, 55, 55)
LIGHT_GREEN = (150, 235, 170)
LIGHT_RED = (255, 170, 170)

class GameEngine:
    def __init__(self, width, height, rounds_total=5, min_wait_ms=1000, max_wait_ms=3000):
        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self.reaction_times = []

        self.result_shown_at = None
        self.result_pause_ms = 800        # pause on the result screen between rounds
        self.false_start_pause_ms = 1200  # pause on the "too early" screen

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)
        self.small_font = pygame.font.SysFont("Arial", 24)
        self.game_over = False
        self.game_over_at = None
        # Ignore input briefly after the results appear so a late/mashed click
        # from the last round can't dismiss the screen before it's seen.
        self.results_lockout_ms = 600

    def handle_event(self, event):
        if self.game_over:
            self._handle_results_event(event)
            return
        is_click = event.type == pygame.MOUSEBUTTONDOWN
        is_space = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
        if not (is_click or is_space):
            return
        # Only react while the round is still live; ignore input during the
        # result / false-start pause screens.
        if self.round.state not in ("waiting", "go"):
            return

        reaction_ms = self.round.register_input()
        self.result_shown_at = pygame.time.get_ticks()
        # A false start returns None: it is shown to the player but is NOT
        # recorded, so it doesn't use up one of the rounds.
        if reaction_ms is not None:
            self.reaction_times.append(reaction_ms)

    def _handle_results_event(self, event):
        # Wait for the player: any key press or click closes the game cleanly
        # (main.py's loop handles pygame.QUIT). Task 3 will replace this with
        # a replay / difficulty choice.
        if pygame.time.get_ticks() - self.game_over_at < self.results_lockout_ms:
            return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_input(self):
        # Reserved for continuously-held-key input; every action here
        # is a discrete click/keypress, handled in handle_event.
        pass

    def update(self):
        if self.game_over:
            return

        self.round.update()

        now = pygame.time.get_ticks()
        if self.round.state == "result":
            if now - self.result_shown_at >= self.result_pause_ms:
                self._start_next_round()
        elif self.round.state == "false_start":
            if now - self.result_shown_at >= self.false_start_pause_ms:
                self._start_next_round()  # same round number, fresh random delay

    def _start_next_round(self):
        if len(self.reaction_times) >= self.rounds_total:
            self.game_over = True
            self.game_over_at = pygame.time.get_ticks()
            return
        self.round = Round(self.min_wait_ms, self.max_wait_ms)

    def average_reaction_ms(self):
        if not self.reaction_times:
            return 0
        return round(sum(self.reaction_times) / len(self.reaction_times))

    def render_results(self, screen):
        screen.fill(BLUE)
        cx = self.width // 2

        title = self.big_font.render("Session Complete", True, WHITE)
        screen.blit(title, title.get_rect(center=(cx, 40)))

        times = self.reaction_times
        best, worst = min(times), max(times)

        # One column for short sessions, two when there are many rounds.
        cols = 1 if len(times) <= 6 else 2
        rows = -(-len(times) // cols)  # ceil division
        row_h = 32
        top = 90
        col_w = self.width // cols
        for i, t in enumerate(times):
            colour = LIGHT_GREEN if t == best else LIGHT_RED if t == worst else WHITE
            line = self.font.render(f"Round {i + 1}:  {t} ms", True, colour)
            col, row = divmod(i, rows)
            x = col * col_w + col_w // 2
            screen.blit(line, line.get_rect(center=(x, top + row * row_h)))

        avg = self.big_font.render(f"Average: {self.average_reaction_ms()} ms", True, WHITE)
        screen.blit(avg, avg.get_rect(center=(cx, 305)))

        summary = self.small_font.render(f"Best: {best} ms     Worst: {worst} ms", True, WHITE)
        screen.blit(summary, summary.get_rect(center=(cx, 345)))

        locked = pygame.time.get_ticks() - self.game_over_at < self.results_lockout_ms
        prompt_text = "" if locked else "Press any key or click to exit"
        prompt = self.small_font.render(prompt_text, True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(cx, 378)))

    def render(self, screen):
        if self.game_over:
            self.render_results(screen)
            return

        sub_message = None
        if self.round.state == "waiting":
            bg = GRAY
            message = "Wait for green..."
        elif self.round.state == "go":
            bg = GREEN
            message = "Click now!"
        elif self.round.state == "false_start":
            bg = RED
            message = "Too early!"
            sub_message = "False start - this round will be redone"
        else:
            bg = BLUE
            message = f"{self.round.reaction_ms} ms"

        screen.fill(bg)

        text_surf = self.big_font.render(message, True, WHITE)
        text_rect = text_surf.get_rect(center=(self.width // 2, self.height // 2))
        screen.blit(text_surf, text_rect)

        if sub_message:
            sub_surf = self.font.render(sub_message, True, WHITE)
            sub_rect = sub_surf.get_rect(center=(self.width // 2, self.height // 2 + 50))
            screen.blit(sub_surf, sub_rect)

        round_num = min(len(self.reaction_times) + 1, self.rounds_total)
        round_text = self.font.render(f"Round {round_num}/{self.rounds_total}", True, WHITE)
        screen.blit(round_text, (10, 10))

        avg_text = self.font.render(f"Avg: {self.average_reaction_ms()} ms", True, WHITE)
        screen.blit(avg_text, (self.width - 190, 10))
