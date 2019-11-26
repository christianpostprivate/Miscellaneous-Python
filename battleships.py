import pygame as pg
import traceback
import random

# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
C_GRID = (50, 50, 150)
C_GRID_LINES = (150, 150, 250)
C_RADAR = (60, 100, 20)
C_RADAR_LINES = (20, 50, 5)
C_SHIPS = (100, 100, 100)
C_SHIPS_SHADOW = (80, 80, 80)

CELLSIZE = 40
CELLSIZE_SMALL = 20

vec = pg.math.Vector2


class State:
    '''
    Parent class for game states
    '''
    def __init__(self, game):
        self.game = game
        self.done = False
        self.next = None
    
    def startup(self):
        pass
        
    def update(self):
        pass
        


class Preparation(State):
    '''
    Players place their ships
    '''
    def __init__(self, game):
        super().__init__(game)
        self.next = 'Combat'
        
        self.highlight_rect = pg.Rect((-1, -1), (0, 0))
        self.ships = [
                Ship(self.game, self.game.ships, 2),
                Ship(self.game, self.game.ships, 3),
                Ship(self.game, self.game.ships, 3),
                Ship(self.game, self.game.ships, 4),
                Ship(self.game, self.game.ships, 5)
                ]
        
        self.highlight = pg.Surface((0, 0))
        
        self.start_button = Button(self.game, (200, 500), (160, 60), 
                                   text='DONE',
                                   callback=self.check_ships_placed)
        
    
    def check_ships_placed(self):
        if len(self.ships) == 0:
            print('Ships placed. Starting battle.')
            self.place_enemy_ships()          
            self.start_button.kill()
            self.done = True
            
    
    def place_enemy_ships(self):
        enemy_ships = [
                Ship(self.game, self.game.enemy_ships, 2),
                Ship(self.game, self.game.enemy_ships, 3),
                Ship(self.game, self.game.enemy_ships, 3),
                Ship(self.game, self.game.enemy_ships, 4),
                Ship(self.game, self.game.enemy_ships, 5)
                ]
        for ship in enemy_ships:
            placed = False
            while not placed:
                # random rotation
                ship.orientation = random.choice(['H', 'V'])
                ship.rotate()
                # choose random spot on enemy main grid
                if ship.orientation == 'H':
                    rand_x = (random.randint(0, 9 - ship.size) * CELLSIZE 
                              + self.game.enemy_main_grid.rect.x)
                    rand_y = (random.randint(0, 9) * CELLSIZE 
                              + self.game.enemy_main_grid.rect.y)
                elif ship.orientation == 'V':
                    rand_x = (random.randint(0, 9) * CELLSIZE 
                              + self.game.enemy_main_grid.rect.x)
                    rand_y = (random.randint(0, 9 - ship.size) * CELLSIZE 
                              + self.game.enemy_main_grid.rect.y)
                ship.rect.topleft = (rand_x, rand_y)
                # check if ship collides with others
                # if not, break and place next ship
                collisions = pg.sprite.spritecollide(ship, 
                                                     self.game.enemy_ships,
                                                     dokill=False)
                if len(collisions) == 1:
                    placed = True
        
    
    def update(self):
        self.game.all_sprites.update()
        
        # translate mouse position to grid position
        grid = self.game.main_grid
        m_pos = pg.mouse.get_pos()
        if grid.rect.collidepoint(m_pos) and len(self.ships) > 0:
            grid_x = (m_pos[0] - grid.rect.x) // CELLSIZE
            grid_y = (m_pos[1] - grid.rect.y) // CELLSIZE
            
            if self.ships[0].orientation == 'H':
                grid_x = min(grid_x, grid.size[0] - self.ships[0].size)
            if self.ships[0].orientation == 'V':
                grid_y = min(grid_y, grid.size[1] - self.ships[0].size)
            
            self.ships[0].rect.topleft = (grid_x * CELLSIZE, grid_y * CELLSIZE)
            self.highlight_rect = self.ships[0].rect
            self.highlight_rect.x += grid.rect.x
            self.highlight_rect.y += grid.rect.y
            self.highlight = pg.Surface((self.highlight_rect.w, 
                                         self.highlight_rect.h))
            self.highlight.fill((50, 50, 50))
        
            if self.game.mouse_pressed[2]:
                for ship in self.ships:
                    ship.rotate()
            elif self.game.mouse_pressed[0]:
                collisions = pg.sprite.spritecollide(self.ships[0], 
                                                     self.game.ships,
                                                     dokill=False)
                if len(collisions) == 1:
                    self.game.main_grid.ships.append(self.ships[0])
                    self.ships.pop(0)
            
            
        else:
            self.highlight_rect = pg.Rect((-1, -1), (0, 0))
            self.highlight = pg.Surface((0, 0))
            self.highlight.fill(WHITE)

    
    def draw(self, screen):
        screen.fill(BLACK)
        self.game.all_sprites.draw(screen)
        screen.blit(self.highlight, self.highlight_rect, 
                    special_flags=pg.BLEND_RGBA_ADD)
        draw_text(screen, 'Place your ships. {} left.'.format(len(self.ships)),
                  self.game.font, WHITE, (400, 500))
        draw_text(screen, 'Click \'done\' when you are finished.'.format(
                                                            len(self.ships)),
                  self.game.font, WHITE, (400, 540))
        pg.display.update()
        
        
        
class Combat(State):
    '''
    Players take their turns
    '''
    def __init__(self, game):
        super().__init__(game)
        self.next = 'Game_end'
        self.whose_turn = 'player'

        self.highlight = pg.Surface((CELLSIZE_SMALL, CELLSIZE_SMALL))
        self.highlight.fill((50, 50, 50))
        self.highlight_rect = self.highlight.get_rect()
        self.enemy_guesses = []
        self.enemy_correct_guesses = []
        self.enemy_state = 'seek_random'
        
    
    def update(self):
        pg.display.set_caption(str(len(self.enemy_correct_guesses)))
        
        self.game.all_sprites.update()
        
        # translate mouse position to grid position
        grid = self.game.radar
        m_pos = pg.mouse.get_pos()
        if grid.rect.collidepoint(m_pos):
            grid_x = (m_pos[0] - grid.rect.x) // CELLSIZE_SMALL
            grid_y = (m_pos[1] - grid.rect.y) // CELLSIZE_SMALL
            
            self.highlight_rect.topleft = (grid_x * CELLSIZE_SMALL, 
                                           grid_y * CELLSIZE_SMALL)
            self.highlight_rect.x += grid.rect.x
            self.highlight_rect.y += grid.rect.y
            hit = False
            for spr in self.game.all_sprites:
                if isinstance(spr, X) and spr.rect.collidepoint(m_pos):
                    hit = True
            if self.game.mouse_pressed[0] and not hit:
                # place marker on radar
                x_radar = X(self.game, 
                            (grid_x * CELLSIZE_SMALL 
                             + self.game.radar.rect.x, 
                             grid_y * CELLSIZE_SMALL + self.game.radar.rect.y),
                            (CELLSIZE_SMALL, CELLSIZE_SMALL))
                # place marker on enemy grid
                x_grid = X(self.game, 
                           (grid_x * CELLSIZE 
                            + self.game.enemy_main_grid.rect.x, 
                            grid_y * CELLSIZE 
                            + self.game.enemy_main_grid.rect.y),
                           (CELLSIZE, CELLSIZE))
                
                # if hit, turn radar image red
                x_grid.update()
                if x_grid.hit:
                    x_radar.image = x_radar.image_red

                # let enemy make a guess
                x, y = self.enemy_move()
                
                enemy_hit = X(self.game, 
                              (x * CELLSIZE + self.game.main_grid.rect.x, 
                               y * CELLSIZE + self.game.main_grid.rect.y),
                              (CELLSIZE, CELLSIZE))
                               
                # check if enemy hit a ship
                enemy_hit.update()
                if enemy_hit.hit:
                    self.enemy_correct_guesses.append((x, y))
                    self.enemy_state = 'return_ship'
                
                ship_sunk = None
                
                for ship in self.game.ships:
                    s = ship.count_hits()
                    if s != None:
                        ship_sunk = s
                
                for ship in self.game.enemy_ships:
                    ship.count_hits()

                    
                if ship_sunk != None:
                    # this means, an enemy move made a ship sink
                    # get sunken ship's coordinates
                    x = int((ship_sunk['pos'][0] - self.game.main_grid.rect.x) 
                             / CELLSIZE)
                    y = int((ship_sunk['pos'][1] - self.game.main_grid.rect.y) 
                             / CELLSIZE)
                    coords = []    
                    if ship_sunk['orientation'] == 'H':
                        for i in range(ship_sunk['size']):
                            coords.append((x + i, y))
                    elif ship_sunk['orientation'] == 'V':
                        for i in range(ship_sunk['size']):
                            coords.append((x, y + i))
                    print(coords)
                    # remove sunken ship coordinates from correct guesses
                    self.enemy_correct_guesses  = [x for x in 
                                                   self.enemy_correct_guesses
                                                   if x not in coords]
                    self.enemy_state = 'seek_random'
                
                if len(self.game.enemy_ships.sprites()) == 0:
                    # player wins
                    self.done = True
                
                if len(self.game.ships.sprites()) == 0:
                    # player loses
                    self.game.game_lost = True
                    self.done = True
                                  
        else:
            self.highlight_rect.topleft = (-100, -100)
    
    
    def enemy_move(self):
        if len(self.enemy_correct_guesses) > 0:
            self.enemy_state = 'return_ship'
        else:
            self.enemy_state = 'seek_random'
        
        safety_net = 0
        if self.enemy_state == 'seek_random':
            move_made = False
            while not move_made:
                rand_x = random.randint(0, 9)
                rand_y = random.randint(0, 9)
                if (rand_x, rand_y) not in self.enemy_guesses:
                    self.enemy_guesses.append((rand_x, rand_y))
                    move_made = True
            return rand_x, rand_y
        
        elif self.enemy_state == 'return_ship':
            move_made = False
            while not move_made:
                prev_x = self.enemy_correct_guesses[-1][0]
                prev_y = self.enemy_correct_guesses[-1][1]
                # decide whether to go horizontal or vertical
                if random.choice(['H', 'V']) == 'H':
                    target_x = prev_x + random.choice([1, -1])
                    target_y = prev_y
                else:
                    target_x = prev_x
                    target_y = prev_y + random.choice([1, -1])
                if ((target_x, target_y) not in self.enemy_guesses 
                    and 0 < target_x < 9 and 0 < target_y < 9):
                    self.enemy_guesses.append((target_x, target_y))
                    move_made = True
                
                safety_net += 1
                if safety_net > 1000:
                    move_made = True
                    print('got stuck returning to ship')
                    self.enemy_state = 'seek_random'
                    target_x, target_y = self.enemy_move()
            return target_x, target_y
            
    
    def draw(self, screen):
        screen.fill(BLACK)
        self.game.all_sprites.draw(screen)
        screen.blit(self.highlight, self.highlight_rect, 
                    special_flags=pg.BLEND_RGBA_ADD)
        txt = 'The battle is on. Mark your shots on the radar.'
        draw_text(screen, txt, self.game.font_small, WHITE, (400, 500))
        pg.display.update()
        


class Game_end(State):
    '''
    Game has ended
    '''
    def __init__(self, game):
        super().__init__(game)
        self.next = 'Preparation'
    
    
    def startup(self):
        self.restart_button = Button(self.game, (160, 500), (200, 60), 
                                   text='RESTART GAME',
                                   callback=self.restart_game)
        
    def update(self):
        self.game.all_sprites.update()
        
    
    def draw(self, screen):
        screen.fill(BLACK)
        self.game.all_sprites.draw(screen)
        if self.game.game_lost:
            string = 'THE GAME HAS ENDED. YOU LOST.'
        else:
            string = 'THE GAME HAS ENDED. YOU WON!'
        draw_text(screen, string, self.game.font, WHITE, 
                  (380, 500))
        pg.display.update()
        
    
    def restart_game(self):
        self.done = True
        self.game.start()
        



class Game:
    def __init__(self):
        pg.init()
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((800, 600))
        pg.display.set_caption('Battleship')
        self.screen_rect = self.screen.get_rect()          
        self.fps = 60              
        self.event = None
        self.font = pg.font.SysFont('Arial', 28)
        self.font_small = pg.font.SysFont('Arial', 20)     
        
    
    def start(self):
        self.all_sprites = pg.sprite.Group()
        self.ships = pg.sprite.Group()
        self.enemy_ships = pg.sprite.Group()
        
        self.main_grid = Main_grid(self, (10, 10))
        self.radar = Radar_grid(self, (10, 10))
        self.main_grid.rect.topleft = (60, 60)
        self.radar.rect.topleft = (500, 60)
        
        self.states_dict = {
                'Preparation': Preparation(self),
                'Combat': Combat(self),
                'Game_end': Game_end(self)
                }
        
        self.state = self.states_dict['Preparation']
        # enemy grids
        self.enemy_main_grid = Main_grid(self, (10, 10))
        self.enemy_radar = Main_grid(self, (10, 10))
        self.enemy_main_grid.rect.topleft = (1000, 1000)
        self.enemy_radar.rect.topleft = (1000, 2000)
                
        self.game_lost = False

    
    def events(self):
        self.event = None
        self.mouse_pressed = [0, 0, 0, 0, 0]
        for event in pg.event.get():
            self.event = event
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                self.mouse_pressed[event.button - 1] = 1
                
    
    def switch_states(self):
        if self.state.done:
            self.state = self.states_dict[self.state.next]
            self.state.startup()
        
        
    def run(self):
        self.start()
        self.running = True
        while self.running:
            self.clock.tick(self.fps)
            self.events()
            self.switch_states()
            self.state.update()
            self.state.draw(self.screen)
        
        pg.quit()



class Main_grid(pg.sprite.Sprite):
    def __init__(self, game, size):
        super().__init__(game.all_sprites)
        self.size = size
        self.image = pg.Surface((self.size[0] * CELLSIZE, 
                                 self.size[1] * CELLSIZE))
        self.image.fill(C_GRID)
        self.rect = self.image.get_rect()
        self.ships = []
        self.draw_image()
        
        
    def update(self):
        pass
        
    
    def draw_image(self):
        # construct image
        for x in range(self.size[0] + 1):            
            pg.draw.line(self.image, C_GRID_LINES, 
                         (x * CELLSIZE, 0), (x * CELLSIZE, self.rect.w))
            pg.draw.line(self.image, C_GRID_LINES, 
                         (x * CELLSIZE - 1, 0), 
                         (x * CELLSIZE - 1, self.rect.w))
        for y in range(self.size[1] + 1):            
            pg.draw.line(self.image, C_GRID_LINES, 
                     (0, y * CELLSIZE), (self.rect.h, y * CELLSIZE))           
            pg.draw.line(self.image, C_GRID_LINES, 
                     (0, y * CELLSIZE - 1), (self.rect.h, y * CELLSIZE - 1))
        
    

class Radar_grid(pg.sprite.Sprite):
    def __init__(self, game, size):
        super().__init__(game.all_sprites)
        self.size = size
        self.image = pg.Surface((self.size[0] * CELLSIZE_SMALL, 
                                 self.size[1] * CELLSIZE_SMALL))
        self.image.fill(C_RADAR)
        self.rect = self.image.get_rect()
        
        # construct image
        for x in range(self.size[0] + 1):            
            pg.draw.line(self.image, C_RADAR_LINES, 
                         (x * CELLSIZE_SMALL, 0), 
                         (x * CELLSIZE_SMALL, self.rect.w))
            pg.draw.line(self.image, C_RADAR_LINES, 
                         (x * CELLSIZE_SMALL - 1, 0), 
                         (x * CELLSIZE_SMALL - 1, self.rect.w))
        for y in range(self.size[1] + 1):            
            pg.draw.line(self.image, C_RADAR_LINES, 
                     (0, y * CELLSIZE_SMALL), 
                     (self.rect.h, y * CELLSIZE_SMALL))           
            pg.draw.line(self.image, C_RADAR_LINES, 
                     (0, y * CELLSIZE_SMALL - 1), 
                     (self.rect.h, y * CELLSIZE_SMALL - 1))
                
    
    def update(self):
        pass
    
    

class Ship(pg.sprite.Sprite):
    def __init__(self, game, group, size):
        super().__init__(game.all_sprites, group)
        self.game = game
        self.group = group
        self.size = size
        self.image_h = pg.Surface((CELLSIZE * self.size, CELLSIZE))
        self.image_h.fill(C_SHIPS_SHADOW)
        pg.draw.ellipse(self.image_h, C_SHIPS, self.image_h.get_rect())
        self.image_v = pg.Surface((CELLSIZE, CELLSIZE * self.size))
        self.image_v.fill(C_SHIPS_SHADOW)
        pg.draw.ellipse(self.image_v, C_SHIPS, self.image_v.get_rect())     
        self.image = self.image_h
        self.rect = self.image.get_rect()
        self.rect.topleft = (-1000, -1000)
        self.orientation = 'H'
        self.hits = 0
        
    
    def update(self):
        pass
        
    
    def rotate(self):
        if self.orientation == 'H':
            pos = self.rect.topleft
            self.image = self.image_v
            self.rect = self.image.get_rect()
            self.rect.topleft = pos
            self.orientation = 'V'
        elif self.orientation == 'V':
            pos = self.rect.topleft
            self.image = self.image_h
            self.rect = self.image.get_rect()
            self.rect.topleft = pos
            self.orientation = 'H'
            
    
    def count_hits(self):
        self.hits = 0
        for sprite in self.game.all_sprites:
            if isinstance(sprite, X):
                if self.rect.colliderect(sprite.rect):
                    self.hits += 1
        
        if self.hits >= self.size:
            if self.group == self.game.enemy_ships:
                Sunken_ship_radar(self.game, self.rect.topleft, 
                                  self.size, self.orientation)
            
            attributes = {'pos': self.rect.topleft,
                    'orientation': self.orientation,
                    'size': self.size}
            self.kill()
            return attributes
        
        else:
            return None
                


class Sunken_ship_radar(pg.sprite.Sprite):
    def __init__(self, game, pos, size, orientation):
        super().__init__(game.all_sprites)
        self.game = game
        if orientation == 'H':
            self.image = pg.Surface((CELLSIZE_SMALL * size, CELLSIZE_SMALL),
                                    pg.SRCALPHA)
        elif orientation == 'V':
            self.image = pg.Surface((CELLSIZE_SMALL, CELLSIZE_SMALL * size),
                                    pg.SRCALPHA)
        self.image.fill((255, 0, 0, 150))
        self.rect = self.image.get_rect()
        x = (int((pos[0] - self.game.enemy_main_grid.rect.x) / CELLSIZE) 
             * CELLSIZE_SMALL + self.game.radar.rect.x)
        y = (int((pos[1] - self.game.enemy_main_grid.rect.y) / CELLSIZE) 
             * CELLSIZE_SMALL + self.game.radar.rect.y)
        self.rect.topleft = (x, y)
                


class X(pg.sprite.Sprite):
    def __init__(self, game, pos, size):
        super().__init__(game.all_sprites)
        self.game = game
        self.size = size
        self.pos = pos
        self.image = pg.Surface(size, pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        pg.draw.line(self.image, WHITE, (0, 0), (size[1], size[0]), 4)
        pg.draw.line(self.image, WHITE, (size[0], 0), (0, size[1]), 4)
        # red cross image for indicating hits
        self.image_red = pg.Surface(size, pg.SRCALPHA)
        self.image_red.fill((0, 0, 0, 0))
        pg.draw.line(self.image_red, RED, (0, 0), (size[1], size[0]), 4)
        pg.draw.line(self.image_red, RED, (size[0], 0), (0, size[1]), 4)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        
        self.hit = False
    
    
    def update(self):
        # check for collision with any ships
        ships = self.game.ships.sprites() + self.game.enemy_ships.sprites()
        for ship in ships:
            if (self.rect.colliderect(ship.rect)):
                self.image = self.image_red
                self.hit = True
            
            
        

class Button(pg.sprite.Sprite):
    def __init__(self, game, pos, size, text, callback):
        super().__init__(game.all_sprites)
        self.game = game
        self.pos = pos
        self.image = pg.Surface(size)
        self.image.fill(WHITE)
        self.font = pg.font.SysFont('Arial', 24)
        self.text = text
        txt_surf = self.font.render(self.text, False, BLACK)
        self.image.blit(txt_surf, (2, 2))
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.callback = callback
        self.clicked = False
        
    
    def update(self):
        m_pos = pg.mouse.get_pos()
        if self.rect.collidepoint(m_pos):
            if self.game.mouse_pressed[0]:
                self.clicked = True
                print('clicked the button')
                self.callback()
                
                

def draw_text(surface, text, font, color, position):
    txt_surf = font.render(text, False, color)
    surface.blit(txt_surf, position)
            
    
        
        
if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()