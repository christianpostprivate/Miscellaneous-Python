import pygame as pg
import pygame.freetype
import traceback


# Constants
TEXT = ('Hello, World! This is a long text to test my new textbox feature. ' +
        'It should span a couple of lines. For that, I have to write ' +
        'some more text. Okay, I hope this is enough.')

DISPLAY_W = 800
DISPLAY_H = 600
BG_COLOR = 'darkgreen'
TEXTBOX_W = 400
TEXTBOX_H = 300
TEXTBOX_COLOR = 'darkblue'
# FONTNAME = 'comic-sans-ms'
FONTNAME = 'arial'
FONTSIZE = 32
TEXT_COLOR = 'white'


class Game:
    """Game controller object"""
    def __init__(self):
        # initialise screen and clock
        pg.init()
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((DISPLAY_W, DISPLAY_H))
        self.screen_rect = self.screen.get_rect()

        # create a sprite group for the textbox sprite
        self.all_sprites = pg.sprite.Group()
        # instantiate the textbox
        t = Textbox(self, TEXT, capitalize=False)
        t.render_text()

        self.running = True

    def update(self):
        self.all_sprites.update()

    def draw(self):
        self.screen.fill(pg.Color(BG_COLOR))
        for sprite in self.all_sprites:
            sprite.draw(self.screen)
        pg.display.flip()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

    def run(self):
        while self.running:
            self.events()
            self.clock.tick(30)
            self.update()
            self.draw()
        pg.quit()


class Textbox(pg.sprite.Sprite):
    def __init__(self, game, text, capitalize=False):
        super().__init__(game.all_sprites)
        self.game = game
        self.image = pg.Surface((TEXTBOX_W, TEXTBOX_H))
        self.image.fill(TEXTBOX_COLOR)
        self.rect = self.image.get_rect()
        # set the rect to be in the center of the display surface
        self.rect.center = game.screen_rect.center

        # create a font
        self.font = pygame.freetype.SysFont(name=FONTNAME, size=FONTSIZE)
        self.font_height = self.font.get_sized_height()
        self.text_surface = None
        self.text_rect = None
        self.text = text
        if capitalize:
            self.text = self.text.upper()

        # variables that are used during the font rendering
        self.lines = []
        self.border_x = 20
        self.border_y = 20

    def render_text(self):
        self.lines = []  # list to store the text surfaces line by line
        text = ''  # string that is incremented by each word in the orig. text

        # create a list of words from the string
        words = self.text.split(' ')
        for word in words:
            # test if the text plus the new word fits in the textbox
            test_text = text + word + ' '
            test_rect = self.font.get_rect(text=test_text)
            # check if the text is too wide, or if the last word is reached
            text_too_big = test_rect.w > self.rect.w - 2 * self.border_x
            last_word = word == words[-1]
            if text_too_big and last_word:
                # render the current text except for the last word
                text_surface, _ = self.font.render(text, TEXT_COLOR)
                self.lines.append(text_surface)
                # render the last word
                text_surface, _ = self.font.render(word, TEXT_COLOR)
                self.lines.append(text_surface)
            elif text_too_big and not last_word:
                # render the current text, than reset text to start with the
                # last word that didn't fit
                text_surface, _ = self.font.render(text, TEXT_COLOR)
                self.lines.append(text_surface)
                text = word + ' '
            elif last_word and not text_too_big:
                # if it's the last word, but the text is not too wide
                # add the last word to the text and render that
                text_surface, _ = self.font.render(text + '' + word,
                                                   TEXT_COLOR)
                self.lines.append(text_surface)
            else:
                # increment the text by the current word
                text += word + ' '

        self.image.fill(TEXTBOX_COLOR)
        for line, text_surface in enumerate(self.lines):
            self.image.blit(text_surface,
                            (self.border_x,
                             self.font_height * line + self.border_y))

    def draw(self, surface):
        surface.blit(self.image, self.rect)



if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except Exception:
        traceback.print_exc()
