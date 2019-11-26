import pygame as pg
import traceback

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
FPS = 60

vec = pg.math.Vector2


class Game:
    def __init__(self):
        pg.init()
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((800, 600))
        self.screen_rect = self.screen.get_rect()          
        self.fps = FPS       
        self.all_sprites = pg.sprite.Group()
        
        self.player = Player(self, (100, 100))

    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

    
    def update(self, dt):
        self.all_sprites.update(dt)

    
    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen) 

        # draw some vectors
        # player velocity
        v1 = self.player.pos + self.player.vel * 0.4
        pg.draw.line(self.screen, RED, self.player.pos, v1, 2)
        
        # player direction
        v2 = vec()
        v2.from_polar((40, self.player.rotation))
        v2 = self.player.pos + v2       
        pg.draw.line(self.screen, BLUE, self.player.pos, v2, 4)
         
        pg.display.update()
        
        
    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0
            pg.display.set_caption(str(round(self.clock.get_fps(), 2)))
            self.events()        
            self.update(dt)
            self.draw()
        
        pg.quit()
        


class Player(pg.sprite.Sprite):
    def __init__(self, game, position):
        super().__init__(game.all_sprites)
        self.game = game
        self.vel = vec()
        self.acc = vec()
        self.speed = 500
        self.friction = 2
        self.pos = position
        self.image = pg.Surface((40, 40))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        
        self.rotation = 0
        self.rotation_speed = 100
        
    
    def update(self, dt):
        keys = pg.key.get_pressed()
        self.acc *= 0
        rot = keys[pg.K_RIGHT] - keys[pg.K_LEFT]
        angle = rot * dt * self.rotation_speed
        self.rotation += angle
        
        move = keys[pg.K_UP] - keys[pg.K_DOWN]
        self.acc.x = move * self.speed
        self.acc = self.acc.rotate(self.rotation) 
        temp_accel = self.acc - self.friction * self.vel
        self.vel += temp_accel * dt
        vel_change = self.vel * dt
        self.pos += vel_change
        self.rect.center = self.pos

  
        
if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()