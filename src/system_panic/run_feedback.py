"""Presentation-only hull feedback and the input-free interval after defeat."""
import pygame

GAME_OVER_SECONDS = 1.3
RELEASE_SECONDS = .3


def desaturate_hull(surface, scratch, health, maximum):
    amount = max(0., min(1., 1. - health / max(1., maximum) / .2))
    if amount:
        pygame.transform.grayscale(surface, scratch)
        scratch.set_alpha(round(255 * amount))
        surface.blit(scratch, (0, 0))


class GameOverTransition:
    def __init__(self):
        self.elapsed = 0.
        self.quiet = 0.
        self.input_seen = False

    def pressed(self):
        self.quiet = 0.
        self.input_seen = True

    def update(self, elapsed, neutral):
        self.elapsed += elapsed
        self.quiet = self.quiet + elapsed if neutral and not self.input_seen else 0.
        self.input_seen = False
        return self.elapsed >= GAME_OVER_SECONDS and self.quiet >= RELEASE_SECONDS
