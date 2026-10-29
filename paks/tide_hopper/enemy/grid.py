"""Local 48px canal lattice. Independently copyable with this role."""
from system_panic.model import Vec,WIDTH,HEIGHT

SPACING=48
def nodes():return (Vec(x,y) for y in range(24,HEIGHT,48) for x in range(24,WIDTH,48))
def clear(world,body,point):
    return all(s.health<=0 or not s.blocks_body(body) or not s.overlaps_circle(point,body.radius) for s in world.geometry)
def nearest(world,body,point):
    found=next((p for p in sorted(nodes(),key=lambda p:p.distance_squared_to(point)) if clear(world,body,p)),None)
    return found if found is not None else world.safe_position(point,body.radius,body=body)
def delta(a,b):
    d=b-a
    if d.x>WIDTH/2:d.x-=WIDTH
    elif d.x<-WIDTH/2:d.x+=WIDTH
    return d
def passage(world,body,start,end):
    d=end-start
    count=max(1,int(d.length()/6))
    return all(clear(world,body,start+d*(i/count)) for i in range(1,count+1))
