import pygame
import random

LANE_W=80
COLORS=[(220,60,60),(220,140,40),(140,60,180),(60,180,80),(180,180,40),(60,80,200)]

class Raft:
    def __init__(self, lane_x, y):
        self.rect=pygame.Rect(lane_x+5,y+15,70,50)
        self.speed=2
        self.direction=1
        self.color=(120,80,40)

    def update(self, min_x, max_x):
        old_x=self.rect.x
        self.rect.x+=self.direction*self.speed

        if self.rect.left<=min_x:
            self.rect.left=min_x
            self.direction=1
        elif self.rect.right>=max_x:
            self.rect.right=max_x
            self.direction=-1

        return self.rect.x-old_x

    def draw(self,screen):
        pygame.draw.rect(screen,self.color,self.rect,border_radius=10)
        for x in range(self.rect.x+8,self.rect.right-5,12):
            pygame.draw.line(
                screen,(80,50,25),
                (x,self.rect.y+5),(x,self.rect.bottom-5),3
            )


class Car:
    def __init__(self, lane_x, y, direction, speed):
        self.rect=pygame.Rect(lane_x+10,y,60,80)
        self.direction=direction  # 1=down, -1=up
        self.speed=speed
        self.color=random.choice(COLORS)

    def update(self):
        self.rect.y+=self.direction*self.speed

    def off_screen(self,height):
        return self.rect.top>height+100 or self.rect.bottom<-100

    def draw(self,screen,night=False):
        pygame.draw.rect(screen,self.color,self.rect,border_radius=8)
        pygame.draw.rect(screen,(180,220,240),pygame.Rect(self.rect.x+8,self.rect.y+10,44,22),border_radius=4)
        for wx in [self.rect.x+6,self.rect.right-16]:
            for wy in [self.rect.y+4,self.rect.bottom-16]:
                pygame.draw.rect(screen,(30,30,30),pygame.Rect(wx,wy,10,12),border_radius=3)

        if night:
            # Headlights extend ahead of the car in its travel direction.
            light_color=(255,245,170)
            if self.direction==-1:
                headlights_y=self.rect.top-18
            else:
                headlights_y=self.rect.bottom+2

            for hx in [self.rect.x+12,self.rect.right-22]:
                pygame.draw.rect(
                    screen,light_color,
                    pygame.Rect(hx,headlights_y,10,16),
                    border_radius=4
                )

def make_raft(lane_idx, y):
    x=lane_idx*LANE_W
    return Raft(x,y)


def make_car(lane_idx,height,speed):
    x=lane_idx*LANE_W
    direction=1 if lane_idx%2==0 else -1
    y=-90 if direction==1 else height+10
    return Car(x,y,direction,speed)
