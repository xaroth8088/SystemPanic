import itertools
import sys
from time import perf_counter

import pygame

from SystemPanic.Core import config
from SystemPanic.Core.game_state import new_game_state, advance, GAME_MODES
from SystemPanic.Core.paks import new_paks, load_all_paks


class Engine:
    def __init__(self):
        # game state
        self.running = True
        self.game_state = None
        self.start_time = None
        self.last_frame_time = None

        # config
        self.show_fps = False
        self.show_hitboxes = False

        # pygame state
        self.screen = None
        self.game_surface = None
        self.font = None
        self.pygame_clock = None

        # paks
        self.paks = new_paks()

    def start(self):
        self.init_pygame()
        self.paks = load_all_paks()
        self.init_game()
        self.start_music(self.game_state["active_config"]["music"])
        self.main()

    def init_pygame(self):
        pygame.init()
        pygame.mixer.init()

        self.font = pygame.font.Font('./Core/PressStart2P-Regular.ttf', 8)

        self.pygame_clock = pygame.time.Clock()

        # Screen init
        size = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        # TODO: configuration / display options
        # self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.screen = pygame.display.set_mode(size, pygame.DOUBLEBUF)

        self.game_surface = pygame.Surface(
            (config.GAME_SURFACE_WIDTH, config.GAME_SURFACE_HEIGHT),
            flags=pygame.SRCALPHA
        ).convert_alpha()

        pygame.display.toggle_fullscreen()

    def init_game(self):
        # Game init
        self.start_time = perf_counter()
        self.last_frame_time = self.start_time

        self.game_state = new_game_state(self.paks, 0)

    def main(self):
        # The main game loop
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            # Get the time delta
            now = perf_counter()
            delta_t = now - self.last_frame_time
            self.last_frame_time = now

            # Get the current player input state
            pressed_buttons = self.get_pressed_buttons()

            # Keep track of the current music, in case we need to swap it out in a moment
            old_music = None
            if self.game_state["active_config"] is not None:
                old_music = self.game_state["active_config"]["music"]

            # Advance the frame
            self.game_state = advance(self.paks, self.game_state, now - self.start_time, delta_t, pressed_buttons)

            # Restart music, if needs be
            if self.game_state["active_config"]["music"] != old_music:
                self.start_music(self.game_state["active_config"]["music"])

            # Blank the screen
            self.screen.fill((0, 0, 0, 0))

            # Draw the frame
            if self.game_state["game_mode"] == GAME_MODES.IN_GAME:
                self.draw_ingame()
            elif self.game_state["game_mode"] == GAME_MODES.TITLE_SCREEN:
                self.draw_title_screen()
            elif self.game_state["game_mode"] == GAME_MODES.GAME_OVER:
                self.draw_game_over_screen()

            # TODO: make FPS drawing toggleable
            if self.show_fps is True:
                self.draw_fps()

            # Put the game surface onto the screen
            surface = pygame.transform.scale(
                self.game_surface,
                (
                    config.SCREEN_WIDTH,
                    config.SCREEN_HEIGHT
                )
            )

            self.screen.blit(
                surface,
                [
                    0,
                    0
                ],
            )

            pygame.display.flip()

    @staticmethod
    def start_music(music):
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)

    def draw_text(self, text, position):
        # Draw the shadow first
        shadow_position = position[0] + 1, position[1] + 1

        surface = self.font.render(text, True, (0, 0, 0))
        self.game_surface.blit(surface, shadow_position)

        # Then the actual text
        surface = self.font.render(text, True, (255, 255, 255))
        self.game_surface.blit(surface, position)

    def draw_fps(self):
        self.pygame_clock.tick()
        fps = "FPS: {:3.3}".format(self.pygame_clock.get_fps(), )
        text_width, _ = self.font.size(fps)
        self.draw_text(
            fps,
            (config.GAME_SURFACE_WIDTH - text_width - 4, 4)
        )

    @staticmethod
    def get_pressed_buttons():
        buttons = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "fire": False
        }

        # TODO: configurable input keys
        # TODO: joystick input
        # TODO: configurable joystick input

        # Pre-defined keyboard input
        keys_pressed = pygame.key.get_pressed()
        buttons["up"] = keys_pressed[pygame.K_UP] != 0
        buttons["down"] = keys_pressed[pygame.K_DOWN] != 0
        buttons["left"] = keys_pressed[pygame.K_LEFT] != 0
        buttons["right"] = keys_pressed[pygame.K_RIGHT] != 0
        buttons["fire"] = keys_pressed[pygame.K_SPACE] != 0

        return buttons

    def draw_sprite(self, sprite_data):
        if sprite_data["sprite"] is None or sprite_data["sprite"]["image"] is None:
            return

        sprite = pygame.transform.scale(
            sprite_data["sprite"]["image"],
            (
                sprite_data["sprite_size"]["width"],
                sprite_data["sprite_size"]["height"]
            )
        )

        self.game_surface.blit(
            sprite,
            [
                sprite_data["position"]["x"] - (sprite_data["sprite_size"]["width"] // 2),
                sprite_data["position"]["y"] - (sprite_data["sprite_size"]["height"] // 2)
            ],
        )

        # TODO: make this toggleable
        if self.show_hitboxes is True:
            self.draw_hitbox(sprite_data)

    def draw_hitbox(self, sprite_data):
        hitbox_x_ratio = sprite_data["sprite_size"]["width"] / sprite_data["sprite"]["original size"]["width"]
        hitbox_y_ratio = sprite_data["sprite_size"]["height"] / sprite_data["sprite"]["original size"]["height"]

        x = sprite_data["position"]["x"] - (sprite_data["sprite_size"]["width"] / 2) + (
            sprite_data["sprite"]["hitbox"]["x"] * hitbox_x_ratio)
        y = sprite_data["position"]["y"] - (sprite_data["sprite_size"]["height"] / 2) + (
            sprite_data["sprite"]["hitbox"]["y"] * hitbox_y_ratio)
        width = sprite_data["sprite"]["hitbox"]["width"] * hitbox_x_ratio
        height = sprite_data["sprite"]["hitbox"]["height"] * hitbox_y_ratio

        pygame.draw.rect(
            self.game_surface,
            (255, 0, 255),
            [
                int(x),
                int(y),
                int(width),
                int(height)
            ],
            2
        )

    def draw_ingame(self):
        # Add the background
        self.game_surface.blit(
            self.game_state["active_config"]["background"],
            [0, 0]
        )

        # Add the sprites (each is drawn atop the previous)
        for sprite_data in itertools.chain(
                self.game_state["walls"],
                self.game_state["enemies"],
                self.game_state["player_missiles"],
                self.game_state["enemy_missiles"],
                self.game_state["players"]
        ):
            if sprite_data["active"] is True:
                self.draw_sprite(sprite_data)

        # Add the score, etc.
        self.draw_text("Score: %s" % (self.game_state["score"],), (8, 4))
        self.draw_text("Level: %s" % (self.game_state["level"],), (125, 4))
        self.draw_text("Lives: %s" % (self.game_state["lives"],), (240, 4))

    def draw_title_screen(self):
        # Add the background
        self.game_surface.blit(
            self.game_state["active_config"]["background"],
            [0, 0]
        )

        self.draw_text("SYSTEM PANIC!", (160, 120))
        self.draw_text("PRESS FIRE TO START", (160, 130))

    def draw_game_over_screen(self):
        # Add the background
        self.game_surface.blit(
            self.game_state["active_config"]["background"],
            [0, 0]
        )

        self.draw_text("GAME OVER", (160, 120))
        self.draw_text("FINAL SCORE: %s" % (self.game_state["score"],), (160, 130))
        if self.game_state["mode_specific"].get("fade_percent") is not None:
            fade_mask = pygame.Surface(self.game_surface.get_size(), flags=pygame.SRCALPHA)
            alpha = 255 - self.game_state["mode_specific"]["fade_percent"] * 255.0
            if alpha < 0:
                alpha = 0
            fade_mask.fill((0, 0, 0, alpha))
            self.game_surface.blit(
                fade_mask,
                [0, 0]
            )
