import pygame as pg
import traceback
from random import randrange, uniform

vec = pg.math.Vector2

WIDTH = 800
HEIGHT = 800

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

NO_OF_SPRITES = 1000


class Circle(pg.sprite.Sprite):
    def __init__(self, pos, radius):
        pg.sprite.Sprite.__init__(self)
        self.pos = vec(pos)
        self.image = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
        self.color = WHITE
        self.radius = radius
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.dir = vec(uniform(-1, 1), uniform(-1, 1))
        
    
    def update(self, others):
        # move
        self.pos += self.dir
        self.rect.center = self.pos
        
        # screen wrap
        if self.pos.x < 0:
            self.pos.x = WIDTH
        elif self.pos.x > WIDTH:
            self.pos.x = 0
            
        if self.pos.y < 0:
            self.pos.y = HEIGHT
        elif self.pos.y > HEIGHT:
            self.pos.y = 0
        
        # check collision
        for other in others:
            if other != self:
                dist = other.pos - self.pos
                if dist.length_squared() < (self.radius + other.radius) ** 2:
                    self.color = RED
    
    
    def draw(self, screen):
        pg.draw.circle(self.image, self.color, (self.radius, self.radius), 
                                                               self.radius)
        screen.blit(self.image, self.rect.topleft)
        self.color = WHITE
        
        

class Quadtree:
    def __init__(self, boundary, capacity):
        # boundary has to be a pg.Rect object
        if not isinstance(boundary, pg.Rect):
            print('boundary has to be a Rect object')
        self.boundary = boundary
        self.capacity = capacity
        self.sprites = []
        self.divided = False
    
    
    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2
        
        ne = pg.Rect(x, y, w, h)
        self.northeast = Quadtree(ne, self.capacity)
        nw = pg.Rect(x + w, y, w, h)
        self.northwest = Quadtree(nw, self.capacity)
        se = pg.Rect(x, y + h, w, h)
        self.southeast = Quadtree(se, self.capacity)
        sw = pg.Rect(x + w, y + h, w, h)
        self.southwest = Quadtree(sw, self.capacity)
        
        self.divided = True
        
    
    def insert(self, sprite):
        if not self.boundary.collidepoint(sprite.pos):
            return False
        
        if len(self.sprites) < self.capacity:
            self.sprites.append(sprite)
            return True
        
        if not self.divided:
            self.subdivide()
            
        return (self.northeast.insert(sprite) or self.northwest.insert(sprite)
                or self.southeast.insert(sprite) or self.southwest.insert(sprite))
        
        
    def query(self, rect, found=None):
        if found == None:
            found = []
            
        if not rect.colliderect(self.boundary):
            return found
        
        for s in self.sprites:
            if rect.collidepoint(s.pos):
                found.append(s)
                
        if self.divided:
            self.northwest.query(rect, found)
            self.northeast.query(rect, found)
            self.southwest.query(rect, found)
            self.southeast.query(rect, found)

        return found
    
    
    def draw(self, screen):
        pg.draw.rect(screen, (100, 100, 100), self.boundary, 1)
        
        if self.divided:
            self.northwest.draw(screen)
            self.northeast.draw(screen)
            self.southwest.draw(screen)
            self.southeast.draw(screen)

    
try:
    # initialize pygame
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    
    sprites = set()
    qt_on = True
    mouse_up = False
    
    avg_fps = []
    
    # define rects for the Quadtree and for each sprite
    qt_rect = pg.Rect((0, 0), (WIDTH, HEIGHT))
    query_rect = pg.Rect((0, 0), (60, 60))
    
    # instantiate the sprites
    for i in range(NO_OF_SPRITES):
        c = Circle((randrange(WIDTH), randrange(HEIGHT)), 10)
        sprites.add(c)
        
    # game loop
    running = True
    while running:
        clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            
            if event.type == pg.KEYUP:
                if event.key == pg.K_q:
                    qt_on = not qt_on
                    
        screen.fill(BLACK)
        
        # make a new empty Quadtree
        qt = Quadtree(qt_rect, 4)
        # add each sprite to the tree
        for s in sprites:
            qt.insert(s)
        
        if qt_on:
            qt.draw(screen)         
        
        for s in sprites:
            if not qt_on:
                s.update(sprites)
            else:
                query_rect.center = s.pos 
                #pg.draw.rect(screen, (0, 255, 0), query_rect, 1)
                neighbors = qt.query(query_rect)
                s.update(neighbors)
            s.draw(screen)
        
        # paint all sprites red that are in a Rect around the mouse cursor
        mouse_rect = pg.Rect(0, 0, 200, 200)
        mouse_rect.center = pg.mouse.get_pos()
        pg.draw.rect(screen, (0, 255, 0), mouse_rect, 1)      
        mouse_points = qt.query(mouse_rect)
        for sprite in mouse_points:
            sprite.color = RED
        
        # set caption and log FPS
        fps = clock.get_fps()
        avg_fps.append(fps)
        pts = len(qt.query(pg.Rect(0, 0, WIDTH, HEIGHT)))
        caption = (f'Quadtree on: {qt_on}  FPS: {round(fps, 2):.02f}  Points in Tree: {pts:04d}')

        pg.display.set_caption(caption)
    
        pg.display.update()
    
    print(f'average fps: {sum(avg_fps) / len(avg_fps)}')
    pg.quit()
except Exception:
    traceback.print_exc()
    pg.quit()