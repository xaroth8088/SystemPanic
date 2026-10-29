"""Read-only origami charge assembly anchored to the live pilot, including remixes."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT
from system_panic.pak_api import ProjectileBase


def smooth(value):
    value = max(0., min(1., value))
    return value*value*(3-2*value)


class PaperFold(ProjectileBase):
    """A harmless scheduled drawing; charge and all combat remain in the weapon."""
    def __init__(self, weapon, position, art, accent):
        super().__init__(position, Vec(), 0.)
        self.weapon, self.art, self.accent = weapon, art, accent

    @property
    def fraction(self):
        return max(0., min(1., self.weapon.charge/self.weapon.MAX_CHARGE))

    @property
    def stage(self):
        return min(3, int(self.fraction*4))

    def update(self, world, dt):
        self.pos = world.player.pos.copy()
        if not self.weapon.previous_fire or self.weapon.charge <= 0:
            self.alive = False

    def draw(self, graphics, surface, world):
        if not self.alive or not self.weapon.previous_fire or self.weapon.charge <= 0:
            return
        p = world.player
        progress = self.fraction
        reduced = world.prefs.reduced_motion
        radius = max(8., min(32., p.radius))
        distance = radius+30
        # Place the finished fold below a pilot at the top edge. A foreign
        # perimeter pilot must not lose essential charge feedback offscreen.
        assembly = p.pos+Vec(0, distance if p.pos.y-distance < 24 else -distance)
        assembly.x = max(23., min(WIDTH-23., assembly.x))
        assembly.y = max(23., min(HEIGHT-23., assembly.y))
        gather = smooth((progress-.12)/.78)
        fold = smooth(progress)
        ready = self.weapon.charge+1e-9 >= self.weapon.MIN_CHARGE
        paper = (244, 224, 186)
        underside = (205, 77, 64) if ready else (133, 126, 134)
        edge = (74, 88, 122)
        for index in range(4):
            bearing = 45+index*90
            direction = Vec(1, 0).rotate(bearing)
            start = p.pos+direction*(radius+18)
            start.x = max(18., min(WIDTH-18., start.x))
            start.y = max(18., min(HEIGHT-18., start.y))
            finish = assembly+direction*7
            center = start.lerp(finish, gather)
            flutter = 0. if reduced else math.sin(world.time*5+index*1.7)*7*(1-gather)
            angle = bearing+flutter
            width, height = 10.5, 9.5
            opened = ((-width, -height), (width, -height), (width, height), (-width, height))
            folded = ((-width, -height*.3), (width, 0), (-width, height*.3), (-width*.3, 0))
            points = [center+Vec(a).lerp(Vec(b), fold).rotate(angle) for a, b in zip(opened, folded)]
            shadow = [point+Vec(1, 2) for point in points]
            pygame.draw.polygon(surface, (12, 18, 30), shadow)
            pygame.draw.polygon(surface, paper, points)
            pygame.draw.polygon(surface, edge, points, 1)
            crease = [center+Vec(-width*.65, -height*(.7-.4*fold)).rotate(angle),
                      center+Vec(width*(.25+.75*fold), 0).rotate(angle),
                      center+Vec(-width*.65, height*(.7-.4*fold)).rotate(angle)]
            if progress > .12:
                pygame.draw.polygon(surface, underside, crease)
            pygame.draw.lines(surface, edge, False, crease, 1)
            pygame.draw.line(surface, (255, 241, 209), center+Vec(-width*.55, 0).rotate(angle),
                             center+Vec(width*.45, 0).rotate(angle), 1)
        materialize = smooth((progress-.48)/.52)
        if materialize > 0:
            image = graphics.render_sprite(self.art.frame(self.stage, columns=4), 20+round(12*progress), self.accent).copy()
            image.set_alpha(round(255*materialize))
            surface.blit(image, image.get_rect(center=assembly))
        if progress >= 1:
            # Crease highlights form a steady finished-paper silhouette. No
            # flashing, spinning ring, text or fixed-screen meter is required.
            for side in (-1, 1):
                a = assembly+Vec(side*18, -6)
                b = assembly+Vec(side*21, 0)
                c = assembly+Vec(side*18, 6)
                pygame.draw.lines(surface, (255, 224, 166), False, (a, b, c), 2)
