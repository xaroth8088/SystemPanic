"""Cached procedural light and particles; no simulation or random state."""
from functools import lru_cache
import math
import pygame


@lru_cache(maxsize=36)
def black_hole_frame(phase):
    layer=pygame.Surface((512,512),pygame.SRCALPHA)
    center=pygame.Vector2(256,256)
    turn=phase*math.tau/36
    # Soft gravitational glow, dim enough to leave ships and projectiles clear.
    for radius in range(224,38,-4):
        strength=(1-radius/230)**2
        pygame.draw.circle(layer,(65,45,135,round(44*strength)),center,radius)
    # A tilted disk, with the far half passing behind the dark horizon.
    def disk(angle,radius):
        return center+pygame.Vector2(math.cos(angle)*radius,math.sin(angle)*radius*.32).rotate(-19)
    for band in range(7):
        radius=72+band*7
        points=[disk(i*math.tau/100,radius) for i in range(101)]
        pygame.draw.lines(layer,(140+band*10,62+band*7,40+band*4,155-band*12),False,points,5)
    for stream in range(3):
        points=[]
        for sample in range(82):
            t=sample/81
            angle=turn+stream*math.tau/3+t*2.9
            points.append(disk(angle,124-68*t))
        pygame.draw.lines(layer,(255,165+stream*15,85+stream*22,200),False,points,3)
    # Light bent above the disk and a sharp photon ring around the silhouette.
    for width,alpha in ((12,30),(7,65),(3,195)):
        pygame.draw.arc(layer,(245,166,104,alpha),(196,182,120,114),.1,math.pi-.1,width)
    pygame.draw.circle(layer,(2,3,10,255),center,43)
    pygame.draw.circle(layer,(255,200,137,245),center,47,3)
    pygame.draw.arc(layer,(255,242,203,255),(209,209,94,94),.3,2.9,3)
    # Near-side streams cross the lower silhouette, producing depth.
    for band in range(3):
        points=[disk(.12+i*math.pi/64,66+band*9) for i in range(61)]
        pygame.draw.lines(layer,(255,185+band*18,105+band*26,215),False,points,3)
    for index in range(15):
        angle=turn*.7+index*2.39996
        radius=140+(index*19)%61
        point=disk(angle,radius)
        pygame.draw.circle(layer,(155,151,235,90+index%3*35),point,2)
    return pygame.transform.smoothscale(layer,(256,256))


COMET_HEAD=pygame.Vector2(176,40)


@lru_cache(maxsize=24)
def comet_frame(phase):
    layer=pygame.Surface((432,160),pygame.SRCALPHA)
    head=COMET_HEAD*2
    turn=phase*math.tau/24
    # Layered tapered ion plume; all variation is a pure function of age.
    for width,color in ((21,(62,65,155,35)),(13,(75,125,235,70)),(7,(97,205,255,155)),(3,(203,248,255,235))):
        upper=[];lower=[]
        for sample in range(36):
            t=sample/35
            x=head.x-330*(1-t)
            drift=math.sin(t*7-turn)*6*(1-t)
            spread=width*math.sin(t*math.pi)*2+1
            upper.append((x,head.y+drift-spread))
            lower.append((x,head.y+drift+spread))
        pygame.draw.polygon(layer,color,upper+lower[::-1])
    for index in range(16):
        t=(index/16+phase/96)%1
        x=head.x-24-295*t
        y=head.y+math.sin(index*2.4+turn)*16*t
        pygame.draw.line(layer,(134,194,255,round(170*(1-t))), (x,y),(x-6-10*t,y),2)
    for radius in range(52,23,-3):
        pygame.draw.circle(layer,(90,176,255,round((1-radius/56)*80)),head,radius)
    offsets=((-8,-7),(-1,-12),(8,-9),(12,-1),(8,8),(0,11),(-10,5))
    points=[head+pygame.Vector2(x,y)*2 for x,y in offsets]
    pygame.draw.polygon(layer,(72,91,115,255),points)
    pygame.draw.lines(layer,(173,215,236,255),False,points[1:5],3)
    pygame.draw.polygon(layer,(134,168,188,255),[head+pygame.Vector2(-14,-6),head+pygame.Vector2(0,-21),head+pygame.Vector2(9,-3),head+pygame.Vector2(-2,10)])
    pygame.draw.line(layer,(226,244,250,255),head+pygame.Vector2(3,-17),head+pygame.Vector2(15,-9),3)
    pygame.draw.circle(layer,(41,57,80,255),head+pygame.Vector2(-7,8),5)
    pygame.draw.circle(layer,(208,246,255,255),head+pygame.Vector2(-17,-1),4)
    return pygame.transform.smoothscale(layer,(216,80))


def draw_black_hole(surface,world,position):
    phase=0 if world.prefs.reduced_motion else int(world.time*12)%36
    image=black_hole_frame(phase)
    surface.blit(image,image.get_rect(center=position))


def draw_comet(surface,world,comet):
    phase=0 if world.prefs.reduced_motion else int(comet.age*18)%24
    image=comet_frame(phase)
    angle=math.atan2(comet.vel.y,comet.vel.x)
    offset=(COMET_HEAD-pygame.Vector2(image.get_size())/2).rotate_rad(angle)
    rotated=pygame.transform.rotate(image,-math.degrees(angle))
    surface.blit(rotated,rotated.get_rect(center=comet.pos-offset))
