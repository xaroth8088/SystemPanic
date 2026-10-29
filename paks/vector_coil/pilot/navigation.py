"""QA cardinal route planning around actual body-filtered geometry."""
from collections import deque
from system_panic.model import Vec

class Route:
    def __init__(self,cardinal=True):
        self.cardinal=cardinal
        self.waypoint=None
        self.key=None
        self.nodes={}
    def clear(self,world,a,b):
        delta=b-a
        count=max(1,int(delta.length()/8)+1)
        return all(not any(w.health>0 and w.blocks_body(self.body) and w.overlaps_circle(a+delta*i/count,self.body.radius+1) for w in world.geometry) for i in range(count+1))
    def direction(self,world,target,body=None):
        self.body=body if body is not None else world.player
        p=self.body.pos
        key=(id(self.body),tuple((id(w),tuple(w.rect),w.health>0) for w in world.geometry))
        if key!=self.key:
            self.key=key
            self.waypoint=None
            self.nodes={(x,y):Vec(x*32,y*32) for x in range(1,30) for y in range(1,15) if self.clear(world,Vec(x*32,y*32),Vec(x*32,y*32))}
            self.links={n:[other for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) if (other:=(n[0]+dx,n[1]+dy)) in self.nodes and self.clear(world,self.nodes[n],self.nodes[other])] for n in self.nodes}
        if not self.nodes:return target-p
        if self.waypoint is not None and p.distance_to(self.waypoint)>4 and self.clear(world,p,self.waypoint):
            return self.vector(self.waypoint-p)
        candidates=sorted(self.nodes,key=lambda n:self.nodes[n].distance_squared_to(p))
        start=next((n for n in candidates[:12] if self.clear(world,p,self.nodes[n])),candidates[0])
        goal=min(self.nodes,key=lambda n:self.nodes[n].distance_squared_to(target))
        queue=deque([start]);previous={start:None}
        while queue:
            here=queue.popleft()
            if here==goal:break
            for node in self.links[here]:
                if node not in previous:
                    previous[node]=here;queue.append(node)
        if goal not in previous:goal=min(previous,key=lambda n:self.nodes[n].distance_squared_to(target))
        while previous[goal] is not None and previous[goal]!=start:goal=previous[goal]
        aligned=abs(p.x-self.nodes[start].x)<4 or abs(p.y-self.nodes[start].y)<4
        waypoint=self.nodes[goal] if aligned else self.nodes[start]
        if self.clear(world,p,target) and p.distance_to(target)<90:waypoint=target
        self.waypoint=waypoint.copy()
        return self.vector(waypoint-p)

    def vector(self,delta):
        if not self.cardinal:return delta
        return Vec(1 if delta.x>0 else -1,0) if abs(delta.x)>abs(delta.y) else Vec(0,1 if delta.y>0 else -1)
