"""Cardinal grid routing with geometry-filtered horizontal wrap edges."""
from collections import deque
from functools import lru_cache
import math
from types import MappingProxyType
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

@lru_cache(maxsize=1)
def _lattice():
    """Immutable coordinates/incidence only; no run, body or collider state."""
    positions={(x,y):(16.+x*32,16.+y*32) for x in range(30) for y in range(15)}
    neighbors={n:tuple(other for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) if (other:=((n[0]+dx)%30,n[1]+dy)) in positions) for n in positions}
    probes={position:[node,set()] for node,position in positions.items()}
    for node,targets in neighbors.items():
        a=Vec(positions[node])
        for target in targets:
            d=delta(a,Vec(positions[target]));count=max(1,int(d.length()/8)+1)
            for i in range(count+1):
                point=a+d*i/count;point.x%=WIDTH
                probes.setdefault((point.x,point.y),[None,set()])[1].add((node,target))
    buckets={}
    for coordinate,(node,edges) in probes.items():
        bucket=(math.floor(coordinate[0]/32),math.floor(coordinate[1]/32))
        buckets.setdefault(bucket,[]).append((coordinate,node,tuple(edges)))
    return MappingProxyType(positions),MappingProxyType(neighbors),MappingProxyType({key:tuple(value) for key,value in buckets.items()})

def _rectangular_graph(blockers,radius):
    """Index bounded snapshots, still querying each shape's exact overlap."""
    positions,neighbors,buckets=_lattice()
    blocked_points=set();blocked_nodes=set();blocked_edges=set()
    margin=2*math.ceil(radius)
    # Snapshot-capable shapes promise conservative rect bounds. Rectangles,
    # segments and polygons all retain their actual public contact query.
    for wall in blockers:
        bounds=wall.rect.inflate(margin,margin)
        for x in range(bounds.left//32,bounds.right//32+1):
            for y in range(bounds.top//32,bounds.bottom//32+1):
                for coordinate,node,edges in buckets.get((x,y),()):
                    if coordinate not in blocked_points and bounds.collidepoint(coordinate) and wall.overlaps_circle(Vec(coordinate),radius):
                        blocked_points.add(coordinate)
                        if node is not None:blocked_nodes.add(node)
                        blocked_edges.update(edges)
    nodes={node:Vec(position) for node,position in positions.items() if node not in blocked_nodes}
    links={node:[other for other in neighbors[node] if other in nodes and (node,other) not in blocked_edges] for node in nodes}
    return nodes,links

class Route:
    MAX_GRAPHS=8
    def __init__(self,cardinal=True,graphs=None):
        self.cardinal=cardinal;self.graphs=graphs if graphs is not None else {}
        self.waypoint=self.key=None;self.nodes={}
    def clear(self,world,a,b):
        d=delta(a,b);count=max(1,int(d.length()/8)+1)
        for i in range(count+1):
            point=a+d*i/count;point.x%=WIDTH
            coordinate=(point.x,point.y)
            result=self._points.get(coordinate)
            if result is None:
                result=not any((bounds is None or bounds.collidepoint(point)) and w.overlaps_circle(point,self.body.radius+1) for w,bounds in self._blockers)
                self._points[coordinate]=result
            if not result:return False
        return True
    def direction(self,world,target,body=None):
        self.body=body if body is not None else world.player;p=self.body.pos
        blockers=[w for w in world.geometry if w.health>0 and w.blocks_body(self.body)]
        snapshots=[w.navigation_key() for w in blockers]
        bounded=all(key is not None for key in snapshots)
        margin=2*math.ceil(self.body.radius+1)
        self._blockers=[(w,w.rect.inflate(margin,margin) if key is not None else None) for w,key in zip(blockers,snapshots)]
        # Point samples are pure queries for this body and geometry snapshot.
        # Reuse endpoints/reverse edges without rounding their coordinates.
        self._points={}
        topology=tuple(key if key is not None else (id(w),tuple(w.rect)) for w,key in zip(blockers,snapshots))
        key=(id(self.body),self.body.radius,topology)
        if key!=self.key:
            self.key=key;self.waypoint=None
            # Only explicitly immutable collision snapshots share graphs.
            # Recreated equal shapes reuse them; arbitrary overrides stay local.
            shared=(self.body.radius,topology) if bounded else None
            cached=self.graphs.pop(shared,None) if shared is not None else None
            if cached is not None:
                self.nodes,self.links=cached
                self.graphs[shared]=cached
            else:
                if bounded:self.nodes,self.links=_rectangular_graph(blockers,self.body.radius+1)
                else:
                    self.nodes={(x,y):Vec(16+x*32,16+y*32) for x in range(30) for y in range(15) if self.clear(world,Vec(16+x*32,16+y*32),Vec(16+x*32,16+y*32))}
                    self.links={n:[other for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) if (other:=((n[0]+dx)%30,n[1]+dy)) in self.nodes and self.clear(world,self.nodes[n],self.nodes[other])] for n in self.nodes}
                if shared is not None:
                    self.graphs[shared]=(self.nodes,self.links)
                    while len(self.graphs)>self.MAX_GRAPHS:self.graphs.pop(next(iter(self.graphs)))
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
        if 3.5<abs(d.x)<min(16,abs(d.y)):return Vec(1 if d.x>0 else -1,0)
        if 3.5<abs(d.y)<min(16,abs(d.x)):return Vec(0,1 if d.y>0 else -1)
        return Vec(1 if d.x>0 else -1,0) if abs(d.x)>abs(d.y) else Vec(0,1 if d.y>0 else -1)
