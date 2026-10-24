"""Exercise component folders, ABC contracts and run-owned assets through real discovery."""
import json
import os
from pathlib import Path
import py_compile
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame
from system_panic.app import App, autopilot
from system_panic.model import Controls, FIXED_DT
from system_panic.paks import CHANNELS, discover
from system_panic.pak_api import PilotBase, WeaponBase, ImageAsset, SoundAsset
from system_panic.pak_assets import AssetLoader
from system_panic.preferences import Preferences
from system_panic.world import World

TEMP_ROOT = ROOT / "output/test-temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
FILES = {c:c + ".py" for c in CHANNELS} | {"obstacles":"obstacle.py"}


class SoundBus:
    def __init__(self):
        self.playing = set()
        self.events = []

    def play_asset(self, asset, *, loop=False, volume=1.):
        self.playing.add(asset)
        self.events.append((asset, loop, volume))

    def stop_asset(self, asset):
        self.playing.discard(asset)


class PakTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.root = Path(self.temp.name)
        self.source = ROOT / "paks/signal_runner"

    def tearDown(self):
        pygame.quit()
        self.temp.cleanup()

    def make_pak(self, id, components=CHANNELS, code=None, inherits=None):
        folder = self.root / id
        folder.mkdir()
        configs = {}
        for channel in components:
            target = folder / channel
            if inherits and channel in inherits:
                target.mkdir()
                asset = next((self.source / channel).glob("*.png"), None)
                if asset is None:
                    asset = next((self.source / channel).glob("*.ogg"))
                shutil.copyfile(asset, target / ("alternate" + asset.suffix))
                configs[channel] = {"inherits":inherits[channel], "assets":{asset.name:"alternate" + asset.suffix}}
            else:
                shutil.copytree(self.source / channel, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                configs[channel] = {}
        data = json.loads((self.source / "pak.json").read_text(encoding="utf-8"))
        data.update(id=id, name=id.replace("_", " ").title(), components=configs, order=100)
        data.pop("authoring", None)
        for channel, text in (code or {}).items():
            (folder / channel / FILES[channel]).write_text(text, encoding="utf-8")
        self.write_manifest(folder, data)
        return folder

    def write_manifest(self, folder, data):
        (folder / "pak.json").write_text(json.dumps(data), encoding="utf-8")

    def catalog(self):
        catalog = discover([self.root])
        self.assertEqual(catalog.issues, ())
        return catalog

    def test_external_complete_pak_plays_without_launch_paks(self):
        self.make_pak("external")
        catalog = self.catalog()
        world = World(Preferences(), 24, solo="external", catalog=catalog)
        for _ in range(1200):
            world.advance(1 / 60, autopilot(world))
            if world.wave > 1:
                break
        self.assertGreater(world.wave, 1)
        self.assertEqual(set(world.mix.values()), {"external"})
        self.assertEqual(catalog.complete_ids(), ("external",))

    def test_six_partial_paks_form_a_playable_locked_mix_without_a_complete_pak(self):
        for channel in CHANNELS:
            self.make_pak("only_" + channel, [channel])
        catalog = self.catalog()
        world = World(Preferences(enabled=list(catalog.by_id), mix_mode="coherent"), 24, catalog=catalog)
        self.assertEqual(world.prefs.mix_mode, "remix")
        self.assertFalse(world.can_shuffle)
        self.assertEqual(world.mix, {c:"only_" + c for c in CHANNELS})
        for _ in range(1200):
            world.advance(1 / 60, autopilot(world))
            if world.wave > 1:
                break
        self.assertGreater(world.wave, 1)
        world.phase, world.shuffle_timer = "active", FIXED_DT / 2
        world.step(FIXED_DT, Controls())
        self.assertEqual(world.shuffle_count, 0)
        for id in catalog.by_id:
            with self.assertRaisesRegex(ValueError, "complete Pak"):
                World(Preferences(), solo=id, catalog=catalog)

    def test_partial_weapon_only_enters_weapon_pool_and_coherent_excludes_partials(self):
        self.make_pak("base")
        self.make_pak("addon", ["weapon"])
        catalog = self.catalog()
        world = World(Preferences(enabled=list(catalog.by_id)), 24, catalog=catalog)
        seen = set()
        for _ in range(12):
            world.shuffle()
            seen.add(world.mix["weapon"])
            self.assertTrue(all(world.mix[c] == "base" for c in CHANNELS if c != "weapon"))
        self.assertEqual(seen, {"base", "addon"})
        world.prefs.mix_mode = "coherent"
        self.assertFalse(world.can_shuffle)
        world.shuffle()
        self.assertEqual(set(world.mix.values()), {"base"})

    def test_music_and_background_are_independent_without_resetting_locked_behavior(self):
        self.make_pak("base")
        self.make_pak("scenery", ["music", "background"])
        catalog = self.catalog()
        world = World(Preferences(enabled=list(catalog.by_id), shuffle_channels=["music"]), 24, catalog=catalog)
        pilot, enemy = world.component("pilot"), world.component("enemy")
        geometry = world.cover
        world.cover[0].health = 7
        before = world.mix.copy()
        world.shuffle()
        self.assertNotEqual(world.mix["music"], before["music"])
        self.assertEqual(world.mix["background"], before["background"])
        self.assertIs(world.component("pilot"), pilot)
        self.assertIs(world.component("enemy"), enemy)
        self.assertIs(world.cover, geometry)
        self.assertEqual(world.cover[0].health, 7)
        world.prefs.shuffle_channels = ["background"]
        before = world.mix.copy()
        world.shuffle()
        self.assertNotEqual(world.mix["background"], before["background"])
        self.assertEqual(world.mix["music"], before["music"])

    def test_asset_only_partial_reuses_class_and_overrides_component_local_handle(self):
        self.make_pak("base")
        self.make_pak("aaa_skin", ["weapon"], inherits={"weapon":"base"})
        catalog = self.catalog()
        base, addon = catalog.by_id["base"], catalog.by_id["aaa_skin"]
        self.assertIs(addon.parts["weapon"].implementation, base.parts["weapon"].implementation)
        app = App(self.root / "profile", 24, catalog)
        app.start()
        app.world.mix["weapon"] = addon.id
        weapon = app.world.component("weapon")
        handle = weapon.sprite(app.world)
        self.assertEqual(handle.path, self.root / "aaa_skin/weapon/alternate.png")
        self.assertEqual(weapon.cooldown, base.create("weapon").cooldown)
        app.world.fire_weapon()
        app.draw()
        self.assertIn(handle.path, app.graphics.images)
        self.assertFalse(addon.complete)

    def test_music_only_asset_variant_streams_its_own_track(self):
        self.make_pak("base")
        self.make_pak("score", ["music"], inherits={"music":"base"})
        catalog = self.catalog()
        app = App(self.root / "profile", 24, catalog)
        track = catalog.by_id["score"].create("music").track()
        with patch("pygame.mixer.music.load") as load:
            app.audio.music(track)
            load.assert_called_once_with(self.root / "score/music/alternate.ogg")

    def test_abstract_wrong_base_and_missing_assets_are_isolated(self):
        self.make_pak("valid")
        self.make_pak("abstract", ["pilot"], code={"pilot":"from system_panic.pak_api import PilotBase\nclass Broken(PilotBase):\n    def sprite(self, world, entity=None): return None\n"})
        self.make_pak("wrong_base", ["weapon"], code={"weapon":"class Wrong: pass\nCOMPONENT = Wrong\n"})
        self.make_pak("missing_asset", ["weapon"], code={"weapon":"from system_panic.pak_api import WeaponBase\nclass Broken(WeaponBase):\n    def init(self): self.x = self.load_asset('absent.png')\n    def sprite(self, world, entity=None): return self.x\n    def fire(self, world, direction): pass\n"})
        self.make_pak("import_failure", ["music"], code={"music":"raise SystemExit('broken plugin')\n"})
        catalog = discover([self.root])
        self.assertEqual(tuple(catalog.by_id), ("valid",))
        self.assertEqual(len(catalog.issues), 4)
        self.assertTrue(any("abstract methods missing: move" in i.message for i in catalog.issues))
        self.assertTrue(any("WeaponBase" in i.message for i in catalog.issues))
        self.assertTrue(any("Missing component asset" in i.message for i in catalog.issues))

    def test_bad_manifests_duplicate_ids_and_asset_path_escape_are_isolated(self):
        self.make_pak("valid")
        for id, change in (("wrong_api", {"api_version":1}), ("bad_color", {"color":[-1,0,0]}),
                           ("zz_duplicate", {"id":"valid"}), ("bad_components", {"components":[]})):
            folder = self.make_pak(id)
            data = json.loads((folder / "pak.json").read_text())
            data.update(change)
            self.write_manifest(folder, data)
        self.make_pak("escaped", ["weapon"], inherits={"weapon":"valid"})
        data = json.loads((self.root / "escaped/pak.json").read_text())
        data["components"]["weapon"]["assets"] = {"weapon_sheet.png":"../../valid/weapon/weapon_sheet.png"}
        self.write_manifest(self.root / "escaped", data)
        catalog = discover([self.root])
        self.assertEqual(tuple(catalog.by_id), ("valid",))
        self.assertEqual(len(catalog.issues), 5)
        self.assertTrue(any("out-of-folder" in i.message for i in catalog.issues))

    def test_invalid_preview_and_track_handle_types_are_reported_at_discovery(self):
        weapon = (self.source / "weapon/weapon.py").read_text(encoding="utf-8")
        weapon += "\nclass Invalid(SignalRunnerWeapon):\n    def sprite(self, world, entity=None): return self.shot_sound\nCOMPONENT = Invalid\n"
        self.make_pak("bad_sprite", ["weapon"], code={"weapon":weapon})
        music = (self.source / "music/music.py").read_text(encoding="utf-8")
        music += "\nclass Invalid(SignalRunnerMusic):\n    def track(self, world=None): return self.score.path\nCOMPONENT = Invalid\n"
        self.make_pak("bad_track", ["music"], code={"music":music})
        catalog = discover([self.root])
        self.assertFalse(catalog.paks)
        self.assertEqual(len(catalog.issues), 2)
        self.assertTrue(any("ImageAsset" in i.message for i in catalog.issues))
        self.assertTrue(any("SoundAsset" in i.message for i in catalog.issues))

    def test_missing_and_cyclic_inheritance_are_reported(self):
        self.make_pak("missing", ["weapon"], inherits={"weapon":"absent"})
        self.make_pak("cycle_a", ["weapon"], inherits={"weapon":"cycle_b"})
        self.make_pak("cycle_b", ["weapon"], inherits={"weapon":"cycle_a"})
        catalog = discover([self.root])
        self.assertFalse(catalog.paks)
        self.assertEqual(len(catalog.issues), 3)

    def test_relative_helpers_are_isolated_and_rescan_ignores_stale_bytecode(self):
        original = (self.source / "weapon/weapon.py").read_text(encoding="utf-8")
        for id, value in (("one", 11), ("two", 22)):
            folder = self.make_pak(id, ["weapon"], code={"weapon":original + "\nfrom .helper import VALUE\n"})
            (folder / "weapon/helper.py").write_text(f"VALUE = {value}\n")
        catalog = self.catalog()
        self.assertEqual([p.parts["weapon"].implementation.fire.__globals__["VALUE"] for p in catalog.paks], [11,22])
        helper = self.root / "one/weapon/helper.py"
        py_compile.compile(str(helper), doraise=True)
        timestamp = helper.stat()
        helper.write_text("VALUE = 33\n")
        os.utime(helper, ns=(timestamp.st_atime_ns,timestamp.st_mtime_ns))
        catalog = self.catalog()
        self.assertEqual(catalog.by_id["one"].parts["weapon"].implementation.fire.__globals__["VALUE"], 33)

    def test_rescan_changed_component_code_and_removed_selection(self):
        folder = self.make_pak("external")
        app = App(self.root / "profile", 24, self.catalog())
        path = folder / "weapon/weapon.py"
        timestamp = path.stat()
        path.write_text(path.read_text(encoding="utf-8").replace("damage=16", "damage=99"), encoding="utf-8")
        os.utime(path, ns=(timestamp.st_atime_ns,timestamp.st_mtime_ns))
        app.reload_paks()
        app.start("external")
        app.world.fire_weapon()
        self.assertEqual(app.world.projectiles[0].damage, 99)
        app.home()
        app.prefs.enabled = ["removed"]
        app.save()
        app.reload_paks()
        self.assertEqual(app.prefs.enabled, ["external"])

    def test_author_asset_names_are_private_and_instances_never_leak_between_runs(self):
        self.make_pak("external")
        catalog = self.catalog()
        first, second = [World(Preferences(), 24, catalog=catalog) for _ in range(2)]
        a, b = first.component("pilot"), second.component("pilot")
        self.assertIsNot(a, b)
        self.assertIsNot(a.spritesheet, b.spritesheet)
        a.my_custom_animation_counter = 17
        self.assertFalse(hasattr(b, "my_custom_animation_counter"))
        self.assertFalse(hasattr(PilotBase, "spritesheet"))
        self.assertFalse(hasattr(WeaponBase, "projectiles"))

    def test_component_sounds_are_owned_and_stopped_on_pause_replacement_and_end(self):
        self.make_pak("base")
        self.make_pak("pilot_addon", ["pilot"])
        catalog = self.catalog()
        bus = SoundBus()
        world = World(Preferences(enabled=list(catalog.by_id)), 24, catalog=catalog, audio=bus)
        pilot = world.component("pilot")
        pilot.dash_sound.play(loop=True, volume=.4)
        self.assertIn(pilot.dash_sound, bus.playing)
        world.suspend()
        self.assertFalse(bus.playing)
        pilot.dash_sound.play(loop=True)
        world.shuffle()
        self.assertNotIn(pilot.dash_sound, bus.playing)
        current = world.component("pilot")
        current.dash_sound.play(loop=True)
        world.close()
        self.assertFalse(bus.playing)

    def test_real_loop_playback_is_idempotent_and_obeys_effects_preferences(self):
        self.make_pak("base")
        app = App(self.root / "profile", 24, self.catalog())
        app.start("base")
        asset = app.world.component("pilot").dash_sound
        asset.play(loop=True, volume=.4)
        asset.play(loop=True, volume=.4)
        owned = [index for index, (owner, _, _) in app.audio.voices.items() if owner is asset]
        self.assertEqual(len(owned), 1)
        app.prefs.effects = 0
        app.audio.set_volumes()
        self.assertEqual(pygame.mixer.Channel(owned[0]).get_volume(), 0)
        app.navigate("pause")
        self.assertFalse(any(owner is asset for owner, _, _ in app.audio.voices.values()))

    def test_scaffolder_creates_runnable_complete_and_partial_folders_without_overwriting(self):
        from tools.new_pak import create_pak
        complete = create_pak(self.root / "new_game", self.source)
        partial = create_pak(self.root / "new_weapon", self.source, ["weapon"])
        catalog = self.catalog()
        self.assertTrue(catalog.by_id[complete.name].complete)
        self.assertEqual(catalog.by_id[partial.name].components, ("weapon",))
        self.assertTrue((complete / "pilot/pilot.py").is_file())
        self.assertFalse((partial / "pilot").exists())
        with self.assertRaises(ValueError): create_pak(complete, self.source)

    def test_frame_bounded_and_quit_event_runs_release_components_without_reactivation(self):
        code = (self.source / "pilot/pilot.py").read_text(encoding="utf-8")
        code += "\nEVENTS = []\nclass Tracked(SignalRunnerPilot):\n    def activate(self, world): EVENTS.append('active')\n    def deactivate(self, world): EVENTS.append('inactive')\nCOMPONENT = Tracked\n"
        self.make_pak("tracked", code={"pilot":code})
        catalog = self.catalog()
        events = catalog.by_id["tracked"].parts["pilot"].implementation.activate.__globals__["EVENTS"]
        for immediate_quit in (False, True):
            with self.subTest(immediate_quit=immediate_quit):
                events.clear()
                app = App(self.root / "profile", 24, catalog)
                app.start("tracked")
                if immediate_quit:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                app.run(frames=2, demo=True)
                self.assertEqual(events, ["active", "inactive"])

    def test_frame_handles_select_real_sheet_rectangles_and_path_checks_apply(self):
        folder = self.root / "images"
        folder.mkdir()
        surface = pygame.Surface((4, 2), pygame.SRCALPHA)
        surface.fill((10,20,30))
        surface.fill((200,100,50),(2,0,2,2))
        pygame.image.save(surface, folder / "sheet.png")
        loader = AssetLoader(folder)
        sheet = loader.load("sheet.png")
        self.assertIsInstance(sheet, ImageAsset)
        frame = sheet.frame(1, columns=2)
        self.assertEqual(frame.rect, (2,0,2,2))
        self.assertEqual(frame.image.surface.subsurface(frame.rect).get_at((0,0))[:3], (200,100,50))
        with self.assertRaises(ValueError): sheet.frame(2, columns=2)
        with self.assertRaises(ValueError): loader.load("../sheet.png")

    def test_folder_detection_and_explicit_export_make_class_discovery_unambiguous(self):
        folder = self.make_pak("detected", ["weapon"])
        data = json.loads((folder / "pak.json").read_text())
        data.pop("components")
        self.write_manifest(folder, data)
        path = folder / "weapon/weapon.py"
        code = path.read_text(encoding="utf-8")
        code += "\nclass Alternative(SignalRunnerWeapon): pass\nCOMPONENT = Alternative\n"
        path.write_text(code,encoding="utf-8")
        catalog = self.catalog()
        self.assertEqual(catalog.by_id["detected"].components, ("weapon",))
        self.assertEqual(catalog.by_id["detected"].parts["weapon"].implementation.__name__, "Alternative")

    def test_library_paginates_partials_without_solo_and_preserves_coverage(self):
        self.make_pak("base")
        for index in range(7): self.make_pak(f"weapon_{index}", ["weapon"])
        app = App(self.root / "profile", 24, self.catalog())
        seen = set()
        for page in (0,1):
            app.library_page = page
            app.draw()
            seen.update(b.id for b in app.buttons if b.id.startswith("toggle:"))
            self.assertTrue(all(b.id == "solo:base" for b in app.buttons if b.id.startswith("solo:")))
            self.assertTrue(all(app.canvas.get_rect().contains(b.rect) for b in app.buttons))
        self.assertEqual(len(seen),8)
        app.prefs.enabled = ["base","weapon_0"]
        app.toggle_pak("base")
        self.assertIn("base",app.prefs.enabled)

    def test_empty_and_incomplete_installs_can_rescan_into_play(self):
        app = App(self.root / "profile",24,discover([self.root]))
        app.draw()
        self.assertNotIn("start",[b.id for b in app.buttons])
        app.start()
        self.assertIsNone(app.world)
        self.make_pak("music_only",["music"])
        app.reload_paks()
        app.draw()
        self.assertNotIn("start",[b.id for b in app.buttons])
        self.make_pak("complete")
        app.reload_paks()
        app.draw()
        self.assertIn("start",[b.id for b in app.buttons])
        app.start()
        self.assertIsNotNone(app.world)
