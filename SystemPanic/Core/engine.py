import sys
from time import perf_counter

import pygame

from SystemPanic.Core import config
from SystemPanic.Core.game_state import new_game_state, advance, GAME_MODES
from SystemPanic.Core.paks import new_paks, load_all_paks
from SystemPanic.Core.draw_util import init_font, draw_text
from SystemPanic.Core.Screens.title import draw_title_screen
from SystemPanic.Core.Screens.in_game import draw_ingame
from SystemPanic.Core.Screens.game_over import draw_game_over_screen


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

        init_font()

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
                draw_ingame(self.game_surface, self.game_state)
            elif self.game_state["game_mode"] == GAME_MODES.TITLE_SCREEN:
                draw_title_screen(self.game_surface, self.game_state)
            elif self.game_state["game_mode"] == GAME_MODES.GAME_OVER:
                draw_game_over_screen(self.game_surface, self.game_state)

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

    def draw_fps(self):
        self.pygame_clock.tick()
        fps = "FPS: {:3.3}".format(self.pygame_clock.get_fps(), )
        text_width, _ = self.font.size(fps)
        draw_text(
            self.game_surface,
            fps,
            (config.GAME_SURFACE_WIDTH - text_width - 4, 4)
        )
