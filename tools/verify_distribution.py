"""Verify frozen drop-in Paks, partial-only play and wheel layout after a build."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ("pilot", "enemy", "weapon", "music", "background", "obstacles")


def main():
    folder = ROOT / "dist/SystemPanic"
    exe = folder / "SystemPanic.exe"
    output = ROOT / "output/verification/distribution"
    output.mkdir(parents=True, exist_ok=True)
    records = []

    def run(name, *arguments, frames=240):
        result = subprocess.run([str(exe), "--headless", "--seed", "24", "--frames", str(frames),
                                 "--data-dir", str(output / "profile"), *map(str, arguments)],
                                cwd=output, timeout=40, capture_output=True)
        if result.returncode:
            raise AssertionError((name, result.returncode, result.stderr.decode(errors="replace")))
        records.append({"check":name, "frames":frames, "exit_code":result.returncode})
        print(name + ": passed", flush=True)

    manifests = sorted((folder / "paks").glob("*/pak.json"))
    expected_paks = len(list((ROOT / "paks").glob("*/pak.json")))
    assert len(manifests) == expected_paks
    for manifest in manifests:
        data = json.loads(manifest.read_text())
        assert not (manifest.parent / "pak.py").exists()
        assert not (manifest.parent / "assets").exists()
        for channel in data["components"]:
            filename = "obstacle.py" if channel == "obstacles" else channel + ".py"
            assert (manifest.parent / channel / filename).is_file()
        if len(data["components"]) == 6:
            run(data["id"], "--demo", "--solo", data["id"])

    with tempfile.TemporaryDirectory(dir=output) as temporary:
        temp = Path(temporary)
        source = ROOT / "paks/signal_runner"

        def make_pak(destination, id, components):
            destination.mkdir(parents=True)
            for channel in components:
                shutil.copytree(source / channel, destination / channel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            data = json.loads((source / "pak.json").read_text(encoding="utf-8"))
            data.update(id=id, name=id.replace("_", " ").title(), components=list(components), order=100)
            data.pop("authoring", None)
            (destination / "pak.json").write_text(json.dumps(data), encoding="utf-8")
            if "weapon" in components:
                code = (destination / "weapon/weapon.py").read_text(encoding="utf-8")
                code += '''
from .helper import PROOF
from pathlib import Path
import json
class ProbeWeapon(SignalRunnerWeapon):
    def fire(self, world, direction):
        super().fire(world, direction)
        Path(__file__).with_name("played.json").write_text(json.dumps({"proof":PROOF,"mix":world.mix,"wave":world.wave}),encoding="utf-8")
COMPONENT = ProbeWeapon
'''
                (destination / "weapon/weapon.py").write_text(code, encoding="utf-8")
                (destination / "weapon/helper.py").write_text('PROOF = "loaded after executable build"\n', encoding="utf-8")

        probe = (folder / "paks/_verification_probe").resolve()
        assert probe.parent == (folder / "paks").resolve() and not probe.exists()
        try:
            make_pak(probe, "external_probe", CHANNELS)
            run("drop_in_after_build", "--solo", "external_probe", "--demo")
            proof = json.loads((probe / "weapon/played.json").read_text())
            assert proof["proof"] == "loaded after executable build"
            assert set(proof["mix"].values()) == {"external_probe"}
        finally:
            if probe.exists():
                shutil.rmtree(probe)

        partials = temp / "partials"
        for channel in CHANNELS:
            make_pak(partials / ("only_" + channel), "only_" + channel, [channel])
        run("partial_only_mix", "--pak-dir", partials, "--demo", "--screenshot", output / "partial-only.png")
        proof = json.loads((partials / "only_weapon/weapon/played.json").read_text())
        assert proof["mix"] == {c:"only_" + c for c in CHANNELS}
        run("partial_library", "--pak-dir", partials, "--screenshot", output / "partial-library.png", frames=1)
        empty = temp / "empty"
        empty.mkdir()
        run("empty_install", "--pak-dir", empty, "--screenshot", output / "empty.png", frames=1)
        broken = partials / "broken"
        broken.mkdir()
        (broken / "pak.json").write_text('{"api_version":99}')
        run("invalid_pak_isolated", "--pak-dir", partials, "--screen", "paks", "--screenshot", output / "issues.png", frames=1)

    wheel = ROOT / "dist/system_panic-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel) as bundle:
        names = bundle.namelist()
        assert "system_panic/pak_api.py" in names
        assert not any("/data/share/system-panic/paks/" in name and (name.endswith("/pak.py") or "/assets/" in name) for name in names)
        code = [name for name in names if name.startswith("system_panic/paks/") and name.endswith(".py")]
        assert set(code) == {f"system_panic/paks/{name}.py" for name in ("__init__", "model", "registry")}, code
        assert len([name for name in names if "/data/share/system-panic/paks/" in name and name.endswith("/pak.json")]) == expected_paks
        assert bundle.testzip() is None
    report = {"checks":records, "external_code_and_helpers_executed":True, "partial_only_mix_executed":True,
              "wheel_external_layout_verified":True, "executable_sha256":hashlib.sha256(exe.read_bytes()).hexdigest()}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Frozen drop-in/partial/empty-install checks and external wheel layout passed.")


if __name__ == "__main__":
    main()
