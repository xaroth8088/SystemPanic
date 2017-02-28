import itertools
import os
import sys
import types
from time import perf_counter

import pygame

from SystemPanic.Core import config
from SystemPanic.Core.game_configuration import get_randomized_config
from SystemPanic.Core.game_state import next_level, new_game_state, reconfigure, advance

RANDOMIZE_CONFIGURATION_TIME = 3.0  # in seconds


class Engine:
    def __init__(self):
        # game state
        self.running = True
        self.game_state = None
        self.start_time = None
        self.last_frame_time = None
        self.last_randomize_time = None

        # pygame state
        self.screen = None
        self.game_surface = None
        self.font = None
        self.pygame_clock = None

        # paks
        self.backgrounds = []
        self.enemies = []
        self.missiles = []
        self.level_generators = []
        self.level_tiles = []
        self.music = []
        self.players = []

    def load_all_paks(self):
        # TODO: move the paks directory to be outside of SystemPanic
        # TODO: move paks handling to its own class, rather than living in the engine
        self.backgrounds = self.load_pak_images('Backgrounds')
        self.music = self.load_pak_sounds('Music')
        self.level_generators = self.load_pak_classes('LevelGenerators')
        self.enemies = self.load_pak_sprites('Enemies')
        self.level_tiles = self.load_pak_sprites('LevelTiles')
        self.missiles = self.load_pak_sprites('Missiles')
        self.players = self.load_pak_sprites('Players')

    @staticmethod
    def load_pak_classes(path):
        paks = []

        # For each directory...
        for directory in os.listdir(os.path.join('GamePaks', path)):
            # load the class included in the pak file
            pak_path = os.path.join('GamePaks', path, directory, "pak.py")
            if os.path.isfile(pak_path):
                with open(pak_path) as pak_file:
                    pak_module = types.ModuleType('pak')
                    exec(pak_file.read(), pak_module.__dict__)
                paks.append(
                    pak_module.Pak
                )

        # return our final list
        return paks

    def load_pak_sprites(self, path):
        paks = []

        # For each directory...
        for directory in os.listdir(os.path.join('GamePaks', path)):
            # load the class included in the pak file
            pak_path = os.path.join('GamePaks', path, directory, "pak.py")
            pak_png_path = os.path.join('GamePaks', path, directory, "pak.png")
            if os.path.isfile(pak_path) and os.path.isfile(pak_png_path):
                with open(pak_path) as pak_file:
                    pak_module = types.ModuleType('pak')
                    exec(pak_file.read(), pak_module.__dict__)

                # Set up the pak
                pak = new_sprite_pak()
                for func in pak.keys():
                    if func in pak_module.__dict__:
                        pak[func] = pak_module.__dict__[func]

                # Set up the spritesheet
                spritesheet = pygame.image.load(pak_png_path).convert_alpha()

                details = pak["get_sprite_details"]()
                sprites = {}
                for key, value in details.items():
                    if key not in sprites:
                        sprites[key] = []
                    for rect in value:
                        sprites[key].append(self.image_at(spritesheet, rect))

                pak["sprites"] = sprites

                paks.append(pak)

        # return our final list
        return paks

    @staticmethod
    def image_at(spritesheet, rectangle):
        rect = pygame.Rect((rectangle["x"], rectangle["y"], rectangle["width"], rectangle["height"]))
        image = pygame.Surface(rect.size, flags=pygame.SRCALPHA).convert_alpha()
        image.blit(spritesheet, (0, 0), rect)
        return image

    @staticmethod
    def load_pak_images(path):
        paks = []

        # For each directory...
        for directory in os.listdir(os.path.join('GamePaks', path)):
            # load the image included in the pak file
            pak_path = os.path.join('GamePaks', path, directory, "pak.png")
            if os.path.isfile(pak_path):
                paks.append(pygame.image.load(pak_path).convert_alpha())

        # return our final list
        return paks

    @staticmethod
    def load_pak_sounds(path):
        paks = []

        # For each directory...
        for directory in os.listdir(os.path.join('GamePaks', path)):
            # load the sound included in the pak file
            pak_path = os.path.join('GamePaks', path, directory, "pak.ogg")
            if os.path.isfile(pak_path):
                paks.append(pak_path)

        # return our final list
        return paks

    def start(self):
        self.init_pygame()
        self.load_all_paks()
        self.init_game()
        self.randomize_config()
        self.game_state = next_level(self.game_state)
        self.main()

    def init_pygame(self):
        pygame.init()
        pygame.mixer.init()

        self.font = pygame.font.Font('./Core/PressStart2P-Regular.ttf', 8)
        # self.font = pygame.font.SysFont('mono', 8, bold=True)

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

        self.game_state = new_game_state()

    def randomize_config(self):
        old_music = None
        if self.game_state["active_config"] is not None:
            old_music = self.game_state["active_config"]["music"]

        self.game_state = reconfigure(
            self.game_state,
            get_randomized_config(
                self.backgrounds,
                self.enemies,
                self.missiles,
                self.level_generators,
                self.level_tiles,
                self.music,
                self.players
            )
        )
        self.last_randomize_time = perf_counter()

        # Restart music
        if self.game_state["active_config"]["music"] != old_music:
            pygame.mixer.music.load(self.game_state["active_config"]["music"])
            pygame.mixer.music.play(-1)

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

            # Advance the frame
            self.game_state = advance(self.game_state, now - self.start_time, delta_t, pressed_buttons)

            # Decide whether it's time to re-randomize
            if now - self.last_randomize_time > RANDOMIZE_CONFIGURATION_TIME:
                self.randomize_config()

            # Draw the frame

            # Blank it out
            self.screen.fill((0, 0, 0, 0))

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

            # Add the score, FPS, etc.
            # TODO: make FPS drawing toggleable
            # self.draw_fps()

            self.draw_text("Score: %s" % (self.game_state["score"],), (8, 4))
            self.draw_text("Level: %s" % (self.game_state["level"],), (125, 4))
            self.draw_text("Lives: %s" % (self.game_state["lives"],), (240, 4))

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
        if sprite_data["sprite"] is None:
            return

        sprite = pygame.transform.scale(
            sprite_data["sprite"],
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
        # self.draw_hitbox(sprite_data)

    def draw_hitbox(self, sprite_data):
        pygame.draw.rect(
            self.screen,
            (255, 0, 255),
            [
                sprite_data["position"]["x"] - (sprite_data["sprite_size"]["width"] // 2) + sprite_data["hitbox"]["x"],
                sprite_data["position"]["y"] - (sprite_data["sprite_size"]["height"] // 2) + sprite_data["hitbox"]["y"],
                sprite_data["hitbox"]["width"],
                sprite_data["hitbox"]["height"]
            ],
            2
        )


def new_sprite_pak():
    return {
        "get_sprite_details": lambda: {},
        "advance": lambda sprites, path, game_state, time_since_start, delta_t, new_missiles: game_state,
        "collided_with_enemy": lambda player_state, enemy_state: None,
        "collided_with_player": lambda player_state, enemy_state: None,
        "collided_with_player_missile": lambda player_state, missile_state: None,
        "collided_with_enemy_missile": lambda player_state, missile_state: None,
        "collided_with_level": lambda player_state, previous_position: None,
        "get_top_left_outer": lambda sprites: None,
        "get_top_left_inner": lambda sprites: None,
        "get_top": lambda sprites: None,
        "get_top_right_outer": lambda sprites: None,
        "get_top_right_inner": lambda sprites: None,
        "get_left": lambda sprites: None,
        "get_center": lambda sprites: None,
        "get_right": lambda sprites: None,
        "get_bottom_left_outer": lambda sprites: None,
        "get_bottom_left_inner": lambda sprites: None,
        "get_bottom": lambda sprites: None,
        "get_bottom_right_outer": lambda sprites: None,
        "get_bottom_right_inner": lambda sprites: None
    }
