
# modules/players/knight_player/__init__.py
# SPRITESHEET_LAYOUT_NOTE:
# Spritesheet should be horizontal. Frame dimensions: 32w x 48h.
# Frame 0: Idle
# Frame 1: Walk 1
# Frame 2: Walk 2
# Frame 3: Jump
# Frame 4: Attack
# Total image: 160w x 48h.

import pygame
import os
from modules.players import BasePlayer

PLAYER_GRAVITY = 0.5 
PLAYER_SPEED_BASE = 200 # Pixels per second
PLAYER_JUMP_STRENGTH = -12 
PROJECTILE_SPEED = 400 # Pixels per second

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, assets):
        super().__init__()
        self.image_orig = assets.get('projectile_image')
        if not self.image_orig: 
            self.image_orig = pygame.Surface([10, 5], pygame.SRCALPHA)
            self.image_orig.fill((255,255,0)) 
        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(x,y))
        self.speed_val = PROJECTILE_SPEED 
        self.direction = direction 
        self.damage = 25

    def update(self, dt=1/60.0): # Add dt for frame-independent movement
        self.rect.x += self.speed_val * self.direction * dt
        if self.rect.right < 0 or self.rect.left > 800: # Screen width
            self.kill()


class Player(BasePlayer):
    SPRITESHEET_LAYOUT_NOTE = "Frames (32x48px): Idle, Walk1, Walk2, Jump, Attack. Horizontal strip."
    SPRITE_WIDTH = 32
    SPRITE_HEIGHT = 48

    @staticmethod
    def load_assets(module_path):
        spritesheet_path = os.path.join(module_path, "sprite.png")
        projectile_image_path = os.path.join(module_path, "projectile.png")
        assets = {}
        try:
            sheet = pygame.image.load(spritesheet_path).convert_alpha()
            assets['spritesheet'] = sheet
            if os.path.exists(projectile_image_path):
                 assets['projectile_image'] = pygame.image.load(projectile_image_path).convert_alpha()
            else:
                proj_img = pygame.Surface((10,5), pygame.SRCALPHA); proj_img.fill((255,255,0))
                assets['projectile_image'] = proj_img

            assets['frames'] = []
            for i in range(sheet.get_width() // Player.SPRITE_WIDTH):
                frame = sheet.subsurface(pygame.Rect(i * Player.SPRITE_WIDTH, 0, Player.SPRITE_WIDTH, Player.SPRITE_HEIGHT))
                assets['frames'].append(frame)
        except pygame.error as e:
            print(f"Error loading Knight player assets: {e}")
            assets['frames'] = [pygame.Surface((Player.SPRITE_WIDTH,Player.SPRITE_HEIGHT), pygame.SRCALPHA) for _ in range(5)]
            colors = [(200,0,0),(180,0,0),(160,0,0),(140,0,0),(220,50,50)]
            for i, frame in enumerate(assets['frames']): frame.fill(colors[i])
            if 'projectile_image' not in assets:
                proj_img = pygame.Surface((10,5), pygame.SRCALPHA); proj_img.fill((255,255,0))
                assets['projectile_image'] = proj_img
        return assets

    def __init__(self, x, y, assets):
        super().__init__(x, y, assets)
        self.assets = assets
        self.frames = self.assets.get('frames', [])
        self.image = self.frames[0] if self.frames else pygame.Surface([Player.SPRITE_WIDTH, Player.SPRITE_HEIGHT]); self.image.fill((200,0,0))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_y = 0
        self.on_ground = False
        self.health = 100
        self.facing_direction = 1 # 1 for right, -1 for left

        self.current_frame_idx = 0
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_fps = 10 # Animation frames per second for walk
        self.anim_state = 'idle'

        self.projectiles = pygame.sprite.Group()
        self.can_attack = True
        self.attack_cooldown_time = 500 
        self.last_attack_timestamp = 0
        self.attack_anim_duration = 200 # How long attack animation shows

    def update(self, keys, platforms, dt):
        dx = 0
        current_time_ms = pygame.time.get_ticks()

        # Horizontal Movement
        speed = PLAYER_SPEED_BASE * dt
        if keys[pygame.K_LEFT]:
            dx = -speed
            self.facing_direction = -1
            if self.on_ground and self.anim_state != 'attack': self.set_anim_state('walk')
        elif keys[pygame.K_RIGHT]:
            dx = speed
            self.facing_direction = 1
            if self.on_ground and self.anim_state != 'attack': self.set_anim_state('walk')
        else:
            if self.on_ground and self.anim_state == 'walk': self.set_anim_state('idle')

        # Jump
        if keys[pygame.K_UP] and self.on_ground and self.anim_state != 'attack':
            self.vel_y = PLAYER_JUMP_STRENGTH
            self.on_ground = False
            self.set_anim_state('jump')

        # Attack
        if keys[pygame.K_SPACE] and self.can_attack:
            self.attack()

        if not self.can_attack and current_time_ms - self.last_attack_timestamp > self.attack_cooldown_time:
            self.can_attack = True

        # If attack animation finished
        if self.anim_state == 'attack' and current_time_ms - self.last_attack_timestamp > self.attack_anim_duration:
             self.set_anim_state('idle' if self.on_ground else 'jump')


        # Apply gravity
        self.vel_y += PLAYER_GRAVITY 
        if self.vel_y > 15: self.vel_y = 15 # Terminal velocity
        dy = self.vel_y # For this frame, vel_y already includes gravity effect over time if dt was used for gravity too
                        # If PLAYER_GRAVITY is an acceleration, it should be vel_y += PLAYER_GRAVITY * dt
                        # Assuming PLAYER_GRAVITY is per-frame addition as in many simple Pygame examples.
                        # For consistency, let's make it dt dependent:
                        # self.vel_y += PLAYER_GRAVITY_ACCEL * dt (where PLAYER_GRAVITY_ACCEL is like 30-50)
                        # Sticking to per-frame for now to match common simpler examples. dy = self.vel_y (per frame jump)

        # Collision
        self.rect.x += dx
        self.collide_with_platforms(dx, 0, platforms)

        self.rect.y += dy
        self.on_ground = False # Assume not on ground until proven by vertical collision
        self.collide_with_platforms(0, dy, platforms)

        if self.rect.top > 600 + Player.SPRITE_HEIGHT: self.take_damage(self.health) # Fell off
        self.rect.clamp_ip(pygame.Rect(0, -Player.SPRITE_HEIGHT*2, 800, 600 + Player.SPRITE_HEIGHT*2)) # Clamp to screen with some leeway for jumping up

        self.animate(current_time_ms)
        self.projectiles.update(dt) # Pass dt to projectiles

    def collide_with_platforms(self, dx, dy, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dx > 0: self.rect.right = platform.rect.left
                if dx < 0: self.rect.left = platform.rect.right
                if dy > 0: 
                    self.rect.bottom = platform.rect.top
                    self.on_ground = True
                    self.vel_y = 0
                    if self.anim_state == 'jump': self.set_anim_state('idle')
                if dy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

    def set_anim_state(self, new_state):
        if self.anim_state != new_state:
            self.anim_state = new_state
            self.current_frame_idx = 0 
            self.last_anim_update = pygame.time.get_ticks() 

    def animate(self, current_time_ms):
        if not self.frames: return

        idx = 0 # Default to idle frame
        if self.anim_state == 'idle':
            idx = 0
        elif self.anim_state == 'jump':
            idx = 3 
        elif self.anim_state == 'attack':
            idx = 4
        elif self.anim_state == 'walk':
            # Walk animation: frames 0 (briefly), 1, 0 (briefly), 2
            walk_cycle = [self.frames[1], self.frames[0], self.frames[2], self.frames[0]]
            time_per_anim_frame = 1000 / self.anim_fps
            if current_time_ms - self.last_anim_update > time_per_anim_frame:
                self.last_anim_update = current_time_ms
                self.current_frame_idx = (self.current_frame_idx + 1) % len(walk_cycle)
            current_image = walk_cycle[self.current_frame_idx]
            self.image = pygame.transform.flip(current_image, self.facing_direction == -1, False)
            return # Walk animation handles its own image setting and flipping

        current_image = self.frames[idx]
        self.image = pygame.transform.flip(current_image, self.facing_direction == -1, False)

    def attack(self):
        self.last_attack_timestamp = pygame.time.get_ticks()
        self.can_attack = False
        self.set_anim_state('attack')

        proj_x = self.rect.centerx + (25 * self.facing_direction) 
        proj_y = self.rect.centery - 5 
        self.projectiles.add(Projectile(proj_x, proj_y, self.facing_direction, self.assets))

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0: self.health = 0
        # print(f"Knight took {amount} damage, health: {self.health}")

    def is_alive(self): return self.health > 0
    def draw(self, surface): surface.blit(self.image, self.rect)
    def handle_event(self, event): pass
