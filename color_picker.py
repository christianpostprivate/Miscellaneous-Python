import pygame as pg
import pygame.freetype
import traceback


vec = pg.math.Vector2

def constrain(n, low, high):
    return max(min(n, high), low)


def rgb_to_hex(color):
    return '#{:02x}{:02x}{:02x}'.format(*color).upper()


class ColorPicker(pg.sprite.Sprite):
    def __init__(self, game, groups):
        super().__init__(groups)
        self.game = game
        self.rect = game.screen_rect.copy()
        self.image = pg.Surface(self.rect.size)
        
        # initialize sliders
        slider_positions = (
            (self.rect.centerx, 200),
            (self.rect.centerx, 300),
            (self.rect.centerx, 400)
            )
        self.sliders = [
            Slider(game, groups, slider_positions[0], 'Red'),
            Slider(game, groups, slider_positions[1], 'Green'),
            Slider(game, groups, slider_positions[2], 'Blue')
        ]
        
        self.color_value = [0, 0, 0]
        self.color_test = pg.Surface((100, 100))
        
        # Text fields for color values
        self.text_fields = [
            TextField(game, groups, position=(80, 500), 
                      default_text = '255', anchor='topleft'),
            TextField(game, groups, position=(140, 500), 
                      default_text = '255', anchor='topleft'),
            TextField(game, groups, position=(200, 500), 
                      default_text = '255', anchor='topleft'),
        ]
        
    
    def update(self, dt):
        self.image.fill(pg.Color('Black'))
        
        for i, slider in enumerate(self.sliders):
            self.color_value[i] = int(slider.value * 255)
            if slider.held:
                self.text_fields[i].highlighted = False
        
        for i, field in enumerate(self.text_fields):
            # if highlighted, get inputs from the user
            if field.highlighted:
                # deactivate all other text fields:
                others = [o for o in self.text_fields if o != field]
                for other in others:
                    other.highlighted = False
                
                for event in self.game.event_queue:
                    if event.type == pg.KEYDOWN:
                        char = chr(event.key)
                        if char in '1234567890':
                            field.text += chr(event.key)
                        elif event.key == pg.K_BACKSPACE:
                            field.text = field.text[:-1]
                if field.text:
                    self.color_value[i] = constrain(int(field.text), 0, 255)
                    field.text = f'{self.color_value[i]}'
                    #self.sliders[i].set_value(self.color_value[i])
                    self.sliders[i].value = self.color_value[i]
            else:
                field.text = f'{self.color_value[i]}'
        
        self.color_test.fill(self.color_value)
        self.image.blit(self.color_test, (80, 250))
        pg.draw.rect(self.image, pg.Color('white'), (80, 250, 100, 100), 1)
        
        font = self.game.fonts['arial']
        txt, rect = font.render('Pick a Color',
                                fgcolor=pg.Color('white'),
                                size=64)
        rect.centerx = self.rect.centerx
        rect.y = 20
        self.image.blit(txt, rect)
        
        txt, rect = font.render('Preview:',
                                fgcolor=pg.Color('white'),
                                size=32)
        rect.topleft = (80, 200)
        self.image.blit(txt, rect)

        rgb_text = f'RGB value: {tuple(self.color_value)}'
        txt, rect = font.render(rgb_text,
                                fgcolor=pg.Color('white'),
                                size=28)
        rect.topleft = (80, 360)
        self.image.blit(txt, rect)
        
        rgb_text = f'Hex value: {rgb_to_hex(self.color_value)}'
        txt, rect = font.render(rgb_text,
                                fgcolor=pg.Color('white'),
                                size=28)
        rect.topleft = (80, 400)
        self.image.blit(txt, rect)



class Slider(pg.sprite.Sprite):
    # TODO: to avoid floating point values, store the pct value
    # and blit the slider according to that
    def __init__(self, game, groups, pos, text):
        super().__init__(groups)
        self.game = game
        self.pos = vec(pos)
        self.text = text
        self.image = pg.Surface((200, 80), flags=pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.slider_rect = pg.Rect((0, 40), (20, 20))
        self.held = False
        
        font = self.game.fonts['arial']
        self.text_surf, _ = font.render(text,
                                   fgcolor=pg.Color(text),
                                   size=32)
        
        self.mouse_distance = 40
        self.line_thickness = 10
        
    
    def update(self, dt):
        # calculate if mouse is on slider
        m_pos = vec(pg.mouse.get_pos())
        s_pos = self.pos + self.slider_rect.center
        # check if left mouse is pressed and within range to the slider
        if pg.mouse.get_pressed()[0]:
            if s_pos.distance_to(m_pos) < self.mouse_distance:
                self.held = True
        else:
            self.held = False
            
        if self.held:
            # change the sliders x value based on mouse x position
            self.slider_rect.centerx = m_pos.x - self.pos.x
        self.slider_rect.centerx = constrain(self.slider_rect.centerx, 
                        self.slider_rect.w / 2, 
                        self.rect.w - self.slider_rect.w / 2)
        
        # construct the slider's image
        # fill with transparent color
        self.image.fill((0, 0, 0, 0))
        # draw a colored line up to the slider
        pg.draw.line(self.image, 
                     pg.Color(self.text), 
                     (0, self.slider_rect.centery), 
                     self.slider_rect.center, 
                     self.line_thickness)
        # draw a white line from the slider to the end
        pg.draw.line(self.image, 
                     pg.Color('lightgrey'), 
                     self.slider_rect.center, 
                     (self.rect.w, self.slider_rect.centery), 
                     self.line_thickness)
        # draw the slider element
        #self.draw_button(self.image, self.slider_rect)
        self.draw_box(self.image, self.slider_rect)
        # draw the slider's title
        self.image.blit(self.text_surf, (0, 6))
        
    
    def draw_button(self, surface, rect):
        # draws a pretty button
        rect_off = rect.copy()
        rect_off.y -= 3
        pg.draw.ellipse(surface, pg.Color('darkgrey'), rect)
        pg.draw.ellipse(surface, pg.Color('white'), rect_off)
    
    
    def draw_box(self, surface, rect):
        # draws a rectangular button
        rect_off = rect.copy()
        rect_off.y -= 3
        pg.draw.rect(surface, pg.Color('darkgrey'), rect)
        pg.draw.rect(surface, pg.Color('white'), rect_off)
     
    
    @property
    def value(self):
        # returns a value between 0 and 1, calculated from the slider's position
        return ((self.slider_rect.centerx - self.slider_rect.w * 0.5) / 
                (self.rect.w - self.slider_rect.w))

    
    @value.setter
    def value(self, value):
        pct_value = value / 255
        self.slider_rect.centerx = (pct_value * 
                                    (self.rect.w - self.slider_rect.w) 
                                    + self.slider_rect.w * 0.5)
    

class TextField(pg.sprite.Sprite):
    def __init__(self, game, groups, position, anchor='center', 
                 default_text='Hello World', 
                 text_size=32,
                 text_color='Black'):
        super().__init__(groups)
        self.game = game
        self.text_size = text_size
        self.text_color = text_color
        font = self.game.fonts['arial']
        self.text = default_text
        self.text_surf, self.text_rect = font.render(self.text,
                                            fgcolor=pg.Color(text_color),
                                            size=text_size)
        self.rect = self.text_rect.inflate(10, 10)
        setattr(self.rect, anchor, position)
        self.text_rect.center = (self.rect.w / 2, self.rect.h / 2)
        self.image = pg.Surface(self.rect.size)
        self.color = pg.Color('white')
        
        self.highlighted = False
        self.highlighted_before = False
        
    
    def update(self, dt):
        # check if mouse is on field
        m_pos = vec(pg.mouse.get_pos())
        if self.rect.collidepoint(m_pos):
            for event in self.game.event_queue:
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.highlighted = not self.highlighted
                    if self.highlighted:
                        self.text = ''
        
        if self.highlighted:
            self.color = pg.Color('darkgrey')
        else:
            self.color = pg.Color('white')
        
        # construct image
        self.image.fill(self.color)
        if self.text:
            font = self.game.fonts['arial']
            self.text_surf, self.text_rect = font.render(self.text,
                                            fgcolor=pg.Color(self.text_color),
                                            size=self.text_size)
            self.text_rect.center = (self.rect.w / 2, self.rect.h / 2)
            self.image.blit(self.text_surf, self.text_rect)


class Game:
    def __init__(self):
        pg.init()
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((800, 600))
        self.screen_rect = self.screen.get_rect()
        self.fps = 30
        self.all_sprites = pg.sprite.Group()
        self.event_queue = []
        
        self.fonts = {
            'arial': pygame.freetype.SysFont('arial', size=32)
            }
        
        ColorPicker(self, self.all_sprites)

    
    def events(self):
        self.event_queue = []
        for event in pg.event.get():
            self.event_queue.append(event)
            if event.type == pg.QUIT:
                self.running = False

    
    def update(self, dt):
        self.all_sprites.update(dt)

    
    def draw(self):
        self.all_sprites.draw(self.screen)
        pg.display.update()
        
        
    def run(self):
        self.running = True
        while self.running:
            delta_time = self.clock.tick(self.fps) / 1000
            self.events()
            self.update(delta_time)
            self.draw()
        
        pg.quit()
        

def main():
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()
        
    
    
if __name__ == '__main__':
    main()
