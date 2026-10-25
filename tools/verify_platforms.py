"""Exercise Sky Forge's generated jump routes through the real pilot physics."""
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
from system_panic.world import World
from system_panic.preferences import Preferences
from system_panic.model import Vec,Controls,FIXED_DT


def reaches(world,source,target):
    pilot=world.component("pilot")
    p=world.player
    landing=world.cover[target].rect
    if source<0:
        starts=(landing.left-p.radius-12,landing.right+p.radius+12)
        top=470
    else:
        platform=world.cover[source].rect
        starts=(platform.left+p.radius+2,platform.centerx,platform.right-p.radius-2)
        top=platform.top
    for x in starts:
        if not p.radius+10<=x<=950-p.radius:continue
        for horizontal_delay in (0.,.25,.4,.55):
            for delay in (.15,.23,.31,.39,.47):
                p.pos,p.vel=Vec(x,top-p.radius-.01),Vec()
                pilot._jumps,pilot._grounded=0,True
                pilot._previous_y,pilot._previous_special=0,False
                pilot._dash_remaining=0
                for frame in range(210):
                    delta=landing.centerx-p.pos.x
                    direction=max(-1,min(1,delta/12)) if frame*FIXED_DT>=horizontal_delay else 0
                    jump=frame==0 or frame==round(delay/FIXED_DT)
                    pilot.update(world,FIXED_DT,Controls(direction,-1 if jump else 0))
                    if abs(p.pos.y+p.radius-landing.top)<.05 and landing.left+p.radius*.5<p.pos.x<landing.right-p.radius*.5 and p.vel.y==0:
                        return True
    return False


def main():
    records=[]
    failures=[]
    for seed in (0,24,101):
        world=World(Preferences(),seed,solo="sky_forge")
        for level in range(1,6):
            world.wave=level
            world.cover=world.component("obstacles").build(world)
            routes=list(world.component("obstacles").routes)
            for source,target in routes:
                okay=reaches(world,source,target)
                record={"seed":seed,"level":level,"source":source,"target":target,"reachable":okay}
                records.append(record)
                if not okay:failures.append(record)
        world.close()
    output=ROOT/"output/verification/platforms"
    output.mkdir(parents=True,exist_ok=True)
    (output/"report.json").write_text(json.dumps({"routes_tested":len(records),"failures":failures,"routes":records},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"routes_tested":len(records),"failures":failures}),flush=True)
    if failures:raise SystemExit("Some authored jump links failed real-pilot verification")


if __name__=="__main__":main()
