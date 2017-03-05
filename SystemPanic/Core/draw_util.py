import random

import pygame

font = None

# TODO: make this toggleable
draw_hitboxes = False


def init_font():
    global font
    font = pygame.font.Font('./Core/PressStart2P-Regular.ttf', 8)


def draw_text(draw_surface, text, position, garbled=False):
    global font

    # "Flicker" effect, courtesy of randomly going back and forth
    if random.uniform(0, 1) < 0.6:
        garbled = False

    if garbled:
        draw_garbled_text(draw_surface, text, position)
        return

    # Draw the shadow first
    shadow_position = position[0] + 1, position[1] + 1

    surface = font.render(text, True, (0, 0, 0))
    draw_surface.blit(surface, shadow_position)

    # Then the actual text
    surface = font.render(text, True, (255, 255, 255))
    draw_surface.blit(surface, position)


def draw_garbled_text(draw_surface, text, position):
    text = str(text)
    for index in range(0, len(text)):
        char = text[index]
        if char == ' ':
            continue

        garbled_surface = new_garbled_char(char, font.size(text[index]))
        draw_surface.blit(
            garbled_surface,
            (position[0] + font.size(text[:index])[0], position[1])
        )


def new_garbled_char(char, char_size):
    block_density = 0.35
    rand = random.Random()
    rand.seed(ord(char))
    block_size = int(rand.uniform(1, 3))

    surface = pygame.Surface(char_size, flags=pygame.SRCALPHA)

    for x in range(0, char_size[0] // block_size):
        for y in range(0, char_size[1] // block_size):
            if rand.uniform(0, 1) < block_density:
                pygame.draw.rect(
                    surface,
                    (0, 0, 0),
                    [
                        x * block_size + 1,
                        y * block_size + 1,
                        block_size,
                        block_size
                    ]
                )
                pygame.draw.rect(
                    surface,
                    (255, 255, 255),
                    [
                        x * block_size,
                        y * block_size,
                        block_size,
                        block_size
                    ]
                )
    return surface


def draw_sprite(draw_surface, sprite_data, garbled=False):
    global draw_hitboxes

    # "Flicker" effect, courtesy of randomly going back and forth
    if random.uniform(0, 1) < 0.8:
        garbled = False

    if garbled is True:
        draw_garbled_sprite(draw_surface, sprite_data)
        return

    if sprite_data["sprite"] is None or sprite_data["sprite"]["image"] is None:
        return

    sprite = pygame.transform.scale(
        sprite_data["sprite"]["image"],
        (
            sprite_data["sprite_size"]["width"],
            sprite_data["sprite_size"]["height"]
        )
    )

    draw_surface.blit(
        sprite,
        [
            sprite_data["position"]["x"] - (sprite_data["sprite_size"]["width"] // 2),
            sprite_data["position"]["y"] - (sprite_data["sprite_size"]["height"] // 2)
        ],
    )

    if draw_hitboxes is True:
        draw_hitbox(draw_surface, sprite_data)


def draw_hitbox(draw_surface, sprite_data):
    hitbox_x_ratio = sprite_data["sprite_size"]["width"] / sprite_data["sprite"]["original size"]["width"]
    hitbox_y_ratio = sprite_data["sprite_size"]["height"] / sprite_data["sprite"]["original size"]["height"]

    x = sprite_data["position"]["x"] - (sprite_data["sprite_size"]["width"] / 2) + (
        sprite_data["sprite"]["hitbox"]["x"] * hitbox_x_ratio)
    y = sprite_data["position"]["y"] - (sprite_data["sprite_size"]["height"] / 2) + (
        sprite_data["sprite"]["hitbox"]["y"] * hitbox_y_ratio)
    width = sprite_data["sprite"]["hitbox"]["width"] * hitbox_x_ratio
    height = sprite_data["sprite"]["hitbox"]["height"] * hitbox_y_ratio

    pygame.draw.rect(
        draw_surface,
        (255, 0, 255),
        [
            int(x),
            int(y),
            int(width),
            int(height)
        ],
        2
    )


def draw_garbled_sprite(draw_surface, sprite_data):
    draw_sprite(draw_surface, sprite_data, False)

    glitch_surface, blend_mode = new_garbled_sprite(
        hash(frozenset(sprite_data["position"].items())),
        (sprite_data["sprite_size"]["width"], sprite_data["sprite_size"]["height"])
    )

    draw_surface.blit(
        glitch_surface,
        [
            sprite_data["position"]["x"] - (sprite_data["sprite_size"]["width"] // 2),
            sprite_data["position"]["y"] - (sprite_data["sprite_size"]["height"] // 2)
        ],
        special_flags=blend_mode
    )


def new_garbled_sprite(seed, char_size):
    block_density = 0.45
    rand = random.Random()
    rand.seed(seed)
    block_size = int(rand.uniform(1, 2))

    surface = pygame.Surface(char_size, flags=pygame.SRCALPHA)

    for x in range(0, char_size[0] // block_size):
        for y in range(0, char_size[1] // block_size):
            if rand.uniform(0, 1) < block_density:
                pygame.draw.rect(
                    surface,
                    (
                        int(rand.uniform(0, 255)),
                        int(rand.uniform(0, 255)),
                        int(rand.uniform(0, 255)),
                        int(rand.uniform(0, 255))
                    ),
                    [
                        x * block_size,
                        y * block_size,
                        block_size,
                        block_size
                    ]
                )

    blend_mode = rand.choice([
        pygame.BLEND_RGBA_ADD, pygame.BLEND_RGBA_SUB, pygame.BLEND_RGBA_MULT, pygame.BLEND_RGBA_MIN,
        pygame.BLEND_RGBA_MAX
    ])

    return surface, blend_mode
