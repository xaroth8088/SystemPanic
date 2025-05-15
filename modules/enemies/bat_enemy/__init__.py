import pygame
import os
import random
import math

from modules.enemies import BaseEnemy

# Bat Constants
BAT_SPEED_BASE = 90  # Base speed (pixels per second)
BAT_SWOOP_SPEED_MULTIPLIER = 1.8
BAT_HEALTH = 30
BAT_CONTACT_DAMAGE = 15
BAT_ANIM_FPS = 10

# AI parameters
BAT_TARGET_Y_OFFSET_MIN = -80
BAT_TARGET_Y_OFFSET_MAX = -40
BAT_TARGET_X_OFFSET_MIN = -100
BAT_TARGET_X_OFFSET_MAX = 100
BAT_SWOOP_COOLDOWN_MIN = 3000  # ms
BAT_SWOOP_COOLDOWN_MAX = 6000  # ms
BAT_SIGHT_RADIUS_FOR_SWOOP = (
    250  # pixels, how close player needs to be for bat to consider swooping
)
BAT_LOSE_AGGRO_RADIUS_SWOOP = (
    350  # pixels, if player gets this far during swoop, bat might give up
)


class Enemy(BaseEnemy):
    SPRITE_WIDTH = 32  # Default width
    SPRITE_HEIGHT = 26  # Default height

    @staticmethod
    def load_assets(module_path):
        spritesheet_path = os.path.join(module_path, "sprite.png")
        assets = {}

        sheet = pygame.image.load(spritesheet_path).convert_alpha()
        assets["spritesheet"] = sheet
        assets["frames"] = []
        num_expected_frames = 3
        for i in range(num_expected_frames):
            frame = sheet.subsurface(
                pygame.Rect(
                    i * Enemy.SPRITE_WIDTH,
                    0,
                    Enemy.SPRITE_WIDTH,
                    Enemy.SPRITE_HEIGHT,
                )
            )
            assets["frames"].append(frame)
        return assets

    def __init__(
        self, x, y, assets, player_rect_for_ai
    ):  # player_rect_for_ai can be None
        super().__init__(x, y, assets, player_rect_for_ai)
        self.assets = assets
        self.frames = self.assets.get("frames", [])
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))

        self.health = BAT_HEALTH
        self.speed_val = random.uniform(BAT_SPEED_BASE * 0.8, BAT_SPEED_BASE * 1.2)
        self.facing_direction = random.choice([-1, 1])  # For sprite flipping

        self.vel_x = 0.0  # Current velocity x
        self.vel_y = 0.0  # Current velocity y

        self.current_frame_idx = 0
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_fps = BAT_ANIM_FPS

        # AI State
        self.ai_state = "hover"  # "hover", "swoop"
        self.target_y_offset = random.randint(
            BAT_TARGET_Y_OFFSET_MIN, BAT_TARGET_Y_OFFSET_MAX
        )
        self.target_x_offset = random.uniform(
            BAT_TARGET_X_OFFSET_MIN, BAT_TARGET_X_OFFSET_MAX
        )

        self.swoop_cooldown = random.randint(
            BAT_SWOOP_COOLDOWN_MIN, BAT_SWOOP_COOLDOWN_MAX
        )
        self.last_swoop_attempt_time = pygame.time.get_ticks() - random.randint(
            0, self.swoop_cooldown
        )  # Stagger initial swoops
        self.swoop_target_pos = None  # Store (x,y) for current swoop

    def update(self, platforms, player_rect, dt):
        current_time_ms = pygame.time.get_ticks()

        # --- AI Logic ---
        # Desired movement direction and speed based on AI state
        target_vel_x, target_vel_y = 0.0, 0.0
        current_speed_multiplier = 1.0

        if player_rect:
            player_dist_x = player_rect.centerx - self.rect.centerx
            player_dist_y = player_rect.centery - self.rect.centery
            distance_to_player = math.hypot(player_dist_x, player_dist_y)

            if self.ai_state == "hover":
                if (
                    distance_to_player < BAT_SIGHT_RADIUS_FOR_SWOOP
                    and current_time_ms - self.last_swoop_attempt_time
                    > self.swoop_cooldown
                ):
                    self.ai_state = "swoop"
                    self.swoop_target_pos = (
                        player_rect.center
                    )  # Target current player position
                    self.last_swoop_attempt_time = current_time_ms
                    self.swoop_cooldown = random.randint(
                        BAT_SWOOP_COOLDOWN_MIN, BAT_SWOOP_COOLDOWN_MAX
                    )  # Reset for next
                else:
                    # Hover logic: try to maintain offset from player
                    hover_target_x = player_rect.centerx + self.target_x_offset
                    hover_target_y = player_rect.centery + self.target_y_offset

                    dx_to_hover = hover_target_x - self.rect.centerx
                    dy_to_hover = hover_target_y - self.rect.centery

                    angle_to_hover = math.atan2(dy_to_hover, dx_to_hover)
                    target_vel_x = math.cos(angle_to_hover) * self.speed_val
                    target_vel_y = (
                        math.sin(angle_to_hover) * self.speed_val * 0.7
                    )  # Slower vertical adjustment

                    # If very close to hover point, pick new offset
                    if math.hypot(dx_to_hover, dy_to_hover) < 20:
                        self.target_x_offset = random.uniform(
                            BAT_TARGET_X_OFFSET_MIN, BAT_TARGET_X_OFFSET_MAX
                        )
                        self.target_y_offset = random.randint(
                            BAT_TARGET_Y_OFFSET_MIN, BAT_TARGET_Y_OFFSET_MAX
                        )

            elif self.ai_state == "swoop":
                current_speed_multiplier = BAT_SWOOP_SPEED_MULTIPLIER
                if self.swoop_target_pos:
                    dx_to_swoop = self.swoop_target_pos[0] - self.rect.centerx
                    dy_to_swoop = self.swoop_target_pos[1] - self.rect.centery
                    dist_to_swoop_target = math.hypot(dx_to_swoop, dy_to_swoop)

                    if (
                        dist_to_swoop_target < 20
                        or distance_to_player > BAT_LOSE_AGGRO_RADIUS_SWOOP
                    ):  # Reached target or player too far
                        self.ai_state = "hover"
                        self.swoop_target_pos = None
                    else:
                        angle_to_swoop = math.atan2(dy_to_swoop, dx_to_swoop)
                        target_vel_x = math.cos(angle_to_swoop) * self.speed_val
                        target_vel_y = math.sin(angle_to_swoop) * self.speed_val
                else:  # Should not happen if swoop_target_pos is set
                    self.ai_state = "hover"
        else:  # No player, simple erratic movement or static
            self.ai_state = (
                "hover"  # Default to hover behavior (which will be static if no player)
            )
            target_vel_x = random.uniform(-0.3, 0.3) * self.speed_val
            target_vel_y = random.uniform(-0.3, 0.3) * self.speed_val

        # Apply speed multiplier
        self.vel_x = target_vel_x * current_speed_multiplier
        self.vel_y = target_vel_y * current_speed_multiplier

        # --- Movement and Collision ---
        # Update facing direction based on horizontal velocity
        if self.vel_x > 0.1:
            self.facing_direction = 1
        elif self.vel_x < -0.1:
            self.facing_direction = -1

        # Horizontal movement and collision
        self.rect.x += self.vel_x * dt
        self.collide_with_platforms_axis(platforms, "x")

        # Vertical movement and collision
        self.rect.y += self.vel_y * dt
        self.collide_with_platforms_axis(platforms, "y")

        # Screen boundaries (clamp position and zero out velocity if hit)
        screen_rect = pygame.Rect(
            0, 0, 800, 600
        )  # Assuming 800x600, get from game ideally
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x = 0
        if self.rect.right > screen_rect.width:
            self.rect.right = screen_rect.width
            self.vel_x = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.vel_y = 0
        if self.rect.bottom > screen_rect.height:
            self.rect.bottom = screen_rect.height
            self.vel_y = 0

        self.animate(current_time_ms)

    def collide_with_platforms_axis(self, platforms, axis):
        """Handles collision with platforms along a specific axis."""
        collided_sprites = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collided_sprites:
            if axis == "x":
                if self.vel_x > 0:  # Moving right, collided
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left, collided
                    self.rect.left = platform.rect.right
                self.vel_x *= -0.5  # Bounce slightly or stop
                if self.ai_state == "swoop":
                    self.ai_state = "hover"  # Knock out of swoop
            elif axis == "y":
                if self.vel_y > 0:  # Moving down, collided
                    self.rect.bottom = platform.rect.top
                elif self.vel_y < 0:  # Moving up, collided
                    self.rect.top = platform.rect.bottom
                self.vel_y *= -0.5  # Bounce slightly or stop
                if self.ai_state == "swoop":
                    self.ai_state = "hover"  # Knock out of swoop

    def animate(self, current_time_ms):
        if not self.frames:
            return
        time_per_anim_frame = 1000 / self.anim_fps
        if current_time_ms - self.last_anim_update > time_per_anim_frame:
            self.last_anim_update = current_time_ms
            self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)

        new_image = self.frames[self.current_frame_idx]
        self.image = pygame.transform.flip(
            new_image, self.facing_direction == -1, False
        )

    def take_damage(self, amount):
        self.health -= amount
        self.health = max(0, self.health)

    def is_alive(self):
        return self.health > 0

    def deal_damage_on_contact(self):
        return BAT_CONTACT_DAMAGE

    def draw(self, surface):  # Default draw is fine for this enemy
        surface.blit(self.image, self.rect)
