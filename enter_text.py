import pygame as pg
import traceback


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

vec = pg.math.Vector2


class Game:
    def __init__(self):
        pg.init()
        pg.key.set_repeat(500, 10)
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((600, 800))
        self.screen_rect = self.screen.get_rect()         
        self.fps = 60
        # a list to store the text surfaces line by line
        self.lines = [] 
        # I have to add an empty string at the start, otherwise the text 
        # surface creation crashes
        self.lines.append('')
        # index of the current line
        self.current = 0 
        self.font = pg.font.SysFont('Arial', 24)
        # timer for the blinking cursor
        self.timer = 0
        # boolean that determines if the cursor is shown or not
        self.cursor = True 
        # how much characters fit into a line before a line break
        self.character_limit = 50 
    
    def input_to_text(self):
        for event in self.stored_events:
            if event.type == pg.KEYDOWN:
                # if the player presses a key
                if event.key == pg.K_BACKSPACE:
                    # backspace erases the last char in the current line
                    if len(self.lines[self.current]) > 0:
                        # if there are characters in the current line, 
                        # erase the last char at index -1
                        self.lines[self.current] = self.lines[self.current][:-1]
                    else:
                        # if the current line is emtpy, go to the previous line 
                        # and delete the last char there
                        self.current = max(0, self.current -1)
                        self.lines = self.lines[:-1]
                elif event.key == pg.K_RETURN:
                    # 'Enter' key jumps to the next line
                    self.lines.append('')
                    self.current += 1
                else:
                    # any other key
                    # if the char limit is reached, go to the next line
                    if len(self.lines[self.current]) > self.character_limit:
                        self.lines.append('')
                        self.current += 1
                    # get the letter as a unicode string char from the event
                    letter = event.unicode
                    if pg.key.get_pressed()[pg.K_LSHIFT]:
                        # if shift is pressed simultaneously, change the string 
                        # to upper case
                        letter = letter.upper()
                    # add the char to the current line
                    self.lines[self.current] += letter
            
        pg.display.set_caption(f'Current line: {self.current}') # just for debugging

    
    def events(self):
        # store the current events in a variable to pass to the text creation function
        self.stored_events = []
        for event in pg.event.get():
            self.stored_events.append(event)
            if event.type == pg.QUIT:
                self.running = False

    
    def update(self, dt):
        if self.events:
            self.input_to_text()        
        self.timer += dt       
        if self.timer >= 0.5:
            # toggle the cursor
            self.cursor = not self.cursor
            self.timer = 0
               
    
    def draw(self):
        self.screen.fill(WHITE) 
        spacing = 0
        indent_x = 20 # left margin
        indent_y = 20 # top margin
        line_space = 30 # pixels between the y position of each line 
                        # (should be dynamic based on the font size...)
        for line in self.lines:
            # loop through each line and display it
            txt_surf = self.font.render(line, False, BLACK)
            self.screen.blit(txt_surf, (indent_x, indent_y + spacing))
            spacing += line_space        
        if self.cursor:
            # if cursor is True, show the cursor
            rect = pg.Rect((indent_x + txt_surf.get_rect().w, 
                            indent_y + (spacing - line_space)), 
                           (4, txt_surf.get_rect().h))
            pg.draw.rect(self.screen, BLACK, rect)       
        pg.display.update()
        
                
    def run(self):
        self.running = True
        while self.running:
            delta_time = self.clock.tick(self.fps) / 1000.0
            self.events()
            self.update(delta_time)
            self.draw()
        pg.quit()
        
        # save the text after closing the window
        with open('test_file.txt', 'w') as f:
            for line in self.lines:
                f.write("%s\n" % line)
        
        
        
if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()