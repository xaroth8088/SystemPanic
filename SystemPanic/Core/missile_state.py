import pygame
from SystemPanic.Core.sprite_state import SpriteState


class MissileState(SpriteState):
    def __init__(self, initial_direction, initial_position, time_since_start):
        SpriteState.__init__(self)

        # missile-specific state
        self.position = initial_position
        if initial_direction["x"] == 0 and initial_direction["y"] == 0:
            self.direction = {
                "x": 0,
                "y": 0
            }
        else:
            dir_vector = pygame.math.Vector2(initial_direction["x"], initial_direction["y"]).normalize()
            self.direction = {
                "x": dir_vector.x,
                "y": dir_vector.y
            }

        self.start_time = time_since_start
