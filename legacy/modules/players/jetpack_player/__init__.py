import pygame
import os
import math
from modules.players import BasePlayer

# --- Jetpack Player Constants ---
PLAYER_MAX_SPEED = 250  # Max speed in any direction (pixels per second)
THRUST_FORCE = 500  # Acceleration from thrusters (pixels per second^2)
DRAG_COEFFICIENT = (
    0.985  # Multiplier for velocity each frame (closer to 1 means less drag)
)
# Applied as: vel *= DRAG_COEFFICIENT ^ (dt * 60) to be frame-rate independent
WEAK_GRAVITY = 15  # Slight downward pull (pixels per second^2)

MAX_FUEL = 100.0
FUEL_REGEN_RATE = 10.0  # Fuel per second
FUEL_CONSUMPTION_RATE = 30.0  # Fuel per second while thrusting

BOMB_COOLDOWN = 1000  # Milliseconds
BOMB_DAMAGE = 40
BOMB_LIFETIME = 3000  # Milliseconds
BOMB_DROP_SPEED = 120  # Pixels per second, downwards


class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y, assets):
        super().__init__()
        self.image_orig = assets.get("projectile_image")
        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = BOMB_DROP_SPEED
        self.damage = BOMB_DAMAGE
        self.lifetime = BOMB_LIFETIME
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt=1 / 60.0):  # dt is delta time in seconds
        self.rect.y += self.speed_y * dt
        # Check screen boundaries (assuming screen_height is around 600)
        # A more robust way would be to pass screen_height or get it from a global config
        if (
            pygame.time.get_ticks() - self.spawn_time > self.lifetime
            or self.rect.top > 700
        ):  # Give some leeway
            self.kill()


class Player(BasePlayer):
    SPRITE_WIDTH = 32  # Default if spritesheet fails
    SPRITE_HEIGHT = 32  # Default if spritesheet fails

    @staticmethod
    def load_assets(module_path):
        spritesheet_path = os.path.join(module_path, "sprite.png")
        projectile_image_path = os.path.join(
            module_path, "projectile.png"
        )  # Bomb image
        assets = {}

        sprite_width_from_sheet = Player.SPRITE_WIDTH
        sprite_height_from_sheet = Player.SPRITE_HEIGHT

        sheet = pygame.image.load(spritesheet_path).convert_alpha()
        assets["spritesheet"] = sheet

        assets["projectile_image"] = pygame.image.load(
            projectile_image_path
        ).convert_alpha()

        assets["frames"] = []
        num_expected_frames = 3  # Idle, Thrust, Fire
        for i in range(num_expected_frames):
            # Use sprite_width_from_sheet if derived, else Player.SPRITE_WIDTH
            frame = sheet.subsurface(
                pygame.Rect(
                    i * sprite_width_from_sheet,
                    0,
                    sprite_width_from_sheet,
                    sprite_height_from_sheet,
                )
            )
            assets["frames"].append(frame)

        # Update class attributes if derived from sheet, for main.py's enemy spawn logic
        Player.SPRITE_WIDTH = sprite_width_from_sheet
        Player.SPRITE_HEIGHT = sprite_height_from_sheet
        return assets

    def __init__(self, x, y, assets):
        super().__init__(x, y, assets)
        self.assets = assets
        self.frames = self.assets.get("frames", [])
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.health = 120
        self.facing_direction = (
            1  # 1 for right, -1 for left (visual only for this player)
        )

        self.current_fuel = MAX_FUEL
        self.is_thrusting_visual = False  # For animation state if thrusters are active
        self.is_firing_anim = False  # For attack animation state

        self.projectiles = pygame.sprite.Group()  # Stores bombs
        self.can_attack = True
        self.last_attack_timestamp = 0
        self.attack_anim_duration = 300  # ms for the firing animation

        self.current_anim_frame_idx = 0  # Used by animate method
        self.last_anim_update_time = pygame.time.get_ticks()
        # self.anim_fps = 5 # Not used for this simple animation

    def update(self, keys, platforms, dt):  # dt is delta time in seconds
        current_time_ms = pygame.time.get_ticks()
        self.is_thrusting_visual = False  # Reset visual flag each frame

        # Regenerate Fuel
        self.current_fuel += FUEL_REGEN_RATE * dt
        self.current_fuel = min(self.current_fuel, MAX_FUEL)

        # Input and Thrust
        thrust_applied_this_frame = False
        if self.current_fuel > 0:
            if keys[pygame.K_LEFT]:
                self.vel_x -= THRUST_FORCE * dt
                self.facing_direction = -1
                thrust_applied_this_frame = True
            if keys[pygame.K_RIGHT]:
                self.vel_x += THRUST_FORCE * dt
                self.facing_direction = 1
                thrust_applied_this_frame = True
            if keys[pygame.K_UP]:
                self.vel_y -= THRUST_FORCE * dt
                thrust_applied_this_frame = True
            if keys[pygame.K_DOWN]:
                self.vel_y += THRUST_FORCE * dt * 0.7  # Less powerful downward thrust
                thrust_applied_this_frame = True

        if thrust_applied_this_frame:
            self.is_thrusting_visual = True
            self.current_fuel -= FUEL_CONSUMPTION_RATE * dt
            self.current_fuel = max(0, self.current_fuel)

        # Apply weak gravity / downward drift
        self.vel_y += WEAK_GRAVITY * dt

        # Apply drag (frame-rate independent)
        # The (dt * 60.0) part normalizes the exponent so DRAG_COEFFICIENT feels consistent
        # regardless of FPS, assuming it was tuned for 60 FPS.
        self.vel_x *= DRAG_COEFFICIENT ** (dt * 60.0)
        self.vel_y *= DRAG_COEFFICIENT ** (dt * 60.0)

        # Limit speed
        speed_magnitude_sq = self.vel_x**2 + self.vel_y**2
        if speed_magnitude_sq > PLAYER_MAX_SPEED**2:
            speed_magnitude = math.sqrt(speed_magnitude_sq)
            if speed_magnitude > 0:  # Avoid division by zero
                scale_factor = PLAYER_MAX_SPEED / speed_magnitude
                self.vel_x *= scale_factor
                self.vel_y *= scale_factor

        # Threshold to stop tiny movements (helps prevent infinite small drifts)
        # Adjust threshold based on typical dt values if needed
        stop_threshold = 0.5
        if abs(self.vel_x) < stop_threshold * (dt * 60):
            self.vel_x = 0
        if (
            abs(self.vel_y) < stop_threshold * (dt * 60)
            and not thrust_applied_this_frame
            and WEAK_GRAVITY < stop_threshold
        ):
            self.vel_y = 0

        # Attack (drop bomb)
        if keys[pygame.K_SPACE] and self.can_attack:
            self.attack()

        if (
            not self.can_attack
            and current_time_ms - self.last_attack_timestamp > BOMB_COOLDOWN
        ):
            self.can_attack = True

        if (
            self.is_firing_anim
            and current_time_ms - self.last_attack_timestamp > self.attack_anim_duration
        ):
            self.is_firing_anim = False  # End firing animation

        # --- Collision Handling ---
        # Move horizontally, then check for X collisions
        self.rect.x += self.vel_x * dt
        self.collide_with_platforms_axis(platforms, "x")

        # Move vertically, then check for Y collisions
        self.rect.y += self.vel_y * dt
        self.collide_with_platforms_axis(platforms, "y")

        # Screen boundaries (ensure player stays within screen)
        # Assuming screen_width=800, screen_height=600. These should ideally be passed or global.
        screen_rect = pygame.Rect(0, 0, 800, 600)
        if not screen_rect.contains(self.rect):  # If outside, clamp and adjust velocity
            if self.rect.left < 0:
                self.rect.left = 0
                self.vel_x = 0
            if self.rect.right > 800:
                self.rect.right = 800
                self.vel_x = 0
            if self.rect.top < 0:
                self.rect.top = 0
                self.vel_y = 0
            if self.rect.bottom > 600:
                self.rect.bottom = 600
                self.vel_y = 0

        self.animate(current_time_ms)
        self.projectiles.update(dt)

    def collide_with_platforms_axis(self, platforms, axis):
        collided_sprites = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collided_sprites:
            if axis == "x":
                if self.vel_x > 0:  # Moving right, collided
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left, collided
                    self.rect.left = platform.rect.right
                self.vel_x = 0  # Stop horizontal movement on collision
            elif axis == "y":
                if self.vel_y > 0:  # Moving down, collided
                    self.rect.bottom = platform.rect.top
                elif self.vel_y < 0:  # Moving up, collided
                    self.rect.top = platform.rect.bottom
                self.vel_y = 0  # Stop vertical movement on collision

    def animate(self, current_time_ms):
        if not self.frames:
            return

        target_frame_idx = 0  # Default to Idle (frame 0)
        if self.is_firing_anim and len(self.frames) > 2:
            target_frame_idx = 2  # Firing frame
        elif self.is_thrusting_visual and len(self.frames) > 1:
            target_frame_idx = 1  # Thrusting frame
            if current_time_ms // 100 % 2 == 0:  # Every 100ms, alternate
                target_frame_idx = 0  # Briefly show idle during thrust for flicker

        # This simple animation just sets the frame, no timed cycling here.
        # If more complex (e.g. multi-frame thrust), you'd update self.current_anim_frame_idx
        self.image = self.frames[target_frame_idx]

        # Jetpack player sprite might not need horizontal flipping, or always faces forward.
        # If flipping is desired:
        # self.image = pygame.transform.flip(self.frames[target_frame_idx], self.facing_direction == -1, False)

    def attack(self):  # Drop bomb
        self.last_attack_timestamp = pygame.time.get_ticks()
        self.can_attack = False
        self.is_firing_anim = True  # Trigger firing animation visual

        # Bomb drops from slightly below the player
        bomb_x = self.rect.centerx
        bomb_y = self.rect.bottom + 8  # Small offset below player
        self.projectiles.add(Bomb(bomb_x, bomb_y, self.assets))

    def take_damage(self, amount):
        self.health -= amount
        self.health = max(0, self.health)  # Ensure health doesn't go below 0
        # print(f"Jetpack Player took {amount} damage, health: {self.health}")

    def is_alive(self):
        return self.health > 0

    def draw(self, surface):  # Custom draw to include fuel bar
        surface.blit(self.image, self.rect)

        # Draw Fuel Bar above player
        # Only draw if not full or always draw for visibility
        # if self.current_fuel < MAX_FUEL or True:
        bar_total_width = Player.SPRITE_WIDTH
        bar_height = 5
        fuel_percentage = self.current_fuel / MAX_FUEL if MAX_FUEL > 0 else 0.0

        current_fuel_bar_width = int(bar_total_width * fuel_percentage)
        bar_pos_x = self.rect.left
        bar_pos_y = self.rect.top - bar_height - 3  # Position 3 pixels above player

        # Background of the fuel bar (e.g., dark grey)
        pygame.draw.rect(
            surface, (50, 50, 50), (bar_pos_x, bar_pos_y, bar_total_width, bar_height)
        )
        # Actual fuel portion (e.g., light blue)
        pygame.draw.rect(
            surface,
            (50, 150, 255),
            (bar_pos_x, bar_pos_y, current_fuel_bar_width, bar_height),
        )

    def handle_event(self, event):
        # This player type primarily uses continuous key checks (get_pressed) in update().
        # Single key press events (like for a menu) could be handled here if needed.
        pass
