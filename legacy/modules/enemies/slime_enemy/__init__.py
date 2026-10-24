import pygame
import os
import random
from modules.enemies import BaseEnemy

ENEMY_GRAVITY = 0.5


class Enemy(BaseEnemy):
    SPRITE_WIDTH = 32
    SPRITE_HEIGHT = 32

    @staticmethod
    def load_assets(module_path):
        spritesheet_path = os.path.join(module_path, "sprite.png")
        assets = {}
        sheet = pygame.image.load(spritesheet_path).convert_alpha()
        assets["spritesheet"] = sheet
        assets["frames"] = []
        for i in range(sheet.get_width() // Enemy.SPRITE_WIDTH):
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

    def __init__(self, x, y, assets, player_rect_for_ai):  # player_rect can be None
        super().__init__(x, y, assets, player_rect_for_ai)
        self.assets = assets
        self.frames = self.assets.get("frames", [])
        self.image = (
            self.frames[0]
            if self.frames
            else pygame.Surface([Enemy.SPRITE_WIDTH, Enemy.SPRITE_HEIGHT])
        )
        self.rect = self.image.get_rect(topleft=(x, y))

        self.health = 50
        self.speed_val = random.uniform(30, 70)  # Pixels per second
        self.vel_y = 0
        self.on_ground = False
        self.facing_direction = random.choice([-1, 1])

        self.current_frame_idx = 0
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_fps = 3

        self.ai_state = "patrol"
        self.patrol_change_dir_interval = random.randint(2000, 5000)  # ms
        self.last_patrol_dir_change = pygame.time.get_ticks()
        self.chase_dist_x = 200
        self.chase_dist_y = 50  # Vertical distance for aggro
        self.lose_aggro_dist_x = 300

    def update(self, platforms, player_rect, dt):
        dx = 0
        current_time_ms = pygame.time.get_ticks()
        speed = self.speed_val * dt

        # AI
        if player_rect:
            dist_x = player_rect.centerx - self.rect.centerx
            dist_y = abs(player_rect.centery - self.rect.centery)

            if self.ai_state == "patrol":
                if abs(dist_x) < self.chase_dist_x and dist_y < self.chase_dist_y:
                    self.ai_state = "chase"
                else:
                    if (
                        current_time_ms - self.last_patrol_dir_change
                        > self.patrol_change_dir_interval
                    ):
                        self.facing_direction *= -1
                        self.last_patrol_dir_change = current_time_ms
                        self.patrol_change_dir_interval = random.randint(2000, 5000)
                    dx = speed * self.facing_direction

            elif self.ai_state == "chase":
                if (
                    abs(dist_x) > self.lose_aggro_dist_x
                    or dist_y > self.chase_dist_y * 2
                ):
                    self.ai_state = "patrol"
                    self.last_patrol_dir_change = current_time_ms  # Reset patrol timer
                else:
                    self.facing_direction = 1 if dist_x > 0 else -1
                    dx = speed * self.facing_direction * 1.5  # Chase faster
        else:  # No player, just patrol
            self.ai_state = "patrol"
            if (
                current_time_ms - self.last_patrol_dir_change
                > self.patrol_change_dir_interval
            ):
                self.facing_direction *= -1
                self.last_patrol_dir_change = current_time_ms
            dx = speed * self.facing_direction

        self.vel_y += ENEMY_GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy = self.vel_y

        self.rect.x += dx
        self.collide_with_platforms(dx, 0, platforms)
        self.rect.y += dy
        self.on_ground = False
        self.collide_with_platforms(0, dy, platforms)

        if self.rect.top > 600 + Enemy.SPRITE_HEIGHT:
            self.kill()

        self.animate(current_time_ms)

    def collide_with_platforms(self, dx, dy, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    self.rect.right = platform.rect.left
                    self.facing_direction = -1  # Turn on wall hit
                if dx < 0:
                    self.rect.left = platform.rect.right
                    self.facing_direction = 1  # Turn on wall hit
                if dy > 0:
                    self.rect.bottom = platform.rect.top
                    self.on_ground = True
                    self.vel_y = 0
                if dy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

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
        if self.health <= 0:
            self.health = 0  # is_alive will handle kill

    def is_alive(self):
        return self.health > 0

    def deal_damage_on_contact(self):
        return 10

    def draw(self, surface):
        surface.blit(self.image, self.rect)
