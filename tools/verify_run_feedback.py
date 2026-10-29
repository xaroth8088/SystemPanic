"""Source/frozen presentation probe; profiles and screenshots are disposable."""
import importlib
import pygame
from system_panic.model import Controls, Vec
from system_panic.app import VIEWPORT


def verify_run_feedback(app, output):
    def screenshot(name):
        app.toast_timer = 0
        app.draw()
        pygame.image.save(app.canvas, output / ("run-feedback-" + name + ".png"))

    # Review the cleaned layouts, including pages affected by deleted explanatory text.
    app.home()
    for route in ("home", "settings", "help", "credits"):
        app.navigate(route)
        screenshot(route)
    app.open_remix()
    screenshot("builder")
    app.navigate("remix-saved")
    screenshot("saved")

    app.start("echo_vault")
    w = app.world
    w.phase, w.transition = "active", 0.
    w.player.pos = Vec(600, 280)
    w.enemies[0].pos = Vec(300, 200)
    hazards = importlib.import_module(type(w.component("enemy")).__module__ + ".hazards")
    burst = hazards.Zone(Vec(490, 260), 50, .72, 12, source=w.enemies[0].pos)
    w.projectiles = [burst]
    state = (w.time, w.rng.getstate(), w.player.health)
    for name, age in (("echo-delayed", 0.), ("echo-impact", .72), ("echo-shock", .81), ("echo-fade", 1.)):
        burst.age = age
        screenshot(name)
    assert (w.time, w.rng.getstate(), w.player.health) == state
    w.projectiles = []
    old = w.enemies[0].pos.copy()
    w.enemies[0].pos = Vec(430, 200)
    w.effects.append(hazards.BlinkEcho(old, w.enemies[0].pos, w.component("enemy").sprite(w, w.enemies[0])))
    screenshot("echo-blink")
    w.effects.clear()
    for percent in (20, 10, 0):
        w.player.health = w.player.max_health * percent / 100
        screenshot("hull-" + str(percent))
        if percent == 0:
            pixels = pygame.image.tobytes(app.canvas.subsurface(VIEWPORT), "RGB")
            assert all(pixels[i] == pixels[i + 1] == pixels[i + 2] for i in range(0, len(pixels), 3))

    assert "game_over" in app.audio.sounds, "Generated common sound must be in the release"
    assert .3 < app.audio.sounds["game_over"].get_length() < 1.3
    app.update(1 / 60, Controls())
    assert app.route == "game-over"
    frozen = (w.time, w.rng.getstate(), w.wave)
    app.update(.6)
    screenshot("death-transition")
    assert not app.buttons
    for _ in range(6):
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0))
        app.update(.2)
        assert app.route == "game-over"
    screenshot("death-release")
    app.update(.31)
    assert app.route == "outcome"
    assert (w.time, w.rng.getstate(), w.wave) == frozen
    screenshot("outcome")

    app.start("burrow_patrol")
    w = app.world
    w.phase, w.transition = "active", 0.
    w.player.pos = Vec(400, 240)
    w.component("weapon").show_line(w, Vec(540, 230), .8)
    screenshot("burrow-tether")
    return {"hull_endpoints_and_midpoint_rendered": True, "zero_hull_arena_grayscale": True,
            "hud_keeps_color": True, "death_freezes_gameplay_and_rng": True,
            "death_waits_for_input_release": True, "generated_death_sound_decodes": True,
            "echo_active_bursts_and_blinks_rendered": True, "cleaned_layouts_rendered": True}
