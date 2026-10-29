"""Cardinal grid routing with geometry-filtered horizontal wrap edges."""
from collections import deque
from system_panic.model import Vec,Cover,WIDTH,HEIGHT

def delta(a,b):
    d=b-a
    if abs(d.x)>WIDTH/2:d.x-=WIDTH*(1 if d.x>0 else -1)
    return d

def move(world,body,step,radius):
    result=world.move_body(body,step,radius,bounds=None)
    body.pos.x%=WIDTH
    body.pos.y=max(radius,min(HEIGHT-radius,body.pos.y))
    return result

def grid_position(world,point,body):
    nodes=[Vec(16+x*32,16+y*32) for x in range(30) for y in range(15)]
    nodes.sort(key=lambda p:delta(point,p).length_squared())
    found=next((p for p in nodes if not any(w.health>0 and w.blocks_body(body) and w.overlaps_circle(p,body.radius+1) for w in world.geometry)),None)
    return found if found is not None else world.safe_position(point,body.radius,body=body)

class Route:
    def __init__(self,cardinal=True,graphs=None):
        self.cardinal=cardinal;self.graphs=graphs if graphs is not None else {}
        self.waypoint=self.key=None;self.nodes={}
    def clear(self,world,a,b):
        d=delta(a,b);count=max(1,int(d.length()/8)+1)
        for i in range(count+1):
            point=a+d*i/count;point.x%=WIDTH
            if any(w.health>0 and w.blocks_body(self.body) and w.overlaps_circle(point,self.body.radius+1) for w in world.geometry):return False
        return True
    def direction(self,world,target,body=None):
        self.body=body if body is not None else world.player;p=self.body.pos
        key=(id(self.body),tuple((id(w),tuple(w.rect),w.health>0) for w in world.geometry))
        if key!=self.key:
            self.key=key;self.waypoint=None
            shared=(self.body.radius,key[1]) if all(type(w) is Cover for w in world.geometry) else None
            if shared is not None and shared in self.graphs:self.nodes,self.links=self.graphs[shared]
            else:
                self.nodes={(x,y):Vec(16+x*32,16+y*32) for x in range(30) for y in range(15) if self.clear(world,Vec(16+x*32,16+y*32),Vec(16+x*32,16+y*32))}
                self.links={n:[other for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) if (other:=((n[0]+dx)%30,n[1]+dy)) in self.nodes and self.clear(world,self.nodes[n],self.nodes[other])] for n in self.nodes}
                if shared is not None:self.graphs[shared]=(self.nodes,self.links)
        if not self.nodes:return delta(p,target)
        if self.waypoint is not None and delta(p,self.waypoint).length()>4 and self.clear(world,p,self.waypoint):return self.vector(delta(p,self.waypoint))
        nearest=sorted(self.nodes,key=lambda n:delta(p,self.nodes[n]).length_squared())
        start=next((n for n in nearest[:12] if self.clear(world,p,self.nodes[n])),nearest[0])
        goal=min(self.nodes,key=lambda n:delta(target,self.nodes[n]).length_squared())
        queue=deque([start]);previous={start:None}
        while queue:
            here=queue.popleft()
            if here==goal:break
            for node in self.links[here]:
                if node not in previous:previous[node]=here;queue.append(node)
        if goal not in previous:goal=min(previous,key=lambda n:delta(target,self.nodes[n]).length_squared())
        while previous[goal] is not None and previous[goal]!=start:goal=previous[goal]
        aligned=abs(p.x-self.nodes[start].x)<4 or abs(p.y-self.nodes[start].y)<4
        self.waypoint=(self.nodes[goal] if aligned else self.nodes[start]).copy()
        return self.vector(delta(p,self.waypoint))
    def vector(self,d):
        if not self.cardinal:return d
        if d.length_squared()<.0625:return Vec()
        # Finish the small alignment leg after a chomp/knockback before
        # following a long corridor. Dominant-axis pursuit can oscillate
        # between two nearest cells forever when slightly off their centers.
        if 3.5<abs(d.x)<min(16,abs(d.y)):return Vec(1 if d.x>0 else -1,0)
        if 3.5<abs(d.y)<min(16,abs(d.x)):return Vec(0,1 if d.y>0 else -1)
        return Vec(1 if d.x>0 else -1,0) if abs(d.x)>abs(d.y) else Vec(0,1 if d.y>0 else -1)
