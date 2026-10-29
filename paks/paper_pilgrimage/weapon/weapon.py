"""Charge a folded blade; release, unfold at its apex, and catch its return."""
import math
from system_panic.model import Vec, normalized, unit
from system_panic.pak_api import WeaponBase
from .blade import FoldBlade
from .folding import PaperFold
from .powerup import Upgrade


class PaperWeapon(WeaponBase):
    MIN_CHARGE = .16
    MAX_CHARGE = 1.1

    def init(self):
        self.art = self.load_asset('weapon_sheet.png')
        self.sound = self.load_asset('shot.ogg')
        self.chime = self.load_asset('pickup.ogg')
        self.charge = self.cooldown = 0.
        self.previous_fire = False
        self.blades = []
        self.fold = None

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*8)%4, columns=4)

    def aim(self, world):
        intent = world.component('pilot').aim_direction(world)
        if intent is not None: return normalized(intent)
        living = [e for e in world.enemies if e.health > 0]
        if world.prefs.aim_assist and living:
            return normalized(min(living, key=lambda e:e.pos.distance_squared_to(world.player.pos)).pos-world.player.pos)
        return unit(world.player.angle)

    def update(self, world, dt, control):
        self.blades = [b for b in self.blades if b.alive and b in world.projectiles]
        self.cooldown = max(0., self.cooldown-dt)
        if control.fire:
            self.charge = min(self.MAX_CHARGE, self.charge+dt)
        if self.previous_fire and not control.fire:
            if self.charge >= self.MIN_CHARGE and self.cooldown <= 0 and len(self.blades) < 2:
                blade = FoldBlade(world.player.pos, self.aim(world), self.charge, world.powerups_collected,
                                  self.art, self)
                world.projectiles.append(blade)
                self.blades.append(blade)
                self.sound.play(volume=.5)
                self.cooldown = .55
            self.charge = 0.
        self.previous_fire = control.fire
        self.show_charge(world, control.fire)

    def clear_charge_display(self):
        if self.fold is not None:
            self.fold.alive = False
        self.fold = None

    def show_charge(self, world, held):
        if self.fold is not None and (not self.fold.alive or self.fold not in world.projectiles):
            self.clear_charge_display()
        if not held:
            self.clear_charge_display()
        elif self.fold is None:
            self.fold = PaperFold(self, world.player.pos, self.art, world.pak('weapon').color)
            world.projectiles.append(self.fold)

    def on_level_start(self, world):
        self.clear_charge_display()
        self.charge = self.cooldown = 0.
        self.previous_fire = False
        self.blades.clear()

    def on_shuffle(self, world, changed):
        self.clear_charge_display()
        self.blades.clear()
        self.charge = 0.
        self.previous_fire = False

    def deactivate(self, world):
        self.clear_charge_display()
        for blade in self.blades: blade.alive = False
        self.blades.clear()

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, world.pak('weapon').color, self.chime)

    def on_powerup(self, world, count):
        world.burst(world.player.pos, world.pak('weapon').color, 12)

    def demo_controls(self, world, controls):
        controls.fire = world.time%1.05 < .68
        return controls
