import hashlib
import json
import os
from array import array
import math
from pathlib import Path, PureWindowsPath
import unittest
import wave

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

ROOT = Path(__file__).resolve().parents[1]


class AssetTests(unittest.TestCase):
    def test_short_expansion_generations_decay_instead_of_sustained_noise(self):
        jobs = json.loads((ROOT / "tools/assetforge/prompts.json").read_text())["jobs"]
        for job in jobs:
            if job["kind"] != "sfx" or float(job["duration"]).is_integer():
                continue
            with self.subTest(job=job["id"]):
                with wave.open(str(ROOT / "assets/audio/local" / (job["id"] + ".wav")), "rb") as source:
                    pcm = array("h", source.readframes(source.getnframes()))
                section = len(pcm) // 5
                rms = lambda samples: math.sqrt(sum(value * value for value in samples) / len(samples))
                # These fixed one-shot launch/special fixtures decay to silence.
                # The faulty fractional conditioning instead made steady noise.
                peak = max(rms(pcm[start:start + section]) for start in range(0, len(pcm) - section + 1, section))
                self.assertLess(rms(pcm[-section:]), peak * .7, job["id"])

    def test_every_recorded_source_and_derivative_has_its_recorded_hash(self):
        manifest = json.loads((ROOT / "assets/manifest.json").read_text())
        for entry in manifest["assets"]:
            path = ROOT / PureWindowsPath(entry["file"]).as_posix()
            self.assertTrue(path.is_file(), entry["file"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"], entry["file"])
            if entry.get("operation", "").startswith("Unmodified"):
                self.assertEqual(path.read_bytes(), (ROOT / PureWindowsPath(entry["source"]).as_posix()).read_bytes(), entry["file"])
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
