import pygame as pg
import traceback
from random import randint, randrange, uniform, random
import math
import noise

vec = pg.math.Vector2

WIDTH = 1000
HEIGHT = 800

# simulation mode
# modes = 'wander', 'arrive', 'follow', 'path'
# TODO: make an iterable of modes
MODE = 'follow'

FPS = 60
FLOWFIELD_COLOR = (10, 100, 50)
BG_COLOR = (10, 40, 70)


# ----------- helper functions ------------------------------------------------

def limit(vector, lim):
    if vector.length_squared() > (lim * lim):
        vector.scale_to_length(lim)


def remap(n, start1, stop1, start2, stop2):
    # https://p5js.org/reference/#/p5/map
    newval = (n - start1) / (stop1 - start1) * (stop2 - start2) + start2
    if start2 < stop2:
        return constrain(newval, start2, stop2)
    else:
        return constrain(newval, stop2, start2)


def constrain(n, low, high):
    return max(min(n, high), low)


def create_random_vec():
    angle = uniform(0, 2.0 * math.pi)
    return vec(math.cos(angle), math.sin(angle))


# ---------- game class -------------------------------------------------------

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.vehicles = pg.sprite.LayeredUpdates()

        self.flowfield = None
        self.show_field = True
        self.path = []
        self.num_boids = 40
        self.mode = MODE

    def new(self):
        # start a new game
        self.all_sprites.empty()
        self.vehicles.empty()

        for i in range(self.num_boids):
            pos = (randint(0, WIDTH), randint(0, HEIGHT))
            size = randint(10, 50)
            Vehicle(self, (size, int(size * 1.4)), pos)

        self.flowfield = FlowField(50)
        self.path = []

        self.run()

    def run(self):
        # game loop
        while self.running:
            self.clock.tick(FPS)  # TODO: delta time
            self.events()
            self.update()
            self.draw()

    def update(self):
        # game loop update
        self.all_sprites.update()

        for v in self.vehicles:
            v.separate(self.vehicles)

        # self.flowfield.changeNoise()
        self.flowfield.change()

    def events(self):
        # game loop events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    # left mouse click
                    pos = vec(pg.mouse.get_pos())
                    self.path.append(pos)
                elif event.button == 3:
                    # right mouse click resets the path
                    self.path = []
                    for v in self.vehicles:
                        v.target_index = 0
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    self.show_field = not self.show_field

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.mode == 'wander':  # TODO: use a state machine for this!
            if self.show_field:
                self.draw_vectors()
        if self.mode == 'follow':
            if self.show_field:
                self.draw_field()
        if self.mode == 'path':
            self.draw_path()

        self.all_sprites.draw(self.screen)
        pg.display.flip()

    def draw_vectors(self):
        """
        draws a representation of the velocity vectors and the targets
        of the boids
        """
        for v in self.vehicles:
            pg.draw.line(self.screen, (0, 255, 0), v.pos, v.pos + v.extent, 1)
            pg.draw.circle(self.screen, (0, 255, 0),
                           (int(v.pos.x + v.extent.x),
                            int(v.pos.y + v.extent.y)), 30, 1)
            start = v.pos + v.extent
            end = v.target
            d = end - start
            if d.length_squared() < 2000:
                pg.draw.line(self.screen, (0, 255, 0), start, end, 1)

    def draw_field(self):
        """
        Draws the flow field vectors
        """
        field = self.flowfield.field
        w = len(field)
        h = len(field[0])
        for i in range(h):
            for j in range(w):
                start = vec(WIDTH / w * j + (WIDTH / w) / 2,
                            HEIGHT / h * i + (HEIGHT / h) / 2)
                end1 = start + field[j][i] * self.flowfield.resolution / 2.5
                end2 = start - field[j][i] * self.flowfield.resolution / 2.5
                pg.draw.line(self.screen, FLOWFIELD_COLOR, end1, end2, 2)

    def draw_path(self):
        """Draws the path for the boids to follow"""
        if len(self.path) > 1:
            for i in range(1, len(self.path)):
                pg.draw.line(self.screen, (0, 150, 0),
                             self.path[i - 1], self.path[i], 1)
        elif len(self.path) == 1:
            pg.draw.circle(self.screen, (0, 150, 0),
                           (int(self.path[0].x), int(self.path[0].y)), 1)


class FlowField:
    def __init__(self, resolution):
        self.resolution = resolution
        self.cols = WIDTH // self.resolution
        self.rows = HEIGHT // self.resolution
        self.field = [[None for i in range(self.cols)]
                      for j in range(self.rows)]

        self.timer = 0
        self.dir = vec(1, 1)

        for i in range(self.rows):
            for j in range(self.cols):
                self.field[i][j] = vec()

        self.z_off = random()  # z offset for perlin noise

    def lookup(self, vector):
        column = int(constrain(vector.x / self.resolution, 0, self.cols - 1))
        row = int(constrain(vector.y / self.resolution, 0, self.rows - 1))
        return vec(self.field[row][column])

    def change(self):
        self.timer += 1
        if self.timer > randrange(10, 20):
            for i in range(self.rows):
                for j in range(self.cols):
                    change = 0.8
                    # change the angle by a small random amount
                    self.field[i][j] += (vec(uniform(-change, change),
                                             uniform(-change,
                                                     change)) + self.dir)
                    self.field[i][j] = self.field[i][j].normalize()

            # change the general direction
            change2 = 0.5

            self.dir.x += uniform(-change2, change2)
            self.dir.y += uniform(-change2, change2)
            self.dir = self.dir.normalize()
            self.timer = 0

    def change_noise(self):
        self.timer += 1

        if self.timer > 2:
            self.z_off += 0.02
            self.timer = 0

        x_off = self.z_off
        for i in range(self.rows):
            y_off = self.z_off
            for j in range(self.cols):
                n = noise.pnoise2(x_off, y_off)
                theta = remap(n, -1, 1, 0, math.pi * 2)
                self.field[i][j] = vec(math.cos(theta), math.sin(theta))
                y_off += 0.1
            x_off += 0.1

# ------ SPRITES --------------------------------------------------------------


class Vehicle(pg.sprite.Sprite):
    def __init__(self, game, size, pos):
        groups = game.all_sprites, game.vehicles
        self._layer = size[0]
        super().__init__(groups)

        # for g in self.groups:
        #     g.add(self, layer=self.layer)
        self.game = game
        self.size = size
        self.pos = vec(pos)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.steer = vec(0, 0)
        self.desired = vec(0, 0)
        self.extent = vec(0, 0)
        self.target = vec(0, 0)

        self.maxspeed = self.size[0] * 0.3
        self.maxforce = uniform(0.05, 0.15)
        self.theta = 0

        self.clock = 0
        self.particle_interval = 2
        self.particle_vanishing_rate = 15

        self.image = pg.Surface(self.size, pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.rect = self.image.get_rect()

        hue = remap(self.maxspeed, 0, 15, 100, 240)
        self.color = (hue, hue, hue)  # huehuehue

        pg.draw.polygon(self.image, self.color, (self.rect.bottomleft,
                                                 self.rect.midtop,
                                                 self.rect.bottomright))
        self.normal_image = self.image
        self.points_visited = []
        self.target_index = 0

    def update(self):
        self.clock += 1
        if MODE == 'wander':
            self.wander()
        elif MODE == 'follow':
            self.follow()
        elif MODE == 'arrive':
            self.arrive(vec(pg.mouse.get_pos()))
        elif MODE == 'path' and len(self.game.path) >= 1:
            self.seek_points()

        self.vel += self.acc
        limit(self.vel, self.maxspeed)  # TODO: incorporate friction!
        self.pos += self.vel
        self.acc *= 0

        # manage screen wrapping
        if self.pos.x < 0:
            self.pos.x = WIDTH
        elif self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT
        elif self.pos.y > HEIGHT:
            self.pos.y = 0

        # rotate image in the direction of velocity
        angle = self.vel.angle_to(vec(0, -1))
        self.image = pg.transform.rotate(self.normal_image, angle)
        self.rect = self.image.get_rect()

        self.rect.center = self.pos

        # create some particles for visual appeal
        self.emit_particle()

    def wander(self):
        self.arrive(self.target)

        if self.vel.length_squared() != 0:
            # extent vector as a multiple of the velocity
            self.extent = self.vel.normalize() * 80
            # radius
            r = 30
            # change the angle by a small random amount each frame
            self.theta += randrange(-2, 3) / 16
            self.target = self.pos + self.extent + vec(
                r * math.cos(self.theta),
                r * math.sin(self.theta))

    def seek(self, target):
        # get vector from self to target
        self.desired = target - self.pos
        self.desired = self.desired.normalize()

        self.desired *= self.maxspeed

        # calculate steering force
        self.steer = self.desired - self.vel
        limit(self.steer, self.maxforce)

        self.acc += self.steer

    def seek_points(self):
        target = self.game.path[self.target_index]
        self.seek(target)
        d = target - self.pos
        if d.length() < 40:
            self.target_index += 1
            if self.target_index == len(self.game.path):
                self.target_index = 0

    def arrive(self, target):
        # get vector from self to target
        self.desired = target - self.pos
        d = self.desired.length()
        self.desired = self.desired.normalize()

        radius = 100

        if d < radius:
            m = remap(d, 0, radius, 0, self.maxspeed)
            self.desired *= m

        else:
            self.desired *= self.maxspeed

        # calculate steering force
        self.steer = self.desired - self.vel
        limit(self.steer, self.maxforce)

        self.acc += self.steer

    def follow(self):
        desired = self.game.flowfield.lookup(self.pos)
        desired *= self.maxspeed

        steer = desired - self.vel
        limit(steer, self.maxforce)
        self.acc += steer

    def separate(self, vehicles):
        # separates from all other vehicles within a certain range
        desiredseparation = self.size[0] * 4
        v_sum = vec()
        count = 0
        for other in vehicles:
            d = self.pos.distance_to(other.pos)
            if 0 < d < desiredseparation:
                diff = self.pos - other.pos
                diff = diff.normalize()
                diff /= d
                v_sum += diff
                count += 1

        if count > 0:
            v_sum /= count
            v_sum = v_sum.normalize()
            v_sum *= self.maxspeed
            steer = v_sum - self.vel
            limit(steer, self.maxforce)
            self.acc += steer

    def emit_particle(self):
        if self.clock >= self.particle_interval:
            self.clock = 0
            Particle(self.game, self.pos, self.size[0] / 3,
                     self.particle_vanishing_rate)


class Particle(pg.sprite.Sprite):
    def __init__(self, game, pos, diameter, vanishing_rate):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self)
        self.layer = -1
        self.groups.add(self, layer=self.layer)
        self.game = game
        self.pos = vec(pos)

        self.image = pg.Surface((diameter, diameter))
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()

        pg.draw.ellipse(self.image, (255, 100, 0), self.rect)
        self.alpha = 255
        self.vanishing_rate = vanishing_rate

        self.rect.center = self.pos

    def update(self):
        self.rect.center = self.pos

        self.image.set_alpha(self.alpha)

        self.alpha -= self.vanishing_rate
        if self.alpha <= 0:
            self.kill()


# ------ MAIN -----------------------------------------------------------------

def run():
    g = Game()
    try:
        while g.running:
            g.new()
    except Exception:
        traceback.print_exc()
        pg.quit()

    pg.quit()


if __name__ == '__main__':
    run()
