"""Source/frozen QA for every Pak's tenth-kill collectible and upgrade count."""
from pathlib import Path
import pygame
from system_panic.model import Vec
from system_panic.pak_api import PowerupBase


def exercise(app, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    runs = []
    for pak in app.catalog.complete_ids():
        app.start(pak)
        world = app.world
        world.phase = "active"
        world.cover = []
        world.enemies.clear()
        world.player.pos = Vec(200, 200)
        for index in range(10):
            enemy = world.spawn_enemy(Vec(110 + index * 65, 220))
            position = enemy.pos.copy()
            enemy.health = 0
            world.remove_dead()
        assert world.kills == 10 and len(world.powerups) == 1, pak
        pickup = world.powerups[0]
        assert isinstance(pickup, PowerupBase) and pickup.pos == position, pak
        before = (world.time, pickup.pos.copy(), pickup.age, world.rng.getstate())
        app.draw()
        pygame.image.save(app.canvas, output / (pak + "-drop.png"))
        assert before == (world.time, pickup.pos, pickup.age, world.rng.getstate())
        played=[]
        original=app.audio.play_asset
        def observe(asset,**options):
            played.append((asset,options))
            original(asset,**options)
        app.audio.play_asset=observe
        try:
            world.player.pos = pickup.pos.copy()
            pickup.update(world, 0)
            pickup.update(world, 0)
        finally:app.audio.play_asset=original
        assert world.powerups_collected == 1 and not pickup.alive, pak
        assert not world.collect_powerup(pickup), pak
        assert pickup.chime.path.parent==Path(pickup.art.path).parent, pak
        assert played==[(pickup.chime,dict(loop=False,volume=.45))], pak
        if app.audio.available:
            assert pickup.chime.path in app.audio.asset_sounds, pak
            assert any(asset is pickup.chime for asset,volume,loop in app.audio.voices.values()), pak
        app.draw()
        pygame.image.save(app.canvas, output / (pak + "-picked.png"))
        world.mix["weapon"] = "signal_runner" if pak != "signal_runner" else "star_bastion"
        world.component("weapon")
        world.enemies.clear()
        world.start_wave()
        assert world.powerups_collected == 1, pak
        runs.append({"pak": pak, "tenth_kill_drop": True, "exact_death_position": True,
                     "pak_subclass": type(pickup).__name__, "collected_once": True,
                     "local_chime_once": True, "mixer_available": app.audio.available,
                     "upgrade_survives_weapon_and_level_changes": True, "read_only_render": True})
    return {"runs": runs, "all_paks": len(runs), "kill_interval": 10, "shared_pickup_counter": True}
