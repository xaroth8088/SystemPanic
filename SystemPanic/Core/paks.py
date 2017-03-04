from copy import deepcopy
import os
import types
import pygame


Paks = {
    "backgrounds": [],
    "enemies": [],
    "missiles": [],
    "level_generators": [],
    "level_tiles": [],
    "music": [],
    "players": []
}


def new_paks():
    return deepcopy(Paks)


def load_all_paks():
    paks = new_paks()

    paks["backgrounds"] = load_pak_images('Backgrounds')

    paks["music"] = load_pak_sounds('Music')

    paks["level_generators"] = load_pak_classes('LevelGenerators')

    paks["enemies"] = load_pak_sprites('Enemies')
    paks["level_tiles"] = load_pak_sprites('LevelTiles')
    paks["missiles"] = load_pak_sprites('Missiles')
    paks["players"] = load_pak_sprites('Players')

    return paks


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


def load_pak_sprites(path):
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
            spritesheet_raw_image = pygame.image.load(pak_png_path).convert_alpha()

            details = pak["get_sprite_details"]()

            sprites = {}
            for key, value in details.items():
                if key not in sprites:
                    sprites[key] = []
                for sprite_spec in value:
                    sprites[key].append(construct_sprite(spritesheet_raw_image, sprite_spec))

            pak["sprites"] = sprites

            paks.append(pak)

    # return our final list
    return paks


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


def construct_sprite(spritesheet_image, sprite_spec):
    rect = pygame.Rect((sprite_spec["image rect"]["x"], sprite_spec["image rect"]["y"],
                        sprite_spec["image rect"]["width"], sprite_spec["image rect"]["height"]))
    image = pygame.Surface(rect.size, flags=pygame.SRCALPHA).convert_alpha()
    image.blit(spritesheet_image, (0, 0), rect)
    return {
        "image": image,
        "original size": sprite_spec["image rect"],
        "hitbox": sprite_spec["hitbox"]
    }


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
