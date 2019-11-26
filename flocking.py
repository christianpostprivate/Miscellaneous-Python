'''
watch https://www.youtube.com/watch?v=mhjuuHl6qHM
'''

import pygame as pg
import traceback
from random import randint, uniform
from math import sin, cos


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
LIGHTGREY = (200, 200, 200)
RED = (255, 0, 0)

vec = pg.math.Vector2

# constants for the window and user interface size
W_WIDTH = 800
W_HEIGHT = 600
GUI_HEIGHT = 100


# ------------- helper functions ----------------------------------------------

def limit(vector, length):
    if vector.length_squared() <= length * length:
        return
    else:
        vector.scale_to_length(length)
        

def remap(n, start1, stop1, start2, stop2):
    # https://p5js.org/reference/#/p5/map
    newval = (n - start1) / (stop1 - start1) * (stop2 - start2) + start2
    if (start2 < stop2):
        return constrain(newval, start2, stop2)
    else:
        return constrain(newval, stop2, start2)
    

def constrain(n, low, high):
    return max(min(n, high), low)

# -----------------------------------------------------------------------------



class Game:
    def __init__(self):
        pg.init()
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((W_WIDTH, W_HEIGHT))
        self.screen_rect = self.screen.get_rect()
        self.screen_rect.h -= GUI_HEIGHT          
        self.fps = 60       
        self.all_sprites = pg.sprite.Group()
        self.gui_elements = pg.sprite.Group()
        self.font = pg.font.SysFont('Arial', 18)
        self.player = Player(self, (400, 300))
        
        # make a 100 boids
        for i in range(100):
            pos = (randint(0, 800), randint(0, 600))
            Boid(self, pos)
        
        # create some sliders for adjusting the flocking behavior
        self.slider1 = Slider(self, (20, W_HEIGHT - GUI_HEIGHT), 'alignment')
        self.slider2 = Slider(self, (260, W_HEIGHT - GUI_HEIGHT), 'separation')
        self.slider3 = Slider(self, (500, W_HEIGHT - GUI_HEIGHT), 'cohesion')

    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

    
    def update(self):
        self.all_sprites.update()
        self.gui_elements.update()

    
    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)

        # draw the interface with the sliders
        self.screen.fill(BLACK, ((0, self.screen_rect.h), (W_WIDTH, GUI_HEIGHT)))
        self.gui_elements.draw(self.screen)
           
        pg.display.update()
        
        
    def run(self):
        self.running = True
        while self.running:
            self.clock.tick(self.fps)
            self.events()        
            self.update()
            self.draw()
        
        pg.quit()



class Physics_object(pg.sprite.Sprite):
    '''
    parent class for all sprites that experience physics
    '''
    def __init__(self, game, position):
        super().__init__(game.all_sprites)
        self.game = game
        self.acc = vec(0, 0)
        self.vel = vec(0, 0)
        self.pos = vec(position)
        # the velocity vector gets multiplied by the speed and friction values
        self.speed = 1
        # smaller friction value = more friction (makes sense!?)
        self.friction = 0.9
        
    
    def update(self):       
        self.vel += self.acc
        self.pos += self.vel * self.speed
        # reset acceleration
        self.acc *= 0
        # apply friction
        self.vel *= self.friction   
                        
        # wrap around the edges of the screen
        if self.pos.x > self.game.screen_rect.w:
            self.pos.x = -self.rect.w
        elif self.pos.x < -self.rect.h:
            self.pos.x = self.game.screen_rect.w        
        if self.pos.y > self.game.screen_rect.h:
            self.pos.y = -self.rect.h
        elif self.pos.y < -self.rect.h:
            self.pos.y = self.game.screen_rect.h
        
        self.rect.topleft = self.pos  



class Player(Physics_object):
    def __init__(self, game, position):
        super().__init__(game, position)
        self.image = pg.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.speed = 0.5
        
    
    def update(self):
        # steer player with WASD
        keys = pg.key.get_pressed() 
        self.acc.x = keys[pg.K_d] - keys[pg.K_a]
        self.acc.y = keys[pg.K_s] - keys[pg.K_w]
        # normalize the acceleration vector
        limit(self.acc, 1)      
        super().update()
        


class Boid(Physics_object):
    def __init__(self, game, position):
        super().__init__(game, position)
        self.image = pg.Surface((20, 20))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        
        self.speed = randint(2, 3)
        self.max_force = 0.3
        self.friction = 0.75
        self.target = vec(0, 0)
        self.extent = vec(0, 0)
        self.theta = 0

    
    def update(self):
        # seek a target
        self.acc += self.wander()
        
        # flocking behavior (see youtube video for explanation)
        alignment = self.alignment()
        separation = self.separation()
        cohesion = self.cohesion()      
        # adjust the vectors according to the chosen slider values
        alignment *= self.game.slider1.get_val()
        separation *= self.game.slider2.get_val()
        cohesion *= self.game.slider3.get_val()
        # add flocking to the acceleration vector
        self.acc += alignment     
        self.acc += separation
        self.acc += cohesion 
        super().update()


    def alignment(self):
        perception_radius = 40
        steering = vec(0, 0)
        total = 0
        for other in self.game.all_sprites:
            if other != self:
                dist = other.pos.distance_to(self.pos)
                if dist < perception_radius:
                    steering += other.vel
                    total += 1
        if total > 0:
            steering *= 1 / total
            steering -= self.vel
            limit(steering, self.max_force)
        
        return steering
    
    
    def separation(self):
        perception_radius = 40
        steering = vec(0, 0)
        total = 0
        for other in self.game.all_sprites:
            if other != self:
                d = self.pos - other.pos
                dist = d.length()
                if dist < perception_radius:
                    d /= (dist * dist)
                    steering += d
                    total += 1      
        if total > 0:
            steering /= total
            steering.scale_to_length(self.speed)
            steering -= self.vel
            limit(steering, self.max_force)
            
        return steering
    
    
    def cohesion(self):
        perception_radius = 80
        steering = vec(0, 0)
        total = 0
        for other in self.game.all_sprites:
            if other != self:
                dist = other.pos.distance_to(self.pos)
                if dist < perception_radius:
                    steering += other.pos
                    total += 1      
        if total > 0:
            steering *= 1 / total
            steering -= self.pos
            steering.scale_to_length(self.speed)
            steering -= self.vel
            limit(steering, self.max_force)
            
        return steering
    
    
    def arrive(self, target):
        # make the boid move to a target position
        desired = target - self.pos
        d = desired.length()
        desired = desired.normalize()    
        radius = 100
        
        if d < radius:
            m = remap(d, 0, radius, 0, self.speed)
            desired *= m
            
        else:
            desired *= self.speed
        
        # calculate steering force
        steering = desired - self.vel
        limit(steering, self.max_force)
        
        return steering
        
    
    def wander(self):
        # calculate a target that changes slightly each frame by a random angle
        if self.vel.length_squared() != 0:
            # extent vector as a multiple of the velocity
            self.extent = self.vel.normalize() * 80
            # radius
            r = 30
            # change the angle by a small random amount each frame
            self.theta += uniform(-1, 1) / 16
            self.target = self.pos + self.extent + vec(r * cos(self.theta), 
                                                       r * sin(self.theta))
            
        return self.arrive(self.target)
    
    

class Slider(pg.sprite.Sprite):
    def __init__(self, game, pos, text):
        super().__init__(game.gui_elements)
        self.game = game
        self.pos = vec(pos)
        self.text = text
        self.image = pg.Surface((200, 80))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.slider_rect = pg.Rect((0, 40), (20, 20))
        
        font = self.game.font
        self.text = font.render(text, False, WHITE)
        
    
    def update(self):
        # calculate if mouse is on slider
        m_pos = vec(pg.mouse.get_pos())
        s_pos = self.pos + self.slider_rect.center
        if s_pos.distance_to(m_pos) < 20:
            if pg.mouse.get_pressed()[0]:
                # change the sliders x value based on mouse x
                self.slider_rect.centerx = m_pos.x - self.pos.x
        self.slider_rect.centerx = constrain(self.slider_rect.centerx, 10, 190)
        
        # construct the slider's image
        self.image.fill(BLACK)
        pg.draw.line(self.image, LIGHTGREY, (0, self.slider_rect.centery), 
                                        (200, self.slider_rect.centery), 2)
        self.draw_button(self.image, self.slider_rect)
        
        self.image.blit(self.text, (0, 6))
        
    
    def draw_button(self, surface, rect):
        # draws a pretty button
        rect_off = rect.copy()
        rect_off.y -= 3
        pg.draw.ellipse(surface, GREY, rect)
        pg.draw.ellipse(surface, WHITE, rect_off)
     
    
    def get_val(self):
        # returns a value from 0 to 1
        return (self.slider_rect.centerx - 10) / 180
        
    
    
if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()