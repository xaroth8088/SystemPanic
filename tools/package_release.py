"""Package the built external-Pak Windows folder and Python wheel, verifying every Pak byte."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

root=Path(__file__).resolve().parents[1]
destination=(root/'dist/SystemPanic/paks').resolve()
assert destination.is_relative_to(root/'dist/SystemPanic')
# Pak-only releases can add assets without changing the executable. Keep its
# externally bundled provenance data current with the new role-local files.
shutil.copyfile(root/'assets/manifest.json',root/'dist/SystemPanic/_internal/assets/manifest.json')
files=[]
for manifest in sorted((root/'paks').glob('*/pak.json')):
    shutil.copytree(manifest.parent,destination/manifest.parent.name,dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    files.extend(p for p in manifest.parent.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
with (root/'output/renewal-wheel-build.log').open('w') as log:
    subprocess.run([sys.executable,'-c',"import setuptools.build_meta; print(setuptools.build_meta.build_wheel('dist'))"],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
wheel=root/'dist/system_panic-0.1.0-py3-none-any.whl'
with zipfile.ZipFile(wheel) as bundle:
    names=bundle.namelist()
    for source in files:
        relative=source.relative_to(root).as_posix()
        target=root/'dist/SystemPanic'/relative
        assert target.read_bytes()==source.read_bytes(),relative
        name=next(n for n in names if n.endswith('/share/system-panic/'+relative))
        assert bundle.read(name)==source.read_bytes(),relative
    assert bundle.testzip() is None
archive=Path(shutil.make_archive(str(root/'dist/SystemPanic-Windows'),'zip',root_dir=root/'dist',base_dir='SystemPanic'))
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    for source in files:
        assert bundle.read('SystemPanic/'+source.relative_to(root).as_posix())==source.read_bytes()
record=dict(source_pak_files=len(files),windows_matches_source=True,wheel_matches_source=True,zip_matches_source=True,zip_crc=True,
            executable_sha256=hashlib.sha256((root/'dist/SystemPanic/SystemPanic.exe').read_bytes()).hexdigest(),
            wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
(root/'output/renewal-packaging.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
