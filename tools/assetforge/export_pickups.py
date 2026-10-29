"""Copy the original mastered pickup chime into independently owned weapon folders."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]

def main():
    source=ROOT/'assets/audio/production/pickup.ogg'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    records=[]
    for manifest in sorted((ROOT/'paks').glob('*/pak.json')):
        folder=manifest.parent/'weapon'
        if not (folder/'powerup.py').is_file():continue
        target=folder/'pickup.ogg'
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            shutil.copyfile(source,target)
        records.append(dict(file=target.relative_to(ROOT).as_posix(),source=source.relative_to(ROOT).as_posix(),
                            operation='Unmodified mastered original local Stable Audio 3 pickup chime; role-local copy',sha256=digest))
    ledger=ROOT/'assets/pak-exports.json'
    previous=json.loads(ledger.read_text(encoding='utf-8'))
    replaced={row['file'] for row in records}
    ledger.write_text(json.dumps([row for row in previous if row['file'] not in replaced]+records,indent=2)+'\n',encoding='utf-8')
    print(f'Exported {len(records)} role-local pickup chimes.')

if __name__=='__main__':main()
