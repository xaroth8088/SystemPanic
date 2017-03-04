import pygame

font = None

# TODO: make this toggleable
draw_hitboxes = False


def init_font():
    global font
    font = pygame.font.Font('./Core/PressStart2P-Regular.ttf', 8)


def draw_text(draw_surface, text, position):
    global font
    # Draw the shadow first
    shadow_position = position[0] + 1, position[1] + 1

    surface = font.render(text, True, (0, 0, 0))
    draw_surface.blit(surface, shadow_position)

    # Then the actual text
    surface = font.render(text, True, (255, 255, 255))
    draw_surface.blit(surface, position)


def draw_sprite(draw_surface, sprite_data):
    global draw_hitboxes

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
