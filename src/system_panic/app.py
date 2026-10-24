"""Desktop shell, accessible menus and fixed-step gameplay."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
import secrets
import tempfile

import pygame

from .audio import Audio
from .graphics import Graphics, BG, PANEL, EDGE, TEXT, MUTED, CYAN, DIM
from .model import WIDTH, HEIGHT, Vec, Controls, normalized
from .paks import PAKS, BY_ID, CHANNELS
from .preferences import Preferences, PreferenceStore
from .world import World

SIZE = (1280, 800)
VIEWPORT = pygame.Rect(32, 136, 1216, 608)


@dataclass
class Button:
    id: str
    rect: pygame.Rect
    label: str
    action: object


class App:
    def __init__(self, data_dir=None, seed=None):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.store = PreferenceStore(data_dir)
        self.prefs = self.store.load()
        self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("System Panic — Six worlds. One unstable system.")
        self.canvas = pygame.Surface(SIZE).convert()
        self.arena_surface = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.graphics = Graphics()
        pygame.display.set_icon(self.graphics.sprite("signal_runner", 0, 64))
        self.audio = Audio(self.prefs)
        self.clock = pygame.time.Clock()
        self.running = True
        self.route = "home"
        self.return_route = "home"
        self.world = None
        self.seed = seed
        self.buttons: list[Button] = []
        self.focus = 0
        self.keyboard_focus = False
        self.pointer = (-100, -100)
        self.elapsed = 0.
        self.toast = self.store.error
        self.toast_timer = 6. if self.toast else 0.
        self.recorded = False
        if self.prefs.fullscreen:
            self.apply_display()
        self.audio.music("signal_runner")

    def apply_display(self):
        try:
            if self.prefs.fullscreen:
                self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        except pygame.error:
            self.prefs.fullscreen = False
            self.window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)

    def save(self):
        if not self.store.save(self.prefs):
            self.notify("Preferences could not be saved. This session still works.")

    def notify(self, text):
        self.toast, self.toast_timer = text, 4.

    def navigate(self, route):
        self.route, self.focus = route, 0
        self.keyboard_focus = False
        self.buttons.clear()

    def start(self, solo=None):
        self.world = World(self.prefs, self.seed if self.seed is not None else secrets.randbelow(1_000_000), solo)
        self.recorded = False
        self.navigate("game")
        self.audio.music(self.world.mix["pilot"])

    def home(self):
        self.world = None
        self.navigate("home")
        self.audio.music("signal_runner")

    def open_page(self, route):
        self.return_route = self.route
        self.navigate(route)

    def back(self):
        self.save()
        self.navigate(self.return_route)

    def toggle_pak(self, pak_id):
        if pak_id in self.prefs.enabled:
            if len(self.prefs.enabled) == 1:
                self.notify("Keep at least one Pak enabled in the mix.")
                return
            self.prefs.enabled.remove(pak_id)
        else:
            self.prefs.enabled.append(pak_id)
        self.save()

    def cycle(self, name, options):
        current = getattr(self.prefs, name)
        setattr(self.prefs, name, options[(options.index(current) + 1) % len(options)] if current in options else options[0])
        self.audio.set_volumes()
        if name == "fullscreen":
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
        hover = rect.collidepoint(self.pointer) or (self.keyboard_focus and self.focus == index)
        fill = accent if filled else tuple(min(255, c + 7) for c in PANEL) if hover else PANEL
        border = accent if hover or filled else EDGE
        self.graphics.panel(self.canvas, rect, fill, border, 7)
        self.graphics.text(self.canvas, label, rect.center, size, BG if filled else TEXT,
                           filled, anchor="center")
        if self.keyboard_focus and self.focus == index:
            pygame.draw.rect(self.canvas, TEXT, rect.inflate(6, 6), 1, border_radius=9)

    def header(self, location):
        g = self.graphics
        g.text(self.canvas, "S / P", (40, 28), 23, CYAN, True, True)
        g.text(self.canvas, "SYSTEM PANIC", (130, 31), 17, TEXT, True, True)
        g.text(self.canvas, "/  " + location, (300, 32), 15, MUTED, mono=True)
        pygame.draw.line(self.canvas, EDGE, (40, 78), (1240, 78))

    def draw_home(self):
        g = self.graphics
        self.header("PAK LIBRARY")
        self.button("quit", (1140, 25, 100, 34), "QUIT", self.quit, size=13)
        g.text(self.canvas, "SIX WORLDS.", (40, 127), 13, CYAN, True, True)
        g.text(self.canvas, "ONE UNSTABLE SYSTEM.", (40, 149), 13, MUTED, mono=True)
        g.text(self.canvas, "SYSTEM", (35, 190), 69, TEXT, True)
        g.text(self.canvas, "PANIC", (35, 261), 88, CYAN, True)
        g.wrapped(self.canvas, "The rules will change. Keep moving.", (42, 372), 335, 23, TEXT)
        g.wrapped(self.canvas, "Six complete arcade Paks. Play one alone, or let their worlds collide.", (42, 445), 315, 18)
        mode = "COMPONENT REMIX" if self.prefs.mix_mode == "remix" else "COHERENT SHUFFLE"
        g.text(self.canvas, f"{len(self.prefs.enabled):02d} / 06 ENABLED   ·   {mode}", (42, 535), 12, CYAN, mono=True)
        self.button("start", (40, 571, 340, 61), "START REMIX  >" if len(self.prefs.enabled) > 1 else "START SOLO  >", self.start, filled=True, size=21)
        self.button("settings", (40, 648, 160, 44), "PREFERENCES", lambda: self.open_page("settings"), size=14)
        self.button("help", (218, 648, 162, 44), "HOW TO PLAY", lambda: self.open_page("help"), size=14)
        g.text(self.canvas, "BEST", (42, 727), 12, MUTED, mono=True)
        g.text(self.canvas, f"{self.prefs.high_score:07d}", (94, 719), 27, TEXT, mono=True)
        self.button("credits", (248, 718, 132, 32), "CREDITS", lambda: self.open_page("credits"), size=12)
        g.text(self.canvas, "CHOOSE YOUR MIX", (430, 107), 15, TEXT, True, True)
        g.text(self.canvas, "EVERY PAK WORKS ALONE", (1230, 108), 12, MUTED, mono=True, anchor="topright")
        for index, pak in enumerate(PAKS):
            x, y = 430 + index % 2 * 410, 150 + index // 2 * 190
            enabled = pak.id in self.prefs.enabled
            g.panel(self.canvas, (x, y, 390, 174), PANEL,
                    tuple(int(c * .55) for c in pak.color) if enabled else EDGE)
            pygame.draw.rect(self.canvas, pak.color if enabled else DIM, (x + 16, y + 15, 3, 15), border_radius=1)
            g.text(self.canvas, f"PAK {index + 1:02d}", (x + 28, y + 14), 12, pak.color if enabled else MUTED, mono=True)
            g.text(self.canvas, "IN THE MIX" if enabled else "DISABLED", (x + 372, y + 16), 10, pak.color if enabled else DIM, mono=True, anchor="topright")
            g.text(self.canvas, pak.name, (x + 17, y + 41), 25, TEXT, True)
            g.text(self.canvas, pak.subtitle, (x + 18, y + 83), 11, pak.color, mono=True)
            image = g.sprite(pak.id, 0, 90)
            self.canvas.blit(image, (x + 286, y + 35))
            self.button("solo:" + pak.id, (x + 17, y + 126, 145, 31), "PLAY SOLO  >", lambda p=pak.id: self.start(p), accent=pak.color, size=12)
            self.button("toggle:" + pak.id, (x + 269, y + 126, 104, 31), "[x] ENABLED" if enabled else "[ ] ENABLE", lambda p=pak.id: self.toggle_pak(p), accent=pak.color, size=11)
        g.text(self.canvas, "ARROWS / WASD + SPACE + X", (430, 747), 12, MUTED, mono=True)
        g.text(self.canvas, "OFFLINE / ORIGINAL AI ASSETS", (1230, 747), 12, DIM, mono=True, anchor="topright")

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
        self.setting(210, "Shuffle style", "Independent components, or complete Paks together.", "mix_mode", ["remix", "coherent"], ["COMPONENT REMIX", "COHERENT PAKS"])
        self.setting(292, "Time between changes", "A protected transition gives you time to read the new rules.", "shuffle_seconds", [5, 8, 12, 20, 30], ["5 SECONDS", "8 SECONDS", "12 SECONDS", "20 SECONDS", "30 SECONDS"])
        self.setting(374, "Challenge", "Relaxed reduces damage and enemy speed.", "difficulty", ["relaxed", "standard", "intense"])
        self.setting(456, "Run length", "A complete eight-wave run, or keep going indefinitely.", "endless", [False, True], ["8 WAVES / FINALE", "ENDLESS"])
        g.text(self.canvas, "COMPONENTS IN THE SHUFFLE", (80, 553), 12, MUTED, mono=True)
        for index, channel in enumerate(CHANNELS):
            enabled = channel in self.prefs.shuffle_channels
            self.button("channel:" + channel, (80 + index * 160, 582, 145, 36), ("[x] " if enabled else "[ ] ") + channel.upper(), lambda c=channel: self.toggle_channel(c), size=13)
        self.button("assist", (830, 582, 370, 36), "AIM ASSIST: " + ("ON" if self.prefs.aim_assist else "OFF"), lambda: self.cycle("aim_assist", [True, False]), size=13)
        for name, label, x in (("music", "MUSIC", 80), ("effects", "EFFECTS", 440)):
            g.text(self.canvas, f"{label}  {getattr(self.prefs, name):.0%}", (x, 653), 13, MUTED, mono=True)
            self.button(name + "-", (x + 150, 644, 43, 36), "-", lambda n=name: self.volume(n, -.1))
            self.button(name + "+", (x + 201, 644, 43, 36), "+", lambda n=name: self.volume(n, .1))
        self.button("motion", (830, 644, 175, 36), "MOTION: " + ("REDUCED" if self.prefs.reduced_motion else "FULL"), lambda: self.cycle("reduced_motion", [False, True]), size=12)
        self.button("display", (1020, 644, 180, 36), "FULLSCREEN" if self.prefs.fullscreen else "WINDOWED", lambda: self.cycle("fullscreen", [False, True]), size=12)
        g.wrapped(self.canvas, "Turn Paks on or off in the library. Solo launch holds every component to that Pak. In component remix, unchecked channels keep their starting Pak. Coherent mode always swaps the whole Pak.", (80, 714), 1120, 15)

    def draw_help(self):
        g = self.graphics
        self.header("HOW TO PLAY")
        self.button("back", (1100, 25, 140, 34), "<  BACK", self.back, size=13)
        g.text(self.canvas, "Adapt. Survive. Clear the wave.", (80, 108), 35, TEXT, True)
        g.wrapped(self.canvas, "Hold SPACE to fire. Aim assistance targets the nearest enemy, so every control style can fight every enemy family. X uses your current pilot's special. Destroy cover to open a route. Clear all enemies to advance; each cleared wave restores 15 health.", (80, 166), 1100, 18)
        for index, pak in enumerate(PAKS):
            x, y = 80 + index % 2 * 575, 280 + index // 2 * 135
            image = g.sprite(pak.id, 0, 66)
            self.canvas.blit(image, (x, y))
            g.text(self.canvas, pak.name, (x + 80, y), 22, pak.color, True)
            g.text(self.canvas, pak.controls, (x + 80, y + 35), 16, TEXT)
            g.text(self.canvas, pak.special, (x + 80, y + 62), 15, MUTED)
        g.text(self.canvas, "ESC: pause / back     F11: fullscreen     TAB + ENTER: navigate menus", (80, 731), 16, MUTED, mono=True)

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
        g.text(self.canvas, f"WAVE {w.wave:02d}" + (" / 08" if not w.prefs.endless else " / ENDLESS"), (40, 98), 17, TEXT, True, True)
        g.text(self.canvas, f"SCORE  {w.score:07d}", (340, 98), 17, CYAN, mono=True)
        g.text(self.canvas, f"{len(w.enemies):02d} HOSTILES", (700, 98), 15, MUTED, mono=True)
        g.text(self.canvas, "HULL", (968, 98), 12, MUTED, mono=True)
        pygame.draw.rect(self.canvas, EDGE, (1020, 100, 170, 12), border_radius=3)
        pygame.draw.rect(self.canvas, CYAN if w.player.health > 30 else (255, 119, 137), (1020, 100, max(0, 170 * w.player.health / 100), 12), border_radius=3)
        g.text(self.canvas, f"{math.ceil(w.player.health):03d}", (1238, 94), 17, TEXT, mono=True, anchor="topright")
        g.draw_world(self.arena_surface, w, self.prefs.reduced_motion)
        frame = pygame.transform.scale(self.arena_surface, VIEWPORT.size)
        offset = (0, 0)
        if w.shake and not self.prefs.reduced_motion:
            offset = (int(math.sin(self.elapsed * 91) * w.shake), int(math.cos(self.elapsed * 83) * w.shake * .5))
        self.canvas.blit(frame, VIEWPORT.move(offset))
        for index, channel in enumerate(CHANNELS):
            pak = w.pak(channel)
            x = 42 + index * 246
            g.text(self.canvas, channel.upper(), (x, 24), 10, MUTED, mono=True)
            g.text(self.canvas, pak.name, (x, 44), 16, pak.color, True)
        timer = f"SHIFT {max(0, w.shuffle_timer):04.1f}s" if len(w.enabled) > 1 else "SOLO / LOCKED"
        self.button("pause", (1075, 25, 165, 36), "ESC / PAUSE", lambda: self.navigate("pause"), size=13)
        g.text(self.canvas, timer, (1235, 758), 13, CYAN, mono=True, anchor="topright")
        g.text(self.canvas, w.pak("pilot").controls + "    SPACE: fire    " + w.pak("pilot").special, (40, 759), 14, MUTED)
        if w.phase in ("ready", "clear"):
            rect = pygame.Rect(365, 353, 550, 118)
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((5, 14, 23, 225))
            self.canvas.blit(overlay, rect)
            text = f"WAVE {w.wave:02d} / GET READY" if w.phase == "ready" else "WAVE CLEAR"
            g.text(self.canvas, text, (640, 389), 32, TEXT, True, True, "center")
            g.text(self.canvas, "+15 HULL NEXT WAVE" if w.phase == "clear" else "HOLD SPACE TO FIRE / X FOR SPECIAL", (640, 435), 14, CYAN, mono=True, anchor="center")

    def draw_overlay(self, outcome=False):
        g, w = self.graphics, self.world
        shade = pygame.Surface(SIZE, pygame.SRCALPHA)
        shade.fill((4, 10, 18, 210))
        self.canvas.blit(shade, (0, 0))
        g.panel(self.canvas, (330, 160, 620, 510), (13, 24, 36), EDGE, 16)
        title = "SYSTEM RESTORED" if outcome and w.phase == "victory" else "SIGNAL LOST" if outcome else "SYSTEM PAUSED"
        color = CYAN if not outcome or w.phase == "victory" else (255, 119, 137)
        g.text(self.canvas, title, (640, 214), 35, color, True, True, "center")
        if outcome:
            g.text(self.canvas, f"SCORE  {w.score:07d}", (640, 285), 31, TEXT, mono=True, anchor="center")
            g.text(self.canvas, f"{w.kills} HOSTILES CLEARED  /  {w.shuffle_count} SHIFTS  /  SEED {w.seed}", (640, 337), 13, MUTED, mono=True, anchor="center")
            self.button("retry", (440, 400, 400, 52), "PLAY AGAIN  >", lambda: self.start(w.solo), filled=True, size=18)
            self.button("library", (440, 470, 400, 48), "PAK LIBRARY", self.home)
        else:
            g.text(self.canvas, "The system can wait.", (640, 279), 21, MUTED, anchor="center")
            self.button("resume", (440, 350, 400, 52), "RESUME  >", lambda: self.navigate("game"), filled=True, size=19)
            self.button("pause-settings", (440, 421, 400, 46), "PREFERENCES", lambda: self.open_page("settings"))
            self.button("pause-help", (440, 482, 400, 46), "CONTROLS", lambda: self.open_page("help"))
            self.button("abandon", (440, 543, 400, 46), "END RUN / PAK LIBRARY", self.home, size=15)
        g.text(self.canvas, "YOUR PAK SELECTION IS SAVED", (640, 624), 12, DIM, mono=True, anchor="center")

    def draw(self):
        self.buttons = []
        self.graphics.backdrop(self.canvas, self.elapsed, art=self.route == "home")
        if self.route == "home":
            self.draw_home()
        elif self.route == "settings":
            self.draw_settings()
        elif self.route == "help":
            self.draw_help()
        elif self.route == "credits":
            self.draw_credits()
        elif self.route in ("game", "pause", "outcome") and self.world:
            self.draw_game()
            if self.route in ("pause", "outcome"):
                self.buttons = []
                self.draw_overlay(outcome=self.route == "outcome")
        self.focus = min(self.focus, max(0, len(self.buttons) - 1))
        if self.toast_timer > 0:
            self.graphics.panel(self.canvas, (200, 750, 880, 36), (28, 45, 58), CYAN, 6)
            self.graphics.text(self.canvas, self.toast, (640, 768), 15, TEXT, anchor="center")
        self.present()

    def present(self):
        width, height = self.window.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        size = (max(1, int(SIZE[0] * scale)), max(1, int(SIZE[1] * scale)))
        self.window.fill(BG)
        self.window.blit(pygame.transform.smoothscale(self.canvas, size), ((width - size[0]) // 2, (height - size[1]) // 2))
        pygame.display.flip()

    def map_pointer(self, pos):
        width, height = self.window.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        return ((pos[0] - (width - SIZE[0] * scale) / 2) / scale,
                (pos[1] - (height - SIZE[1] * scale) / 2) / scale)

    def activate(self, button):
        self.audio.play("select")
        button.action()

    def preferred_focus(self):
        preferred = {"home":"start", "pause":"resume", "outcome":"retry"}.get(self.route, "back")
        return next((i for i, button in enumerate(self.buttons) if button.id == preferred), 0)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.quit()
        elif event.type == pygame.WINDOWFOCUSLOST and self.route == "game":
            self.navigate("pause")
        elif event.type == pygame.MOUSEMOTION:
            self.pointer = self.map_pointer(event.pos)
            self.keyboard_focus = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pointer = self.map_pointer(event.pos)
            for button in self.buttons:
                if button.rect.collidepoint(self.pointer):
                    self.activate(button)
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.cycle("fullscreen", [False, True])
            elif event.key == pygame.K_ESCAPE:
                if self.route == "game":
                    self.navigate("pause")
                elif self.route == "pause":
                    self.navigate("game")
                elif self.route in ("settings", "help", "credits"):
                    self.back()
                elif self.route == "outcome":
                    self.home()
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
        if self.route == "game" and self.world:
            if controls is None:
                keys = pygame.key.get_pressed()
                controls = Controls(float(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - float(keys[pygame.K_LEFT] or keys[pygame.K_a]),
                                    float(keys[pygame.K_DOWN] or keys[pygame.K_s]) - float(keys[pygame.K_UP] or keys[pygame.K_w]),
                                    bool(keys[pygame.K_SPACE]), bool(keys[pygame.K_x] or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]))
            self.world.advance(elapsed, controls)
            for event in self.world.drain_events():
                self.audio.play(event)
            self.audio.music(self.world.mix["pilot"])
            if self.world.phase in ("dead", "victory"):
                if not self.recorded:
                    self.prefs.high_score = max(self.prefs.high_score, self.world.score)
                    self.save()
                    self.recorded = True
                self.navigate("outcome")

    def quit(self):
        self.save()
        self.running = False

    def run(self, frames=None, screenshot=None, demo=False):
        count = 0
        self.draw()
        while self.running and (frames is None or count < frames):
            elapsed = self.clock.tick(120) / 1000 if frames is None else 1 / 60
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(elapsed, autopilot(self.world) if demo and self.world else None)
            self.draw()
            count += 1
        if screenshot:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.canvas, screenshot)
        pygame.quit()


def autopilot(world):
    """Deterministic QA/demo input, using exactly the same player controls."""
    p = world.player
    if not world.enemies:
        return Controls(fire=True)
    target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
    delta = target.pos - p.pos
    vector = normalized(delta)
    kind = world.pak("pilot").pilot
    special = int(world.time * 3) % 11 == 0
    if kind == "drifter":
        angle = math.atan2(delta.y, delta.x)
        diff = (angle - p.angle + math.pi) % math.tau - math.pi
        return Controls(max(-1, min(1, diff * 2)), -1 if delta.length() > 180 else .3, True, special)
    if kind == "driver":
        return Controls(math.sin(world.time * .7) * .7, -.3, True, special)
    if kind == "orbiter":
        return Controls(.7, math.sin(world.time * .7) * .4, True, special)
    if kind == "jumper":
        return Controls(vector.x if delta.length() > 180 else -vector.x, -1 if world.time % 1.2 < .15 else 0, True, special)
    movement = vector if delta.length() > 210 else Vec(-vector.y, vector.x)
    return Controls(movement.x, movement.y, True, special)


def main():
    parser = argparse.ArgumentParser(description="System Panic — six arcade worlds, one unstable system.")
    parser.add_argument("--solo", choices=list(BY_ID))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--screen", choices=("home", "settings", "help", "credits", "game"), default="home")
    parser.add_argument("--demo", action="store_true", help="QA/demo controls; no gameplay advantages")
    args = parser.parse_args()
    if args.headless:
        import os
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    with tempfile.TemporaryDirectory(prefix="system-panic-check-") as temporary:
        app = App(args.data_dir or (Path(temporary) if args.headless else None), args.seed)
        if args.solo or args.screen == "game" or args.demo:
            app.start(args.solo)
        else:
            app.route = args.screen
        app.run(args.frames if args.frames is not None else 1 if args.headless else None,
                args.screenshot, args.demo)


if __name__ == "__main__":
    main()
