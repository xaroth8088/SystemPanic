"""Desktop shell, accessible menus and fixed-step gameplay."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
import math
from pathlib import Path
import secrets
import tempfile

import pygame

from .audio import Audio
from .graphics import Graphics, BG, PANEL, EDGE, TEXT, MUTED, CYAN, DIM
from .input_devices import Gamepads, MenuRepeat, spatial_focus, A, B, START, BACK, LB, RB
from .model import WIDTH, HEIGHT, Controls
from .paks import discover, CHANNELS
from .preferences import PreferenceStore, RENDER_RESOLUTIONS
from .remix_ui import RemixMenus
from .remixes import validate_mix
from .world import World

SIZE = (1280, 800)
VIEWPORT = pygame.Rect(32, 136, 1216, 608)
VOLUME_STEP = .05


@dataclass
class Button:
    id: str
    rect: pygame.Rect
    label: str
    action: object


class App(RemixMenus):
    def __init__(self, data_dir=None, seed=None, catalog=None, gamepads=None):
        self.catalog = catalog if catalog is not None else discover()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.store = PreferenceStore(data_dir, self.catalog)
        self.prefs = self.store.load()
        self.init_remixes()
        self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("System Panic — One unstable system.")
        self.canvas = pygame.Surface(SIZE).convert()
        self.arena_surface = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.graphics = Graphics(self.catalog)
        if self.catalog.paks:
            pak = self.catalog.paks[0]
            pygame.display.set_icon(self.graphics.preview(pak.id, 64))
        self.audio = Audio(self.prefs, self.catalog)
        self.clock = pygame.time.Clock()
        self.gamepads = gamepads if gamepads is not None else Gamepads()
        self.menu_repeat = MenuRepeat()
        self.input_device = "gamepad" if self.gamepads.connected else "keyboard"
        self.window_focused = True
        self.running = True
        self.route = "home"
        self.page_history = []
        self.world = None
        self.seed = seed
        self.buttons: list[Button] = []
        self.focus = 0
        self.keyboard_focus = self.input_device == "gamepad"
        self._focus_pending = self.keyboard_focus
        self.pointer = (-100, -100)
        self.elapsed = 0.
        self.toast = self.store.error or self.remix_store.error
        self.toast_timer = 6. if self.toast else 0.
        self.recorded = False
        self.library_page = 0
        self.help_page = 0
        self.status_page = 0
        if self.prefs.fullscreen or self.prefs.render_resolution != "auto":
            self.apply_display()
        self.menu_music()

    def menu_music(self):
        providers = self.catalog.providers("music")
        self._menu_part = self.catalog.by_id[providers[0]].create("music") if providers else None
        self.audio.music(self._menu_part.track() if self._menu_part else None)

    def reload_paks(self):
        if self.world is not None:
            return
        self.catalog = discover(self.catalog.roots)
        self.store.catalog = self.catalog
        self.prefs = self.store.load()
        self.remix_store.catalog = self.catalog
        self.remixes = self.remix_store.load()
        self.remix_mix = self.default_remix()
        self.remix_selected = None
        self.graphics = Graphics(self.catalog)
        self.audio.prefs = self.prefs
        self.audio.catalog = self.catalog
        self.audio.current = None
        if self.audio.available:
            pygame.mixer.music.stop()
        self.audio.set_volumes()
        self.menu_music()
        self.library_page = self.help_page = self.status_page = 0
        self.notify(f"Loaded {len(self.catalog.paks)} Paks; {len(self.catalog.issues)} skipped. Details in Pak status.")

    def page_controls(self, attribute, count, y, left=430, right=1080):
        pages = max(1, (count + 5) // 6)
        page = min(getattr(self, attribute), pages - 1)
        setattr(self, attribute, page)
        if pages > 1:
            def change(delta):
                setattr(self, attribute, (page + delta) % pages)
                self.focus = 0
                self.keyboard_focus = self.input_device == "gamepad"
                self._focus_pending = self.keyboard_focus
                self.gamepads.block()
                self.menu_repeat.block()
            self.button(attribute + ":prev", (left, y, 140, 29), "< PREVIOUS", lambda: change(-1), size=12)
            self.button(attribute + ":next", (right, y, 140, 29), "NEXT >", lambda: change(1), size=12)
            self.graphics.text(self.canvas, f"{page + 1} / {pages}", ((left + right + 140) / 2, y + 14), 12, MUTED, mono=True, anchor="center")
        return page * 6

    def apply_display(self):
        try:
            if self.prefs.render_resolution == "auto":
                size = (0, 0) if self.prefs.fullscreen else SIZE
            else:
                width, height = map(int, self.prefs.render_resolution.split("x"))
                size = (width, height)
            flags = pygame.FULLSCREEN if self.prefs.fullscreen else pygame.RESIZABLE
            self.window = pygame.display.set_mode(size, flags)
        except (pygame.error, ValueError):
            self.prefs.fullscreen = False
            self.prefs.render_resolution = "auto"
            self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
            self.notify("That display mode is unavailable. Restored automatic windowed output.")

    def save(self):
        if not self.store.save(self.prefs):
            self.notify("Preferences could not be saved. This session still works.")

    def notify(self, text):
        self.toast, self.toast_timer = text, 4.

    def navigate(self, route):
        if self.world and route != "game":
            self.world.suspend()
        self.route, self.focus = route, 0
        if route == "remix-name":
            pygame.key.start_text_input()
        else:
            pygame.key.stop_text_input()
        self.keyboard_focus = self.input_device == "gamepad"
        self._focus_pending = self.keyboard_focus
        self.gamepads.block()
        self.menu_repeat.block()
        self.buttons.clear()

    def start(self, solo=None, *, fixed_mix=None):
        if fixed_mix is not None:
            try:
                fixed_mix = validate_mix(fixed_mix, self.catalog)
            except ValueError as exc:
                self.notify(str(exc))
                return
        if (fixed_mix is None and solo is None and self.catalog.missing(self.prefs.enabled)) or (solo is not None and solo not in self.catalog.complete_ids()):
            self.notify("Enable every component type in the mix, or choose a complete Pak.")
            return
        if self.world:
            self.world.close()
        self.world = World(self.prefs, self.seed if self.seed is not None else secrets.randbelow(1_000_000), solo, self.catalog, self.audio, fixed_mix=fixed_mix)
        self.recorded = False
        self.page_history.clear()
        self.navigate("game")
        self.audio.music(self.world.component("music").track(self.world))

    def home(self):
        if self.world:
            self.world.close()
        self.world = None
        self.page_history.clear()
        self.navigate("home")
        self.menu_music()

    def open_page(self, route):
        self.page_history.append(self.route)
        self.navigate(route)

    def back(self):
        self.save()
        self.navigate(self.page_history.pop() if self.page_history else "home")

    def toggle_pak(self, pak_id):
        if pak_id in self.prefs.enabled:
            candidate = [id for id in self.prefs.enabled if id != pak_id]
            missing = self.catalog.missing(candidate)
            if not candidate or missing:
                self.notify("Keep a provider enabled for: " + ", ".join(missing))
                return
            self.prefs.enabled.remove(pak_id)
        else:
            self.prefs.enabled.append(pak_id)
        if self.prefs.mix_mode == "coherent" and not self.catalog.complete_ids(self.prefs.enabled):
            self.prefs.mix_mode = "remix"
            self.notify("The enabled partial Paks now play together in component remix.")
        self.save()

    def cycle(self, name, options):
        current = getattr(self.prefs, name)
        setattr(self.prefs, name, options[(options.index(current) + 1) % len(options)] if current in options else options[0])
        if name == "mix_mode" and self.prefs.mix_mode == "coherent" and not self.catalog.complete_ids(self.prefs.enabled):
            self.prefs.mix_mode = "remix"
            self.notify("Coherent shuffle needs an enabled complete Pak. Partial Paks use component remix.")
        self.audio.set_volumes()
        if name in ("fullscreen", "render_resolution"):
            self.apply_display()
        self.save()

    def set_render_resolution(self, value):
        if value in RENDER_RESOLUTIONS:
            self.prefs.render_resolution = value
            self.apply_display()
            self.save()

    def volume(self, name, amount):
        setattr(self.prefs, name, round(max(0, min(1, getattr(self.prefs, name) + amount)), 2))
        self.audio.set_volumes()
        self.save()

    def toggle_channel(self, name):
        values = self.prefs.shuffle_channels
        if name in values:
            values.remove(name)
        else:
            values.append(name)
        self.save()

    def button(self, id, rect, label, action, accent=CYAN, filled=False, size=17):
        rect = pygame.Rect(rect)
        index = len(self.buttons)
        self.buttons.append(Button(id, rect, label, action))
        hover = rect.collidepoint(self.pointer) or (self.keyboard_focus and not self._focus_pending and self.focus == index)
        fill = accent if filled else tuple(min(255, c + 7) for c in PANEL) if hover else PANEL
        border = accent if hover or filled else EDGE
        self.graphics.panel(self.canvas, rect, fill, border, 7)
        self.graphics.text(self.canvas, label, rect.center, size, BG if filled else TEXT,
                           filled, anchor="center")

    def header(self, location):
        g = self.graphics
        g.text(self.canvas, "S / P", (40, 28), 23, CYAN, True, True)
        g.text(self.canvas, "SYSTEM PANIC", (130, 31), 17, TEXT, True, True)
        g.text(self.canvas, "/  " + location, (300, 32), 15, MUTED, mono=True)
        if self.input_device == "gamepad":
            g.text(self.canvas, "STICK: move   A: choose   B: back", (680, 35), 11, CYAN, mono=True)
        pygame.draw.line(self.canvas, EDGE, (40, 78), (1240, 78))

    def draw_home(self):
        g = self.graphics
        self.header("PAK LIBRARY")
        self.button("quit", (1140, 25, 100, 34), "QUIT", self.quit, size=13)
        g.text(self.canvas, f"{len(self.catalog.paks)} PAKS DISCOVERED.", (40, 127), 13, CYAN, True, True)
        g.text(self.canvas, "ONE UNSTABLE SYSTEM.", (40, 149), 13, MUTED, mono=True)
        g.text(self.canvas, "SYSTEM", (35, 190), 69, TEXT, True)
        g.text(self.canvas, "PANIC", (35, 261), 88, CYAN, True)
        g.wrapped(self.canvas, "The rules will change. Keep moving.", (42, 372), 335, 23, TEXT)
        g.wrapped(self.canvas, "Play a complete Pak alone, or combine complete and partial Paks in the mix.", (42, 445), 315, 18)
        mode = "COMPONENT REMIX" if self.prefs.mix_mode == "remix" else "COHERENT SHUFFLE"
        g.text(self.canvas, f"{len(self.prefs.enabled):02d} / {len(self.catalog.paks):02d} ENABLED   ·   {mode}", (42, 535), 12, CYAN, mono=True)
        missing = self.catalog.missing(self.prefs.enabled)
        if not missing:
            self.button("start", (40, 563, 340, 51), "START MAIN GAME  >", self.start, filled=True, size=20)
        else:
            g.wrapped(self.canvas, "Mix needs: " + ", ".join(missing) + ". Add Paks and rescan.", (42, 574), 335, 17, CYAN)
        self.button("remix", (40, 628, 340, 44), "REMIX / BUILD & PLAY", self.open_remix, size=17)
        self.button("settings", (40, 684, 160, 34), "PREFERENCES", lambda: self.open_page("settings"), size=14)
        self.button("help", (218, 684, 162, 34), "HOW TO PLAY", lambda: self.open_page("help"), size=14)
        g.text(self.canvas, "BEST", (42, 735), 12, MUTED, mono=True)
        g.text(self.canvas, f"{self.prefs.high_score:07d}", (94, 726), 24, TEXT, mono=True)
        self.button("credits", (248, 725, 132, 28), "CREDITS", lambda: self.open_page("credits"), size=12)
        self.button("rescan", (40, 760, 160, 28), "RESCAN PAKS", self.reload_paks, size=12)
        self.button("pak-status", (218, 760, 162, 28), f"PAK STATUS ({len(self.catalog.issues)})", lambda: self.open_page("paks"), size=11)
        g.text(self.canvas, "CHOOSE YOUR MIX", (430, 107), 15, TEXT, True, True)
        g.text(self.canvas, "PARTIAL PAKS JOIN THE MIX", (1230, 108), 12, MUTED, mono=True, anchor="topright")
        start = self.page_controls("library_page", len(self.catalog.paks), 714)
        for index, pak in enumerate(self.catalog.paks[start:start + 6]):
            x, y = 430 + index % 2 * 410, 150 + index // 2 * 190
            enabled = pak.id in self.prefs.enabled
            g.panel(self.canvas, (x, y, 390, 174), PANEL,
                    tuple(int(c * .55) for c in pak.color) if enabled else EDGE)
            pygame.draw.rect(self.canvas, pak.color if enabled else DIM, (x + 16, y + 15, 3, 15), border_radius=1)
            g.text(self.canvas, f"PAK {start + index + 1:02d} / " + ("COMPLETE" if pak.complete else "PARTIAL"), (x + 28, y + 14), 11, pak.color if enabled else MUTED, mono=True)
            g.text(self.canvas, "IN THE MIX" if enabled else "DISABLED", (x + 372, y + 16), 10, pak.color if enabled else DIM, mono=True, anchor="topright")
            g.fit_text(self.canvas, pak.name, (x + 17, y + 41), 264, 25, TEXT, True)
            g.fit_text(self.canvas, pak.subtitle, (x + 18, y + 83), 262, 11, pak.color)
            g.text(self.canvas, " / ".join(pak.components[:3]).upper(), (x + 18, y + 99), 9, MUTED, mono=True)
            g.text(self.canvas, " / ".join(pak.components[3:]).upper(), (x + 18, y + 112), 9, MUTED, mono=True)
            image = g.preview(pak.id, 90)
            self.canvas.blit(image, (x + 286, y + 35))
            if pak.complete:
                self.button("solo:" + pak.id, (x + 17, y + 126, 145, 31), "PLAY SOLO  >", lambda p=pak.id: self.start(p), accent=pak.color, size=12)
            else:
                g.text(self.canvas, "MIX ONLY", (x + 18, y + 136), 12, MUTED, mono=True)
            self.button("toggle:" + pak.id, (x + 269, y + 126, 104, 31), "[x] ENABLED" if enabled else "[ ] ENABLE", lambda p=pak.id: self.toggle_pak(p), accent=pak.color, size=11)
        if not self.catalog.paks:
            g.text(self.canvas, "No Paks found.", (475, 230), 33, TEXT, True)
            g.wrapped(self.canvas, "Add Pak folders to a location listed in Pak status, then choose Rescan Paks.", (475, 290), 680, 20)
        hint = "STICK / D-PAD + RT/A + X/LB" if self.input_device == "gamepad" else "ARROWS / WASD + SPACE + X"
        g.text(self.canvas, hint, (430, 771), 12, MUTED, mono=True)
        g.text(self.canvas, "OFFLINE / ORIGINAL AI ASSETS", (1230, 771), 12, DIM, mono=True, anchor="topright")

    def draw_pak_status(self):
        g = self.graphics
        self.header("PAK STATUS")
        self.button("back", (1100, 25, 140, 34), "< BACK", self.back, size=13)
        g.text(self.canvas, f"{len(self.catalog.paks)} loaded / {len(self.catalog.issues)} skipped", (80, 115), 33, TEXT, True)
        y = 177
        for root in self.catalog.roots[:3]:
            g.fit_text(self.canvas, str(root), (80, y), 1120, 15)
            y += 28
        if len(self.catalog.roots) > 3:
            g.text(self.canvas, f"+{len(self.catalog.roots) - 3} additional search locations", (80, y), 14, MUTED)
        missing = self.catalog.missing(self.prefs.enabled)
        g.wrapped(self.canvas, "Mix needs: " + ", ".join(missing) if missing else "The enabled mix covers all six components.", (80, y + 10), 1120, 17, CYAN)
        start = self.page_controls("status_page", len(self.catalog.issues), 735, 80, 1060)
        for index, issue in enumerate(self.catalog.issues[start:start + 6]):
            top = 320 + index * 64
            g.fit_text(self.canvas, str(issue.path), (80, top), 1120, 14, TEXT)
            g.fit_text(self.canvas, issue.message, (80, top + 24), 1120, 14, MUTED)

    def setting(self, y, title, description, name, options, labels=None):
        g = self.graphics
        g.text(self.canvas, title, (80, y), 21, TEXT, True)
        g.text(self.canvas, description, (80, y + 31), 15, MUTED)
        value = getattr(self.prefs, name)
        label = labels[options.index(value)] if labels and value in options else str(value).upper()
        self.button(name, (830, y + 3, 370, 43), label + "  >", lambda: self.cycle(name, options), size=16)
        pygame.draw.line(self.canvas, EDGE, (80, y + 70), (1200, y + 70))

    def draw_settings(self):
        g = self.graphics
        self.header("PREFERENCES")
        self.button("back", (1100, 25, 140, 34), "<  BACK", self.back, size=13)
        g.text(self.canvas, "Tune the instability.", (80, 107), 35, TEXT, True)
        g.text(self.canvas, "Saved locally. Gameplay changes apply to the next run.", (80, 158), 17, MUTED)
        self.setting(210, "Shuffle style", "Component remix includes partial Paks; coherent uses complete Paks.", "mix_mode", ["remix", "coherent"], ["COMPONENT REMIX", "COHERENT PAKS"])
        self.setting(292, "Time between changes", "A protected transition gives you time to read the new rules.", "shuffle_seconds", [5, 8, 12, 20, 30], ["5 SECONDS", "8 SECONDS", "12 SECONDS", "20 SECONDS", "30 SECONDS"])
        self.setting(374, "Challenge", "Paks tune attacks and movement to this setting.", "difficulty", ["relaxed", "standard", "intense"])
        g.text(self.canvas, "Endless progression", (80, 456), 21, TEXT, True)
        g.text(self.canvas, "Start with one enemy. Each cleared level adds one more.", (80, 487), 15, MUTED)
        g.text(self.canvas, "1, 2, 3... ENEMIES", (1200, 480), 16, CYAN, mono=True, anchor="midright")
        pygame.draw.line(self.canvas, EDGE, (80, 526), (1200, 526))
        g.text(self.canvas, "COMPONENTS IN THE SHUFFLE", (80, 553), 12, MUTED, mono=True)
        for index, channel in enumerate(CHANNELS):
            enabled = channel in self.prefs.shuffle_channels
            self.button("channel:" + channel, (80 + index * 123, 582, 115, 36), ("[x] " if enabled else "[ ] ") + channel.upper(), lambda c=channel: self.toggle_channel(c), size=10)
        self.button("assist", (830, 582, 370, 36), "AIM ASSIST: " + ("ON" if self.prefs.aim_assist else "OFF"), lambda: self.cycle("aim_assist", [True, False]), size=13)
        for name, label, x in (("music", "MUSIC", 80), ("effects", "EFFECTS", 440)):
            g.text(self.canvas, f"{label}  {getattr(self.prefs, name):.0%}", (x, 653), 13, MUTED, mono=True)
            self.button(name + "-", (x + 150, 644, 43, 36), "-", lambda n=name: self.volume(n, -VOLUME_STEP))
            self.button(name + "+", (x + 201, 644, 43, 36), "+", lambda n=name: self.volume(n, VOLUME_STEP))
        self.button("motion", (830, 644, 175, 36), "MOTION: " + ("REDUCED" if self.prefs.reduced_motion else "FULL"), lambda: self.cycle("reduced_motion", [False, True]), size=12)
        self.button("display", (1020, 644, 180, 36), "DISPLAY  >", lambda: self.open_page("display"), size=12)
        g.wrapped(self.canvas, "Turn Paks on or off in the library. In component remix, unchecked channels keep their starting Pak. Coherent mode swaps the whole Pak.", (80, 704), 700, 15)
        self.button("controls", (830, 703, 370, 36), "GAMEPAD / INPUT  >", lambda: self.open_page("controls"), size=14)

    def draw_display(self):
        g = self.graphics
        self.header("DISPLAY")
        self.button("back", (1100, 25, 140, 34), "<  BACK", self.back, size=13)
        g.text(self.canvas, "Choose the output size.", (80, 107), 35, TEXT, True)
        g.text(self.canvas, "Display changes apply immediately and are saved locally.", (80, 158), 17, MUTED)
        self.setting(210, "Display mode", "F11 also switches between windowed and fullscreen.",
                     "fullscreen", [False, True], ["WINDOWED", "FULLSCREEN"])
        g.text(self.canvas, "Rendering resolution", (80, 310), 21, TEXT, True)
        g.text(self.canvas, "The field of view stays the same at every output size.", (80, 345), 16, MUTED)
        for index, resolution in enumerate(RENDER_RESOLUTIONS):
            x, y = 80 + index % 3 * 380, 389 + index // 3 * 62
            selected = self.prefs.render_resolution == resolution
            label = "AUTOMATIC" if resolution == "auto" else resolution.replace("x", " x ")
            self.button("resolution:" + resolution, (x, y, 360, 46), ("[x] " if selected else "") + label,
                        lambda value=resolution: self.set_render_resolution(value), accent=CYAN if selected else MUTED, size=17)
        width, height = self.window.get_size()
        g.text(self.canvas, f"CURRENT OUTPUT  {width} x {height}", (80, 666), 15, CYAN, mono=True)
        g.text(self.canvas, "Aspect ratio is preserved; some output sizes add black bars.", (80, 704), 16, MUTED)
        g.text(self.canvas, "Automatic uses a 1280 x 800 window or the desktop size in fullscreen.", (80, 737), 15, MUTED)

    def draw_controls(self):
        g = self.graphics
        self.header("INPUT & GAMEPAD")
        self.button("back", (1100, 25, 140, 34), "<  BACK", self.back, size=13)
        g.text(self.canvas, "Play your way.", (80, 112), 35, TEXT, True)
        g.fit_text(self.canvas, self.gamepads.name, (80, 175), 1120, 20, CYAN if self.gamepads.connected else MUTED)
        rows = [
            ("LEFT STICK / D-PAD", "Pilot movement"),
            ("RT / R2 or A / CROSS", "Fire"),
            ("X / SQUARE or LB / L1", "Special"),
            ("START / OPTIONS", "Pause / resume"),
            ("STICK / D-PAD (MENU)", "Move focus"),
            ("A / CROSS    B / CIRCLE", "Choose / back"),
            ("LB / RB (MENU)", "Previous / next page"),
        ]
        for row, (buttons, action) in enumerate(rows):
            y = 251 + row * 50
            g.text(self.canvas, buttons, (80, y), 14, CYAN, mono=True)
            g.text(self.canvas, action, (395, y), 17, TEXT)
        g.text(self.canvas, "STICK DEADZONE", (790, 251), 13, MUTED, mono=True)
        g.wrapped(self.canvas, "Increase this if the stick drifts while centered. Applies immediately.", (790, 281), 410, 17)
        self.button("gamepad_deadzone", (790, 352, 410, 46), f"{self.prefs.gamepad_deadzone:.0%}  >", lambda: self.cycle("gamepad_deadzone", [.12, .18, .24, .30, .36]), size=18)
        self.button("next-gamepad", (790, 421, 410, 44), f"NEXT CONNECTED PAD ({len(self.gamepads.devices)})", self.next_gamepad, size=14)
        g.wrapped(self.canvas, "SDL maps compatible controllers automatically. Button positions follow Xbox / PlayStation conventions. Keyboard and mouse stay available.", (790, 500), 410, 16)
        g.wrapped(self.canvas, "Arrows / WASD: move   SPACE: fire   X / Shift: special   ESC: pause / back. Release the controls after opening a menu, resuming or reconnecting. A disconnected active pad pauses the run.", (80, 663), 1120, 17)
        if self.gamepads.error:
            g.fit_text(self.canvas, "Controller unavailable: " + self.gamepads.error, (80, 751), 1120, 13, MUTED)

    def next_gamepad(self):
        self.notify(self.gamepads.select_next())
        self.menu_repeat.block()

    def draw_help(self):
        g = self.graphics
        self.header("HOW TO PLAY")
        self.button("back", (1100, 25, 140, 34), "<  BACK", self.back, size=13)
        g.text(self.canvas, "Adapt. Survive. Keep going.", (80, 108), 35, TEXT, True)
        g.wrapped(self.canvas, "Adapt to changing pilots and weapons. Levels add one enemy and regenerate terrain; the run ends on defeat. Every 10 destroyed enemies drops a Pak powerup at the kill site. Collect it to strengthen your current weapon; upgrades carry through swaps. Watch UP in the HUD.", (80, 166), 1100, 18)
        pilots = [p for p in self.catalog.paks if "pilot" in p.components]
        start = self.page_controls("help_page", len(pilots), 690, 80, 1060)
        for index, pak in enumerate(pilots[start:start + 6]):
            x, y = 80 + index % 2 * 575, 280 + index // 2 * 135
            image = g.preview(pak.id, 66)
            self.canvas.blit(image, (x, y))
            g.fit_text(self.canvas, pak.name, (x + 80, y), 460, 22, pak.color, True)
            pilot = g.previews[(pak.id, "pilot")]
            g.fit_text(self.canvas, pilot.controls, (x + 80, y + 35), 460, 16, TEXT)
            g.fit_text(self.canvas, pilot.special, (x + 80, y + 62), 460, 15, MUTED)
        footer = "STICK / D-PAD: menus   A: choose   B: back   START: pause" if self.input_device == "gamepad" else "ESC: pause / back   F11: fullscreen   TAB + ENTER: menus"
        g.text(self.canvas, footer, (80, 738), 13, MUTED, mono=True)
        self.button("help-controls", (1010, 727, 190, 34), "GAMEPAD / INPUT", lambda: self.open_page("controls"), size=12)

    def draw_credits(self):
        g = self.graphics
        self.header("CREDITS")
        self.button("back", (1100, 25, 140, 34), "<  BACK", self.back, size=13)
        g.text(self.canvas, "Built to be remixed.", (80, 130), 44, TEXT, True)
        paragraphs = [
            ("CONCEPT", "System Panic by Geoffrey Benson. Inspired by the ever-changing arcade rules of ROM CHECK FAIL by Farbs."),
            ("ORIGINAL ARTWORK", "Original sprite atlas and title illustration generated for this revival with OpenAI imagegen. No artwork from the historical prototypes is used."),
            ("ORIGINAL MUSIC + SOUND", "Generated with Stability AI Stable Audio 3. Prompt jobs, seeds, processing details and file hashes are kept in the asset manifest."),
            ("TECHNOLOGY", "Python and Pygame. All gameplay and playback work offline. Asset creation is a separate development workflow."),
            ("MAKE A PAK", "The project wiki starts at AGENTS.md. Add a complete Pak, preserve the common contracts, then test it alone and in the mix."),
        ]
        y = 235
        for title, paragraph in paragraphs:
            g.text(self.canvas, title, (80, y), 13, CYAN, True, True)
            y = g.wrapped(self.canvas, paragraph, (80, y + 27), 1100, 19) + 30

    def draw_game(self):
        g, w = self.graphics, self.world
        pygame.draw.line(self.canvas, EDGE, (40, 78), (1240, 78))
        g.text(self.canvas, f"LEVEL {w.wave:02d} / ENDLESS", (40, 98), 17, TEXT, True, True)
        g.text(self.canvas, f"SCORE  {w.score:07d}", (340, 98), 17, CYAN, mono=True)
        g.text(self.canvas, f"{len(w.enemies):02d} HOSTILES", (700, 98), 15, MUTED, mono=True)
        g.text(self.canvas, f"UP {w.powerups_collected:02d}", (850, 98), 14, CYAN, mono=True)
        g.text(self.canvas, "HULL", (968, 98), 12, MUTED, mono=True)
        pygame.draw.rect(self.canvas, EDGE, (1020, 100, 170, 12), border_radius=3)
        pygame.draw.rect(self.canvas, CYAN if w.player.health / w.player.max_health > .3 else (255, 119, 137), (1020, 100, max(0, 170 * w.player.health / w.player.max_health), 12), border_radius=3)
        g.text(self.canvas, f"{math.ceil(w.player.health):03d}", (1238, 94), 17, TEXT, mono=True, anchor="topright")
        g.draw_world(self.arena_surface, w, self.prefs.reduced_motion)
        frame = pygame.transform.scale(self.arena_surface, VIEWPORT.size)
        offset = (0, 0)
        if w.shake and not self.prefs.reduced_motion:
            offset = (int(math.sin(self.elapsed * 91) * w.shake), int(math.cos(self.elapsed * 83) * w.shake * .5))
        self.canvas.blit(frame, VIEWPORT.move(offset))
        for index, channel in enumerate(CHANNELS):
            pak = w.pak(channel)
            x = 42 + index * 170
            g.text(self.canvas, channel.upper(), (x, 24), 10, MUTED, mono=True)
            g.fit_text(self.canvas, pak.name, (x, 44), 158, 16, pak.color, True)
        timer = "REMIX / STATIC" if w.fixed_mix is not None else f"SHIFT {max(0, w.shuffle_timer):04.1f}s" if w.can_shuffle else "COMPONENTS / LOCKED" if len(w.enabled) > 1 else "SOLO / LOCKED"
        self.button("pause", (1075, 25, 165, 36), "START / PAUSE" if self.input_device == "gamepad" else "ESC / PAUSE", lambda: self.navigate("pause"), size=13)
        g.text(self.canvas, timer, (1235, 758), 13, CYAN, mono=True, anchor="topright")
        hint = "STICK / D-PAD: movement    RT/A: fire    X/LB: special" if self.input_device == "gamepad" else w.component("pilot").controls + "    SPACE: fire    " + w.component("pilot").special
        status = w.component("pilot").status(w)
        if status:
            hint += "    /    " + status
        g.fit_text(self.canvas, hint, (40, 759), 970, 14, MUTED)
        if w.phase in ("ready", "clear"):
            rect = pygame.Rect(365, 353, 550, 118)
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((5, 14, 23, 225))
            self.canvas.blit(overlay, rect)
            text = f"LEVEL {w.wave:02d} / GET READY" if w.phase == "ready" else f"LEVEL {w.wave:02d} CLEARED"
            g.text(self.canvas, text, (640, 389), 32, TEXT, True, True, "center")
            subtitle = "NEXT LEVEL INCOMING" if w.phase == "clear" else "HOLD RT/A TO FIRE / X/LB FOR SPECIAL" if self.input_device == "gamepad" else "HOLD SPACE TO FIRE / X FOR SPECIAL"
            g.text(self.canvas, subtitle, (640, 435), 14, CYAN, mono=True, anchor="center")

    def draw_overlay(self, outcome=False):
        g, w = self.graphics, self.world
        shade = pygame.Surface(SIZE, pygame.SRCALPHA)
        shade.fill((4, 10, 18, 210))
        self.canvas.blit(shade, (0, 0))
        g.panel(self.canvas, (330, 160, 620, 510), (13, 24, 36), EDGE, 16)
        title = "SIGNAL LOST" if outcome else "SYSTEM PAUSED"
        color = (255, 119, 137) if outcome else CYAN
        g.text(self.canvas, title, (640, 214), 35, color, True, True, "center")
        if outcome:
            g.text(self.canvas, f"SCORE  {w.score:07d}", (640, 285), 31, TEXT, mono=True, anchor="center")
            g.text(self.canvas, f"{w.kills} HOSTILES CLEARED  /  {w.shuffle_count} SHIFTS  /  SEED {w.seed}", (640, 337), 13, MUTED, mono=True, anchor="center")
            self.button("retry", (440, 400, 400, 52), "PLAY AGAIN  >", lambda: self.start(w.solo, fixed_mix=w.fixed_mix), filled=True, size=18)
            self.button("library", (440, 470, 400, 48), "PAK LIBRARY", self.home)
        else:
            g.text(self.canvas, "The system can wait.", (640, 279), 21, MUTED, anchor="center")
            self.button("resume", (440, 325, 400, 49), "RESUME  >", lambda: self.navigate("game"), filled=True, size=19)
            self.button("save-mix", (440, 388, 400, 44), "SAVE CURRENT MIX", lambda: self.name_remix(from_run=True), size=17)
            self.button("pause-settings", (440, 444, 400, 44), "PREFERENCES", lambda: self.open_page("settings"))
            self.button("pause-help", (440, 500, 400, 44), "CONTROLS", lambda: self.open_page("help"))
            self.button("abandon", (440, 556, 400, 44), "END RUN / PAK LIBRARY", self.home, size=15)
        hint = "A: choose   B: back   START: resume" if self.input_device == "gamepad" and not outcome else "A: choose   B: library" if self.input_device == "gamepad" else "YOUR PAK SELECTION IS SAVED"
        g.text(self.canvas, hint, (640, 624), 12, MUTED, mono=True, anchor="center")

    def draw(self):
        self.buttons = []
        self.graphics.backdrop(self.canvas, self.elapsed, art=self.route == "home")
        if self.route == "home":
            self.draw_home()
        elif self.route == "settings":
            self.draw_settings()
        elif self.route == "controls":
            self.draw_controls()
        elif self.route == "help":
            self.draw_help()
        elif self.route == "display":
            self.draw_display()
        elif self.route == "paks":
            self.draw_pak_status()
        elif self.route == "credits":
            self.draw_credits()
        elif self.route == "remix":
            self.draw_remix()
        elif self.route == "remix-picker":
            self.draw_remix_picker()
        elif self.route == "remix-saved":
            self.draw_remix_saved()
        elif self.route == "remix-name":
            self.draw_remix_name()
        elif self.route == "remix-delete":
            self.draw_remix_delete()
        elif self.route in ("game", "pause", "outcome") and self.world:
            self.draw_game()
            if self.route in ("pause", "outcome"):
                self.buttons = []
                self.draw_overlay(outcome=self.route == "outcome")
        if self._focus_pending and self.buttons:
            self.focus = self.preferred_focus()
            self._focus_pending = False
        self.focus = min(self.focus, max(0, len(self.buttons) - 1))
        if self.keyboard_focus and self.buttons and self.route != "game":
            pygame.draw.rect(self.canvas, TEXT, self.buttons[self.focus].rect.inflate(6, 6), 1, border_radius=9)
        if self.toast_timer > 0:
            self.graphics.panel(self.canvas, (200, 84, 880, 36), (28, 45, 58), CYAN, 6)
            self.graphics.text(self.canvas, self.toast, (640, 102), 15, TEXT, anchor="center")
        self.present()

    def presentation_rect(self):
        width, height = self.window.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        size = (max(1, int(SIZE[0] * scale)), max(1, int(SIZE[1] * scale)))
        return pygame.Rect((width - size[0]) // 2, (height - size[1]) // 2, *size)

    def present(self):
        target = self.presentation_rect()
        self.window.fill(BG)
        self.window.blit(pygame.transform.smoothscale(self.canvas, target.size), target)
        pygame.display.flip()

    def map_pointer(self, pos):
        target = self.presentation_rect()
        return ((pos[0] - target.x) * SIZE[0] / target.width,
                (pos[1] - target.y) * SIZE[1] / target.height)

    def activate(self, button):
        self.audio.play("select")
        button.action()

    def preferred_focus(self):
        choices = {"home": ("start", "pak-status", "settings"), "pause": ("resume",), "outcome": ("retry",),
                   "remix": ("remix-play", "remix-saved", "back"), "remix-name": ("name-save",),
                   "remix-delete": ("delete-cancel",)}.get(self.route, ("back",))
        return next((i for id in choices for i, button in enumerate(self.buttons) if button.id == id), 0)

    def move_focus(self, direction):
        if not self.buttons:
            return
        if not self.keyboard_focus:
            self.focus = self.preferred_focus()
        else:
            self.focus = spatial_focus([b.rect for b in self.buttons], self.focus, direction)
        self.keyboard_focus, self._focus_pending = True, False
        self.pointer = (-100, -100)

    def go_back(self):
        if self.route == "game":
            self.navigate("pause")
        elif self.route == "pause":
            self.navigate("game")
        elif self.route in ("settings", "display", "controls", "help", "credits", "paks",
                            "remix", "remix-picker", "remix-saved", "remix-name", "remix-delete"):
            self.back()
        elif self.route == "outcome":
            self.home()

    def device_notices(self):
        for notice in self.gamepads.drain_notices():
            if notice.active_lost and self.route == "game":
                self.navigate("pause")
            self.notify(notice.text)

    def pad_input(self, frame, elapsed):
        self.device_notices()
        if not self.window_focused:
            self.gamepads.block()
            self.menu_repeat.block()
            return
        if frame.activity:
            self.input_device = "gamepad"
            self.pointer = (-100, -100)
            if self.route != "game" and not self.keyboard_focus:
                self.focus = self.preferred_focus()
                self.keyboard_focus, self._focus_pending = True, False
        if START in frame.pressed:
            if self.route in ("game", "pause"):
                self.go_back()
            elif self.route == "home" and self.buttons:
                self.activate(self.buttons[self.preferred_focus()])
            return
        if self.route == "game":
            return
        if B in frame.pressed or BACK in frame.pressed:
            self.go_back()
            return
        if A in frame.pressed and self.buttons:
            self.activate(self.buttons[self.focus if self.keyboard_focus else self.preferred_focus()])
            return
        for button, suffix in ((LB, ":prev"), (RB, ":next")):
            if button in frame.pressed:
                target = next((b for b in self.buttons if b.id.endswith(suffix)), None)
                if target:
                    self.activate(target)
                return
        direction = self.menu_repeat.update(*frame.menu, elapsed)
        if direction:
            self.move_focus(direction)

    def handle_event(self, event):
        self.gamepads.handle_event(event)
        self.device_notices()
        if event.type == pygame.QUIT:
            self.quit()
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.window_focused = False
            self.gamepads.block()
            self.menu_repeat.block()
            if self.route == "game":
                self.navigate("pause")
        elif event.type == pygame.WINDOWFOCUSGAINED:
            self.window_focused = True
            self.gamepads.block()
            self.menu_repeat.block()
        elif not self.window_focused:
            return
        elif event.type == pygame.TEXTINPUT and self.route == "remix-name":
            self.input_device = "keyboard"
            self.append_remix_name(event.text)
        elif event.type == pygame.MOUSEMOTION:
            self.input_device = "mouse"
            self.pointer = self.map_pointer(event.pos)
            self.keyboard_focus = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.input_device = "mouse"
            self.pointer = self.map_pointer(event.pos)
            for button in self.buttons:
                if button.rect.collidepoint(self.pointer):
                    self.activate(button)
                    break
        elif event.type == pygame.KEYDOWN:
            self.input_device = "keyboard"
            if event.key == pygame.K_F11:
                self.cycle("fullscreen", [False, True])
            elif event.key == pygame.K_ESCAPE:
                self.go_back()
            elif self.route == "remix-name" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.save_remix_name()
            elif self.route == "remix-name" and event.key == pygame.K_BACKSPACE:
                self.edit_remix_name(True)
            elif self.route == "remix-name" and event.key == pygame.K_SPACE:
                pass  # TEXTINPUT supplies spaces, just like other typed characters.
            elif self.route != "game" and self.buttons:
                if event.key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_UP):
                    direction = -1 if event.key == pygame.K_UP or (event.key == pygame.K_TAB and event.mod & pygame.KMOD_SHIFT) else 1
                    self.focus = (self.focus + direction) % len(self.buttons) if self.keyboard_focus else self.preferred_focus()
                    self.keyboard_focus = True
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.activate(self.buttons[self.focus if self.keyboard_focus else self.preferred_focus()])

    def update(self, elapsed, controls=None):
        self.elapsed += elapsed
        self.toast_timer = max(0, self.toast_timer - elapsed)
        frame = self.gamepads.poll(self.prefs.gamepad_deadzone)
        self.pad_input(frame, elapsed)
        if self.route == "game" and self.world:
            if controls is None:
                keys = pygame.key.get_pressed()
                pad = self.gamepads.gameplay(frame)
                x = float(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - float(keys[pygame.K_LEFT] or keys[pygame.K_a])
                y = float(keys[pygame.K_DOWN] or keys[pygame.K_s]) - float(keys[pygame.K_UP] or keys[pygame.K_w])
                controls = Controls(x if x or y else pad.x, y if x or y else pad.y,
                                    bool(keys[pygame.K_SPACE]) or pad.fire,
                                    bool(keys[pygame.K_x] or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) or pad.special)
            self.world.advance(elapsed, controls)
            for event in self.world.drain_events():
                self.audio.play(event)
            self.audio.music(self.world.component("music").track(self.world))
            if self.world.phase == "dead":
                if not self.recorded:
                    self.prefs.high_score = max(self.prefs.high_score, self.world.score)
                    self.save()
                    self.recorded = True
                self.navigate("outcome")

    def quit(self):
        if self.world:
            self.world.close()
        self.gamepads.close()
        self.save()
        self.running = False

    def run(self, frames=None, screenshot=None, demo=False):
        count = 0
        self.draw()
        while self.running and (frames is None or count < frames):
            elapsed = self.clock.tick(120) / 1000 if frames is None else 1 / 60
            for event in pygame.event.get():
                self.handle_event(event)
            if not self.running:
                break
            self.update(elapsed, autopilot(self.world) if demo and self.world else None)
            self.draw()
            count += 1
        if screenshot:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.canvas, screenshot)
        if self.world:
            self.world.close()
        self.gamepads.close()
        pygame.quit()


def autopilot(world):
    """Deterministic QA/demo input, using exactly the same player controls."""
    return world.component("pilot").demo_controls(world) or Controls()


def main():
    parser = argparse.ArgumentParser(description="System Panic — remix your installed arcade Paks.")
    parser.add_argument("--solo", help="Installed complete Pak ID")
    parser.add_argument("--pak-dir", type=Path, action="append", help="Pak root to load instead of default locations; repeat for multiple roots")
    parser.add_argument("--list-paks", action="store_true", help="Print discovered Paks and loader issues, then exit")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--screen", choices=("home", "settings", "display", "controls", "help", "credits", "paks", "remix", "game"), default="home")
    parser.add_argument("--demo", action="store_true", help="QA/demo controls; no gameplay advantages")
    args = parser.parse_args()
    catalog = discover(args.pak_dir)
    if args.list_paks:
        print(json.dumps({"paks":[{"id":p.id, "components":p.components, "solo":p.complete, "directory":str(p.directory)} for p in catalog.paks],
                          "issues":[{"path":str(issue.path), "message":issue.message} for issue in catalog.issues]}, indent=2))
        return
    if args.solo and args.solo not in catalog.complete_ids():
        parser.error("--solo requires an installed complete Pak; use --list-paks to inspect the library")
    if args.headless:
        import os
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    with tempfile.TemporaryDirectory(prefix="system-panic-check-") as temporary:
        app = App(args.data_dir or (Path(temporary) if args.headless else None), args.seed, catalog)
        if args.solo or args.screen == "game" or args.demo:
            app.start(args.solo)
        else:
            app.route = args.screen
        app.run(args.frames if args.frames is not None else 1 if args.headless else None,
                args.screenshot, args.demo)


if __name__ == "__main__":
    main()
