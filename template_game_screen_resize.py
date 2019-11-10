'''
Zoria tileset by DragonDePlatino
https://opengameart.org/content/zoria-tileset
https://creativecommons.org/licenses/by/4.0/#

'''

import pygame as pg
import pygame.freetype
import traceback

vec = pg.math.Vector2

# initial resolutions
WINDOW_W = 1024
WINDOW_H = 768

GAME_SCREEN_W = 256
GAME_SCREEN_H = 240



class Game:
    def __init__(self):
        pg.init()
        
        self.flags = (
                pg.RESIZABLE |
                pg.DOUBLEBUF
                )
        # whether the game screen gets resized to the same aspect ratio as the window 
        self.window_stretched = False
        
        # application window surface
        self.app_screen = pg.display.set_mode((WINDOW_W, WINDOW_H),
                                              self.flags)
        self.app_screen_rect = self.app_screen.get_rect()
        
        # game screen surface (where all the ingame stuff gets blitted on)
        self.game_screen = pg.Surface((GAME_SCREEN_W, GAME_SCREEN_H))
        self.game_screen_rect = self.game_screen.get_rect()
        
        self.clock = pg.time.Clock()
        #self.fps = 30
        
        self.all_sprites = pg.sprite.Group()
        
        try:
            self.bg_image = pg.image.load('assets/zoria_mockup.png').convert()
        except pygame.error:
            # create dummy image
            self.bg_image = pg.Surface(self.game_screen_rect.size)
            self.bg_image.fill(pg.Color('black'))
            
            pg.draw.rect(self.bg_image, pg.Color('green'), 
                         pg.Rect(0, 64, self.game_screen_rect.w,
                                 self.game_screen_rect.h - 64))
            
            for y in range(0, self.game_screen_rect.h - 64, 16):
                for x in range(0, self.game_screen_rect.w, 32):
                    r = pg.Rect(x + y % 32, 64 + y, 16, 16)
                    pg.draw.rect(self.bg_image, pg.Color('red'), r)
        
        font = pygame.freetype.Font(None, 12)
        for i, s in enumerate(['S: Toggle window stretching', 
                               'F: Toggle full screen',
                               'R: Make screen resizable']):
            txt, rect = font.render(s, fgcolor=pg.Color('White'), bgcolor=None)

            #rect.center = self.game_screen_rect.center
            rect.x = 2
            rect.y = 8 + i * 16

            self.bg_image.blit(txt, rect)
            
    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
                elif event.key == pg.K_s:
                    self.window_stretched = not self.window_stretched
                    self.reset_app_screen(self.app_screen_rect.size)
                elif event.key == pg.K_f:
                    # toggle fullscreen
                    self.flags = self.flags^pg.FULLSCREEN
                    self.reset_app_screen(self.app_screen_rect.size)
                elif event.key == pg.K_r:
                    # toggle fullscreen
                    self.flags = self.flags^pg.RESIZABLE
                    self.reset_app_screen(self.app_screen_rect.size)
            elif event.type == pg.VIDEORESIZE:
                # if the user resizes the window (drag the bottom right corner)
                # get the new size from the event dict and reset the 
                # window screen surface
                self.reset_app_screen(event.dict['size'])
    
    def reset_app_screen(self, size):
        self.app_screen = pg.display.set_mode(size, self.flags)
        self.app_screen_rect = self.app_screen.get_rect()
        pg.display.update()
    
    
    def update(self, dt):
        pass

    
    def draw(self):
        self.game_screen.blit(self.bg_image, (0, 0))

        if self.window_stretched:
            # scale the game screen to the window size
            resized_screen = pg.transform.scale(self.game_screen, self.app_screen_rect.size)
        else:
            # compare aspect ratios
            game_ratio = self.game_screen_rect.w / self.game_screen_rect.h
            app_ratio = self.app_screen_rect.w / self.app_screen_rect.h

            if game_ratio < app_ratio:
                width = int(self.app_screen_rect.h / self.game_screen_rect.h 
                        * self.game_screen_rect.w)
                height = self.app_screen_rect.h
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




if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()