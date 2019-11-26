import pygame as pg
import traceback
from math import sin, cos, pi

vec = pg.math.Vector2


WIDTH = 800
HEIGHT = 600

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

def vec_to_int(vector):
    return (int(vector.x), int(vector.y))

def translate(vector, offset):
    return vector + vec(offset)


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        
        self.pendulum = Pendulum(self, (400, 50))
        
    
    def events(self):
        self.m_pos = vec(pg.mouse.get_pos())
        self.mouse_pressed = []
        self.mouse_released = []
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.mouse_pressed = event.button
            elif event.type == pg.MOUSEBUTTONUP:
                self.mouse_released = event.button

    
    
    def update(self):
        self.pendulum.update()
    
    
    def draw(self):
        self.screen.fill(BLACK)
        self.pendulum.draw(self.screen)
        pg.display.update()
        
    
    def run(self):
        self.running = True
        while self.running:
            self.events()
            self.update()
            self.draw()
            
            
    
class Pendulum:
    def __init__(self, game, offset):
        self.game = game
        self.start1 = vec()
        self.end1 = vec()
        self.end2 = vec()
        self.offset = offset
        self.r1 = 200
        self.r2 = 200
        self.m1 = 10
        self.m2 = 20
        self.a1 = pi / 4
        self.a2 = pi / 4
        self.a1_v = 0
        self.a2_v = 0
        self.g = 0.01
        
    
    def dragged(self):
        dist = self.game.m_pos - self.end2
        dist -= self.offset
        pg.display.set_caption(str(dist.length()))
        if dist.length() < self.m2:
            if pg.mouse.get_pressed()[0]:
                self.end2 = vec(self.game.m_pos)
        
    
    def update(self): 
        self.dragged()
        
        num1 = -self.g * (2 * self.m1 + self.m2) * sin(self.a1)
        num2 = -self.m2 * self.g * sin(self.a1 - 2 * self.a2)
        num3 = -2 * sin(self.a1 - self.a2) * self.m2
        num4 = self.a2_v**2 * self.r2 + self.a1_v**2 * self.r1 * cos(self.a1 - self.a2)
        den = self.r1 * (2 * self.m1 + self.m2 - self.m2 * cos(2 * self.a1 - 2 * self.a2))
        a1_a = (num1 + num2 + num3 * num4) / den
        
        num1 = 2 * sin(self.a1 - self.a2)
        num2 = (self.a1_v**2 * self.r1 * (self.m1 + self.m2))
        num3 = self.g * (self.m1 + self.m2) * cos(self.a1)
        num4 = self.a2_v**2 * self.r2 * self.m2 * cos(self.a1 - self.a2)
        den = self.r1 * (2 * self.m1 + self.m2 - self.m2 * cos(2 * self.a1 - 2 * self.a2))
        a2_a = (num1 * (num2 + num3 + num4)) / den
        
        
        self.a1_v += a1_a
        self.a2_v += a2_a
        
        self.a1 += self.a1_v
        self.a2 += self.a2_v
        
        self.a1_v *= 0.999
        self.a2_v *= 0.999
        
        self.end1.x = self.r1 * sin(self.a1)
        self.end1.y = self.r1 * cos(self.a1)
        
        self.end2.x = self.end1.x + self.r2 * sin(self.a2)
        self.end2.y = self.end1.y + self.r2 * cos(self.a2)
        
    
    def draw(self, screen):
        start1 = translate(self.start1, self.offset)
        end1 = translate(self.end1, self.offset)
        end2 = translate(self.end2, self.offset)
        pg.draw.line(screen, WHITE, start1, end1)
        pg.draw.circle(screen, WHITE, vec_to_int(end1), self.m1)
        pg.draw.line(screen, WHITE, end1, end2)
        pg.draw.circle(screen, WHITE, vec_to_int(end2), self.m2)
            

try:
    g = Game()
    g.run()
    pg.quit()
except:
    traceback.print_exc()
    pg.quit()