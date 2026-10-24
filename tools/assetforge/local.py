"""Install/run official Stable Audio 3 locally, isolated from game dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

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
    if not PYTHON.exists():
        raise RuntimeError("Run python tools/assetforge/local.py install first")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(PYTHON), "-X", "utf8", str(BACKEND / "scripts/sa3_tflite.py"),
               "--dit", model, "--decoder", "same-s", "--precision", "w8a8",
               "--prompt", prompt, "--seconds", str(seconds), "--steps", "8",
               "--cfg", "1", "--seed", str(seed), "--threads", "8", "--out", str(output)]
    logs = TOOLS / "logs"
    logs.mkdir(exist_ok=True)
    log_path = logs / (output.stem + "-" + str(time.time_ns()) + ".log")
    print(f"Generating locally: {model}, {seconds}s, seed {seed}", flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=BACKEND, env=environment(offline),
                                stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-12:])
        raise RuntimeError(f"Local inference failed ({result.returncode}). Log: {log_path}\n{tail}")
    if not output.is_file() or output.stat().st_size < 1000:
        raise RuntimeError("Local generator did not produce a valid output file")
    return output


def generate(job_id, offline=False):
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
        if output.exists() and records.get(job["id"], {}).get("status") == "generated":
            print("Already generated locally:", job["id"], flush=True)
            continue
        started = time.monotonic()
        model = "sm-music" if job["kind"] == "music" else "sm-sfx"
        render(job["prompt"], model, job["duration"], job["seed"], output, offline)
        records[job["id"]] = dict(job, provider="Stable Audio 3 local LiteRT", backend="CPU / XNNPACK / w8a8",
            repository="https://github.com/Stability-AI/stable-audio-3", revision=REVISION,
            model_repository="stabilityai/stable-audio-3-optimized", status="generated",
            offline=offline, seconds_to_generate=round(time.monotonic() - started, 2),
            file=str(output.relative_to(ROOT)).replace("\\", "/"),
            sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        record_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        print("Saved local job:", job["id"], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "generate", "serve"))
    parser.add_argument("--job", default="all")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.action == "install":
        install()
    elif args.action == "generate":
        generate(args.job, args.offline)
    else:
        subprocess.run([str(PYTHON), "-X", "utf8", str(Path(__file__).with_name("studio.py"))],
                       cwd=ROOT, env=environment(True), check=True)


if __name__ == "__main__":
    main()
