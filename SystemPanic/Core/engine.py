import itertools
import os
import sys
import importlib
from time import perf_counter

import pygame

from SystemPanic.Core import config
from SystemPanic.Core.game_configuration import get_randomized_config
from SystemPanic.Core.game_state import next_level, new_game_state, reconfigure, advance
from SystemPanic.Core.sprite_state import new_sprite

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
                paks.append(
                    importlib.import_module("GamePaks.%s.%s.pak" % (path, directory,)).Pak
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
                pak = {
                    "class": importlib.import_module("GamePaks.%s.%s.pak" % (path, directory,)).Pak
                }

                spritesheet = pygame.image.load(pak_png_path).convert_alpha()

                details = pak["class"]().get_sprite_details()
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

        self.font = pygame.font.SysFont('mono', 20, bold=True)
        self.pygame_clock = pygame.time.Clock()

        # Screen init
        size = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        # TODO: work on a 800x600 surface, and scale up to whatever fullscreen mode we can do
        # TODO: configuration / display options
        # self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.screen = pygame.display.set_mode(size, pygame.DOUBLEBUF)
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
            self.screen.blit(
                self.game_state["active_config"]["background"],
                [0, 0]
            )

            # Add the walls, enemies, player missiles, enemy missiles, and player (in that order)
            for sprite_data in itertools.chain(
                    self.game_state["walls"],
                    self.game_state["enemies"],
                    self.game_state["player_missiles"],
                    self.game_state["enemy_missiles"],
                    [self.game_state["player"]]
            ):
                if sprite_data["active"] is True:
                    self.draw_sprite(sprite_data)

            # Add the score, FPS, etc.
            # TODO: make FPS drawing toggleable
            self.draw_fps()

            self.draw_text("Score: %s" % (self.game_state["score"],), (8, 8))
            self.draw_text("Level: %s" % (self.game_state["level"],), (200, 8))
            self.draw_text("Lives: %s" % (self.game_state["lives"],), (400, 8))

            pygame.display.flip()

    def draw_text(self, text, position):
        surface = self.font.render(text, True, (0, 255, 0))
        self.screen.blit(surface, position)

    def draw_fps(self):
        self.pygame_clock.tick()
        fps = "FPS: {:3.3}".format(self.pygame_clock.get_fps(), )
        text_width, _ = self.font.size(fps)
        self.draw_text(
            fps,
            (config.SCREEN_WIDTH - text_width - 8, 8)
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
        sprite = pygame.transform.scale(
            sprite_data["sprite"],
            (
                sprite_data["sprite_size"]["width"],
                sprite_data["sprite_size"]["height"]
            )
        )

        self.screen.blit(
            sprite,
            [
                sprite_data["position"]["x"] - (sprite_data["sprite_size"]["width"] // 2),
                sprite_data["position"]["y"] - (sprite_data["sprite_size"]["height"] // 2)
            ],
        )

        # TODO: make this toggleable
        self.draw_hitbox(sprite_data)

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
