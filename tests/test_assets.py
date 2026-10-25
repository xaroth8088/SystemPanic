import hashlib
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

ROOT = Path(__file__).resolve().parents[1]


class AssetTests(unittest.TestCase):
    def test_every_recorded_source_and_derivative_has_its_recorded_hash(self):
        manifest = json.loads((ROOT / "assets/manifest.json").read_text())
        for entry in manifest["assets"]:
            path = ROOT / entry["file"]
            self.assertTrue(path.is_file(), entry["file"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"], entry["file"])
            if entry.get("operation", "").startswith("Unmodified"):
                self.assertEqual(path.read_bytes(), (ROOT / entry["source"]).read_bytes(), entry["file"])
        local = json.loads((ROOT / "assets/audio/local/generation.json").read_text())
        jobs = json.loads((ROOT / "tools/assetforge/prompts.json").read_text())["jobs"]
        self.assertEqual(set(local), {job["id"] for job in jobs})
        self.assertTrue(all(entry["status"] == "generated" for entry in local.values()))

    def test_all_production_sounds_decode_and_are_not_silent(self):
        pygame.mixer.init()
        try:
            directory = ROOT / "assets/audio/production"
            paths = list(directory.glob("*.ogg")) + list(directory.glob("*.wav"))
            jobs = json.loads((ROOT / "tools/assetforge/prompts.json").read_text())["jobs"]
            self.assertEqual({path.stem for path in paths}, {job["id"] for job in jobs})
            for path in paths:
                sound = pygame.mixer.Sound(path)
                self.assertGreater(sound.get_length(), .04, path.stem)
                self.assertTrue(any(sound.get_raw()), path.stem)
        finally:
            pygame.mixer.quit()
