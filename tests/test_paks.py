"""Exercise drop-in complete, partial and asset-only Paks through the real loader."""
import json
import os
import py_compile
from pathlib import Path
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
from system_panic.model import Controls, FIXED_DT, Vec
from system_panic.paks import CHANNELS, discover
from system_panic.preferences import Preferences, PreferenceStore
from system_panic.world import World

TEMP_ROOT = ROOT / "output/test-temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


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
        shutil.copytree(self.source / "assets", folder / "assets")
        data = json.loads((self.source / "pak.json").read_text(encoding="utf-8"))
        data.update(id=id, name=id.replace("_", " ").title(), components=list(components), order=100)
        data.pop("authoring", None)
        data["assets"]["sprites"] = {c:p for c, p in data["assets"]["sprites"].items() if c in components}
        if inherits:
            data["inherits"] = inherits
            for channel in inherits:
                data.pop(channel, None)
            data.pop("cooldown", None)
        if code is not False:
            (folder / "pak.py").write_text(code if code is not None else (self.source / "pak.py").read_text(encoding="utf-8"), encoding="utf-8")
        self.write_manifest(folder, data)
        return folder

    def write_manifest(self, folder, data):
        (folder / "pak.json").write_text(json.dumps(data), encoding="utf-8")

    def test_external_complete_pak_plays_without_any_launch_paks(self):
        self.make_pak("external")
        catalog = discover([self.root])
        self.assertEqual(catalog.issues, ())
        self.assertEqual(catalog.complete_ids(), ("external",))
        world = World(Preferences(), 24, solo="external", catalog=catalog)
        for _ in range(20 * 60):
            world.advance(1 / 60, autopilot(world))
            if world.wave > 1:
                break
        self.assertGreater(world.wave, 1)
        self.assertEqual(set(world.mix.values()), {"external"})
        self.assertTrue(all(p.directory.parent == self.root for p in catalog.paks))

    def test_four_partial_paks_form_a_playable_mix_without_a_complete_pak(self):
        for channel in CHANNELS:
            self.make_pak("only_" + channel, [channel])
        catalog = discover([self.root])
        self.assertEqual(catalog.issues, ())
        self.assertFalse(catalog.complete_ids())
        world = World(Preferences(enabled=list(catalog.by_id), mix_mode="coherent"), 24, catalog=catalog)
        self.assertEqual(world.prefs.mix_mode, "remix")
        self.assertFalse(world.can_shuffle)
        for _ in range(12):
            world.shuffle()
            self.assertEqual(world.mix, {c:"only_" + c for c in CHANNELS})
        for _ in range(20 * 60):
            world.advance(1 / 60, autopilot(world))
            if world.wave > 1:
                break
        self.assertGreater(world.wave, 1)
        for id in catalog.by_id:
            with self.assertRaisesRegex(ValueError, "complete Pak"):
                World(Preferences(), solo=id, catalog=catalog)
        world.phase = "active"
        world.transition = 0
        world.shuffle_timer = FIXED_DT / 2
        previous = world.shuffle_count
        world.step(FIXED_DT, Controls())
        self.assertEqual(world.shuffle_count, previous)
        self.assertEqual(world.transition, 0)

    def test_partial_weapon_only_enters_weapon_pool_and_coherent_uses_complete_paks(self):
        self.make_pak("base")
        self.make_pak("weapon_addon", ["weapon"])
        catalog = discover([self.root])
        world = World(Preferences(enabled=list(catalog.by_id)), 24, catalog=catalog)
        self.assertTrue(world.can_shuffle)
        seen = set()
        for _ in range(20):
            world.shuffle()
            seen.add(world.mix["weapon"])
            self.assertTrue(all(world.mix[c] == "base" for c in ("pilot", "enemy", "arena")))
        self.assertEqual(seen, {"base", "weapon_addon"})
        world.prefs.mix_mode = "coherent"
        self.assertFalse(world.can_shuffle)
        for _ in range(10):
            world.shuffle()
            self.assertEqual(set(world.mix.values()), {"base"})

    def test_asset_only_partial_inherits_behavior_without_an_entrypoint(self):
        self.make_pak("base")
        self.make_pak("aaa_visual_weapon", ["weapon"], code=False, inherits={"weapon":"base"})
        catalog = discover([self.root])
        self.assertEqual(catalog.issues, ())
        addon = catalog.by_id["aaa_visual_weapon"]
        self.assertFalse(addon.complete)
        self.assertIs(addon.fire, catalog.by_id["base"].fire)
        self.assertEqual(addon.cooldown, catalog.by_id["base"].cooldown)
        self.assertEqual(addon.weapon, catalog.by_id["base"].weapon)
        app = App(self.root / "profile", 24, catalog)
        app.start()
        app.world.mix["weapon"] = addon.id
        app.world.fire_weapon()
        app.draw()
        self.assertIn(addon.sprites[3], app.graphics.images)
        with patch("pygame.mixer.music.load") as load:
            app.audio.music(addon.id)
            load.assert_called_once_with(addon.music)

    def test_loader_isolates_invalid_paks_duplicate_ids_and_import_failures(self):
        self.make_pak("valid")
        for id, change in (("wrong_api", {"api_version":99}), ("bad_color", {"color":[-1, 0, 0]}),
                           ("zz_duplicate", {"id":"valid"}), ("bad_components", {"components":[]})):
            folder = self.make_pak(id)
            data = json.loads((folder / "pak.json").read_text(encoding="utf-8"))
            data.update(change)
            self.write_manifest(folder, data)
        self.make_pak("missing_callback", code="def move(*args): pass\n")
        self.make_pak("import_failure", code="raise SystemExit('broken plugin')\n")
        folder = self.make_pak("escaped_asset")
        data = json.loads((folder / "pak.json").read_text(encoding="utf-8"))
        data["assets"]["sprites"]["pilot"] = "../valid/assets/pilot.png"
        self.write_manifest(folder, data)
        catalog = discover([self.root])
        self.assertEqual(tuple(catalog.by_id), ("valid",))
        self.assertEqual(len(catalog.issues), 7)
        self.assertTrue(any("Duplicate" in issue.message for issue in catalog.issues))
        self.assertTrue(any("callback" in issue.message for issue in catalog.issues))
        self.assertTrue(any("out-of-folder" in issue.message for issue in catalog.issues))

    def test_inheritance_missing_providers_and_cycles_are_reported(self):
        self.make_pak("missing", ["weapon"], code=False, inherits={"weapon":"absent"})
        self.make_pak("cycle_a", ["weapon"], code=False, inherits={"weapon":"cycle_b"})
        self.make_pak("cycle_b", ["weapon"], code=False, inherits={"weapon":"cycle_a"})
        catalog = discover([self.root])
        self.assertFalse(catalog.paks)
        self.assertEqual(len(catalog.issues), 3)
        self.assertTrue(any("Missing weapon provider" in i.message for i in catalog.issues))
        self.assertEqual(sum("Cyclic" in i.message for i in catalog.issues), 2)

    def test_relative_helpers_are_isolated_between_paks(self):
        code = (self.source / "pak.py").read_text(encoding="utf-8") + "\nfrom .helper import VALUE\n"
        for id, value in (("one", 11), ("two", 22)):
            folder = self.make_pak(id, code=code)
            (folder / "helper.py").write_text(f"VALUE = {value}\n")
        catalog = discover([self.root])
        self.assertEqual(catalog.issues, ())
        self.assertEqual([p.fire.__globals__["VALUE"] for p in catalog.paks], [11, 22])
        helper = self.root / "one/helper.py"
        py_compile.compile(str(helper), doraise=True)
        timestamp = helper.stat()
        helper.write_text("VALUE = 33\n", encoding="utf-8")
        os.utime(helper, ns=(timestamp.st_atime_ns, timestamp.st_mtime_ns))
        rescanned = discover([self.root])
        self.assertEqual(rescanned.by_id["one"].fire.__globals__["VALUE"], 33)

    def test_rescan_loads_changed_code_and_repairs_removed_selection(self):
        folder = self.make_pak("external")
        app = App(self.root / "profile", 24, discover([self.root]))
        old = app.catalog.by_id["external"].fire
        path = folder / "pak.py"
        timestamp = path.stat()
        path.write_text(path.read_text(encoding="utf-8").replace("damage=16", "damage=99"), encoding="utf-8")
        os.utime(path, ns=(timestamp.st_atime_ns, timestamp.st_mtime_ns))
        app.reload_paks()
        new = app.catalog.by_id["external"].fire
        self.assertIsNot(new, old)
        app.start("external")
        app.world.fire_weapon()
        self.assertEqual(app.world.projectiles[0].damage, 99)
        app.home()
        app.prefs.enabled = ["removed"]
        app.save()
        app.reload_paks()
        self.assertEqual(app.prefs.enabled, ["external"])

    def test_library_paginates_partial_paks_and_only_complete_paks_have_solo_buttons(self):
        self.make_pak("base")
        for index in range(7):
            self.make_pak(f"weapon_{index}", ["weapon"])
        app = App(self.root / "profile", 24, discover([self.root]))
        seen = set()
        for page in (0, 1):
            app.library_page = page
            app.draw()
            seen.update(b.id for b in app.buttons if b.id.startswith("toggle:"))
            self.assertTrue(all(b.id == "solo:base" for b in app.buttons if b.id.startswith("solo:")))
            self.assertTrue(all(app.canvas.get_rect().contains(b.rect) for b in app.buttons))
        self.assertEqual(len(seen), 8)
        app.prefs.enabled = ["base", "weapon_0"]
        app.toggle_pak("base")
        self.assertIn("base", app.prefs.enabled)

    def test_empty_or_incomplete_install_shows_menu_and_can_rescan_into_play(self):
        app = App(self.root / "profile", 24, discover([self.root]))
        app.draw()
        self.assertNotIn("start", [b.id for b in app.buttons])
        app.start()
        self.assertIsNone(app.world)
        self.make_pak("weapon_only", ["weapon"])
        app.reload_paks()
        app.draw()
        self.assertNotIn("start", [b.id for b in app.buttons])
        app.route = "paks"
        app.draw()
        self.make_pak("complete")
        app.home()
        app.reload_paks()
        app.draw()
        self.assertIn("start", [b.id for b in app.buttons])
        app.start()
        self.assertIsNotNone(app.world)
        self.assertFalse(app.catalog.missing(app.prefs.enabled))
