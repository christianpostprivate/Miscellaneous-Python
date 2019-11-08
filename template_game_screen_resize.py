import pygame as pg
import traceback

vec = pg.math.Vector2

# initial resolutions
WINDOW_W = 1024
WINDOW_H = 768

GAME_SCREEN_W = 256
GAME_SCREEN_H = 240

# whether the game screen gets resized to the same aspect ratio as the window 
WINDOW_STRETCHED = False 

# additional screen flags
FLAGS = [
        #pg.FULLSCREEN,
        pg.RESIZABLE
        ]


class Game:
    def __init__(self):
        pg.init()
        
        # application window surface
        self.app_screen = pg.display.set_mode((WINDOW_W, WINDOW_H),
                                              *FLAGS)
        self.app_screen_rect = self.app_screen.get_rect()
        
        # game screen surface (where all the ingame stuff gets blitted on)
        self.game_screen = pg.Surface((GAME_SCREEN_W, GAME_SCREEN_H))
        self.game_screen_rect = self.game_screen.get_rect()
        
        self.clock = pg.time.Clock()
        
        self.all_sprites = pg.sprite.Group()
        
        # instantiate a player object for testing
        Player(self, (32, 32))

    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
            elif event.type == pg.VIDEORESIZE:
                # if the user resizes the window (drag the bottom right corner)
                # get the new size from the event dict and reset the 
                # window screen surface
                self.app_screen = pg.display.set_mode(event.dict['size'],
                                                      *FLAGS)
                self.app_screen_rect = self.app_screen.get_rect()
                pg.display.update()
    
    
    def update(self, dt):
        self.all_sprites.update(dt)

    
    def draw(self):
        self.game_screen.fill(pg.Color('green'))
        self.all_sprites.draw(self.game_screen)

        if WINDOW_STRETCHED:
            # scale the game screen to the window size
            resized_screen = pg.transform.scale(self.game_screen, self.app_screen_rect.size)
        else:
            # compare aspect ratios
            game_ratio = self.game_screen_rect.w / self.game_screen_rect.h
            app_ratio = self.app_screen_rect.w / self.app_screen_rect.h

            if game_ratio < app_ratio:
                if self.game_screen_rect.h >= self.app_screen_rect.h:
                    width = int(self.app_screen_rect.h / self.game_screen_rect.h 
                            * self.game_screen_rect.w)
                    height = self.app_screen_rect.h
                else:
                    width = int(self.app_screen_rect.h / self.game_screen_rect.h 
                            * self.game_screen_rect.w)
                    height = self.app_screen_rect.h
            else:
                if self.game_screen_rect.h < self.app_screen_rect.h:
                    width = self.app_screen_rect.w
                    height = int(self.app_screen_rect.w / self.game_screen_rect.w
                             * self.game_screen_rect.h)
                else:
                    width = self.app_screen_rect.w
                    height = int(self.app_screen_rect.w / self.game_screen_rect.w
                             * self.game_screen_rect.h)
            resized_screen = pg.transform.scale(self.game_screen, 
                                                (width, height))
        
        # get the rect of the resized screen for blitting
        # and center it to the window screen
        res_screen_rect = resized_screen.get_rect()
        res_screen_rect.center = self.app_screen_rect.center

        self.app_screen.blit(resized_screen, res_screen_rect)
        
        fps = self.clock.get_fps()
        pg.display.set_caption(f'{round(fps,2)}')

        pg.display.update(res_screen_rect)
        
        
    def run(self):
        self.running = True
        while self.running:
            delta_time = self.clock.tick() / 1000
            self.events()        
            self.update(delta_time)
            self.draw()
        
        pg.quit()
    


class Player(pg.sprite.Sprite):
    def __init__(self, game, pos):
        super().__init__(game.all_sprites)
        self.image = pg.Surface((16, 16))
        self.image.fill(pg.Color('blue'))
        self.rect = self.image.get_rect()
        self.pos = vec(pos)
        self.rect.center = pos
        self.speed = 50
    
    
    def update(self, dt):
        # make the player controllable with the arrow keys
        keys = pg.key.get_pressed()
        move = vec()
        move.x = (keys[pg.K_RIGHT] - keys[pg.K_LEFT]) * self.speed * dt
        move.y = (keys[pg.K_DOWN] - keys[pg.K_UP]) * self.speed * dt
        self.pos += move
        self.rect.center = self.pos



if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()
