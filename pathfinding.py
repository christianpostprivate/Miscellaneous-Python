import pygame as pg
import traceback
from queue import Queue
from random import choice

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREY = (100, 100, 100)
DARKRED = (100, 50, 50)

vec = pg.math.Vector2

RIGHT = vec(1, 0)

# ------------- helper function ----------------------------------------------
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



class Game:
    def __init__(self):
        pg.init()
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((1024, 768)) 
        self.screen_rect = self.screen.get_rect()         
        self.fps = 60       
        self.all_sprites = pg.sprite.Group()
        self.nodes = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.walls = pg.sprite.Group()       
        # create Nodes to indicate the spawn point and the target of the Mobs
        self.start = Node(self, (40, self.screen_rect.h // 2))
        self.finish = Node(self, (self.screen_rect.w - 40 , 
                                  self.screen_rect.h // 2))
        for node in self.nodes:
            node.find_neighbors()
        # variable for placing walls
        self.rect_start = vec(0, 0)
        # text surface for instructions
        self.font = pg.font.SysFont('Arial', 18)
        text = ('MOUSE_1: Place node | MOUSE_2: Hold and drag to place wall | '
                'MOUSE_3: Delete nodes and walls | M: Spawn Mob | '
                'R: Restart')
        self.instructions = self.font.render(text, False, WHITE)
        
        self.timer = 0

    
    def events(self):
        self.mouse_pos = vec(pg.mouse.get_pos())
        self.mouse_pressed = [0, 0, 0, 0, 0]
        self.mouse_released = [0, 0, 0, 0, 0]
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.mouse_pressed[event.button - 1] = 1
            elif event.type == pg.MOUSEBUTTONUP:
                self.mouse_released[event.button - 1] = 1
                
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    # clear all sprites
                    self.all_sprites.empty()
                    self.nodes.empty()
                    self.mobs.empty()
                    self.walls.empty()
                    self.start = Node(self, (40, self.screen_rect.h // 2))
                    self.finish = Node(self, (self.screen_rect.w - 40 , 
                                              self.screen_rect.h // 2))
                    for node in self.nodes:
                        node.find_neighbors()
                
                elif event.key == pg.K_m:
                    # spawns a Mob when pressing the M key
                    Mob(self, self.start.position)
                
                elif event.key == pg.K_f:
                    self.find_paths(self.start, self.finish)

    
    def update(self):   
        pg.display.set_caption(str(round(self.clock.get_fps(), 2)))
        self.all_sprites.update()
        
        if self.mouse_pressed[0]:
            Node(self, self.mouse_pos)
            # call find_neighbors only when something has changed
            # to save on performance
            for node in self.nodes:
                node.find_neighbors()
                
        if self.mouse_pressed[1]:
            # begin a rectangle for placing a wall
            self.rect_start = self.mouse_pos
            
        if self.mouse_released[1]:
            # calculate the topleft, width and height of the Wall 
            # and place it
            w = self.mouse_pos.x - self.rect_start.x
            h = self.mouse_pos.y - self.rect_start.y
            if w > 0 and h > 0:
                x, y = self.rect_start
            elif w > 0 and h < 0:
                x = self.mouse_pos.x - w
                y = self.mouse_pos.y
            elif w < 0 and h > 0:
                x = self.mouse_pos.x
                y = self.mouse_pos.y - h
            else:
                x, y = self.mouse_pos
            if abs(w) > 2 and abs(h) > 2:
                Wall(self, (x, y), (abs(w), abs(h)))                
            self.rect_start = None
            
            for node in self.nodes:
                node.find_neighbors()
              
        if self.mouse_pressed[2]:
            # remove objects with mouse right
            for node in self.nodes:
                if node.rect.collidepoint(self.mouse_pos):
                    node.kill()
            for node in self.nodes:
                node.find_neighbors()
        
        '''           
        self.timer += 1
        if self.timer >= 60:
            self.timer = 0
            Mob(self, self.start.position)'''
        
        
    
    def draw(self):
        self.screen.fill(BLACK)
        # draw lines between connected nodes
        self.draw_connections()
        self.all_sprites.draw(self.screen)
        # draw a rect if the player is holding the middle mouse button
        if self.rect_start:
            w = self.mouse_pos.x - self.rect_start.x
            h = self.mouse_pos.y - self.rect_start.y       
            pg.draw.rect(self.screen, WHITE, pg.Rect(self.rect_start, (w, h)), 2)
        # highlight neibors in red
        for node in self.nodes:
            node.draw_neighbors()
        # draw the path of each mob
        for mob in self.mobs:
            mob.draw_path(self.screen)
        # draw instructions text on the top
        rect = self.instructions.get_rect()
        rect.centerx = self.screen_rect.centerx
        rect.y = 4
        self.screen.blit(self.instructions, rect)

        pg.display.update()
    
    
    def draw_connections(self):
        for node in self.nodes:
            for n in node.neighbors:
                start = node.position
                end = n.position
                pg.draw.line(self.screen, GREY, start, end, 2)
    

    def breadth_first_search(self, start, goal):
        # https://www.redblobgames.com/pathfinding/a-star/introduction.html
        frontier = Queue()
        frontier.put(start)
        came_from = {}
        came_from[start] = None
        # visit all nodes
        while not frontier.empty():
            current = frontier.get()
            for next in current.find_neighbors():
                if next not in came_from:
                    frontier.put(next)
                    came_from[next] = current
        # get path with the fewest nodes
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        path.append(start)
        path.reverse()
        return path
    
    
    def find_paths(self, start, goal):
        q = Queue()
        path = []
        paths = []
        path.append(start)
        q.put(path)
        while not q.empty():
            path = q.get()
            last = path[-1]
            if last == goal:
                paths.append(path)
            
            for node in last.neighbors:
                if node not in path:
                    newpath = list(path)
                    newpath.append(node)
                    q.put(newpath)
        return sorted(paths, key=len)
        
              
    def run(self):
        self.running = True
        while self.running:
            self.clock.tick(self.fps)
            self.events()        
            self.update()
            self.draw()
        
        pg.quit()



class Mob(pg.sprite.Sprite):
    def __init__(self, game, position):
        super().__init__(game.all_sprites, game.mobs)
        self.game = game
        self.image = pg.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        
        self.acc = vec()
        self.vel = vec()
        self.pos = vec(position)
        self.rect.center = self.pos
        '''
        try:
            self.path = self.game.breadth_first_search(self.game.start, 
                                                       self.game.finish)
        except:
            # if no path can be found, kill the mob
            self.kill()
            return
        '''
        try:
            paths = self.game.find_paths(self.game.start, 
                                         self.game.finish)
            self.path = choice(paths[:2])
        except:
            self.kill()
            return

        self.current_target = 0
        self.target = self.path[self.current_target]
        self.speed = 6
        self.friction = 0.9
        
        
        
    
    def update(self):
        # apply motion
        self.acc += self.arrive(self.target.position)
        self.vel += self.acc * self.speed
        self.acc *= 0
        self.vel *= self.friction
        self.pos += self.vel
        self.rect.center = self.pos
        
        # if target is reached, set next target in path
        d = self.target.position - self.pos # distance vector to target
        if d.length() < self.speed:
            self.current_target += 1
            try:
                self.target = self.path[self.current_target]
            except:
                # when there is not target left, remove the Mob
                self.kill()
       
    
    def arrive(self, target):
        # make the mob move to a target position
        desired = target - self.pos
        d = desired.length()
        if d > 0:
            desired = desired.normalize()
        desired *= self.speed
        # calculate steering force
        steering = desired - self.vel
        limit(steering, 1)
        
        return steering
    
    
    def draw_path(self, screen):
        if len(self.path) > 1:
            lines = [node.position for node in self.path]
            pg.draw.lines(screen, RED, False, lines)



class Node(pg.sprite.Sprite):
    def __init__(self, game, position):
        super().__init__(game.all_sprites, game.nodes)
        self.game = game
        self.image = pg.Surface((20, 20))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.position = vec(position)
        self.neighbors = []
    
    
    def __repr__(self):
        return str(self.position)
        
    
    def find_neighbors(self):
        # cast a ray to each other node and if it doesn't intersect a wall
        # add that node to neighbors
        self.neighbors.clear()
        for node in self.game.nodes:
            if node != self:
                dist = Line(self.position, node.position)
                intersects = False
                for wall in self.game.walls:
                    if dist.intersects_rect(wall.rect):
                        intersects = True
                for other in self.game.nodes:
                    if (other != self and other != node and
                        dist.intersects_rect(other.rect)):
                        intersects = True
                if not intersects:
                    self.neighbors.append(node)
        return self.neighbors
    
    
    def draw_neighbors(self):
        for node in self.neighbors:
            if self.rect.collidepoint(self.game.mouse_pos):
                pg.draw.rect(self.game.screen, RED, node.rect)
                
               
    
class Wall(pg.sprite.Sprite):
    def __init__(self, game, position, size):
        super().__init__(game.all_sprites, game.walls)
        self.game = game
        self.image = pg.Surface(size)
        self.image.fill(DARKRED)
        self.rect = self.image.get_rect()
        self.rect.topleft = position
        self.position = vec(position)
        
        # delete any nodes that collide with this wall
        for node in self.game.nodes:
            if self.rect.colliderect(node.rect):
                node.kill()
    
    
    def update(self):
        # check if the player clicks right while hovering over this wall
        if (self.game.mouse_pressed[2] and
            self.rect.collidepoint(self.game.mouse_pos)):
            self.kill() 


class Line:
    # class that represents a line from one point to another
    def __init__(self, start, end):
        self.start = vec(start)
        self.end = vec(end)
    
    def draw(self, screen, color=WHITE, width=1):
        pg.draw.line(screen, color, self.start, self.end, width)
        
    
    def intersects_line(self, other):
        # checks if two Line objects intersect
        #http://www.jeffreythompson.org/collision-detection/line-rect.php
        # calculate denominators for uA and uB
        denA = ((other.end.y - other.start.y) * (self.end.x - self.start.x) - 
                (other.end.x - other.start.x) * (self.end.y - self.start.y))
        denB = ((other.end.y - other.start.y) * (self.end.x - self.start.x) - 
                (other.end.x - other.start.x) * (self.end.y - self.start.y))
        if denA == 0 or denB == 0:
            # if any denominator is 0, the lines are parallel and don't intersect
            return False
        else:
            # calculate numerators for uA and uB
            numA = ((other.end.x - other.start.x) * (self.start.y - other.start.y) - 
                    (other.end.y - other.start.y) * (self.start.x - other.start.x))
            numB = ((self.end.x - self.start.x) * (self.start.y - other.start.y) - 
                    (self.end.y - self.start.y) * (self.start.x - other.start.x))
            uA = numA / denA
            uB = numB / denB
            return (uA >= 0 and uA <= 1 and uB >= 0 and uB <= 1)

    
    def get_lines_from_rect(self, rect):
        # returns a list with all 4 sides of a given rect as Line objects
        l1 = Line(rect.topleft, rect.topright)
        l2 = Line(rect.topright, rect.bottomright)
        l3 = Line(rect.bottomright, rect.bottomleft)
        l4 = Line(rect.bottomleft, rect.topleft)
        return [l1, l2, l3, l4]

    
    def intersects_rect(self, rect):
        # checks if this line intersects any lines from a given rect
        lines = self.get_lines_from_rect(rect)
        for line in lines:
            if self.intersects_line(line):
                return True
        return False
    
    
       
if __name__ == '__main__':
    try:
        g = Game()
        g.run()
    except:
        traceback.print_exc()
        pg.quit()