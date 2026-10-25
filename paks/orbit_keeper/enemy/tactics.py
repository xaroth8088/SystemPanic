"""Local enemy helpers. Copy with the enemy folder when making a partial Pak."""
from system_panic.model import Vec, WIDTH, HEIGHT, circle_rect, normalized


def difficulty(world):
    # This component chooses how the user's difficulty preference affects its rules.
    return {"relaxed": .70, "standard": 1., "intense": 1.28}[world.prefs.difficulty]


def spawn_position(world):
    desired = Vec(world.rng.uniform(25, WIDTH - 25), world.rng.uniform(25, HEIGHT - 25))
    return world.safe_position(desired, 14, away_from=world.player.pos, clearance=160)


def pursue(world, enemy, direction, speed, dt, *, avoid=False, wrap=False):
    if avoid:
        # Probe short routes around cover rather than repeatedly pushing into it.
        probe = max(28, speed * .35)
        for angle in (0, 35, -35, 70, -70, 110, -110, 160):
            candidate = direction.rotate(angle if enemy.id % 2 else -angle)
            point = enemy.pos + candidate * probe
            if not any(w.health > 0 and circle_rect(point, enemy.radius + 3, w.rect) for w in world.cover):
                direction = candidate
                break
    enemy.vel = normalized(direction) * speed
    motion = world.move_body(enemy, enemy.vel * dt, enemy.radius,
                             **({"bounds": None} if wrap else {}))
    if wrap:
        enemy.pos.x %= WIDTH
        enemy.pos.y %= HEIGHT
    return motion
