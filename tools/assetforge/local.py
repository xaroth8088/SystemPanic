"""Install/run official Stable Audio 3 locally, isolated from game dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import wave

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / ".asset-tools"
REPO = TOOLS / "stable-audio-3"
BACKEND = REPO / "optimized/tflite"
ENVIRONMENT = TOOLS / "audio-env"
PYTHON = ENVIRONMENT / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
REVISION = "77e0398c26f7d22d801ec1bb036307e8b231f741"


def environment(offline=False):
    env = os.environ.copy()
    env["HF_HOME"] = str(TOOLS / "cache/huggingface")
    env["HF_HUB_DISABLE_TELEMETRY"] = "1"
    env["GRADIO_ANALYTICS_ENABLED"] = "False"
    env["GRADIO_TEMP_DIR"] = str(TOOLS / "gradio-temp")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    if offline:
        env["HF_HUB_OFFLINE"] = "1"
    elif not env.get("HF_TOKEN"):
        for path in (Path.home() / ".cache/huggingface/token", Path.home() / ".huggingface/token"):
            if path.is_file():
                env["HF_TOKEN"] = path.read_text().strip()
                break
    return env


def install():
    TOOLS.mkdir(exist_ok=True)
    if not REPO.exists():
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/Stability-AI/stable-audio-3", str(REPO)], check=True)
    revision = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        subprocess.run(["git", "-C", str(REPO), "fetch", "--depth", "1", "origin", REVISION], check=True)
        subprocess.run(["git", "-C", str(REPO), "checkout", "--detach", REVISION], check=True)
    if not PYTHON.exists():
        launcher = ["py", "-3.12"] if os.name == "nt" else [sys.executable]
        subprocess.run([*launcher, "-m", "venv", str(ENVIRONMENT)], check=True)
    subprocess.run([str(PYTHON), "-m", "pip", "install", "-r",
                    str(Path(__file__).with_name("local-requirements.lock.txt"))], check=True)
    for model, prompt in (("sm-music", "Instrumental arcade synthesizer music, no vocals"),
                          ("sm-sfx", "One short bright electronic interface click, no music")):
        render(prompt, model, 1, 24, TOOLS / "warmup" / (model + ".wav"))
    print("Local generator installed in", TOOLS)


def render(prompt, model, seconds, seed, output, offline=False):
    seconds = float(seconds)
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Duration must be a finite positive number of seconds")
    # This pinned LiteRT model produces sustained noise with fractional-second
    # conditioning (e.g. .8/1.2). Retain whole-second sources so mastering can
    # remove leading silence before choosing the requested one-shot length.
    inference_seconds = math.ceil(seconds)
    if not PYTHON.exists():
        raise RuntimeError("Run python tools/assetforge/local.py install first")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(PYTHON), "-X", "utf8", str(BACKEND / "scripts/sa3_tflite.py"),
               "--dit", model, "--decoder", "same-s", "--precision", "w8a8",
               "--prompt", prompt, "--seconds", str(inference_seconds), "--steps", "8",
               "--cfg", "1", "--seed", str(seed), "--threads", "8", "--out", str(output)]
    logs = TOOLS / "logs"
    logs.mkdir(exist_ok=True)
    log_path = logs / (output.stem + "-" + str(time.time_ns()) + ".log")
    print(f"Generating locally: {model}, {inference_seconds}s source for {seconds:g}s job, seed {seed}", flush=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        generated = Path(temporary) / "generated.wav"
        command[-1] = str(generated)
        with log_path.open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=BACKEND, env=environment(offline),
                                    stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-12:])
            raise RuntimeError(f"Local inference failed ({result.returncode}). Log: {log_path}\n{tail}")
        with wave.open(str(generated), "rb") as source:
            frames = inference_seconds * source.getframerate()
            if (source.getframerate(), source.getnchannels(), source.getsampwidth()) != (44100, 2, 2) or source.getnframes() < frames:
                raise RuntimeError("Local generator did not produce the expected 44.1kHz stereo PCM")
        generated.replace(output)
    return output


def generate(job_id, offline=False, force=False):
    jobs = json.loads(Path(__file__).with_name("prompts.json").read_text())["jobs"]
    matches = [job for job in jobs if job_id in ("all", job["id"])]
    if not matches:
        raise ValueError("Unknown prompt job: " + job_id)
    directory = ROOT / "assets/audio/local"
    directory.mkdir(exist_ok=True)
    record_path = directory / "generation.json"
    records = json.loads(record_path.read_text()) if record_path.exists() else {}
    for job in matches:
        output = directory / (job["id"] + ".wav")
        if output.exists() and records.get(job["id"], {}).get("status") == "generated" and not force:
            print("Already generated locally:", job["id"], flush=True)
            continue
        started = time.monotonic()
        model = "sm-music" if job["kind"] == "music" else "sm-sfx"
        render(job["prompt"], model, job["duration"], job["seed"], output, offline)
        previous = records.get(job["id"], {})
        history = previous.get("previous_generations", [])
        if previous:
            history = [*history, {key:value for key, value in previous.items() if key != "previous_generations"}]
        records[job["id"]] = dict(job, provider="Stable Audio 3 local LiteRT", backend="CPU / XNNPACK / w8a8",
            repository="https://github.com/Stability-AI/stable-audio-3", revision=REVISION,
            model_repository="stabilityai/stable-audio-3-optimized", status="generated",
            offline=offline, seconds_to_generate=round(time.monotonic() - started, 2),
            inference_duration=math.ceil(job["duration"]),
            output_processing="Whole-second inference; full source retained for onset trimming in mastering",
            previous_generations=history,
            file=str(output.relative_to(ROOT)).replace("\\", "/"),
            sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        record_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        print("Saved local job:", job["id"], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "generate", "serve"))
    parser.add_argument("--job", default="all")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--force", action="store_true", help="Regenerate selected jobs, retaining previous provenance")
    args = parser.parse_args()
    if args.action == "install":
        install()
    elif args.action == "generate":
        generate(args.job, args.offline, args.force)
    else:
        subprocess.run([str(PYTHON), "-X", "utf8", str(Path(__file__).with_name("studio.py"))],
                       cwd=ROOT, env=environment(True), check=True)


if __name__ == "__main__":
    main()
