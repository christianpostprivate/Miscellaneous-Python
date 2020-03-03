import pygame as pg
import pygame.freetype
import traceback

#import warnings
#warnings.filterwarnings("ignore", category=DeprecationWarning)


vec = pg.math.Vector2



def constrain(number, low, high):
    """Constrains a value to the given boundaries

    Args:
        number (int or float)
        low (int or float)
        high (int or float)
        
    Returns:
        int or float
    """
    return max(min(number, high), low)


def rgb_to_hex(color):
    """Converts a RGB tuple or list to a hexadecimal representation

    Args:
        color (tuple, list or pygame.Color object): RGB value

    Returns:
        str: color in hexadecimal
    """
    return '{:02x}{:02x}{:02x}'.format(*color).upper()



class ColorPicker(pg.sprite.Sprite):
    """Base sprite displayed when the user is prompted to specify a color.
    
    """
    def __init__(self, game, groups):
        """
        Args:
            game (Game): instance of a Game object
            groups (pygame.sprite.Group)
        """
        super().__init__(groups)
        self.game = game
        self.rect = game.screen_rect.copy()
        self.image = pg.Surface(self.rect.size)
        
        # initialize the RGB color sliders
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
        
        self.color_value = [0, 0, 0]  # [R, G, B]
        # create a surface that visualized the chosen color
        self.color_test = pg.Surface((100, 100))
        
        # Text fields for color values
        # RGB
        self.rgb_text_fields = [
            TextField(game, groups, position=(80, 400), 
                      default_text = '255', anchor='topleft'),
            TextField(game, groups, position=(140, 400), 
                      default_text = '255', anchor='topleft'),
            TextField(game, groups, position=(200, 400), 
                      default_text = '255', anchor='topleft')
        ]
        # Hexadecimal
        self.hex_text_field = TextField(game, groups, position=(80, 500), 
                                default_text = 'FFFFFF_', anchor='topleft')
        
    
    def update(self, dt):
        self.image.fill(pg.Color('Black'))
        
        # get the RGB color values from the sliders
        for i, slider in enumerate(self.sliders):
            self.color_value[i] = round(slider.value * 255)
            if slider.held:
                # disable all text fields
                self.rgb_text_fields[i].highlighted = False
                self.hex_text_field.highlighted = False
        
        for i, field in enumerate(self.rgb_text_fields):
            # if highlighted, get inputs from the user
            if field.highlighted:
                # deactivate all other text fields:
                # TODO: does not work properly!
                others = [o for o in self.rgb_text_fields if o != field]
                for other in others:
                    other.highlighted = False
                
                # change the field's text based on user input
                for event in self.game.event_queue:
                    if event.type == pg.KEYDOWN:
                        char = chr(event.key)
                        # only allow digits
                        if char in '1234567890':
                            field.text += char
                        elif event.key == pg.K_BACKSPACE:
                            # backspace delete the last character
                            field.text = field.text[:-1]
                        elif event.key == pg.K_RETURN:
                            # Enter key deactivates the text field
                            field.highlighted = False
                if field.text:
                    # if the user put some text, constrain it to be within
                    # 0 and 255 (allowed color values)
                    self.color_value[i] = constrain(round(float(field.text)), 0, 255)
                    field.text = f'{self.color_value[i]}'
                    self.sliders[i].value = self.color_value[i] / 255
            else:
                field.text = f'{self.color_value[i]}'
        
        self.color_test.fill(self.color_value)
        self.image.blit(self.color_test, (80, 250))
        pg.draw.rect(self.image, pg.Color('white'), (80, 250, 100, 100), 1)
        
        font = self.game.fonts['arial']
        
        # define some text labels and their attributes
        texts = {
            'Pick a Color': {
                'fgcolor': pg.Color('white'),
                'size': 64,
                'position': (self.rect.centerx, 20),
                'anchor': 'midtop'
                },
            'Preview': {
                'fgcolor': pg.Color('white'),
                'size': 32,
                'position': (80, 200),
                'anchor': 'topleft'
                },
            'RGB value:': {
                'fgcolor': pg.Color('white'),
                'size': 28,
                'position': (80, 360),
                'anchor': 'topleft'
                },
            'Hex value:': {
                'fgcolor': pg.Color('white'),
                'size': 28,
                'position': (80, 460),
                'anchor': 'topleft'
                }
            }
        
        for text, attributes in texts.items():
            txt, rect = font.render(text,
                                    fgcolor=attributes['fgcolor'],
                                    size=attributes['size'])
            setattr(rect, attributes['anchor'], attributes['position'])
            self.image.blit(txt, rect)
        
        # update hex input field
        field = self.hex_text_field
        if field.highlighted:
            for rgb_field in self.rgb_text_fields:
                rgb_field.highlighted = False
                
            for event in self.game.event_queue:
                if event.type == pg.KEYDOWN:
                    char = chr(event.key).upper()
                    if char in '1234567890ABCDEF' and len(field.text) < 6:
                        field.text += char
                    elif event.key == pg.K_BACKSPACE:
                        field.text = field.text[:-1]
                    elif event.key == pg.K_RETURN:
                        field.highlighted = False
            if len(field.text) == 6:
                self.color_value = list(pg.Color('#' + field.text))[:3]
                for i, slider in enumerate(self.sliders):
                    slider.value = self.color_value[i] / 255
        else:
            field.text = rgb_to_hex(self.color_value)



class Slider(pg.sprite.Sprite):
    """Customizable graphical slider element that can be dragged with the 
    mouse to receive a value between 0 and 1.
    
    """
    def __init__(self, game, groups, pos, text):
        """
        Args:
            game (Game): instance of a Game object.
            groups (pygame.sprite.Group)
            pos (tuple, list or pygame.Vector2): position (topleft) of the 
                                                slider's rect
            text (str): title of the slider (displayed at the topleft)

        Returns:
            None.
        """
        super().__init__(groups)
        self.game = game
        self.pos = vec(pos)
        self.text = text
        self.image = pg.Surface((256, 80), flags=pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.topleft = (int(self.pos[0]), int(self.pos[1]))
        
        self.value = 0  # float between 0 and 1
        self.slider_rect = pg.Rect((0, 0), (20, 20))
        self.slider_rect.y = self.rect.h // 2
        self.held = False  # flag to indicate if the slider is dragged by the mouse
        
        font = self.game.fonts['arial']
        self.text_surf, _ = font.render(text,
                                   fgcolor=pg.Color(text),
                                   size=32)
        
        # maximum distance from mouse to slider rect center for click detection
        self.mouse_distance = 40
        # thickness of the slider bar
        self.line_thickness = 10
    
    
    def value_to_x(self):
        # converts self.value (percentage) to the slider position
        return (self.value * (self.rect.w - self.slider_rect.w) 
                + self.slider_rect.w * 0.5)

    
    def x_to_value(self):
        # converts the slider position to a percentage value
        return ((self.slider_rect.centerx - self.slider_rect.w * 0.5) / 
                (self.rect.w - self.slider_rect.w))
        
    
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
            self.slider_rect.centerx = round(m_pos.x - self.pos.x)
        else:
            self.slider_rect.centerx = self.value_to_x()

        self.slider_rect.centerx = constrain(self.slider_rect.centerx, 
                        self.slider_rect.w / 2, 
                        self.rect.w - self.slider_rect.w / 2)
        self.value = self.x_to_value()  # TODO: no rounding error if this is commented out
        
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
        self.draw_button(self.image, self.slider_rect)
        # draw the slider's title
        self.image.blit(self.text_surf, (0, 6))

    
    def draw_button(self, surface, rect):
        # draws a rectangular button
        rect_off = rect.copy()
        rect_off.y -= 3
        pg.draw.rect(surface, pg.Color('darkgrey'), rect)
        pg.draw.rect(surface, pg.Color('white'), rect_off)



class TextField(pg.sprite.Sprite):
    def __init__(self, game, groups, position, anchor='center', 
                 default_text='Hello World', 
                 text_size=32,
                 text_color='Black'):
        """
        Args:
            default_text (str, optional): Default text that defines the
                element's size. Defaults to 'Hello World'.
            text_size (int, optional): Font height in pixels. Defaults to 32.
            text_color (str, optional): Defaults to 'Black'.

        Returns:
            None.

        """
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
        
        # flag indicating if the text field can be edited
        self.highlighted = False
        
    
    def update(self, dt):
        # check if mouse is on the field's rect
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
        
# =============================================================================
#         # TODO: for debugging
#         for s in self.all_sprites:
#             pg.draw.rect(self.screen, pg.Color('red'), s.rect, 1)
# =============================================================================
        
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
