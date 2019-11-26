import pygame as pg
import traceback

# Window size
WIDTH = 240
HEIGHT = 360

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

BUTTON_SIZE = 40
MARGIN = 6
BUTTON_COLOR = (80, 80, 80)
DISPLAY_COLOR = (80, 120, 80)

NUMBERS = '1234567890'


def add(x):
    return sum(x)

def subtract(x):
    return x[0] - x[1]

def divide(x):
    return x[0] / x[1]

def multiply(x):
    return x[0] * x[1]


OPERATIONS = {
        '+': add,
        '-': subtract,
        '/': divide,
        '*': multiply
        }


class Calculator:
    def __init__(self):
        pg.init()
        pg.display.set_caption('Calculator')
        self.screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)
        self.display = pg.Surface((5 * BUTTON_SIZE + 24, 
                                   2 * BUTTON_SIZE))
        self.display_string = ''
        self.cache_string = ''
        self.clock = pg.time.Clock()
        self.init_buttons()
        self.font = pg.font.SysFont('arial', size=28, bold=True)
        self.font_small = pg.font.SysFont('arial', size=24, bold=False)
        self.numbers = []
        self.result = 0
        self.solved = False
        
        
    def init_buttons(self):
        self.buttons = []
        self.place_button(Button(self, '+'), (0, 0))
        self.place_button(Button(self, '-'), (1, 0))
        self.place_button(Button(self, '*'), (2, 0))
        self.place_button(Button(self, '/'), (3, 0))
        self.place_button(Button(self, '='), (4, 0))
        
        self.place_button(Button(self, '1'), (0, 1))
        self.place_button(Button(self, '2'), (1, 1))
        self.place_button(Button(self, '3'), (2, 1))
        
        self.place_button(Button(self, '4'), (0, 2))
        self.place_button(Button(self, '5'), (1, 2))
        self.place_button(Button(self, '6'), (2, 2))
        
        self.place_button(Button(self, '7'), (0, 3))
        self.place_button(Button(self, '8'), (1, 3))
        self.place_button(Button(self, '9'), (2, 3))
        
        self.place_button(Button(self, '0', size=(BUTTON_SIZE * 2 + MARGIN, 
                                                  BUTTON_SIZE)), (0, 4))
        self.place_button(Button(self, 'C'), (2, 4))
                
    
    def place_button(self, button, grid_pos):
        # translate a grid position to a pixel position
        pos = (8 + grid_pos[0] * (BUTTON_SIZE + MARGIN), 
               128 + grid_pos[1] * (BUTTON_SIZE + MARGIN))
        button.place(pos)
        self.buttons.append(button)
        
    
    def get_result(self):
        operations = self.cache_string.replace(' ', '')
        operations = ''.join(i for i in operations if i not in NUMBERS)
        
        

    def loop(self):
        self.running = True
        while self.running:
            self.clock.tick(60)
        
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
        
            self.screen.fill(BLACK)
            
            for b in self.buttons:
                b.update()
                b.draw(self.screen)
            
            self.display.fill(DISPLAY_COLOR)
            
            text_surf = self.font.render(self.display_string, False, WHITE)
            text_rect = text_surf.get_rect()
            display_rect = self.display.get_rect()
            text_rect.right = display_rect.right - 4
            text_rect.bottom = display_rect.bottom
            self.display.blit(text_surf, text_rect)
            
            # cache string
            text_surf = self.font_small.render(self.cache_string, False, WHITE)
            text_rect = text_surf.get_rect()
            display_rect = self.display.get_rect()
            text_rect.right = display_rect.right - 4
            text_rect.bottom = display_rect.bottom - 32
            self.display.blit(text_surf, text_rect)
            
            self.screen.blit(self.display, (8, 32))
     
            pg.display.update()        
        pg.quit()
        
        

class Button:
    def __init__(self, calc, label, size=(BUTTON_SIZE, BUTTON_SIZE)):
        self.calc = calc
        self.rect = pg.Rect((0, 0), size)
        self.image = pg.Surface(size)
        self.image.fill(BUTTON_COLOR)
        self.label = label
        # button delay in frames
        self.delay = 10
        self.timer = 0
        
        self.font = pg.font.SysFont('arial', 24)
        text_surf = self.font.render(str(self.label), False, WHITE)
        text_rect = text_surf.get_rect()
        text_rect.center = self.rect.center
        self.image.blit(text_surf, text_rect)
        
        
    def place(self, pos):
        self.rect.topleft = pos
    
        
    def update(self):
        self.timer += 1
        m_pos = pg.mouse.get_pos()
        if (pg.mouse.get_pressed()[0] and self.rect.collidepoint(m_pos) and
            self.timer > self.delay):
            self.timer = 0
            # if the last equation was solved, clear the strings
            if self.calc.solved:
                self.calc.cache_string = ''
                self.calc.display_string = ''
                self.calc.solved = False
                
            if self.label in NUMBERS:
                self.calc.display_string += str(self.label)
            else:
                num = int(''.join(i for i in self.calc.display_string
                                if i in NUMBERS))
                self.calc.numbers.append(num)
                
                if self.label == '=':
                    self.calc.cache_string += ' ' + self.calc.display_string
                    self.calc.result = eval(self.calc.cache_string)
                    self.calc.display_string = str(self.calc.result)
                    self.calc.solved = True
                
                elif self.label == 'C':
                    self.calc.display_string = ''
                    self.calc.cache_string = ''
                    self.calc.numbers = []
                
                else:
                    self.calc.cache_string += ' ' + self.calc.display_string
                    self.calc.display_string = self.label + ' '

    
    
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
    

calc = Calculator()

try:
    calc.loop()
except Exception:
    traceback.print_exc()
    pg.quit()
