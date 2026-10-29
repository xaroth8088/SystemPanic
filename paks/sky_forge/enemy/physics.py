"""Crawler-owned gravity and flat-foot landings; never borrowed pilot state."""
import pygame
from system_panic.model import Vec,Cover,WIDTH,HEIGHT

def move(world,body,dt):
    bounds=pygame.Rect(10,10,WIDTH-20,HEIGHT-10)
    horizontal=world.move_body(body,Vec(body.vel.x*dt,0),body.radius,bounds=bounds)
    displacement=Vec(0,body.vel.y*dt)
    deck=None
    for wall in world.geometry:
        if type(wall) is not Cover or wall.health<=0 or not wall.blocks_body(body):continue
        top=wall.rect.top-body.radius
        if body.vel.y>=0 and body.pos.y<=top<=body.pos.y+displacement.y and wall.rect.left-body.radius<body.pos.x<wall.rect.right+body.radius:
            displacement.y=top-body.pos.y
            deck=wall
    vertical=world.move_body(body,displacement,body.radius,bounds=bounds)
    on_deck=deck is not None and abs(body.pos.y-(deck.rect.top-body.radius))<1e-6
    if vertical.blocked_y or on_deck:body.vel.y=0
    return horizontal,vertical.landed or on_deck
