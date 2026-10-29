"""Close new live paths using the connected boundaries of earlier captures."""
import heapq
import math
from system_panic.model import Vec
from .geometry import closest,inside
from .tail import area,intersection

def edges(regions):
    return [(a,b) for region in regions for a,b in zip(region.points,region.points[1:]+region.points[:1])]

def anchor(point,segments,tolerance=6):
    points=[closest(point,a,b) for a,b in segments
            if min(a.x,b.x)-tolerance<=point.x<=max(a.x,b.x)+tolerance
            and min(a.y,b.y)-tolerance<=point.y<=max(a.y,b.y)+tolerance]
    best=min(points,key=lambda p:p.distance_squared_to(point),default=None)
    return best if best is not None and best.distance_to(point)<=tolerance else None

def contact(start,end,segments):
    crossings=[p for a,b in segments if (p:=intersection(start,end,a,b)) is not None]
    nearby=anchor(end,segments)
    if nearby is not None:crossings.append(nearby)
    return min(crossings,key=lambda p:p.distance_squared_to(start),default=None)

def candidate_pairs(segments):
    """Prior edges whose bounds can intersect or share a near endpoint."""
    buckets={}
    for index,(a,b) in enumerate(segments):
        cells=[(x,y) for x in range(math.floor((min(a.x,b.x)-.01)/32),math.floor((max(a.x,b.x)+.01)/32)+1)
               for y in range(math.floor((min(a.y,b.y)-.01)/32),math.floor((max(a.y,b.y)+.01)/32)+1)]
        candidates=set()
        for cell in cells:candidates.update(buckets.get(cell,()))
        yield sorted(candidates)
        for cell in cells:buckets.setdefault(cell,[]).append(index)

def path(segments,start,end):
    """Split the old boundary network at vertices, crossings and both anchors."""
    splits=[[a,b] for a,b in segments]
    for i,((a,b),candidates) in enumerate(zip(segments,candidate_pairs(segments))):
        for p in (start,end):
            if closest(p,a,b).distance_to(p)<.01:splits[i].append(p)
        for j in candidates:
            c,d=segments[j]
            for p in (a,b,c,d):
                if closest(p,a,b).distance_to(p)<.01 and closest(p,c,d).distance_to(p)<.01:
                    splits[i].append(p);splits[j].append(p)
            cross=(b-a).cross(d-c)
            if abs(cross)>1e-8:
                t,u=(c-a).cross(d-c)/cross,(c-a).cross(b-a)/cross
                if 0<=t<=1 and 0<=u<=1:
                    p=a+(b-a)*t;splits[i].append(p);splits[j].append(p)
    nodes={};graph={}
    def key(p):return (round(p.x,4),round(p.y,4))
    for (a,b),points in zip(segments,splits):
        ordered=sorted({key(p):p for p in points}.values(),key=lambda p:p.distance_squared_to(a))
        for p in ordered:nodes[key(p)]=p;graph.setdefault(key(p),{})
        for p,q in zip(ordered,ordered[1:]):
            graph[key(p)][key(q)]=p.distance_to(q);graph[key(q)][key(p)]=p.distance_to(q)
    source,goal=key(start),key(end)
    if source not in graph or goal not in graph:return None
    queue=[(0.,source)];distance={source:0.};previous={source:None}
    while queue:
        cost,here=heapq.heappop(queue)
        if here==goal:break
        if cost>distance[here]:continue
        for node,weight in graph[here].items():
            total=cost+weight
            if total<distance.get(node,float('inf')):
                distance[node]=total;previous[node]=here;heapq.heappush(queue,(total,node))
    if goal not in previous:return None
    route=[];node=goal
    while node is not None:route.append(nodes[node].copy());node=previous[node]
    return route[::-1]

def close(points,end,regions):
    segments=edges(regions)
    if not segments or not points:return None
    first=anchor(points[0],segments)
    last=contact(points[-1],end,segments)
    if first is None or last is None:return None
    live=[first]+points[1:]+[last]
    # Walking an existing outline must not recapture its already filled area.
    if not any(anchor((a+b)*.5,segments) is None and not any(inside((a+b)*.5,r.points) for r in regions) for a,b in zip(live,live[1:])):return None
    route=path(segments,last,first)
    if route is None:return None
    polygon=live+route[1:-1]
    return polygon if len(polygon)>2 and area(polygon)>=900 else None
