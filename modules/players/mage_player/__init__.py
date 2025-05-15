
# modules/players/mage_player/__init__.py
# SPRITESHEET_LAYOUT_NOTE:
# Spritesheet horizontal. Frame dimensions: 32w x 48h.
# Frame 0: Idle
# Frame 1: Walk 1
# Frame 2: Walk 2
# Frame 3: Cast Start (optional, could be part of attack anim)
# Frame 4: Casting/Attack
# Total image: 160w x 48h.

import pygame
import os

from modules.players import BasePlayer

PLAYER_GRAVITY = 0.55 
PLAYER_SPEED_BASE = 180 
PLAYER_JUMP_STRENGTH = -11
PROJECTILE_SPEED = 350

class MageProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, assets):
        super().__init__()
        self.image_orig = assets.get('projectile_image')
        if not self.image_orig:
            self.image_orig = pygame.Surface([12, 12], pygame.SRCALPHA)
            self.image_orig.fill((0,150,255)) 
            pygame.draw.circle(self.image_orig, (200,220,255), (6,6), 4)
        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(x,y))
        self.speed_val = PROJECTILE_SPEED
        self.direction = direction
        self.damage = 35
        self.lifetime = 2500 
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt=1/60.0):
        self.rect.x += self.speed_val * self.direction * dt
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime or            self.rect.right < 0 or self.rect.left > 800:
            self.kill()

class Player(BasePlayer):
    SPRITESHEET_LAYOUT_NOTE = "Frames (32x48px): Idle, Walk1, Walk2, CastStart, Casting. Horizontal."
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
                proj_img = pygame.Surface((12,12), pygame.SRCALPHA); proj_img.fill((0,150,255))
                pygame.draw.circle(proj_img, (200,220,255), (6,6), 4)
                assets['projectile_image'] = proj_img

            assets['frames'] = []
            for i in range(sheet.get_width() // Player.SPRITE_WIDTH):
                frame = sheet.subsurface(pygame.Rect(i * Player.SPRITE_WIDTH, 0, Player.SPRITE_WIDTH, Player.SPRITE_HEIGHT))
                assets['frames'].append(frame)
        except pygame.error as e:
            print(f"Error loading Mage player assets: {e}")
            assets['frames'] = [pygame.Surface((Player.SPRITE_WIDTH,Player.SPRITE_HEIGHT), pygame.SRCALPHA) for _ in range(5)]
            colors = [(0,0,200),(0,0,180),(0,0,160),(50,50,220),(70,70,240)]
            for i, frame in enumerate(assets['frames']): frame.fill(colors[i])
            if 'projectile_image' not in assets:
                proj_img = pygame.Surface((12,12), pygame.SRCALPHA); proj_img.fill((0,150,255))
                pygame.draw.circle(proj_img, (200,220,255), (6,6), 4)
                assets['projectile_image'] = proj_img
        return assets

    def __init__(self, x, y, assets):
        super().__init__(x, y, assets)
        self.assets = assets
        self.frames = self.assets.get('frames', [])
        self.image = self.frames[0] if self.frames else pygame.Surface([Player.SPRITE_WIDTH, Player.SPRITE_HEIGHT]); self.image.fill((0,0,200))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_y = 0
        self.on_ground = False
        self.health = 80 
        self.facing_direction = 1

        self.current_frame_idx = 0
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_fps = 8 
        self.anim_state = 'idle' 

        self.projectiles = pygame.sprite.Group()
        self.can_attack = True
        self.attack_cooldown_time = 700 
        self.last_attack_timestamp = 0
        self.is_casting_anim = False # Different from anim_state 'attack'
        self.cast_anim_duration = 400 # Duration of the casting visual

    def update(self, keys, platforms, dt):
        dx = 0
        current_time_ms = pygame.time.get_ticks()
        speed = PLAYER_SPEED_BASE * dt

        # Movement (restricted if casting animation is playing)
        if not self.is_casting_anim:
            if keys[pygame.K_LEFT]:
                dx = -speed; self.facing_direction = -1
                if self.on_ground: self.set_anim_state('walk')
            elif keys[pygame.K_RIGHT]:
                dx = speed; self.facing_direction = 1
                if self.on_ground: self.set_anim_state('walk')
            else:
                if self.on_ground and self.anim_state == 'walk': self.set_anim_state('idle')

            if keys[pygame.K_UP] and self.on_ground:
                self.vel_y = PLAYER_JUMP_STRENGTH
                self.on_ground = False
                self.set_anim_state('jump')

        if keys[pygame.K_SPACE] and self.can_attack:
            self.attack()

        if not self.can_attack and current_time_ms - self.last_attack_timestamp > self.attack_cooldown_time:
            self.can_attack = True

        if self.is_casting_anim and current_time_ms - self.last_attack_timestamp > self.cast_anim_duration:
            self.is_casting_anim = False
            self.set_anim_state('idle' if self.on_ground else 'jump')

        self.vel_y += PLAYER_GRAVITY
        if self.vel_y > 15: self.vel_y = 15
        dy = self.vel_y

        self.rect.x += dx
        self.collide_with_platforms(dx, 0, platforms)
        self.rect.y += dy
        self.on_ground = False
        self.collide_with_platforms(0, dy, platforms)

        if self.rect.top > 600 + Player.SPRITE_HEIGHT: self.take_damage(self.health)
        self.rect.clamp_ip(pygame.Rect(0, -Player.SPRITE_HEIGHT*2, 800, 600 + Player.SPRITE_HEIGHT*2))

        self.animate(current_time_ms)
        self.projectiles.update(dt)

    def collide_with_platforms(self, dx, dy, platforms): # Identical to Knight's, could be base class
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dx > 0: self.rect.right = platform.rect.left
                if dx < 0: self.rect.left = platform.rect.right
                if dy > 0: 
                    self.rect.bottom = platform.rect.top; self.on_ground = True; self.vel_y = 0
                    if self.anim_state == 'jump': self.set_anim_state('idle')
                if dy < 0: self.rect.top = platform.rect.bottom; self.vel_y = 0

    def set_anim_state(self, new_state):
        if self.anim_state != new_state or (new_state == 'attack' and not self.is_casting_anim): # Allow re-triggering attack anim
            self.anim_state = new_state
            self.current_frame_idx = 0 
            self.last_anim_update = pygame.time.get_ticks()
            if new_state == 'attack': # Mage specific: 'attack' state refers to casting animation
                self.is_casting_anim = True # Trigger the casting visual lock

    def animate(self, current_time_ms):
        if not self.frames: return
        idx = 0 
        if self.anim_state == 'idle': idx = 0
        elif self.anim_state == 'jump': idx = 0 # Mage uses idle for jump, or add specific jump frame
        elif self.anim_state == 'attack': # This is the casting animation
            # Cycle between frame 3 (CastStart) and 4 (Casting) or just use 4
            cast_anim_frames = [self.frames[3], self.frames[4]] # Example 2-frame cast
            time_per_cast_frame = self.cast_anim_duration / len(cast_anim_frames)
            if current_time_ms - self.last_anim_update > time_per_cast_frame:
                self.last_anim_update = current_time_ms
                self.current_frame_idx = (self.current_frame_idx + 1) % len(cast_anim_frames)
            current_image = cast_anim_frames[self.current_frame_idx]
            self.image = pygame.transform.flip(current_image, self.facing_direction == -1, False)
            return
        elif self.anim_state == 'walk':
            walk_cycle = [self.frames[1], self.frames[0], self.frames[2], self.frames[0]]
            time_per_anim_frame = 1000 / self.anim_fps
            if current_time_ms - self.last_anim_update > time_per_anim_frame:
                self.last_anim_update = current_time_ms
                self.current_frame_idx = (self.current_frame_idx + 1) % len(walk_cycle)
            current_image = walk_cycle[self.current_frame_idx]
            self.image = pygame.transform.flip(current_image, self.facing_direction == -1, False)
            return

        current_image = self.frames[idx]
        self.image = pygame.transform.flip(current_image, self.facing_direction == -1, False)


    def attack(self):
        self.last_attack_timestamp = pygame.time.get_ticks()
        self.can_attack = False
        self.set_anim_state('attack') # This now also sets self.is_casting_anim = True

        proj_x = self.rect.centerx + (25 * self.facing_direction)
        proj_y = self.rect.centery - 10 
        self.projectiles.add(MageProjectile(proj_x, proj_y, self.facing_direction, self.assets))

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0: self.health = 0
        # print(f"Mage took {amount} damage, health: {self.health}")

    def is_alive(self): return self.health > 0
    def draw(self, surface): surface.blit(self.image, self.rect)
    def handle_event(self, event): pass
